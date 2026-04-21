#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from property_advisor import OKCoreSkillClient, PropertyAdvisorOrchestrator, PublicOsmMapClient, SearchRequest


def emit(payload: dict, exit_code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Property Advisor orchestration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Run ok-core-skill and map-skill preflight checks")
    doctor.add_argument("--ok-skill-root", default="")
    doctor.add_argument("--skip-browser-smoke", action="store_true")

    search = subparsers.add_parser("search", help="Run the full listing -> detail -> map -> decision pipeline")
    search.add_argument("--keyword", default="")
    search.add_argument("--country", default="australia")
    search.add_argument("--city", default="melbourne")
    search.add_argument("--lang", default="en")
    search.add_argument("--max-results", type=int, default=20)
    search.add_argument("--detail-limit", type=int, default=10)
    search.add_argument("--destination", default="")
    search.add_argument("--budget-min", type=float)
    search.add_argument("--budget-max", type=float)
    search.add_argument("--bedrooms", type=float)
    search.add_argument("--query-text", default="")
    search.add_argument("--priority", action="append", default=[])
    search.add_argument("--skip-map", action="store_true")
    search.add_argument("--map-fixture-dir", default="")
    search.add_argument("--ok-skill-root", default="")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "doctor":
        ok_client = OKCoreSkillClient(skill_root=args.ok_skill_root or None)
        map_client = PublicOsmMapClient()
        payload = {
            "ok_core_skill": ok_client.doctor(run_browser_smoke=not args.skip_browser_smoke).to_dict(),
            "public_osm_map_context": map_client.doctor(),
        }
        return emit(payload, exit_code=0 if payload["ok_core_skill"]["ok"] else 2)

    request = SearchRequest(
        keyword=args.keyword,
        country=args.country,
        city=args.city,
        lang=args.lang,
        max_results=args.max_results,
        detail_limit=args.detail_limit,
        destination=args.destination,
        budget_min=args.budget_min,
        budget_max=args.budget_max,
        bedrooms=args.bedrooms,
        force_map=not args.skip_map,
        query_text=args.query_text,
        user_priorities=args.priority,
    )
    ok_client = OKCoreSkillClient(skill_root=args.ok_skill_root or None)
    map_client = None if args.skip_map else PublicOsmMapClient(fixture_dir=args.map_fixture_dir or None)
    orchestrator = PropertyAdvisorOrchestrator(ok_client, map_client)
    report = orchestrator.search(request)
    exit_code = 0 if not report.errors else 2
    return emit(report.to_dict(), exit_code=exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
