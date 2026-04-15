"""full-search 一站式搜索端到端测试

覆盖所有业务场景：
- 分类浏览（category only）
- 关键词搜索（keyword only）
- 分类 + 关键词组合
- 价格筛选（min/max/range）
- 多国家 × 多城市
- 边界与异常

所有测试需要浏览器（Bridge/CDP/Playwright），标记 @browser。
运行: uv run pytest tests/test_full_search.py -m browser -v
跳过: uv run pytest -m "not browser"
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

CLI = [sys.executable, str(Path(__file__).parent.parent / "scripts" / "cli.py")]
CWD = str(Path(__file__).parent.parent)

browser = pytest.mark.browser


def run_full_search(**kwargs) -> dict:
    """Run full-search and return parsed JSON output."""
    args = [*CLI, "full-search"]
    for key, val in kwargs.items():
        if val is not None:
            args.extend([f"--{key.replace('_', '-')}", str(val)])
    result = subprocess.run(
        args, capture_output=True, text=True, cwd=CWD, timeout=120,
    )
    assert result.returncode == 0, f"CLI failed (rc={result.returncode}): {result.stderr}"
    return json.loads(result.stdout)


def assert_steps_ok(data: dict, expected_steps: list[str] | None = None):
    """Verify all steps succeeded."""
    steps = data["steps"]
    for s in steps:
        assert s["success"], f"Step '{s['step']}' failed: {s.get('error')}"
    if expected_steps:
        actual = [s["step"] for s in steps]
        for exp in expected_steps:
            assert any(exp in a for a in actual), (
                f"Expected step containing '{exp}' not found in {actual}"
            )


def assert_has_listings(data: dict, min_count: int = 1):
    """Verify results contain listings."""
    assert data["total"] >= min_count, (
        f"Expected >= {min_count} listings, got {data['total']}"
    )
    assert len(data["listings"]) >= min_count


# ═══════════════════════════════════════════════════════════════
# 1. 核心场景：分类浏览
# ═══════════════════════════════════════════════════════════════


@browser
class TestCategoryBrowse:
    """仅传 --category，不传 keyword。按分类浏览帖子。"""

    def test_usa_hawaii_property(self):
        """TC-1: 美国夏威夷房产 — 最常用场景"""
        data = run_full_search(country="usa", city="hawaii", category="property")
        assert_steps_ok(data)
        assert_has_listings(data)
        assert "city-hawaii" in data["final_url"]
        assert data["flow"]["category"] == "property"

    def test_usa_new_york_jobs(self):
        """TC-2: 美国纽约招聘"""
        data = run_full_search(country="usa", city="new york", category="jobs")
        assert_steps_ok(data)
        assert_has_listings(data)
        assert "new-york" in data["final_url"] or "new_york" in data["final_url"]

    def test_singapore_marketplace(self):
        """TC-3: 新加坡二手市场"""
        data = run_full_search(
            country="singapore", city="singapore", category="marketplace",
        )
        assert_steps_ok(data)
        assert_has_listings(data)

    def test_canada_vancouver_cars(self):
        """TC-4: 加拿大温哥华汽车"""
        data = run_full_search(country="canada", city="vancouver", category="cars")
        assert_steps_ok(data)
        assert_has_listings(data)

    def test_usa_services(self):
        """TC-5: 美国服务分类"""
        data = run_full_search(
            country="usa", city="los angeles", category="services",
        )
        assert_steps_ok(data)
        assert_has_listings(data)


# ═══════════════════════════════════════════════════════════════
# 2. 核心场景：关键词搜索
# ═══════════════════════════════════════════════════════════════


@browser
class TestKeywordSearch:
    """仅传 --keyword，不传 category。按关键词全站搜索。"""

    def test_search_laptop(self):
        """TC-6: 新加坡搜索 laptop"""
        data = run_full_search(
            country="singapore", city="singapore", keyword="laptop",
        )
        assert_steps_ok(data, expected_steps=["search"])
        assert_has_listings(data)
        assert data["flow"]["keyword"] == "laptop"

    def test_search_iphone(self):
        """TC-7: 美国纽约搜索 iPhone"""
        data = run_full_search(
            country="usa", city="new york", keyword="iPhone",
        )
        assert_steps_ok(data, expected_steps=["search"])
        assert_has_listings(data)

    def test_search_chinese_keyword(self):
        """TC-8: 英文关键词（用户侧中文已由 Agent 映射为英文）"""
        data = run_full_search(
            country="usa", city="hawaii", keyword="house",
        )
        assert_steps_ok(data)
        assert_has_listings(data)


# ═══════════════════════════════════════════════════════════════
# 3. 组合场景：分类 + 关键词
# ═══════════════════════════════════════════════════════════════


@browser
class TestCategoryPlusKeyword:
    """同时传 --category 和 --keyword。先进入分类页，再搜索关键词。"""

    def test_property_plus_house(self):
        """TC-9: 夏威夷房产分类 + house 关键词"""
        data = run_full_search(
            country="usa", city="hawaii",
            category="property", keyword="house",
        )
        assert_steps_ok(data, expected_steps=["click_category", "search"])
        assert_has_listings(data)

    def test_marketplace_plus_keyword(self):
        """TC-10: 新加坡市场分类 + laptop 关键词"""
        data = run_full_search(
            country="singapore", city="singapore",
            category="marketplace", keyword="laptop",
        )
        assert_steps_ok(data, expected_steps=["click_category", "search"])


# ═══════════════════════════════════════════════════════════════
# 4. 价格筛选
# ═══════════════════════════════════════════════════════════════


@browser
class TestPriceFilter:
    """价格区间筛选（通过 UI Confirm 按钮提交）。"""

    def test_price_range(self):
        """TC-11: 价格区间 100k-500k"""
        data = run_full_search(
            country="usa", city="hawaii", category="property",
            min_price=100000, max_price=500000,
        )
        assert_steps_ok(data, expected_steps=["price_filter"])
        price_step = next(s for s in data["steps"] if s["step"] == "price_filter")
        assert price_step["confirmed"] is True
        assert "lowestPrice=100000" in data["final_url"]
        assert "highestPrice=500000" in data["final_url"]

    def test_price_max_only(self):
        """TC-12: 仅设上限 — 50万以下"""
        data = run_full_search(
            country="usa", city="hawaii", category="property",
            max_price=500000,
        )
        assert_steps_ok(data, expected_steps=["price_filter"])
        assert "highestPrice=500000" in data["final_url"]

    def test_price_min_only(self):
        """TC-13: 仅设下限 — 100万以上"""
        data = run_full_search(
            country="usa", city="new york", category="property",
            min_price=1000000,
        )
        assert_steps_ok(data, expected_steps=["price_filter"])
        assert "lowestPrice=1000000" in data["final_url"]

    def test_price_with_keyword(self):
        """TC-14: 关键词搜索 + 价格筛选组合"""
        data = run_full_search(
            country="usa", city="hawaii",
            keyword="house", min_price=200000, max_price=800000,
        )
        assert_steps_ok(data)
        assert data["flow"]["price_min"] == 200000
        assert data["flow"]["price_max"] == 800000


# ═══════════════════════════════════════════════════════════════
# 5. 多国家覆盖
# ═══════════════════════════════════════════════════════════════


@browser
class TestMultiCountry:
    """验证不同国家均可正常执行 full-search。"""

    @pytest.mark.parametrize("country,city,category", [
        ("usa", "hawaii", "property"),
        ("singapore", "singapore", "marketplace"),
        ("canada", "toronto", "jobs"),
        ("uk", "london", "property"),
        ("australia", "sydney", "cars"),
    ])
    def test_country_city_category(self, country, city, category):
        """TC-15~19: 多国家 × 城市 × 分类"""
        data = run_full_search(
            country=country, city=city, category=category, max_results=3,
        )
        assert_steps_ok(data)
        assert data["flow"]["country"] == country
        assert data["flow"]["city_keyword"] == city
        assert data["flow"]["category"] == category


# ═══════════════════════════════════════════════════════════════
# 6. 城市切换验证
# ═══════════════════════════════════════════════════════════════


@browser
class TestCitySwitch:
    """验证城市切换（UI 优先 / API fallback）。"""

    def test_ui_city_switch_succeeds(self):
        """TC-20: UI 城市切换成功（需要 category 先进入列表页）"""
        data = run_full_search(
            country="usa", city="hawaii", category="property", max_results=3,
        )
        assert_steps_ok(data)
        city_step = next(
            (s for s in data["steps"] if "switch_city" in s["step"]), None,
        )
        assert city_step is not None
        assert city_step["city_code"] == "hawaii"

    def test_city_switch_multi_word(self):
        """TC-21: 多单词城市名（new york → new-york）"""
        data = run_full_search(
            country="usa", city="new york", category="property", max_results=3,
        )
        assert_steps_ok(data)
        city_step = next(
            (s for s in data["steps"] if "switch_city" in s["step"]), None,
        )
        assert city_step is not None
        assert "new-york" in city_step.get("city_code", "") or \
               "new-york" in city_step.get("url", "")

    def test_city_switch_without_category(self):
        """TC-22: 无分类时城市切换（keyword-only 模式，走 API fallback）"""
        data = run_full_search(
            country="usa", city="hawaii", keyword="laptop", max_results=3,
        )
        assert_steps_ok(data)
        assert "hawaii" in data["final_url"]


# ═══════════════════════════════════════════════════════════════
# 7. max-results 控制
# ═══════════════════════════════════════════════════════════════


@browser
class TestMaxResults:
    """验证结果数量上限控制。"""

    def test_max_results_3(self):
        """TC-23: 限制返回 3 条"""
        data = run_full_search(
            country="usa", city="hawaii", category="property", max_results=3,
        )
        assert_steps_ok(data)
        assert data["total"] <= 3
        assert len(data["listings"]) <= 3

    def test_max_results_1(self):
        """TC-24: 限制返回 1 条"""
        data = run_full_search(
            country="singapore", city="singapore",
            category="marketplace", max_results=1,
        )
        assert_steps_ok(data)
        assert data["total"] <= 1


# ═══════════════════════════════════════════════════════════════
# 8. 输出结构验证
# ═══════════════════════════════════════════════════════════════


@browser
class TestOutputStructure:
    """验证 JSON 输出结构完整性。"""

    def test_output_has_required_fields(self):
        """TC-25: 输出包含 flow / steps / total / listings / final_url"""
        data = run_full_search(
            country="usa", city="hawaii", category="property", max_results=3,
        )
        assert "flow" in data
        assert "steps" in data
        assert "total" in data
        assert "listings" in data
        assert "final_url" in data

    def test_flow_records_all_params(self):
        """TC-26: flow 记录了所有输入参数"""
        data = run_full_search(
            country="usa", city="hawaii", category="property",
            keyword="house", min_price=100000, max_price=500000,
        )
        flow = data["flow"]
        assert flow["country"] == "usa"
        assert flow["city_keyword"] == "hawaii"
        assert flow["category"] == "property"
        assert flow["keyword"] == "house"
        assert flow["price_min"] == 100000
        assert flow["price_max"] == 500000
        assert "city_code" in flow

    def test_price_filter_in_output(self):
        """TC-27: 传入价格时输出包含 price_filter 字段"""
        data = run_full_search(
            country="usa", city="hawaii", category="property",
            min_price=100000, max_price=500000,
        )
        assert "price_filter" in data
        assert data["price_filter"]["min"] == 100000
        assert data["price_filter"]["max"] == 500000

    def test_listing_fields(self):
        """TC-28: 每条 listing 包含核心字段"""
        data = run_full_search(
            country="usa", city="hawaii", category="property", max_results=3,
        )
        if data["total"] == 0:
            pytest.skip("No listings available")
        listing = data["listings"][0]
        assert "title" in listing
        assert "price" in listing
        assert "url" in listing

    def test_steps_report_method(self):
        """TC-29: city switch step 报告使用的方法（ui / api）"""
        data = run_full_search(
            country="usa", city="hawaii", category="property", max_results=1,
        )
        city_step = next(
            (s for s in data["steps"] if "switch_city" in s["step"]), None,
        )
        assert city_step is not None
        assert city_step.get("method") in ("ui", "api")


# ═══════════════════════════════════════════════════════════════
# 9. 边界与异常
# ═══════════════════════════════════════════════════════════════


class TestEdgeCases:
    """不需要浏览器的参数校验测试。"""

    def test_no_category_no_keyword_fails(self):
        """TC-30: 不传 category 也不传 keyword 应报错"""
        result = subprocess.run(
            [*CLI, "full-search", "--country", "usa", "--city", "hawaii"],
            capture_output=True, text=True, cwd=CWD, timeout=30,
        )
        assert result.returncode == 2

    def test_missing_country_fails(self):
        """TC-31: 缺少必填参数 --country 应报错"""
        result = subprocess.run(
            [*CLI, "full-search", "--city", "hawaii", "--category", "property"],
            capture_output=True, text=True, cwd=CWD, timeout=30,
        )
        assert result.returncode == 2

    def test_missing_city_fails(self):
        """TC-32: 缺少必填参数 --city 应报错"""
        result = subprocess.run(
            [*CLI, "full-search", "--country", "usa", "--category", "property"],
            capture_output=True, text=True, cwd=CWD, timeout=30,
        )
        assert result.returncode == 2


@browser
class TestBrowserEdgeCases:
    """需要浏览器的边界场景。"""

    def test_nonexistent_city_graceful(self):
        """TC-33: 不存在的城市应有合理错误（不崩溃）"""
        data = run_full_search(
            country="usa", city="xyznonexistent", category="property",
            max_results=1,
        )
        city_step = next(
            (s for s in data["steps"] if "switch_city" in s["step"]), None,
        )
        assert city_step is not None
        if not city_step["success"]:
            assert city_step.get("error")

    def test_rare_category(self):
        """TC-34: 较少使用的分类（community）"""
        data = run_full_search(
            country="usa", city="hawaii", category="community", max_results=3,
        )
        assert_steps_ok(data)
        assert data["flow"]["category"] == "community"
