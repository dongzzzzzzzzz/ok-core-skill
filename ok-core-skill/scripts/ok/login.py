"""OK.com 登录检测与登录操作"""

from __future__ import annotations

import logging
import time

from . import selectors as sel
from .client.base import BaseClient
from .errors import OKElementNotFound, OKNotLoggedIn, OKTimeout
from .human import medium_delay, short_delay

logger = logging.getLogger("ok-login")


# ─── 登录状态检测 ─────────────────────────────────────────


def check_login(bridge: BaseClient) -> dict:
    """检查登录状态

    Returns:
        {"logged_in": bool, "user_name": str | None}
    """
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


# ─── 登录弹窗操作 ─────────────────────────────────────────


def _open_login_modal(bridge: BaseClient) -> None:
    """点击 'Log in / Register' 按钮打开登录弹窗"""
    if not bridge.has_element(sel.LOGIN_TRIGGER):
        raise OKElementNotFound("找不到登录按钮，可能已登录或页面未正确加载")

    bridge.click_element(sel.LOGIN_TRIGGER)
    short_delay()

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if bridge.has_element(sel.LOGIN_MODAL):
            return
        time.sleep(0.3)

    raise OKTimeout("登录弹窗未出现")


def _close_login_modal(bridge: BaseClient) -> None:
    """关闭登录弹窗"""
    if bridge.has_element(sel.LOGIN_MODAL_CLOSE):
        bridge.click_element(sel.LOGIN_MODAL_CLOSE)
        short_delay()


def _dismiss_cookie_banner(bridge: BaseClient) -> None:
    """关闭 Cookie 横幅（如果存在）"""
    if bridge.has_element(sel.COOKIE_ACCEPT_BTN):
        bridge.click_element(sel.COOKIE_ACCEPT_BTN)
        short_delay()


def _fill_email(bridge: BaseClient, email: str) -> None:
    """在登录弹窗中填入邮箱"""
    bridge.wait_for_selector(sel.LOGIN_EMAIL_INPUT, timeout=10000)
    bridge.click_element(sel.LOGIN_EMAIL_INPUT)
    short_delay()

    bridge.evaluate(f"""
    (() => {{
        const input = document.querySelector("{sel.LOGIN_EMAIL_INPUT}");
        if (!input) return;
        const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        setter.call(input, '');
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        setter.call(input, '{email}');
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
    }})()
    """)
    short_delay()


def _click_continue(bridge: BaseClient) -> None:
    """点击 Continue 按钮"""
    bridge.wait_for_selector(sel.LOGIN_CONTINUE_BTN, timeout=5000)
    bridge.click_element(sel.LOGIN_CONTINUE_BTN)
    medium_delay()


def _wait_for_password_page(bridge: BaseClient, timeout: float = 10) -> str:
    """等待密码输入页面出现，返回页面类型 'login' 或 'register'

    通过检测页面特征判断：
    - WelcomeTip_welcomeTitle 存在 → 已注册用户，登录页
    - ValidAccount_title 包含 'friend' / 'new' → 新用户，注册页
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        page_type = bridge.evaluate("""
        (() => {
            const modal = document.querySelector("[class*='LoginPC_loginContainer']");
            if (!modal) return '';
            const welcomeTitle = modal.querySelector("[class*='WelcomeTip_welcomeTitle']");
            if (welcomeTitle) return 'login:' + welcomeTitle.textContent.trim();
            const registerTitle = modal.querySelector("[class*='ValidAccount_title']");
            if (registerTitle) {
                const text = registerTitle.textContent.trim().toLowerCase();
                if (text.includes('friend') || text.includes('new') || text.includes('create'))
                    return 'register:' + registerTitle.textContent.trim();
            }
            const pwdInput = modal.querySelector("input[type='password']");
            if (pwdInput) return 'login:(password input found)';
            return '';
        })()
        """)
        if page_type:
            if page_type.startswith("register:"):
                logger.info("检测到注册页面: %s", page_type[9:])
                return "register"
            elif page_type.startswith("login:"):
                logger.info("检测到登录页面: %s", page_type[6:])
                return "login"
        time.sleep(0.3)

    raise OKTimeout("密码输入页面未出现")


def _fill_password_and_submit(bridge: BaseClient, password: str) -> None:
    """在密码页面填入密码并点击提交按钮

    已注册用户登录页和新用户注册页的 DOM 结构不同：
    - 登录页: input[type='password'] with CustomCounterInput class
    - 注册页: .ok_login_input_label_content_input (第二个)
    统一使用 input[type='password'] 定位，兼容两种情况。
    """
    escaped = password.replace("\\", "\\\\").replace("'", "\\'")

    bridge.evaluate(f"""
    (() => {{
        const modal = document.querySelector("[class*='LoginPC_loginContainer']");
        if (!modal) return;
        // 优先找 type=password 的输入框（兼容登录和注册）
        let input = modal.querySelector("input[type='password']");
        if (!input) {{
            // fallback: 找所有文本输入框中的最后一个
            const inputs = modal.querySelectorAll("input");
            input = inputs[inputs.length - 1];
        }}
        if (!input) return;
        input.focus();
        const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        setter.call(input, '');
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        setter.call(input, '{escaped}');
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }})()
    """)
    short_delay()

    # 等待按钮变为可点击状态
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        clicked = bridge.evaluate("""
        (() => {
            const modal = document.querySelector("[class*='LoginPC_loginContainer']");
            if (!modal) return false;
            // 优先找 LoginPC_continueButton（已注册用户的 Log in 按钮）
            let btn = modal.querySelector("[class*='LoginPC_continueButton']");
            if (!btn) {
                // fallback: ValidAccount_loginBtn（注册页的 Register 按钮）
                btn = modal.querySelector("[class*='ValidAccount_loginBtn']");
            }
            if (!btn) {
                // 最后兜底：找按钮文字
                const btns = modal.querySelectorAll("button");
                for (const b of btns) {
                    const t = b.textContent.trim().toLowerCase();
                    if (['log in','login','sign in','register'].includes(t)) { btn = b; break; }
                }
            }
            if (btn && !btn.disabled) { btn.click(); return true; }
            return false;
        })()
        """)
        if clicked:
            break
        time.sleep(0.3)

    medium_delay()


def _wait_for_login_success(bridge: BaseClient, timeout: float = 30) -> bool:
    """等待登录成功（弹窗消失 + 头像出现）"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        modal_exists = bridge.has_element(sel.LOGIN_MODAL)
        if not modal_exists:
            short_delay()
            has_avatar = bridge.has_element(sel.USER_AVATAR)
            if has_avatar:
                logger.info("登录成功")
                return True
            # 弹窗关闭但还没检测到头像，再等一下
        time.sleep(0.5)

    return False


def _get_login_error(bridge: BaseClient) -> str | None:
    """获取登录错误信息"""
    err = bridge.evaluate("""
    (() => {
        const selectors = [
            "[class*='errorMsg']", "[class*='error-msg']",
            "[class*='ErrorTip']", "[class*='errTip']",
            "[class*='LoginPC_loginContainer'] [class*='error']",
        ];
        for (const s of selectors) {
            const el = document.querySelector(s);
            if (el && el.textContent.trim()) return el.textContent.trim();
        }
        return null;
    })()
    """)
    return err


# ─── 对外暴露的登录函数 ─────────────────────────────────────


def login_with_email(
    bridge: BaseClient,
    email: str,
    password: str,
) -> dict:
    """通过邮箱密码登录 OK.com

    完整流程：
    1. 关闭 Cookie 横幅
    2. 点击 'Log in / Register' 打开弹窗
    3. 填入邮箱 → 点击 Continue
    4. 等待密码页面 → 填入密码 → 点击 Login/Register
    5. 等待登录成功

    Args:
        bridge: 浏览器客户端
        email: 邮箱地址
        password: 密码

    Returns:
        {"logged_in": bool, "account_type": "login"|"register", "message": str}
    """
    # 关闭可能存在的 Cookie 横幅
    _dismiss_cookie_banner(bridge)

    # 如果已登录，直接返回
    status = check_login(bridge)
    if status["logged_in"]:
        return {
            "logged_in": True,
            "account_type": "existing",
            "message": f"已登录: {status['user_name'] or '(未知用户)'}",
        }

    # 打开登录弹窗
    _open_login_modal(bridge)
    logger.info("登录弹窗已打开")

    # 填入邮箱并点击 Continue
    _fill_email(bridge, email)
    _click_continue(bridge)
    logger.info("已输入邮箱 %s 并点击 Continue", email)

    # 等待密码页面出现，判断是登录还是注册
    account_type = _wait_for_password_page(bridge)
    logger.info("账号类型: %s", account_type)

    # 填入密码并提交
    _fill_password_and_submit(bridge, password)
    logger.info("已输入密码并提交")

    # 检查是否有错误
    err = _get_login_error(bridge)
    if err:
        logger.warning("登录出错: %s", err)
        return {
            "logged_in": False,
            "account_type": account_type,
            "message": f"登录失败: {err}",
        }

    # 等待登录成功
    success = _wait_for_login_success(bridge, timeout=30)

    if success:
        final_status = check_login(bridge)
        return {
            "logged_in": True,
            "account_type": account_type,
            "user_name": final_status.get("user_name"),
            "message": "登录成功" if account_type == "login" else "注册并登录成功",
        }

    # 再次检查错误
    err = _get_login_error(bridge)
    return {
        "logged_in": False,
        "account_type": account_type,
        "message": f"登录超时{': ' + err if err else ''}",
    }


def wait_for_login(bridge: BaseClient, timeout: float = 120) -> dict:
    """等待用户手动完成登录（用于 OAuth 等场景）

    Agent 引导用户在浏览器中手动操作（如点击 Google 登录），
    此函数轮询检测登录状态直到成功或超时。

    Returns:
        {"logged_in": bool, "message": str}
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        has_avatar = bridge.has_element(sel.USER_AVATAR)
        modal_exists = bridge.has_element(sel.LOGIN_MODAL)

        if has_avatar and not modal_exists:
            user_name = bridge.get_element_text(sel.USER_NAME)
            return {
                "logged_in": True,
                "user_name": user_name,
                "message": "登录成功",
            }
        time.sleep(1)

    return {
        "logged_in": False,
        "message": "等待登录超时",
    }
