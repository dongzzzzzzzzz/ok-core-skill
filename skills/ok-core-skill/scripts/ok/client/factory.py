"""OK client factory: pick Bridge, CDP, or Playwright (in that order)."""

from __future__ import annotations

import logging
import os

from .base import BaseClient
from .bridge import BRIDGE_PORT, BridgeClient
from .cdp_client import CdpClient, CdpConnectionError

logger = logging.getLogger("ok-client-factory")

# 全局单例
_client_instance: BaseClient | None = None

_ENV_CDP_URL = "OK_CDP_URL"
_ENV_CDP_STRICT = "OK_CDP_STRICT"


def _cdp_strict_enabled() -> bool:
    v = os.environ.get(_ENV_CDP_STRICT, "").strip().lower()
    return v in ("1", "true", "yes", "on")


def get_client() -> BaseClient:
    """获取一个可用的 BaseClient"""
    global _client_instance
    if _client_instance:
        return _client_instance

    logger.debug("正在检测客户端运行环境方案...")

    # 1. 尝试检测本地 Extension 桥接是否存在
    bridge_client = BridgeClient(port=BRIDGE_PORT, timeout=3.0)
    try:
        connected = bridge_client.ping()
        if connected:
            logger.debug(
                "Bridge OK: using Chrome extension client.",
            )
            bridge_client.timeout = 90.0
            _client_instance = bridge_client
            return _client_instance
    except Exception:
        pass

    # 2. CDP: connect to Chrome remote debugging if OK_CDP_URL is set
    cdp_url = os.environ.get(_ENV_CDP_URL, "").strip()
    if cdp_url:
        try:
            cdp_client = CdpClient(cdp_url, connect_timeout_ms=3000.0)
            logger.info("Using CDP client: %s", cdp_url)
            _client_instance = cdp_client
            return _client_instance
        except CdpConnectionError as e:
            if _cdp_strict_enabled():
                logger.error("OK_CDP_STRICT: CDP connection failed: %s", e)
                raise
            logger.info("CDP unavailable, falling back to Playwright: %s", e)
        except Exception as e:
            if _cdp_strict_enabled():
                logger.error("OK_CDP_STRICT: CDP init failed: %s", e)
                raise
            logger.info("CDP init error, falling back to Playwright: %s", e)

    # 3. 自动降级为全静默的 Playwright 无头模式
    logger.info("No bridge/CDP; using headless Playwright.")
    try:
        from .playwright_client import PlaywrightClient

        _client_instance = PlaywrightClient()
        return _client_instance
    except ImportError as e:
        logger.error("初始化 Playwright 失败。请确保按要求安装了依赖 `uv sync` => %s", e)
        raise
