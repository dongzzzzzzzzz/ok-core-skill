#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from property_advisor import (
    GTCoreSkillClient,
    OKCoreSkillClient,
    PipelineReport,
    PreflightReport,
    PropertyAdvisorOrchestrator,
    PublicOsmMapClient,
    SearchRequest,
    apply_market_routing,
)
from property_advisor.analysis import unique_strings


def emit(payload: dict, exit_code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Property Advisor orchestration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Run ok-core-skill, gt-core-skill, and map-skill preflight checks")
    doctor.add_argument("--ok-skill-root", default="")
    doctor.add_argument("--gt-skill-root", default="")
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
    search.add_argument("--gt-skill-root", default="")
    search.add_argument("--market", choices=["auto", "ok", "gt"], default="auto")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "doctor":
        ok_client = OKCoreSkillClient(skill_root=args.ok_skill_root or None)
        map_client = PublicOsmMapClient()
        gt_report = _safe_gt_doctor(args.gt_skill_root or None, skip_browser_smoke=args.skip_browser_smoke)
        payload = {
            "ok_core_skill": ok_client.doctor(run_browser_smoke=not args.skip_browser_smoke).to_dict(),
            "gt_core_skill": gt_report.to_dict(),
            "public_osm_map_context": map_client.doctor(),
        }
        exit_code = 0 if payload["ok_core_skill"]["ok"] and payload["public_osm_map_context"].get("status") == "ok" else 2
        return emit(payload, exit_code=exit_code)

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
        market_hint=args.market,
        country_is_default=args.country == "australia",
        city_is_default=args.city == "melbourne",
    )
    routed_request, routing = apply_market_routing(request)
    if routing.error:
        report = PipelineReport(
            request=routed_request,
            preflight=PreflightReport(
                ok=False,
                skill_root=None,
                selected_runner=None,
                warnings=list(routing.warnings),
                source_name="market-router",
            ),
            routing=routing.to_dict(),
            summary={"visible_candidates": 0, "hidden_candidates": 0},
            warnings=list(routing.warnings),
            errors=[routing.error],
        )
        return emit(report.to_dict(), exit_code=2)
    try:
        listing_client = _build_listing_client(
            routed_request,
            ok_skill_root=args.ok_skill_root or None,
            gt_skill_root=args.gt_skill_root or None,
        )
    except Exception as exc:
        report = PipelineReport(
            request=routed_request,
            preflight=PreflightReport(
                ok=False,
                skill_root=args.gt_skill_root or None,
                selected_runner=None,
                warnings=[str(exc)],
                source_name="gt-core-skill" if routed_request.resolved_market == "gt" else "ok-core-skill",
            ),
            routing=routing.to_dict(),
            selected_source=routed_request.resolved_market or None,
            summary={"visible_candidates": 0, "hidden_candidates": 0},
            warnings=[str(exc)],
            errors=[str(exc)],
        )
        return emit(report.to_dict(), exit_code=2)
    map_client = None if args.skip_map else PublicOsmMapClient(fixture_dir=args.map_fixture_dir or None)
    orchestrator = PropertyAdvisorOrchestrator(listing_client, map_client)
    report = orchestrator.search(routed_request)
    report.routing = routing.to_dict()
    report.warnings = unique_strings(report.warnings + routing.warnings)
    exit_code = 0 if not report.errors else 2
    return emit(report.to_dict(), exit_code=exit_code)


def _build_listing_client(request: SearchRequest, *, ok_skill_root: str | None, gt_skill_root: str | None):
    if request.resolved_market == "gt":
        return GTCoreSkillClient(skill_root=gt_skill_root or None)
    return OKCoreSkillClient(skill_root=ok_skill_root or None)


def _safe_gt_doctor(skill_root: str | None, *, skip_browser_smoke: bool) -> PreflightReport:
    try:
        client = GTCoreSkillClient(skill_root=skill_root or None)
    except Exception as exc:
        return PreflightReport(
            ok=False,
            skill_root=skill_root or None,
            selected_runner=None,
            warnings=[str(exc)],
            source_name="gt-core-skill",
        )
    return client.doctor(run_browser_smoke=not skip_browser_smoke)


if __name__ == "__main__":
    raise SystemExit(main())
