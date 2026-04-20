"""Favorites & My Posts CLI tests

Layers:
1. Unit tests (no browser): data model validation, URL construction
2. Browser tests: full CLI integration via subprocess

Browser tests require Bridge/CDP/Playwright, marked @browser.
Run:  uv run pytest tests/test_favorites_posts.py -m browser -v
Skip: uv run pytest -m "not browser"
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


def run_cli(*args: str, timeout: int = 60) -> dict:
    """Run a CLI command and return parsed JSON."""
    result = subprocess.run(
        [*CLI, *args],
        capture_output=True,
        text=True,
        cwd=CWD,
        timeout=timeout,
    )
    assert result.returncode == 0, f"CLI failed (rc={result.returncode}): {result.stderr}"
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Unit tests (no browser)
# ---------------------------------------------------------------------------


class TestFavItemModel:
    """Validate FavItem dataclass."""

    def test_create_fav_item(self):
        from ok.favorites import FavItem

        item = FavItem(title="Test", url="https://sg.ok.com/...", price="S$100")
        assert item.title == "Test"
        assert item.price == "S$100"
        assert item.address is None

    def test_fav_result_defaults(self):
        from ok.favorites import FavResult

        r = FavResult()
        assert r.total == 0
        assert r.items == []
        assert r.url is None


class TestMyPostItemModel:
    """Validate MyPostItem dataclass."""

    def test_create_my_post_item(self):
        from ok.my_posts import MyPostItem

        item = MyPostItem(title="My Item", price="AED 1")
        assert item.title == "My Item"
        assert item.price == "AED 1"
        assert item.address is None

    def test_my_posts_result_defaults(self):
        from ok.my_posts import MyPostsResult

        r = MyPostsResult()
        assert r.total == 0
        assert r.state == "active"
        assert r.items == []

    def test_valid_states(self):
        from ok.my_posts import VALID_STATES

        assert "active" in VALID_STATES
        assert "pending" in VALID_STATES
        assert "expired" in VALID_STATES
        assert "draft" in VALID_STATES


class TestFavUrlConstruction:
    """Validate URL templates."""

    def test_fav_page_url(self):
        from ok.favorites import _FAV_PAGE_TEMPLATE

        url = _FAV_PAGE_TEMPLATE.format(sub="sg", lang="en")
        assert url == "https://sgpub.ok.com/biz/en/list/favorites"

    def test_fav_page_url_other_country(self):
        from ok.favorites import _FAV_PAGE_TEMPLATE

        url = _FAV_PAGE_TEMPLATE.format(sub="us", lang="en")
        assert url == "https://uspub.ok.com/biz/en/list/favorites"

    def test_my_posts_url(self):
        from ok.my_posts import _MY_POSTS_TEMPLATE

        url = _MY_POSTS_TEMPLATE.format(sub="sg", lang="en")
        assert url == "https://sgpub.ok.com/biz/en/publish/list"


class TestCliParserRegistration:
    """Verify CLI subcommands are registered."""

    def test_list_favorites_help(self):
        result = subprocess.run(
            [*CLI, "list-favorites", "--help"],
            capture_output=True,
            text=True,
            cwd=CWD,
        )
        assert result.returncode == 0
        assert "--subdomain" in result.stdout
        assert "--max-results" in result.stdout

    def test_add_favorite_help(self):
        result = subprocess.run(
            [*CLI, "add-favorite", "--help"],
            capture_output=True,
            text=True,
            cwd=CWD,
        )
        assert result.returncode == 0
        assert "--url" in result.stdout

    def test_remove_favorite_help(self):
        result = subprocess.run(
            [*CLI, "remove-favorite", "--help"],
            capture_output=True,
            text=True,
            cwd=CWD,
        )
        assert result.returncode == 0
        assert "--url" in result.stdout

    def test_list_my_posts_help(self):
        result = subprocess.run(
            [*CLI, "list-my-posts", "--help"],
            capture_output=True,
            text=True,
            cwd=CWD,
        )
        assert result.returncode == 0
        assert "--state" in result.stdout
        assert "--subdomain" in result.stdout

    def test_delete_post_help(self):
        result = subprocess.run(
            [*CLI, "delete-post", "--help"],
            capture_output=True,
            text=True,
            cwd=CWD,
        )
        assert result.returncode == 0
        assert "--index" in result.stdout

    def test_edit_post_help(self):
        result = subprocess.run(
            [*CLI, "edit-post", "--help"],
            capture_output=True,
            text=True,
            cwd=CWD,
        )
        assert result.returncode == 0
        assert "--index" in result.stdout


# ---------------------------------------------------------------------------
# Browser integration tests
# ---------------------------------------------------------------------------


@browser
class TestListFavorites:
    """T-FAV-01: list-favorites returns structured data."""

    def test_list_favorites_sg(self):
        data = run_cli("list-favorites", "--subdomain", "sg")
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] == len(data["items"])

    def test_list_favorites_has_fields(self):
        data = run_cli("list-favorites", "--subdomain", "sg")
        if data["total"] > 0:
            item = data["items"][0]
            assert "title" in item
            assert "url" in item
            assert "price" in item

    def test_list_favorites_max_results(self):
        data = run_cli("list-favorites", "--subdomain", "sg", "--max-results", "2")
        assert data["total"] <= 2


@browser
class TestListMyPosts:
    """T-POST-01: list-my-posts returns structured data."""

    def test_list_my_posts_active(self):
        data = run_cli("list-my-posts", "--subdomain", "sg", "--state", "active")
        assert "total" in data
        assert "items" in data
        assert data["state"] == "active"

    def test_list_my_posts_all_states(self):
        for state in ("active", "pending", "expired", "draft"):
            data = run_cli("list-my-posts", "--subdomain", "sg", "--state", state)
            assert data["state"] == state
            assert isinstance(data["items"], list)


@browser
class TestAddRemoveFavorite:
    """T-FAV-02: add/remove favorite toggling.

    Uses the first item from the favorites list to test toggle.
    """

    def test_add_favorite_requires_url(self):
        result = subprocess.run(
            [*CLI, "add-favorite"],
            capture_output=True,
            text=True,
            cwd=CWD,
        )
        assert result.returncode != 0

    def test_remove_favorite_requires_url(self):
        result = subprocess.run(
            [*CLI, "remove-favorite"],
            capture_output=True,
            text=True,
            cwd=CWD,
        )
        assert result.returncode != 0


@browser
class TestEditPost:
    """T-POST-02: edit-post returns link info."""

    def test_edit_post_empty_list(self):
        data = run_cli("list-my-posts", "--subdomain", "sg")
        if data["total"] == 0:
            data = run_cli("edit-post", "--subdomain", "sg", "--index", "0")
            assert data.get("success") is False or data.get("url") is None

    def test_edit_post_ae(self):
        data = run_cli("list-my-posts", "--subdomain", "ae")
        if data["total"] > 0:
            data = run_cli("edit-post", "--subdomain", "ae", "--index", "0")
            assert data.get("success") is True
            assert data.get("title")
