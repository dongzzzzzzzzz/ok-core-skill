#!/usr/bin/env python3
"""OK.com 自动化 CLI

统一命令行入口，所有功能通过子命令调用，输出 JSON 格式。

使用方式：
    python scripts/cli.py <子命令> [参数]

示例：
    python scripts/cli.py list-countries
    python scripts/cli.py list-cities --country singapore
    python scripts/cli.py list-categories --country singapore
    python scripts/cli.py set-locale --country singapore --city singapore --lang en
    python scripts/cli.py search --keyword "laptop" --country singapore --city singapore
    python scripts/cli.py list-feeds --country singapore --city singapore
    python scripts/cli.py get-listing --url "https://sg.ok.com/en/city-singapore/cate-xxx/slug/"
    python scripts/cli.py browse-category --category marketplace --country singapore --city singapore
    python scripts/cli.py check-login
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

# 将 scripts/ 加入搜索路径
sys.path.insert(0, str(Path(__file__).parent))

from ok.bridge import BridgeClient, ensure_bridge_server
from ok.errors import OKError


def _output(data, exit_code: int = 0):
    """输出 JSON 并退出"""
    print(json.dumps(data, ensure_ascii=False, indent=2))
    sys.exit(exit_code)


def _error(message: str, exit_code: int = 2):
    """输出错误并退出"""
    _output({"error": message}, exit_code)


# ─── 子命令实现 ─────────────────────────────────────────────

def cmd_list_countries(args):
    """列出支持的国家"""
    from ok.locale import list_countries
    _output({"countries": list_countries()})


def cmd_list_cities(args):
    """动态获取指定国家的城市列表"""
    from ok.locale import fetch_cities
    cities = fetch_cities(args.country, args.lang)
    _output({
        "country": args.country,
        "total": len(cities),
        "cities": [{"name": c.name, "code": c.code, "local_id": c.local_id} for c in cities],
    })


def cmd_list_categories(args):
    """动态获取分类树"""
    from ok.locale import fetch_categories

    def cat_to_dict(cat):
        d = {"name": cat.name, "code": cat.code, "category_id": cat.category_id}
        if cat.children:
            d["children"] = [cat_to_dict(c) for c in cat.children]
        return d

    categories = fetch_categories(args.country, args.lang)
    _output({
        "country": args.country,
        "total": len(categories),
        "categories": [cat_to_dict(c) for c in categories],
    })


def cmd_set_locale(args):
    """设置 locale（导航到指定国家/城市）"""
    ensure_bridge_server()
    bridge = BridgeClient()
    from ok.locale import navigate_to_locale
    locale = navigate_to_locale(bridge, args.country, args.city, args.lang)
    _output({"locale": asdict(locale), "url": locale.base_url()})


def cmd_get_locale(args):
    """获取当前 locale"""
    ensure_bridge_server()
    bridge = BridgeClient()
    from ok.locale import get_current_locale
    locale = get_current_locale(bridge)
    if locale:
        _output({"locale": asdict(locale), "url": locale.base_url()})
    else:
        _output({"locale": None, "message": "当前页面非 ok.com"})


def cmd_search(args):
    """搜索帖子"""
    ensure_bridge_server()
    bridge = BridgeClient()
    from ok.search import search_listings
    result = search_listings(
        bridge,
        keyword=args.keyword,
        country=args.country,
        city=args.city,
        lang=args.lang,
        max_results=args.max_results,
    )
    _output({
        "keyword": result.keyword,
        "total": result.total_count,
        "listings": [asdict(l) for l in result.listings],
    })


def cmd_list_feeds(args):
    """获取首页推荐"""
    ensure_bridge_server()
    bridge = BridgeClient()
    from ok.feeds import list_feeds
    listings = list_feeds(
        bridge,
        country=args.country,
        city=args.city,
        lang=args.lang,
        max_results=args.max_results,
    )
    _output({
        "total": len(listings),
        "listings": [asdict(l) for l in listings],
    })


def cmd_get_listing(args):
    """获取帖子详情"""
    ensure_bridge_server()
    bridge = BridgeClient()
    from ok.listing_detail import get_listing_detail
    detail = get_listing_detail(bridge, args.url)
    _output(asdict(detail))


def cmd_browse_category(args):
    """按分类浏览"""
    ensure_bridge_server()
    bridge = BridgeClient()
    from ok.categories import browse_category
    listings = browse_category(
        bridge,
        category_code=args.category,
        country=args.country,
        city=args.city,
        lang=args.lang,
        max_results=args.max_results,
    )
    _output({
        "category": args.category,
        "total": len(listings),
        "listings": [asdict(l) for l in listings],
    })


def cmd_check_login(args):
    """检查登录状态"""
    ensure_bridge_server()
    bridge = BridgeClient()

    # 先确保在 ok.com 页面
    url = bridge.get_url()
    if "ok.com" not in url:
        from ok.urls import build_base_url
        bridge.navigate(build_base_url("sg", "en", "singapore"))
        bridge.wait_dom_stable()

    from ok.login import check_login
    status = check_login(bridge)
    _output(status)


# ─── CLI 入口 ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OK.com 自动化 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list-countries
    subparsers.add_parser("list-countries", help="列出支持的国家")

    # list-cities
    p = subparsers.add_parser("list-cities", help="动态获取指定国家的城市列表")
    p.add_argument("--country", required=True, help="国家名/子域名/ISO code")
    p.add_argument("--lang", default="en", help="语言（默认 en）")

    # list-categories
    p = subparsers.add_parser("list-categories", help="动态获取分类树")
    p.add_argument("--country", required=True, help="国家名/子域名/ISO code")
    p.add_argument("--lang", default="en", help="语言（默认 en）")

    # set-locale
    p = subparsers.add_parser("set-locale", help="设置 locale（导航到指定国家/城市）")
    p.add_argument("--country", required=True, help="国家名/子域名/ISO code")
    p.add_argument("--city", required=True, help="城市 code")
    p.add_argument("--lang", default="en", help="语言（默认 en）")

    # get-locale
    subparsers.add_parser("get-locale", help="获取当前 locale")

    # search
    p = subparsers.add_parser("search", help="搜索帖子")
    p.add_argument("--keyword", required=True, help="搜索关键词")
    p.add_argument("--country", default="singapore", help="国家（默认 singapore）")
    p.add_argument("--city", default="singapore", help="城市（默认 singapore）")
    p.add_argument("--lang", default="en", help="语言（默认 en）")
    p.add_argument("--max-results", type=int, default=20, help="最大结果数（默认 20）")

    # list-feeds
    p = subparsers.add_parser("list-feeds", help="获取首页推荐")
    p.add_argument("--country", default="singapore", help="国家（默认 singapore）")
    p.add_argument("--city", default="singapore", help="城市（默认 singapore）")
    p.add_argument("--lang", default="en", help="语言（默认 en）")
    p.add_argument("--max-results", type=int, default=20, help="最大结果数（默认 20）")

    # get-listing
    p = subparsers.add_parser("get-listing", help="获取帖子详情")
    p.add_argument("--url", required=True, help="帖子 URL")

    # browse-category
    p = subparsers.add_parser("browse-category", help="按分类浏览")
    p.add_argument("--category", required=True, help="分类 code（如 marketplace, jobs）")
    p.add_argument("--country", default="singapore", help="国家（默认 singapore）")
    p.add_argument("--city", default="singapore", help="城市（默认 singapore）")
    p.add_argument("--lang", default="en", help="语言（默认 en）")
    p.add_argument("--max-results", type=int, default=20, help="最大结果数（默认 20）")

    # check-login
    subparsers.add_parser("check-login", help="检查登录状态")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    # 路由子命令
    cmd_map = {
        "list-countries": cmd_list_countries,
        "list-cities": cmd_list_cities,
        "list-categories": cmd_list_categories,
        "set-locale": cmd_set_locale,
        "get-locale": cmd_get_locale,
        "search": cmd_search,
        "list-feeds": cmd_list_feeds,
        "get-listing": cmd_get_listing,
        "browse-category": cmd_browse_category,
        "check-login": cmd_check_login,
    }

    handler = cmd_map.get(args.command)
    if not handler:
        parser.print_help()
        sys.exit(1)

    try:
        handler(args)
    except OKError as e:
        _error(str(e))
    except Exception as e:
        _error(f"未预期错误: {e}")


if __name__ == "__main__":
    main()
