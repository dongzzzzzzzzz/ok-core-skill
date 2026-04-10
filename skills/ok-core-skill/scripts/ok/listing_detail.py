"""OK.com 帖子详情获取"""

from __future__ import annotations

import logging

from . import selectors as sel
from .client.base import BaseClient
from .errors import OKElementNotFound, OKNotLoggedIn, OKTimeout
from .human import medium_delay
from .types import ListingDetail

logger = logging.getLogger("ok-listing-detail")


def get_listing_detail(bridge: BaseClient, url: str) -> ListingDetail:
    """进入帖子详情页并提取信息"""
    bridge.navigate(url)
    bridge.wait_dom_stable(timeout=15000)
    medium_delay()

    # 使用 JS 在主 world 中一次性提取所有信息
    js = f"""
    (() => {{
        const title = document.querySelector("{sel.DETAIL_TITLE}")?.textContent?.trim() || '';
        const price = document.querySelector("{sel.DETAIL_PRICE}")?.textContent?.trim() || '';
        const desc = document.querySelector("{sel.DETAIL_DESCRIPTION}")?.textContent?.trim() || '';
        const seller = document.querySelector("{sel.DETAIL_SELLER}")?.textContent?.trim() || '';
        const location = document.querySelector("{sel.DETAIL_LOCATION}")?.textContent?.trim() || '';
        const time = document.querySelector("{sel.DETAIL_TIME}")?.textContent?.trim() || '';

        // 获取图片
        const imgEls = document.querySelectorAll("{sel.DETAIL_IMAGES}");
        const images = Array.from(imgEls).map(img => img.src).filter(Boolean);

        // 获取分类面包屑
        const breadcrumbs = document.querySelectorAll("{sel.DETAIL_CATEGORY}");
        const category = Array.from(breadcrumbs).map(a => a.textContent?.trim()).filter(Boolean).join(' > ');

        return {{
            title, price, description: desc, seller, location,
            time, images, category,
        }};
    }})()
    """

    result = bridge.evaluate(js)
    if not result or not result.get("title"):
        raise OKElementNotFound("帖子详情提取失败，可能页面未正确加载")

    detail = ListingDetail(
        title=result.get("title", ""),
        price=result.get("price") or None,
        description=result.get("description") or None,
        location=result.get("location") or None,
        seller_name=result.get("seller") or None,
        images=result.get("images", []),
        url=url,
        category=result.get("category") or None,
        posted_time=result.get("time") or None,
    )

    logger.info("获取帖子详情: %s", detail.title[:50])
    return detail


def get_listing_detail_from_page(bridge: BaseClient) -> ListingDetail:
    """从当前页面提取帖子详情"""
    url = bridge.get_url()

    js = f"""
    (() => {{
        const title = document.querySelector("{sel.DETAIL_TITLE}")?.textContent?.trim() || '';
        const price = document.querySelector("{sel.DETAIL_PRICE}")?.textContent?.trim() || '';
        const desc = document.querySelector("{sel.DETAIL_DESCRIPTION}")?.textContent?.trim() || '';
        const seller = document.querySelector("{sel.DETAIL_SELLER}")?.textContent?.trim() || '';
        const location = document.querySelector("{sel.DETAIL_LOCATION}")?.textContent?.trim() || '';
        const time = document.querySelector("{sel.DETAIL_TIME}")?.textContent?.trim() || '';
        const imgEls = document.querySelectorAll("{sel.DETAIL_IMAGES}");
        const images = Array.from(imgEls).map(img => img.src).filter(Boolean);
        const breadcrumbs = document.querySelectorAll("{sel.DETAIL_CATEGORY}");
        const category = Array.from(breadcrumbs).map(a => a.textContent?.trim()).filter(Boolean).join(' > ');
        return {{
            title, price, description: desc, seller, location,
            time, images, category,
        }};
    }})()
    """

    result = bridge.evaluate(js)
    if not result:
        raise OKElementNotFound("帖子详情提取失败")

    return ListingDetail(
        title=result.get("title", ""),
        price=result.get("price") or None,
        description=result.get("description") or None,
        location=result.get("location") or None,
        seller_name=result.get("seller") or None,
        images=result.get("images", []),
        url=url,
        category=result.get("category") or None,
        posted_time=result.get("time") or None,
    )
