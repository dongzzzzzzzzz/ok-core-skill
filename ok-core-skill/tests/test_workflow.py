"""Workflow tests: validate the full CLI pipeline for location-based searches.

Two layers:
1. API layer (no browser): city search, country list, categories
2. Browser layer (needs Bridge/CDP/Playwright): set-locale, search, browse-category, get-listing

Browser-layer tests are marked with @pytest.mark.browser; skip in CI via -m "not browser".
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from ok.errors import OKAPIError
from ok.locale import fetch_categories, get_country_info, search_cities

CLI = [sys.executable, str(Path(__file__).parent.parent / "scripts" / "cli.py")]
CWD = str(Path(__file__).parent.parent)

browser = pytest.mark.browser


def run_cli(*args: str) -> dict:
    """Run a CLI command and return parsed JSON."""
    result = subprocess.run(
        [*CLI, *args],
        capture_output=True,
        text=True,
        cwd=CWD,
        timeout=60,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


# --- API layer tests (no browser needed) -----------------------------------


class TestListCountries:
    """T1.1: list-countries returns a valid country list."""

    def test_returns_countries(self):
        data = run_cli("list-countries")
        assert "countries" in data
        assert len(data["countries"]) > 0

    def test_usa_exists(self):
        data = run_cli("list-countries")
        names = [c["name"] for c in data["countries"]]
        assert "usa" in names

    def test_country_has_required_fields(self):
        data = run_cli("list-countries")
        for country in data["countries"]:
            assert "name" in country
            assert "subdomain" in country
            assert "code" in country


class TestCitySearch:
    """T1.2: city search finds Hawaii and other cities."""

    def test_search_hawaii(self):
        cities = search_cities("usa", "hawaii")
        assert len(cities) > 0
        codes = [c.code for c in cities]
        assert any("hawaii" in code.lower() or "honolulu" in code.lower() for code in codes)

    def test_search_hawaii_via_cli(self):
        data = run_cli("list-cities", "--country", "usa", "--mode", "search", "--keyword", "hawaii")
        assert data["total"] > 0
        assert len(data["cities"]) > 0

    def test_search_tokyo(self):
        try:
            cities = search_cities("japan", "tokyo")
        except OKAPIError as e:
            pytest.skip(f"Japan API unavailable: {e}")
        assert len(cities) > 0

    def test_search_vancouver(self):
        cities = search_cities("canada", "vancouver")
        assert len(cities) > 0
        codes = [c.code for c in cities]
        assert any("vancouver" in code.lower() for code in codes)

    def test_search_empty_keyword_no_crash(self):
        """Empty keyword should not crash."""
        cities = search_cities("usa", "")
        assert isinstance(cities, list)

    def test_search_nonexistent_city(self):
        """Nonexistent city should return empty list."""
        cities = search_cities("usa", "xyznonexistent123")
        assert cities == []


class TestGetCountryInfo:
    """Validate country lookup supports multiple input formats."""

    def test_by_name(self):
        info = get_country_info("usa")
        assert info["subdomain"] == "us"

    def test_by_subdomain(self):
        info = get_country_info("us")
        assert info["code"] == "US"

    def test_by_iso_code(self):
        info = get_country_info("US")
        assert info["subdomain"] == "us"

    def test_invalid_country_raises(self):
        from ok.errors import OKLocaleError

        with pytest.raises(OKLocaleError):
            get_country_info("atlantis")


class TestCategories:
    """Validate category fetching."""

    def test_fetch_usa_categories(self):
        categories = fetch_categories("usa")
        assert len(categories) > 0
        codes = [c.code for c in categories]
        assert "property" in codes or any("property" in c.lower() for c in codes)

    def test_categories_via_cli(self):
        data = run_cli("list-categories", "--country", "usa")
        assert data["total"] > 0
        assert len(data["categories"]) > 0


# --- Browser layer tests (need Bridge/CDP/Playwright) ----------------------


@browser
class TestHawaiiWorkflow:
    """T1.3-T1.6: full Hawaii property workflow (requires browser)."""

    @pytest.fixture(autouse=True)
    def hawaii_city_code(self):
        """Look up Hawaii city code for subsequent tests."""
        cities = search_cities("usa", "hawaii")
        assert len(cities) > 0, "Cannot find Hawaii city, API may be unavailable"
        self.city_code = cities[0].code
        self.country = "usa"

    def test_set_locale_hawaii(self):
        """T1.3: switch to Hawaii."""
        data = run_cli("set-locale", "--country", self.country, "--city", self.city_code)
        assert "locale" in data
        assert data["locale"]["city"] == self.city_code

    def test_search_house_in_hawaii(self):
        """T1.4: search for houses in Hawaii."""
        data = run_cli(
            "search",
            "--keyword", "house",
            "--country", self.country,
            "--city", self.city_code,
        )
        assert "listings" in data
        assert "keyword" in data
        assert data["keyword"] == "house"

    def test_browse_property_in_hawaii(self):
        """T1.5: browse property category in Hawaii."""
        data = run_cli(
            "browse-category",
            "--category", "property",
            "--country", self.country,
            "--city", self.city_code,
        )
        assert "listings" in data
        assert data["category"] == "property"

    def test_get_listing_detail(self):
        """T1.6: fetch listing detail (needs a url from search results)."""
        search_data = run_cli(
            "browse-category",
            "--category", "property",
            "--country", self.country,
            "--city", self.city_code,
            "--max-results", "5",
        )
        listings = search_data.get("listings", [])
        if not listings:
            pytest.skip("No property listings in this area")

        url = listings[0].get("url")
        if not url:
            pytest.skip("First listing has no URL")

        detail = run_cli("get-listing", "--url", url)
        assert "title" in detail
        assert detail["title"]


@browser
class TestTokyoWorkflow:
    """TC-2: Tokyo computer search scenario."""

    def test_search_computer_in_tokyo(self):
        try:
            cities = search_cities("japan", "tokyo")
        except OKAPIError as e:
            pytest.skip(f"Japan API unavailable: {e}")
        assert len(cities) > 0
        city_code = cities[0].code

        data = run_cli(
            "search",
            "--keyword", "computer",
            "--country", "japan",
            "--city", city_code,
        )
        assert "listings" in data


@browser
class TestVancouverWorkflow:
    """TC-3: Vancouver jobs scenario."""

    def test_browse_jobs_in_vancouver(self):
        cities = search_cities("canada", "vancouver")
        assert len(cities) > 0
        city_code = cities[0].code

        data = run_cli(
            "browse-category",
            "--category", "jobs",
            "--country", "canada",
            "--city", city_code,
        )
        assert "listings" in data
        assert data["category"] == "jobs"


# --- Edge case tests -------------------------------------------------------


class TestEdgeCases:
    """TC-4 through TC-7 edge cases."""

    def test_tc4_nonexistent_city_returns_empty(self):
        """TC-4: city search returns empty for nonexistent city."""
        data = run_cli(
            "list-cities", "--country", "usa",
            "--mode", "search", "--keyword", "xyznonexistent",
        )
        assert data["total"] == 0
        assert data["cities"] == []

    def test_tc5_ambiguous_city_returns_multiple(self):
        """TC-5: ambiguous keyword returns multiple cities."""
        data = run_cli(
            "list-cities", "--country", "usa",
            "--mode", "search", "--keyword", "new",
        )
        if data["total"] > 1:
            assert len(data["cities"]) > 1

    def test_country_params_accept_multiple_formats(self):
        """Verify --country accepts name/subdomain/ISO code."""
        for arg in ["usa", "us", "US"]:
            data = run_cli("list-cities", "--country", arg, "--mode", "search", "--keyword", "new")
            assert "cities" in data


class TestPriceFilter:
    """Unit tests for _parse_price and _filter_by_price."""

    def test_parse_price_usd(self):
        from ok.search import _parse_price

        assert _parse_price("$2,250,000") == 2250000.0
        assert _parse_price("$500") == 500.0

    def test_parse_price_plain_number(self):
        from ok.search import _parse_price

        assert _parse_price("1500") == 1500.0
        assert _parse_price("30,000") == 30000.0

    def test_parse_price_none_and_empty(self):
        from ok.search import _parse_price

        assert _parse_price(None) is None
        assert _parse_price("") is None
        assert _parse_price("Contact seller") is None

    def test_filter_by_price_min_only(self):
        from ok.search import _filter_by_price
        from ok.types import Listing

        items = [
            Listing(title="A", price="$100"),
            Listing(title="B", price="$500"),
            Listing(title="C", price="$1000"),
            Listing(title="D", price=None),
        ]
        result = _filter_by_price(items, price_min=500, price_max=None)
        titles = [l.title for l in result]
        assert "A" not in titles
        assert "B" in titles
        assert "C" in titles
        assert "D" in titles  # unparseable kept

    def test_filter_by_price_max_only(self):
        from ok.search import _filter_by_price
        from ok.types import Listing

        items = [
            Listing(title="A", price="$100"),
            Listing(title="B", price="$500"),
            Listing(title="C", price="$1000"),
        ]
        result = _filter_by_price(items, price_min=None, price_max=500)
        titles = [l.title for l in result]
        assert "A" in titles
        assert "B" in titles
        assert "C" not in titles

    def test_filter_by_price_range(self):
        from ok.search import _filter_by_price
        from ok.types import Listing

        items = [
            Listing(title="A", price="$100"),
            Listing(title="B", price="$500"),
            Listing(title="C", price="$1000"),
        ]
        result = _filter_by_price(items, price_min=200, price_max=800)
        titles = [l.title for l in result]
        assert titles == ["B"]

    def test_filter_noop_when_no_bounds(self):
        from ok.search import _filter_by_price
        from ok.types import Listing

        items = [Listing(title="A", price="$100"), Listing(title="B", price="$500")]
        result = _filter_by_price(items, price_min=None, price_max=None)
        assert len(result) == 2
