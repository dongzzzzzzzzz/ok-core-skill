"""OK client factory — zero-config four-level detection.

Detection order (each level falls through on failure):
  1. Bridge   — Chrome extension + bridge_server.py
  2. CDP detect — probe localhost:9222-9224 for an existing debug session
  3. CDP launch — auto-start Chrome with --remote-debugging-port
  4. Playwright — headless with persistent context (always works)
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

from .base import BaseClient
from .bridge import BRIDGE_PORT, BridgeClient
from .cdp_client import CdpClient, CdpConnectionError

logger = logging.getLogger("ok-client-factory")

# ── singleton ────────────────────────────────────────────────────────────────
_client_instance: BaseClient | None = None

# ── env vars ─────────────────────────────────────────────────────────────────
_ENV_CDP_URL = "OK_CDP_URL"
_ENV_CDP_STRICT = "OK_CDP_STRICT"
_ENV_NO_AUTO_LAUNCH = "OK_NO_AUTO_LAUNCH"
_ENV_HEADLESS = "OK_HEADLESS"

# ── constants ────────────────────────────────────────────────────────────────
_CDP_PROBE_PORTS = (9222, 9223, 9224)
_CDP_PROBE_TIMEOUT = 1.5
_OK_AGENT_DIR = Path.home() / ".ok-agent"
_CHROME_PROFILE_DIR = _OK_AGENT_DIR / "chrome-profile"
_CHROME_STARTUP_WAIT = 8.0  # seconds to wait for Chrome to be ready
_CHROME_STARTUP_POLL = 0.4

# ── helpers ──────────────────────────────────────────────────────────────────

def _env_flag(name: str) -> bool:
    v = os.environ.get(name, "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _discover_cdp_url() -> str | None:
    """Probe common ports for an existing Chrome debug endpoint."""
    for port in _CDP_PROBE_PORTS:
        url = f"http://127.0.0.1:{port}"
        try:
            req = urllib.request.Request(f"{url}/json/version", method="GET")
            with urllib.request.urlopen(req, timeout=_CDP_PROBE_TIMEOUT):
                logger.info("Auto-detected CDP on port %d", port)
                return url
        except Exception:
            continue
    return None


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _pick_free_port() -> int | None:
    for port in _CDP_PROBE_PORTS:
        if _port_is_free(port):
            return port
    return None


# ── Level 3: Chrome finder & launcher ────────────────────────────────────────

_MACOS_CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)

_LINUX_CHROME_NAMES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium-browser",
    "chromium",
)


def _find_chrome_executable() -> str | None:
    """Locate a Chrome/Chromium executable on the current system."""
    system = platform.system()

    if system == "Darwin":
        for p in _MACOS_CHROME_PATHS:
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p
        found = shutil.which("google-chrome") or shutil.which("chromium")
        return found

    if system == "Linux":
        for name in _LINUX_CHROME_NAMES:
            found = shutil.which(name)
            if found:
                return found
        return None

    # Windows or unknown — best effort
    found = shutil.which("chrome") or shutil.which("chromium")
    return found


_chrome_process: subprocess.Popen | None = None


def _launch_chrome_with_cdp() -> str | None:
    """Start a headed Chrome with a persistent profile and debugging port.

    Returns the CDP base URL (e.g. ``http://127.0.0.1:9222``) on success,
    or *None* if Chrome could not be found or started.
    """
    global _chrome_process

    chrome = _find_chrome_executable()
    if not chrome:
        logger.info("Chrome executable not found; skipping auto-launch.")
        return None

    port = _pick_free_port()
    if port is None:
        logger.info("No free port in %s for CDP; skipping auto-launch.", _CDP_PROBE_PORTS)
        return None

    _CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    args = [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={_CHROME_PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-client-side-phishing-detection",
        "--disable-default-apps",
        "--disable-hang-monitor",
        "--disable-popup-blocking",
        "--disable-sync",
        "--metrics-recording-only",
    ]

    try:
        _chrome_process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as e:
        logger.info("Failed to launch Chrome (%s); skipping.", e)
        return None

    cdp_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + _CHROME_STARTUP_WAIT

    while time.monotonic() < deadline:
        if _chrome_process.poll() is not None:
            logger.info(
                "Chrome exited immediately (code %d); skipping.",
                _chrome_process.returncode,
            )
            _chrome_process = None
            return None
        try:
            req = urllib.request.Request(f"{cdp_url}/json/version", method="GET")
            with urllib.request.urlopen(req, timeout=1.0):
                logger.info(
                    "Chrome auto-launched on port %d (profile: %s)",
                    port, _CHROME_PROFILE_DIR,
                )
                return cdp_url
        except Exception:
            time.sleep(_CHROME_STARTUP_POLL)

    logger.info("Chrome started but CDP not ready within %.1fs; skipping.", _CHROME_STARTUP_WAIT)
    _terminate_chrome()
    return None


def _terminate_chrome() -> None:
    global _chrome_process
    if _chrome_process is None:
        return
    import contextlib

    try:
        _chrome_process.terminate()
        _chrome_process.wait(timeout=5)
    except Exception:
        with contextlib.suppress(Exception):
            _chrome_process.kill()
    _chrome_process = None


# ── public API ───────────────────────────────────────────────────────────────

def get_client() -> BaseClient:
    """Return an available BaseClient (singleton).

    Detection order:
      1. Bridge (Chrome extension + bridge_server.py)
      2. CDP detect — explicit OK_CDP_URL env, or auto-detect ports
      3. CDP launch — auto-start Chrome with persistent profile
      4. Playwright headless with persistent context
    """
    global _client_instance
    if _client_instance:
        return _client_instance

    logger.debug("Detecting client environment...")

    # --- Level 1: Bridge ---
    bridge_client = BridgeClient(port=BRIDGE_PORT, timeout=3.0)
    try:
        if bridge_client.ping():
            logger.info("Bridge OK: using Chrome extension client.")
            bridge_client.timeout = 90.0
            _client_instance = bridge_client
            return _client_instance
    except Exception:
        pass

    # --- Level 2: CDP detect ---
    cdp_url = os.environ.get(_ENV_CDP_URL, "").strip()
    if not cdp_url:
        cdp_url = _discover_cdp_url() or ""

    if cdp_url:
        client = _try_cdp_connect(cdp_url)
        if client:
            return client

    # --- Level 3: CDP auto-launch ---
    if not _env_flag(_ENV_NO_AUTO_LAUNCH) and not _env_flag(_ENV_HEADLESS):
        launched_url = _launch_chrome_with_cdp()
        if launched_url:
            client = _try_cdp_connect(launched_url)
            if client:
                return client

    # --- Level 4: Playwright headless persistent ---
    logger.info("No bridge/CDP; using headless Playwright (persistent).")
    try:
        from .playwright_client import PlaywrightClient

        _client_instance = PlaywrightClient()
        return _client_instance
    except ImportError as e:
        logger.error("Playwright unavailable. Run `uv sync` first: %s", e)
        raise


def _try_cdp_connect(cdp_url: str) -> BaseClient | None:
    """Attempt CDP connection; return client or None (respects STRICT mode)."""
    global _client_instance
    try:
        cdp_client = CdpClient(cdp_url, connect_timeout_ms=3000.0)
        logger.info("Using CDP client: %s", cdp_url)
        _client_instance = cdp_client
        return _client_instance
    except CdpConnectionError as e:
        if _env_flag(_ENV_CDP_STRICT):
            raise
        logger.info("CDP unavailable (%s), falling back.", e)
    except Exception as e:
        if _env_flag(_ENV_CDP_STRICT):
            raise
        logger.info("CDP init error (%s), falling back.", e)
    return None


def shutdown() -> None:
    """Clean up any resources held by the factory (e.g. auto-launched Chrome)."""
    global _client_instance
    _client_instance = None
    _terminate_chrome()
