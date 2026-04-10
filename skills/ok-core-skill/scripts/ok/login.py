"""OK.com 登录检测与状态管理"""

from __future__ import annotations

import logging

from . import selectors as sel
from .client.base import BaseClient
from .errors import OKNotLoggedIn

logger = logging.getLogger("ok-login")


def check_login(bridge: BaseClient) -> dict:
    """检查登录状态

    Returns:
        {"logged_in": bool, "user_name": str | None}
    """
    # 检查是否存在用户头像或用户名元素
    has_avatar = bridge.has_element(sel.USER_AVATAR)
    user_name = None

    if has_avatar:
        user_name = bridge.get_element_text(sel.USER_NAME)

    result = {
        "logged_in": has_avatar,
        "user_name": user_name,
    }

    if has_avatar:
        logger.info("已登录: %s", user_name or "(未获取到用户名)")
    else:
        logger.info("未登录")

    return result


def require_login(bridge: BaseClient) -> dict:
    """要求登录状态，未登录则抛出异常"""
    status = check_login(bridge)
    if not status["logged_in"]:
        raise OKNotLoggedIn("未登录，请先在浏览器中登录 ok.com")
    return status
