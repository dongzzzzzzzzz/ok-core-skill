from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "cli.py"
FIXTURES = ROOT / "tests" / "fixtures"

sys.path.insert(0, str(ROOT / "scripts"))

from cli import JsonCache, PublicOsmClient  # noqa: E402


class CliEndToEndTest(unittest.TestCase):
    def test_fixture_analyze_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--cache-dir",
                    tmp,
                    "analyze-batch",
                    "--input",
                    str(FIXTURES / "melbourne_listings.json"),
                    "--destination",
                    "Melbourne CBD VIC",
                    "--city",
                    "melbourne",
                    "--incremental",
                    "--fixture-dir",
                    str(FIXTURES / "osm"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["provider"], "public_osm_fixture")
        self.assertTrue(payload["incremental"])
        self.assertEqual(len(payload["listings"]), 2)

        by_id = {item["id"]: item for item in payload["listings"]}
        archive = by_id["listing_archive"]
        self.assertEqual(archive["geo"]["precision"], "address")
        self.assertGreaterEqual(archive["amenities"]["supermarket_count"], 1)
        self.assertIsNotNone(archive["transit_access"])
        self.assertIn("origin", archive["transit_access"])
        self.assertEqual(archive["transit_access"]["distance_type"], "straight_line_estimate")
        self.assertFalse(archive["destination_access"]["verified_route"])
        self.assertIn("origin", archive["destination_access"])
        self.assertEqual(archive["destination_access"]["distance_type"], "straight_line_estimate")
        self.assertIn("not_google_maps_verified", archive["limitations"])

        area = by_id["listing_area_only"]
        self.assertEqual(area["geo"]["precision"], "area")
        self.assertIn("area_level_location", area["limitations"])
        self.assertIn("precision_note", area["amenities"])
        self.assertIn("precision_note", area["destination_access"])
        self.assertIn("precision_note", area["risk_signals"])
        self.assertNotIn("near_primary_road_meters", area["risk_signals"])
        self.assertNotIn("distance_meters_range", area["transit_access"])
        self.assertEqual(area["transit_access"]["distance_type"], "not_available_for_area_level_location")

    def test_doctor(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(CLI), "doctor"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["requires_api_key"])
        self.assertFalse(payload["requires_local_database"])

    def test_runtime_budget_exhaustion_is_fast_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = PublicOsmClient(JsonCache(Path(tmp)), max_live_seconds=1)
            client.started_at = time.monotonic() - 2

            timeout = client._request_timeout("overpass", bbox="test")

        self.assertIsNone(timeout)
        self.assertEqual(client.usage["errors"][0]["error"], "runtime_budget_exhausted")


if __name__ == "__main__":
    unittest.main()
