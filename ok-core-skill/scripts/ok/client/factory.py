"""OK Client 连接工厂

自动实现环境降级与容错：
如果在有用户的个人机器上运行，并装了插件，会连接插件使用真人环境。
如果在毫无配置的机器或服务器上运行，会自动创建一个静默的隐身无头浏览器。
"""

from __future__ import annotations

import logging
from typing import Type

from .base import BaseClient
from .bridge import BridgeClient, BRIDGE_PORT

logger = logging.getLogger("ok-client-factory")

# 全局单例
_client_instance: BaseClient | None = None


def get_client() -> BaseClient:
    """获取一个可用的 BaseClient"""
    global _client_instance
    if _client_instance:
        return _client_instance

    logger.debug("正在检测客户端运行环境方案...")

    # 1. 尝试检测本地 Extension 桥接是否存在
    bridge_client = BridgeClient(port=BRIDGE_PORT, timeout=3.0)
    try:
        # 使用极短超时判断 9334 连接
        connected = bridge_client.ping()
        if connected:
            logger.debug("✅ 检测到 [Chrome 插件桥接] 环境！将使用用户的原生浏览器进行操作。")
            # 恢复正常操作的超时时间，否则 3.0s 极化设置会波及后续所有请求导致报错
            bridge_client.timeout = 90.0
            _client_instance = bridge_client
            return _client_instance
    except Exception:
        pass

    # 2. 如果不存在，自动降级为全静默的 Playwright 无头模式
    logger.info("⚠️ 未检测到运行中的 Chrome 插件开发桥，降级使用 [Playwright 静默隐身浏览器] 进行操作...")
    try:
        from .playwright_client import PlaywrightClient
        _client_instance = PlaywrightClient()
        return _client_instance
    except ImportError as e:
        logger.error("初始化 Playwright 失败。请确保按要求安装了依赖 `uv sync` => %s", e)
        raise
