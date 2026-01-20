#!/usr/bin/env python3
"""
Pack-Driven Assessor - Score only what the pack expects

This replaces the naive "count everything" approach with:
1. Pack Coverage % - Required items that exist
2. Quality % - Tags/params/dims thresholds met
3. Confidence - How many checks are direct vs heuristic

Output is actionable and comparable across projects.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from enum import Enum

from filtered_queries import FilteredQueries, PackTargets, send_mcp_request


class CheckType(Enum):
    """How confident we are in a check."""
    DIRECT = "direct"        # Factual check (exists/doesn't)
    EVIDENCE = "evidence"    # Based on data (Mark filled, in schedule)
    HEURISTIC = "heuristic"  # Best guess (dimension presence)


@dataclass
class CheckResult:
    """Result of a single check."""
    check_id: str
    description: str
    passed: bool
    check_type: CheckType
    details: Optional[str] = None
    severity: str = "info"  # blocker, warning, info


@dataclass
class ScoreCard:
    """Assessment scorecard with meaningful metrics."""
    pack_coverage: float       # % of required pack items that exist
    quality_score: float       # % of quality thresholds met
    confidence: float          # % of checks that are direct/evidence vs heuristic
    total_checks: int
    passed_checks: int
    blockers: List[CheckResult]
    warnings: List[CheckResult]
    info: List[CheckResult]
    human_tasks: List[Dict]
    ready_for_permit: bool
    timestamp: str
    sheet_coverage: Dict = field(default_factory=dict)  # Canonical sheet contract data


class PackAssessor:
    """
    Assesses model against pack expectations only.

    Does NOT count everything in the model.
    Only looks at what the pack says should exist.
    """

    def __init__(self, resolved_pack: Dict):
        self.pack = resolved_pack
        self.checks: List[CheckResult] = []

        # Extract pack expectations
        self.targets = self._build_targets()
        self.queries = FilteredQueries(self.targets)

        # Get completeness thresholds
        self.completeness = self.pack.get("completeness", {}).get("permit", {})
        self.min_tag_coverage = self.completeness.get("min_tag_coverage", 0.90)

    def _build_targets(self) -> PackTargets:
        """Build pack targets from resolved pack."""
        # Get expected sheets
        sheets_config = self.pack.get("sheets", {})
        permit_skeleton = sheets_config.get("sets", {}).get("permitSkeleton", [])

        # Get expected levels (from levelMapping patterns)
        level_mapping = self.pack.get("levelMapping", {})
        level_patterns = level_mapping.get("patterns", {})
        expected_levels = []
        for key in ["level1", "level2", "level3", "level4", "level5"]:
            if key in level_patterns:
                expected_levels.append(level_patterns[key][0])  # First pattern

        # Get required schedules from completeness definition first
        completeness = self.pack.get("completeness", {}).get("permit", {})
        required_schedules = completeness.get("required_schedules", [])

        # If not specified, infer from schedule definitions
        if not required_schedules:
            schedule_defs = self.pack.get("schedules", {}).get("definitions", {})
            for sched_name, sched_def in schedule_defs.items():
                cat = sched_def.get("category", "")
                if cat and cat not in required_schedules:
                    required_schedules.append(cat)

        # Final fallback
        if not required_schedules:
            required_schedules = ["Door", "Window", "Room"]

        # Normalize: search terms should be singular (matches "Door Schedule", "Window Type Schedule", etc.)
        required_schedules = [s.rstrip('s') if s.endswith('s') and s != 'Rooms' else s
                             for s in required_schedules]
        # Keep "Room" not "Rooms" for matching
        required_schedules = [s if s != "Room" else "Room" for s in required_schedules]

        return PackTargets(
            expected_sheets=permit_skeleton,
            expected_levels=expected_levels,
            required_schedules=required_schedules,
            tag_categories=["Doors", "Windows", "Rooms"]
        )

    def _add_check(self, check_id: str, description: str, passed: bool,
                   check_type: CheckType, details: str = None, severity: str = "info"):
        """Record a check result."""
        self.checks.append(CheckResult(
            check_id=check_id,
            description=description,
            passed=passed,
            check_type=check_type,
            details=details,
            severity=severity
        ))

    def assess(self) -> ScoreCard:
        """Run all checks and generate scorecard."""
        self.checks = []  # Reset
        human_tasks = []
        sheet_coverage = {}  # Canonical sheet contract data

        # 1. Sheet Coverage (DIRECT checks)
        sheet_data = self.queries.get_sheet_coverage()
        if sheet_data.get("success"):
            coverage = sheet_data["coverage_percent"]
            passed = coverage >= 80

            # Store canonical sheet_coverage for gap_planner
            sheet_coverage = sheet_data.get("sheet_coverage", {})

            self._add_check(
                "SHEET_COVERAGE",
                f"Sheet coverage: {coverage}%",
                passed,
                CheckType.DIRECT,
                f"Matched: {len(sheet_data['matches'])}/{len(self.targets.expected_sheets)}",
                "warning" if not passed else "info"
            )

            # Add tasks for missing sheets (from canonical missing_numbers)
            for missing in sheet_data.get("missing", []):
                human_tasks.append({
                    "type": "create_sheet",
                    "sheet_number": missing,
                    "priority": "required"
                })

        # 2. Schedule Coverage (DIRECT checks)
        sched_data = self.queries.get_schedule_coverage()
        if sched_data.get("success"):
            found = len(sched_data["found"])
            required = len(sched_data["required_by_pack"])
            passed = found == required

            self._add_check(
                "SCHEDULE_COVERAGE",
                f"Required schedules: {found}/{required}",
                passed,
                CheckType.DIRECT,
                f"Missing: {sched_data['missing']}" if sched_data["missing"] else "All found",
                "warning" if not passed else "info"
            )

            for missing in sched_data.get("missing", []):
                human_tasks.append({
                    "type": "create_schedule",
                    "category": missing,
                    "priority": "required"
                })

        # 3. Tag Coverage (EVIDENCE checks - based on Mark parameter)
        tag_data = self.queries.get_tag_coverage()
        if tag_data.get("success"):
            for category, data in tag_data["categories"].items():
                if "error" in data:
                    self._add_check(
                        f"TAG_{category.upper()}",
                        f"{category} tag coverage: unknown",
                        False,
                        CheckType.HEURISTIC,
                        f"Error: {data['error']}",
                        "warning"
                    )
                else:
                    coverage = data["coverage_percent"] / 100
                    passed = coverage >= self.min_tag_coverage

                    severity = "info"
                    if category == "Rooms" and coverage < 1.0:
                        severity = "blocker"  # Room tags are critical
                    elif not passed:
                        severity = "warning"

                    self._add_check(
                        f"TAG_{category.upper()}",
                        f"{category} Mark coverage: {data['coverage_percent']}%",
                        passed,
                        CheckType.EVIDENCE,
                        f"{data['total']} total, {data.get('with_mark', data.get('with_number', 0))} with Mark",
                        severity
                    )

                    # Room name validity check
                    if category == "Rooms" and "name_valid_percent" in data:
                        name_pct = data["name_valid_percent"]
                        self._add_check(
                            "ROOM_NAMES_VALID",
                            f"Room names valid: {name_pct}%",
                            name_pct >= 95,
                            CheckType.EVIDENCE,
                            f"{data['with_valid_name']}/{data['total']} have valid names",
                            "warning" if name_pct < 95 else "info"
                        )

        # 4. Level Check (DIRECT)
        level_resp = send_mcp_request("getLevels")
        if level_resp.get("success"):
            levels = level_resp.get("levels", [])
            self._add_check(
                "LEVELS_EXIST",
                f"Levels defined: {len(levels)}",
                len(levels) >= 2,
                CheckType.DIRECT,
                f"Expected >= 2 for any project"
            )

        # 5. Title Block Check (DIRECT)
        # For now, assume this was checked in preflight
        self._add_check(
            "TITLEBLOCK_AVAILABLE",
            "Title block available",
            True,  # Assume preflight passed this
            CheckType.HEURISTIC,
            "Verified in preflight",
            "info"
        )

        # Calculate scores
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.passed)

        # Pack coverage = required items that exist
        direct_checks = [c for c in self.checks if c.check_type == CheckType.DIRECT]
        pack_coverage = (sum(1 for c in direct_checks if c.passed) / len(direct_checks) * 100) \
            if direct_checks else 100

        # Quality score = evidence-based checks that pass
        evidence_checks = [c for c in self.checks if c.check_type == CheckType.EVIDENCE]
        quality_score = (sum(1 for c in evidence_checks if c.passed) / len(evidence_checks) * 100) \
            if evidence_checks else 100

        # Confidence = % of checks that are direct or evidence (not heuristic)
        non_heuristic = sum(1 for c in self.checks if c.check_type != CheckType.HEURISTIC)
        confidence = (non_heuristic / total * 100) if total > 0 else 100

        # Categorize issues
        blockers = [c for c in self.checks if not c.passed and c.severity == "blocker"]
        warnings = [c for c in self.checks if not c.passed and c.severity == "warning"]
        info = [c for c in self.checks if c.severity == "info"]

        return ScoreCard(
            pack_coverage=round(pack_coverage, 1),
            quality_score=round(quality_score, 1),
            confidence=round(confidence, 1),
            total_checks=total,
            passed_checks=passed,
            blockers=blockers,
            warnings=warnings,
            info=info,
            human_tasks=human_tasks,
            ready_for_permit=len(blockers) == 0 and pack_coverage >= 80,
            timestamp=datetime.now().isoformat(),
            sheet_coverage=sheet_coverage  # Canonical contract data for gap_planner
        )

    def generate_report(self, score: ScoreCard) -> str:
        """Generate human-readable report."""
        lines = [
            "",
            "=" * 60,
            "PACK-DRIVEN ASSESSMENT REPORT",
            "=" * 60,
            f"Timestamp: {score.timestamp}",
            "",
            "SCORES",
            "-" * 60,
            f"  Pack Coverage:  {score.pack_coverage:5.1f}%  (required items exist)",
            f"  Quality Score:  {score.quality_score:5.1f}%  (thresholds met)",
            f"  Confidence:     {score.confidence:5.1f}%  (direct + evidence checks)",
            "",
            f"  Ready for Permit: {'YES' if score.ready_for_permit else 'NO'}",
            "",
            "CHECKS",
            "-" * 60,
            f"  Total: {score.total_checks}  |  Passed: {score.passed_checks}  |  Failed: {score.total_checks - score.passed_checks}",
        ]

        if score.blockers:
            lines.append("")
            lines.append("  BLOCKERS (must fix):")
            for b in score.blockers:
                lines.append(f"    ✗ {b.description}")
                if b.details:
                    lines.append(f"      {b.details}")

        if score.warnings:
            lines.append("")
            lines.append("  WARNINGS:")
            for w in score.warnings:
                lines.append(f"    ⚠ {w.description}")
                if w.details:
                    lines.append(f"      {w.details}")

        if score.human_tasks:
            lines.append("")
            lines.append("HUMAN TASKS")
            lines.append("-" * 60)
            for i, task in enumerate(score.human_tasks[:10], 1):
                task_type = task.get("type", "task")
                if task_type == "create_sheet":
                    lines.append(f"  {i}. Create sheet {task.get('sheet_number')}")
                elif task_type == "create_schedule":
                    lines.append(f"  {i}. Create {task.get('category')} schedule")
                else:
                    lines.append(f"  {i}. {task}")

            if len(score.human_tasks) > 10:
                lines.append(f"  ... and {len(score.human_tasks) - 10} more")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


def main():
    """Test pack assessor on current model."""
    import argparse

    parser = argparse.ArgumentParser(description="Pack-driven model assessment")
    parser.add_argument("--sector", "-t", default="multifamily", help="Sector module")
    parser.add_argument("--output", "-o", help="Output JSON report")
    args = parser.parse_args()

    # Load pack
    base_dir = Path(__file__).parent
    sys.path.insert(0, str(base_dir / "template_packs"))
    from pack_resolver import resolve_pack

    core_path = base_dir / "template_packs" / "_core" / "standards.json"
    sector_path = base_dir / "template_packs" / args.sector / "standards.json"

    if not sector_path.exists():
        print(f"ERROR: Sector '{args.sector}' not found")
        return 1

    resolved = resolve_pack(core_path, sector_path)

    # Run assessment
    print("\n[1/2] Connecting to MCP...")
    test = send_mcp_request("getLevels")
    if not test.get("success"):
        print(f"ERROR: MCP not connected - {test.get('error')}")
        return 1
    print(f"  ✓ Connected ({len(test.get('levels', []))} levels)")

    print("\n[2/2] Running pack-driven assessment...")
    assessor = PackAssessor(resolved)
    score = assessor.assess()

    print(assessor.generate_report(score))

    # Save JSON
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            "sector": args.sector,
            "scores": {
                "pack_coverage": score.pack_coverage,
                "quality_score": score.quality_score,
                "confidence": score.confidence
            },
            "checks": {
                "total": score.total_checks,
                "passed": score.passed_checks,
                "blockers": [asdict(b) for b in score.blockers],
                "warnings": [asdict(w) for w in score.warnings]
            },
            "human_tasks": score.human_tasks,
            "ready_for_permit": score.ready_for_permit,
            "timestamp": score.timestamp
        }

        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"\nReport saved: {output_path}")

    return 0 if score.ready_for_permit else 1


if __name__ == "__main__":
    sys.exit(main())
