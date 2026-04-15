"""get_client() four-level detection: Bridge -> CDP detect -> CDP launch -> Playwright"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import ok.client.factory as factory
import pytest
from ok.client.cdp_client import CdpConnectionError


@pytest.fixture(autouse=True)
def _reset_singleton():
    factory._client_instance = None
    factory._chrome_process = None
    yield
    factory._client_instance = None
    factory._chrome_process = None


def _make_bridge(ping: bool) -> MagicMock:
    m = MagicMock()
    m.ping.return_value = ping
    return m


# ── Level 1: Bridge ─────────────────────────────────────────────────────────


@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_prefers_bridge_when_ping_succeeds(mock_bridge_cls, _cdp, _pw):
    mock_bridge_cls.return_value = _make_bridge(True)
    client = factory.get_client()
    assert client is mock_bridge_cls.return_value
    _cdp.assert_not_called()
    _pw.assert_not_called()


# ── Level 2: CDP detect (env var / auto-discover) ───────────────────────────


@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_cdp_with_env_var(mock_bridge_cls, mock_cdp_cls, _pw, monkeypatch):
    monkeypatch.setenv("OK_CDP_URL", "http://127.0.0.1:9222")
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_cdp_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_cdp_cls.return_value
    _pw.assert_not_called()


@patch("ok.client.factory._discover_cdp_url", return_value="http://127.0.0.1:9222")
@patch("ok.client.factory._launch_chrome_with_cdp")
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_auto_detect_cdp_when_no_env_var(
    mock_bridge_cls, mock_cdp_cls, _pw, _launch, _discover, monkeypatch,
):
    monkeypatch.delenv("OK_CDP_URL", raising=False)
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_cdp_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_cdp_cls.return_value
    mock_cdp_cls.assert_called_once_with(
        "http://127.0.0.1:9222", connect_timeout_ms=3000.0,
    )
    _launch.assert_not_called()


@patch("ok.client.factory._discover_cdp_url")
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_env_var_takes_priority_over_auto_detect(
    mock_bridge_cls, mock_cdp_cls, _pw, mock_discover, monkeypatch,
):
    monkeypatch.setenv("OK_CDP_URL", "http://127.0.0.1:9999")
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_cdp_cls.return_value = MagicMock()

    factory.get_client()
    mock_cdp_cls.assert_called_once_with(
        "http://127.0.0.1:9999", connect_timeout_ms=3000.0,
    )
    mock_discover.assert_not_called()


@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_cdp_strict_raises_on_connection_error(
    mock_bridge_cls, mock_cdp_cls, _pw, monkeypatch,
):
    monkeypatch.setenv("OK_CDP_URL", "http://127.0.0.1:9222")
    monkeypatch.setenv("OK_CDP_STRICT", "1")
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_cdp_cls.side_effect = CdpConnectionError("refused")

    with pytest.raises(CdpConnectionError):
        factory.get_client()


# ── Level 3: CDP auto-launch ────────────────────────────────────────────────


@patch("ok.client.factory._discover_cdp_url", return_value=None)
@patch("ok.client.factory._launch_chrome_with_cdp", return_value="http://127.0.0.1:9222")
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_auto_launch_when_no_existing_cdp(
    mock_bridge_cls, mock_cdp_cls, _pw, mock_launch, _discover, monkeypatch,
):
    """Level 2 finds nothing -> Level 3 launches Chrome -> CDP connects."""
    monkeypatch.delenv("OK_CDP_URL", raising=False)
    monkeypatch.delenv("OK_NO_AUTO_LAUNCH", raising=False)
    monkeypatch.delenv("OK_HEADLESS", raising=False)
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_cdp_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_cdp_cls.return_value
    mock_launch.assert_called_once()
    _pw.assert_not_called()


@patch("ok.client.factory._discover_cdp_url", return_value=None)
@patch("ok.client.factory._launch_chrome_with_cdp", return_value="http://127.0.0.1:9222")
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_auto_launch_cdp_fail_falls_to_playwright(
    mock_bridge_cls, mock_cdp_cls, mock_pw_cls, mock_launch, _discover, monkeypatch,
):
    """Level 3 launches Chrome but CdpClient connect fails -> Level 4."""
    monkeypatch.delenv("OK_CDP_URL", raising=False)
    monkeypatch.delenv("OK_CDP_STRICT", raising=False)
    monkeypatch.delenv("OK_NO_AUTO_LAUNCH", raising=False)
    monkeypatch.delenv("OK_HEADLESS", raising=False)
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_cdp_cls.side_effect = CdpConnectionError("refused")
    mock_pw_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_pw_cls.return_value


@patch("ok.client.factory._discover_cdp_url", return_value=None)
@patch("ok.client.factory._launch_chrome_with_cdp")
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_no_auto_launch_env_skips_level3(
    mock_bridge_cls, _cdp, mock_pw_cls, mock_launch, _discover, monkeypatch,
):
    """OK_NO_AUTO_LAUNCH=1 -> skip Level 3 entirely."""
    monkeypatch.delenv("OK_CDP_URL", raising=False)
    monkeypatch.setenv("OK_NO_AUTO_LAUNCH", "1")
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_pw_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_pw_cls.return_value
    mock_launch.assert_not_called()


@patch("ok.client.factory._discover_cdp_url", return_value=None)
@patch("ok.client.factory._launch_chrome_with_cdp")
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_headless_env_skips_level3(
    mock_bridge_cls, _cdp, mock_pw_cls, mock_launch, _discover, monkeypatch,
):
    """OK_HEADLESS=1 -> skip Level 3 entirely."""
    monkeypatch.delenv("OK_CDP_URL", raising=False)
    monkeypatch.delenv("OK_NO_AUTO_LAUNCH", raising=False)
    monkeypatch.setenv("OK_HEADLESS", "1")
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_pw_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_pw_cls.return_value
    mock_launch.assert_not_called()


@patch("ok.client.factory._discover_cdp_url", return_value=None)
@patch("ok.client.factory._launch_chrome_with_cdp", return_value=None)
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_auto_launch_returns_none_falls_to_playwright(
    mock_bridge_cls, _cdp, mock_pw_cls, mock_launch, _discover, monkeypatch,
):
    """Level 3 cannot launch Chrome (no executable) -> Level 4."""
    monkeypatch.delenv("OK_CDP_URL", raising=False)
    monkeypatch.delenv("OK_NO_AUTO_LAUNCH", raising=False)
    monkeypatch.delenv("OK_HEADLESS", raising=False)
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_pw_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_pw_cls.return_value
    mock_launch.assert_called_once()


# ── Level 4: Playwright fallback ────────────────────────────────────────────


@patch("ok.client.factory._discover_cdp_url", return_value=None)
@patch("ok.client.factory._launch_chrome_with_cdp", return_value=None)
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_playwright_fallback_full_chain(
    mock_bridge_cls, _cdp, mock_pw_cls, _launch, _discover, monkeypatch,
):
    """All three levels fail -> Playwright persistent fallback."""
    monkeypatch.delenv("OK_CDP_URL", raising=False)
    monkeypatch.delenv("OK_NO_AUTO_LAUNCH", raising=False)
    monkeypatch.delenv("OK_HEADLESS", raising=False)
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_pw_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_pw_cls.return_value


@patch("ok.client.factory._discover_cdp_url", return_value="http://127.0.0.1:9223")
@patch("ok.client.factory._launch_chrome_with_cdp")
@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_detect_cdp_fail_falls_to_playwright_not_strict(
    mock_bridge_cls, mock_cdp_cls, mock_pw_cls,
    mock_launch, _discover, monkeypatch,
):
    """Level 2 detects but connect fails (not strict) -> Level 3 -> Level 4."""
    monkeypatch.delenv("OK_CDP_URL", raising=False)
    monkeypatch.delenv("OK_CDP_STRICT", raising=False)
    monkeypatch.delenv("OK_NO_AUTO_LAUNCH", raising=False)
    monkeypatch.delenv("OK_HEADLESS", raising=False)
    mock_bridge_cls.return_value = _make_bridge(False)
    mock_cdp_cls.side_effect = CdpConnectionError("refused")
    mock_launch.return_value = None
    mock_pw_cls.return_value = MagicMock()

    client = factory.get_client()
    assert client is mock_pw_cls.return_value


# ── _find_chrome_executable unit tests ──────────────────────────────────────


class TestFindChromeExecutable:
    @patch("platform.system", return_value="Darwin")
    @patch("os.path.isfile", return_value=True)
    @patch("os.access", return_value=True)
    def test_macos_finds_system_chrome(self, _access, _isfile, _sys):
        result = factory._find_chrome_executable()
        assert result == factory._MACOS_CHROME_PATHS[0]

    @patch("platform.system", return_value="Darwin")
    @patch("os.path.isfile", return_value=False)
    @patch("shutil.which", return_value=None)
    def test_macos_no_chrome(self, _which, _isfile, _sys):
        result = factory._find_chrome_executable()
        assert result is None

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value="/usr/bin/google-chrome")
    def test_linux_finds_chrome(self, _which, _sys):
        result = factory._find_chrome_executable()
        assert result == "/usr/bin/google-chrome"

    @patch("platform.system", return_value="Linux")
    @patch("shutil.which", return_value=None)
    def test_linux_no_chrome(self, _which, _sys):
        result = factory._find_chrome_executable()
        assert result is None


# ── _port_is_free / _pick_free_port ─────────────────────────────────────────


def test_port_is_free_returns_bool():
    result = factory._port_is_free(0)
    assert isinstance(result, bool)


# ── shutdown ────────────────────────────────────────────────────────────────


def test_shutdown_clears_singleton():
    factory._client_instance = MagicMock()
    factory.shutdown()
    assert factory._client_instance is None


@patch("ok.client.factory._terminate_chrome")
def test_shutdown_terminates_chrome(mock_term):
    factory._client_instance = MagicMock()
    factory.shutdown()
    mock_term.assert_called_once()
