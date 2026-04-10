"""OK Playwright Client (Headless Fallback)"""

from __future__ import annotations

import logging
from typing import Any

from playwright.sync_api import sync_playwright, Page, BrowserContext
from playwright_stealth import Stealth

from .base import BaseClient
from .. import cookies as cookie_utils

logger = logging.getLogger("ok-playwright-client")


class PlaywrightClient(BaseClient):
    """
    Playwright 客户端模式。
    使用 stealth 完全绕过机器人检测，并读取/保存本地域名的 Cookies。
    全程无头静默运行，不干扰用户原本屏幕。
    """

    def __init__(self) -> None:
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        self.context: BrowserContext = self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800}
        )

        # 加载持久化 cookie
        saved_cookies = cookie_utils.load_cookies("playwright_fallback")
        if saved_cookies:
            # Playwright 要求 url 域或 domain，我们稍作转换处理
            pw_cookies = []
            for c in saved_cookies:
                c.pop("hostOnly", None)
                c.pop("session", None)
                c.pop("storeId", None)
                if c.get("sameSite") == "no_restriction":
                    c["sameSite"] = "None"
                elif c.get("sameSite") == "unspecified":
                    c.pop("sameSite", None)
                pw_cookies.append(c)
            try:
                self.context.add_cookies(pw_cookies)
            except Exception as e:
                logger.warning("加载 Playwright Cookie 失败: %s", e)

        self.page: Page = self.context.new_page()
        Stealth().apply_stealth_sync(self.page)
        logger.info("Playwright Client 已静默初始化")

    def _save_cookies(self):
        # 将最新的 Cookie 存储下来
        current = self.context.cookies()
        # 将 playwright 格式转为我们之前的插件格式
        cookie_utils.save_cookies(current, "playwright_fallback")

    def navigate(self, url: str) -> None:
        self.page.goto(url, wait_until="commit")

    def wait_for_load(self, timeout: int = 60000) -> None:
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def get_url(self) -> str:
        return self.page.url

    def wait_dom_stable(self, timeout: int = 10000, interval: int = 500) -> None:
        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

    def wait_for_selector(self, selector: str, timeout: int = 30000) -> None:
        self.page.wait_for_selector(selector, timeout=timeout)

    def has_element(self, selector: str) -> bool:
        return self.page.locator(selector).count() > 0

    def get_elements_count(self, selector: str) -> int:
        return self.page.locator(selector).count()

    def get_element_text(self, selector: str) -> str | None:
        loc = self.page.locator(selector).first
        if loc.count() > 0:
            return loc.text_content()
        return None

    def get_element_attribute(self, selector: str, attr: str) -> str | None:
        loc = self.page.locator(selector).first
        if loc.count() > 0:
            return loc.get_attribute(attr)
        return None

    def click_element(self, selector: str) -> None:
        self.page.locator(selector).first.click()

    def input_text(self, selector: str, text: str) -> None:
        # Playwright 的 fill 会自动处理 React 受控组件
        self.page.locator(selector).first.fill(text)

    def scroll_by(self, x: int = 0, y: int = 0) -> None:
        self.page.evaluate(f"window.scrollBy({x}, {y})")

    def scroll_to_bottom(self) -> None:
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def scroll_element_into_view(self, selector: str) -> None:
        loc = self.page.locator(selector).first
        if loc.count() > 0:
            loc.scroll_into_view_if_needed()

    def evaluate(self, expression: str) -> Any:
        return self.page.evaluate(expression)

    def send_command(self, method: str, params: dict | None = None) -> Any:
        # Fallback 兼容
        if method == "press_key":
            key = params.get("key")
            self.page.keyboard.press(key)
        elif method == "get_cookies":
            return self.context.cookies()
        else:
            logger.warning("Playwright 客户端暂未实现底层命令: %s", method)

    def __del__(self):
        try:
            self._save_cookies()
            self.context.close()
            self.browser.close()
            self.playwright.stop()
        except:
            pass
