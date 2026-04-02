"""OK.com 搜索帖子"""

from __future__ import annotations

import logging
import time

from . import selectors as sel
from .bridge import BridgeClient
from .errors import OKElementNotFound, OKTimeout
from .human import medium_delay, short_delay
from .locale import build_locale, get_country_info
from .types import Listing, SearchResult
from .urls import build_base_url

logger = logging.getLogger("ok-search")


def search_listings(
    bridge: BridgeClient,
    keyword: str,
    country: str = "singapore",
    city: str = "singapore",
    lang: str = "en",
    max_results: int = 20,
) -> SearchResult:
    """搜索帖子

    Args:
        bridge: BridgeClient 实例
        keyword: 搜索关键词
        country: 国家
        city: 城市 code
        lang: 语言
        max_results: 最大返回结果数

    Returns:
        SearchResult 对象
    """
    locale = build_locale(country, city, lang)

    # 导航到搜索所在城市页面
    base_url = build_base_url(locale.subdomain, locale.lang, locale.city)
    bridge.navigate(base_url)
    bridge.wait_dom_stable()
    medium_delay()

    # 在搜索框输入关键词
    try:
        bridge.wait_for_selector(sel.SEARCH_INPUT, timeout=15000)
    except Exception:
        raise OKElementNotFound("搜索框未找到")

    bridge.click_element(sel.SEARCH_INPUT)
    short_delay()
    bridge.input_text(sel.SEARCH_INPUT, keyword)
    short_delay()

    # 按回车或点击搜索按钮
    bridge.send_command("press_key", {"key": "Enter"})
    medium_delay()

    # 等待搜索结果加载
    bridge.wait_dom_stable(timeout=15000)
    medium_delay()

    # 提取搜索结果
    listings = _extract_listings(bridge, max_results)

    result = SearchResult(
        keyword=keyword,
        total_count=len(listings),
        listings=listings,
        locale=locale,
    )

    logger.info("搜索 '%s' 在 %s/%s: 找到 %d 条结果", keyword, country, city, len(listings))
    return result


def _extract_listings(bridge: BridgeClient, max_results: int = 20) -> list[Listing]:
    """从当前页面提取帖子列表"""
    listings = []

    # 获取列表卡片数量
    count = bridge.get_elements_count(sel.LISTING_CARD)
    if count == 0:
        # 尝试备选选择器
        count = bridge.get_elements_count("a[href*='/cate-']")

    count = min(count, max_results)
    logger.info("页面上找到 %d 个帖子卡片", count)

    for i in range(count):
        try:
            listing = _extract_single_listing(bridge, i)
            if listing:
                listings.append(listing)
        except Exception as e:
            logger.warning("提取第 %d 个帖子失败: %s", i, e)
            continue

    return listings


def _extract_single_listing(bridge: BridgeClient, index: int) -> Listing | None:
    """提取单个帖子信息"""
    # 使用 JS 在主 world 中提取
    js = f"""
    (() => {{
        const cards = document.querySelectorAll("{sel.LISTING_CARD}");
        if (cards.length === 0) {{
            const links = document.querySelectorAll("a[href*='/cate-']");
            if ({index} >= links.length) return null;
            const card = links[{index}];
            return {{
                title: card.textContent?.trim()?.substring(0, 200) || '',
                url: card.href || '',
                price: '',
                location: '',
                image: '',
            }};
        }}
        if ({index} >= cards.length) return null;
        const card = cards[{index}];
        const link = card.querySelector('a') || card.closest('a');
        const titleEl = card.querySelector("{sel.CARD_TITLE}");
        const priceEl = card.querySelector("{sel.CARD_PRICE}");
        const locationEl = card.querySelector("{sel.CARD_LOCATION}");
        const imgEl = card.querySelector("{sel.CARD_IMAGE}");
        return {{
            title: titleEl?.textContent?.trim() || card.textContent?.trim()?.substring(0, 200) || '',
            price: priceEl?.textContent?.trim() || '',
            location: locationEl?.textContent?.trim() || '',
            url: link?.href || '',
            image: imgEl?.src || '',
        }};
    }})()
    """

    result = bridge.evaluate(js)
    if not result:
        return None

    return Listing(
        title=result.get("title", ""),
        price=result.get("price") or None,
        location=result.get("location") or None,
        url=result.get("url") or None,
        image_url=result.get("image") or None,
    )
