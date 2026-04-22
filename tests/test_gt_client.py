from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from property_advisor.gt_client import GTCoreSkillClient, canonicalize_gumtree_url, extract_gumtree_listing_id


def completed(*, returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


BRIDGE_HELP = "usage: cli.py [-h] {check-login,login,logout,search,home-recommend,detail} ..."
API_HELP = "usage: cli.py [-h] {check-login,login,show-session,delete-session,search-listings,publish-listing} ..."


class GTCoreSkillClientTests(unittest.TestCase):
    def test_bridge_doctor_is_ok_when_logged_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "cli.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

            def runner(command, **kwargs):
                cwd = kwargs.get("cwd")
                if cwd != str(root):
                    return completed(returncode=1, stderr="unexpected cwd")
                if command == [sys.executable, "-B", "scripts/cli.py", "--help"]:
                    return completed(stdout=BRIDGE_HELP)
                if command == ["uv", "run", "python", "scripts/cli.py", "--help"]:
                    return completed(stdout=BRIDGE_HELP)
                if command == ["uv", "run", "python", "scripts/cli.py", "check-login"]:
                    return completed(stdout=json.dumps({"ok": True, "logged_in": False}))
                return completed(returncode=1, stderr="unexpected command")

            client = GTCoreSkillClient(
                skill_root=root,
                runner=runner,
                which=lambda command: "/usr/bin/uv" if command == "uv" else "/usr/bin/python3",
                env={},
            )
            report = client.doctor(run_browser_smoke=True)

        self.assertTrue(report.ok)
        self.assertEqual(report.runtime_mode, "bridge")
        self.assertFalse(report.logged_in)
        self.assertIn("公开搜索与详情抓取仍可用", " ".join(report.warnings))

    def test_bridge_search_and_detail_are_normalized(self) -> None:
        search_payload = {
            "ok": True,
            "items": [
                {
                    "title": "Bridge Listing",
                    "description": None,
                    "price": None,
                    "location": "Heathrow, London",
                    "url": "https://gumtree.com/p/property-to-rent/bridge-listing/1511100050",
                    "age": "0 days",
                    "number_of_images": 13,
                    "promotions": ["FEATURED"],
                }
            ],
        }
        detail_payload = {
            "ok": True,
            "item": {
                "title": "Bridge Listing",
                "description": "Modern studio flat in London.",
                "price": "£1,000pm",
                "location": "Heathrow, London",
                "url": "https://www.gumtree.com/p/property-to-rent/bridge-listing/1511100050",
                "age": "0 days",
                "category": "To Rent",
                "seller_name": "Tanya",
                "image_urls": ["https://img.gumtree.com/sample/1"],
                "attributes": {
                    "Number Of Bedrooms": "Studio",
                    "Date Available": "31 Mar 2026",
                    "Seller Type": "Agency",
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "cli.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

            def runner(command, **kwargs):
                cwd = kwargs.get("cwd")
                if cwd != str(root):
                    return completed(returncode=1, stderr="unexpected cwd")
                if command == [sys.executable, "-B", "scripts/cli.py", "--help"]:
                    return completed(stdout=BRIDGE_HELP)
                if command == ["uv", "run", "python", "scripts/cli.py", "--help"]:
                    return completed(stdout=BRIDGE_HELP)
                if command[:5] == ["uv", "run", "python", "scripts/cli.py", "search"]:
                    return completed(stdout=json.dumps(search_payload))
                if command[:5] == ["uv", "run", "python", "scripts/cli.py", "detail"]:
                    return completed(stdout=json.dumps(detail_payload))
                return completed(returncode=1, stderr="unexpected command")

            client = GTCoreSkillClient(
                skill_root=root,
                runner=runner,
                which=lambda command: "/usr/bin/uv" if command == "uv" else "/usr/bin/python3",
                env={},
            )
            listings = client.search_property(
                keyword="flat",
                country="united kingdom",
                city="London",
                lang="en",
                max_results=1,
                search_location="London",
            )
            detail = client.get_listing_detail(url=listings[0]["url"])

        self.assertEqual(listings[0]["listing_id"], "1511100050")
        self.assertEqual(listings[0]["url"], "https://www.gumtree.com/p/property-to-rent/bridge-listing/1511100050")
        self.assertEqual(detail["price"], "£1,000pm")
        self.assertEqual(detail["bedrooms_text"], "Studio")
        self.assertEqual(detail["seller_type"], "Agency")
        self.assertTrue(detail["detail_fetched"])

    def test_api_search_normalizes_and_detail_gracefully_degrades(self) -> None:
        search_payload = {
            "ok": True,
            "items": [
                {
                    "id": 1511100050,
                    "title": "API Listing",
                    "description": "Fallback result",
                    "price": 1000,
                    "primaryLocation": "Richmond",
                    "primaryCategory": "To Rent",
                    "publicWebsiteUrl": "https://gumtree.com/p/property-to-rent/api-listing/1511100050",
                    "primaryImageUrl": "https://img.gumtree.com/sample/1",
                    "publishedDate": 1769760599069,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "cli.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

            def runner(command, **kwargs):
                cwd = kwargs.get("cwd")
                if cwd != str(root):
                    return completed(returncode=1, stderr="unexpected cwd")
                if command == [sys.executable, "-B", "scripts/cli.py", "--help"]:
                    return completed(stdout=API_HELP)
                if command == ["python3", "scripts/cli.py", "--help"]:
                    return completed(stdout=API_HELP)
                if command[:3] == ["python3", "scripts/cli.py", "search-listings"]:
                    return completed(stdout=json.dumps(search_payload))
                return completed(returncode=1, stderr="unexpected command")

            client = GTCoreSkillClient(
                skill_root=root,
                runner=runner,
                which=lambda command: "/usr/bin/python3" if command == "python3" else None,
                env={},
            )
            listings = client.search_property(
                keyword="flat",
                country="united kingdom",
                city="London",
                lang="en",
                max_results=1,
            )
            detail = client.get_listing_detail(url=listings[0]["url"])

        self.assertEqual(listings[0]["price"], "£1,000")
        self.assertEqual(listings[0]["listing_id"], "1511100050")
        self.assertFalse(detail["detail_fetched"])
        self.assertEqual(detail["detail_degraded_reason"], "GT 当前运行模式不支持详情补全")

    def test_gumtree_url_is_canonicalized(self) -> None:
        self.assertEqual(
            canonicalize_gumtree_url("https://gumtree.com/p/property-to-rent/test/1511100050?foo=1"),
            "https://www.gumtree.com/p/property-to-rent/test/1511100050",
        )
        self.assertEqual(extract_gumtree_listing_id("https://gumtree.com/p/test/1511100050"), "1511100050")


if __name__ == "__main__":
    unittest.main()
