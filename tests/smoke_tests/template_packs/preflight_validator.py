#!/usr/bin/env python3
"""
Preflight Validator - Check project readiness + estimate cost before running

Usage:
    python preflight_validator.py --pack resolved/resolved_multifamily.json
    python preflight_validator.py --sector multifamily  # Auto-resolve then validate

Generates:
    - Readiness checklist (pass/warn/fail items)
    - Cost estimate (task count, MCP calls, time budget)
    - Overall go/no-go recommendation
"""

import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class CheckStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


class Severity(Enum):
    BLOCKER = "blocker"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class CheckResult:
    id: str
    name: str
    status: CheckStatus
    severity: Severity
    message: str
    details: Dict = field(default_factory=dict)
    remediation: str = ""


def send_mcp_request(method: str, params: dict = None, timeout: int = 30) -> dict:
    """Send MCP request to RevitMCPBridge."""
    request = {"method": method}
    if params:
        request["params"] = params

    try:
        cmd = [
            "powershell.exe", "-Command",
            f'''
            $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
            $pipe.Connect({timeout * 1000})
            $writer = New-Object System.IO.StreamWriter($pipe)
            $reader = New-Object System.IO.StreamReader($pipe)
            $writer.WriteLine('{json.dumps(request).replace("'", "''")}')
            $writer.Flush()
            $response = $reader.ReadLine()
            $pipe.Close()
            Write-Output $response
            '''
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        output = result.stdout.strip()

        json_start = output.find('{')
        if json_start == -1:
            return {"success": False, "error": "No JSON in response"}

        return json.loads(output[json_start:])

    except Exception as e:
        return {"success": False, "error": str(e)}


class PreflightValidator:
    """Validates project readiness against a standards pack."""

    def __init__(self, standards_pack: Dict):
        self.pack = standards_pack
        self.results: List[CheckResult] = []
        self.project_data: Dict = {}

    def run_all_checks(self) -> Dict:
        """Run all preflight checks and return summary."""
        print("\n" + "=" * 60)
        print("PREFLIGHT VALIDATION + COST ESTIMATE")
        print("=" * 60)
        print(f"Pack: {self.pack.get('identity', {}).get('name', 'Unknown')}")
        print(f"Type: {self.pack.get('identity', {}).get('projectType', 'Unknown')}")
        print("-" * 60)

        # Environment checks
        print("\n[1/6] Environment checks...")
        self._check_mcp_connection()

        # Template checks
        print("\n[2/6] Template requirements...")
        self._check_title_blocks()

        # Project checks
        print("\n[3/6] Project model checks...")
        self._check_levels()
        self._check_walls()
        self._check_elements()

        # View checks
        print("\n[4/6] View requirements...")
        self._check_existing_views()

        # Custom preflight from pack
        print("\n[5/6] Pack-specific checks...")
        self._run_pack_preflight_checks()

        # Cost estimation
        print("\n[6/6] Cost estimation...")
        cost = self.estimate_cost()
        self._print_cost_estimate(cost)

        # Generate summary
        summary = self._generate_summary()
        summary["cost"] = cost

        return summary

    def _print_cost_estimate(self, cost: Dict):
        """Print cost estimate in readable format."""
        tasks = cost["tasks"]
        mcp = cost["mcp_calls"]
        time_est = cost["time_estimate"]
        budget = cost["budget"]

        print(f"  Workflow Tasks: {tasks['workflow_total']}")
        print(f"    - Sheets: {tasks['create_sheet']}")
        print(f"    - Views: {tasks['create_view']}")
        print(f"    - Viewports: {tasks['place_viewport']}")
        print(f"    - Schedules: {tasks['create_schedule']}")
        print(f"    - Exports: {tasks['export']}")
        print(f"  Cleanup: {tasks['cleanup']} (automatic)")
        print(f"  MCP Calls: {mcp['total']} ({mcp['workflow']} workflow + {mcp['cleanup']} cleanup)")
        print(f"  Est. Time: {time_est['display']}")
        print(f"  Complexity: {cost['complexity']}")
        if budget["within_budget"]:
            print(f"  Budget: ✓ Within limits ({tasks['workflow_total']}/{budget['max_steps']} steps)")
        else:
            print(f"  Budget: ✗ EXCEEDS limits ({tasks['workflow_total']}/{budget['max_steps']} steps)")

    def _check_mcp_connection(self):
        """Check MCP bridge connectivity."""
        resp = send_mcp_request("getLevels", timeout=10)

        if resp.get("success"):
            self.results.append(CheckResult(
                id="MCP_CONNECTED",
                name="MCP Bridge Connected",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                message="RevitMCPBridge is responding"
            ))
            print("  ✓ MCP Bridge connected")
        else:
            self.results.append(CheckResult(
                id="MCP_CONNECTED",
                name="MCP Bridge Connected",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                message=f"Cannot connect: {resp.get('error', 'Unknown error')}",
                remediation="Ensure Revit is running with MCP add-in loaded"
            ))
            print("  ✗ MCP Bridge NOT connected")

    def _check_title_blocks(self):
        """Check title block availability."""
        resp = send_mcp_request("getTitleblockTypes")

        if not resp.get("success"):
            self.results.append(CheckResult(
                id="TITLEBLOCK_CHECK",
                name="Title Block Check",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                message="Could not query title blocks",
                remediation="Ensure MCP connection is working"
            ))
            print("  ✗ Could not query title blocks")
            return

        titleblocks = resp.get("titleblocks", [])
        self.project_data["titleblocks"] = titleblocks

        # Check for preferred patterns
        preferred = self.pack.get("titleBlocks", {}).get("preferredPatterns", [])
        exclude = self.pack.get("titleBlocks", {}).get("excludePatterns", [])

        found_preferred = None
        found_any = None

        for tb in titleblocks:
            name = tb.get("familyName", "")

            # Check excludes
            if any(ex.lower() in name.lower() for ex in exclude):
                continue

            if found_any is None:
                found_any = name

            # Check preferred
            for pref in preferred:
                if pref.lower() in name.lower():
                    found_preferred = name
                    break

        if found_preferred:
            self.results.append(CheckResult(
                id="TITLEBLOCK_PREFERRED",
                name="Preferred Title Block",
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message=f"Found preferred: {found_preferred}",
                details={"titleblock": found_preferred}
            ))
            print(f"  ✓ Preferred title block: {found_preferred}")
        elif found_any:
            self.results.append(CheckResult(
                id="TITLEBLOCK_AVAILABLE",
                name="Title Block Available",
                status=CheckStatus.WARN,
                severity=Severity.WARNING,
                message=f"No preferred, using: {found_any}",
                details={"titleblock": found_any},
                remediation=f"Load preferred title block matching: {preferred}"
            ))
            print(f"  ~ Fallback title block: {found_any}")
        else:
            self.results.append(CheckResult(
                id="TITLEBLOCK_MISSING",
                name="Title Block Missing",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                message="No suitable title block found",
                remediation="Load a title block family into the project"
            ))
            print("  ✗ No suitable title block found")

    def _check_levels(self):
        """Check levels against pack requirements."""
        resp = send_mcp_request("getLevels")

        if not resp.get("success"):
            self.results.append(CheckResult(
                id="LEVELS_CHECK",
                name="Levels Check",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                message="Could not query levels"
            ))
            print("  ✗ Could not query levels")
            return

        levels = resp.get("levels", [])
        self.project_data["levels"] = levels

        # Check against pack level mapping
        level_mapping = self.pack.get("levelMapping", {}).get("patterns", {})
        mapped_levels = {}

        for level in levels:
            name = level.get("name", "").lower()
            for role, patterns in level_mapping.items():
                if any(p.lower() in name or name in p.lower() for p in patterns):
                    mapped_levels[role] = level
                    break

        # Check required levels for permit skeleton
        permit_sheets = self.pack.get("sheets", {}).get("sets", {}).get("permitSkeleton", [])
        required_levels = set()
        for sheet in permit_sheets:
            if sheet.get("viewType") == "FloorPlan" and sheet.get("level"):
                level_num = sheet.get("level")
                if isinstance(level_num, int):
                    required_levels.add(f"level{level_num}")

        missing_levels = required_levels - set(mapped_levels.keys())

        if not missing_levels:
            self.results.append(CheckResult(
                id="LEVELS_MAPPED",
                name="Required Levels Present",
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message=f"Found {len(levels)} levels, {len(mapped_levels)} mapped",
                details={"total": len(levels), "mapped": list(mapped_levels.keys())}
            ))
            print(f"  ✓ Levels: {len(levels)} found, {len(mapped_levels)} mapped")
        else:
            self.results.append(CheckResult(
                id="LEVELS_MISSING",
                name="Missing Required Levels",
                status=CheckStatus.WARN,
                severity=Severity.WARNING,
                message=f"Missing levels: {missing_levels}",
                details={"missing": list(missing_levels)},
                remediation="Create missing levels or skip those sheets"
            ))
            print(f"  ~ Missing levels: {missing_levels}")

    def _check_walls(self):
        """Check if model has walls for extents calculation."""
        resp = send_mcp_request("getWalls")

        if not resp.get("success"):
            self.results.append(CheckResult(
                id="WALLS_CHECK",
                name="Walls Check",
                status=CheckStatus.WARN,
                severity=Severity.WARNING,
                message="Could not query walls"
            ))
            print("  ~ Could not query walls")
            return

        walls = resp.get("walls", [])
        self.project_data["walls"] = walls

        if walls:
            self.results.append(CheckResult(
                id="WALLS_EXIST",
                name="Model Has Walls",
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message=f"Found {len(walls)} walls",
                details={"count": len(walls)}
            ))
            print(f"  ✓ Walls: {len(walls)} found")
        else:
            self.results.append(CheckResult(
                id="WALLS_MISSING",
                name="No Walls Found",
                status=CheckStatus.WARN,
                severity=Severity.WARNING,
                message="No walls - crop regions will use default size",
                remediation="Model walls before running permit skeleton"
            ))
            print("  ~ No walls found")

    def _check_elements(self):
        """Check for doors, windows, rooms."""
        # Doors
        resp = send_mcp_request("getElementsByCategory", {"category": "Doors"})
        door_count = len(resp.get("elements", [])) if resp.get("success") else 0
        self.project_data["door_count"] = door_count

        if door_count > 0:
            print(f"  ✓ Doors: {door_count} found")
        else:
            print("  ~ Doors: 0 (schedule will be empty)")

        # Windows
        resp = send_mcp_request("getElementsByCategory", {"category": "Windows"})
        window_count = len(resp.get("elements", [])) if resp.get("success") else 0
        self.project_data["window_count"] = window_count

        if window_count > 0:
            print(f"  ✓ Windows: {window_count} found")
        else:
            print("  ~ Windows: 0 (schedule will be empty)")

        # Rooms
        resp = send_mcp_request("getRooms")
        room_count = len(resp.get("rooms", [])) if resp.get("success") else 0
        self.project_data["room_count"] = room_count

        if room_count > 0:
            print(f"  ✓ Rooms: {room_count} found")
        else:
            print("  ~ Rooms: 0 (finish schedule will be empty)")

    def _check_existing_views(self):
        """Check for existing views that can be reused."""
        resp = send_mcp_request("getViews")

        if not resp.get("success"):
            print("  ~ Could not query views")
            return

        views = resp.get("views", [])
        self.project_data["views"] = views

        # Categorize views
        floor_plans = [v for v in views if "FloorPlan" in v.get("viewType", "")]
        elevations = [v for v in views if "Elevation" in v.get("viewType", "")]
        sections = [v for v in views if "Section" in v.get("viewType", "")]

        self.results.append(CheckResult(
            id="EXISTING_VIEWS",
            name="Existing Views",
            status=CheckStatus.PASS if views else CheckStatus.INFO,
            severity=Severity.INFO,
            message=f"Plans: {len(floor_plans)}, Elevs: {len(elevations)}, Sects: {len(sections)}",
            details={
                "floor_plans": len(floor_plans),
                "elevations": len(elevations),
                "sections": len(sections)
            }
        ))
        print(f"  ✓ Views: {len(floor_plans)} plans, {len(elevations)} elevations, {len(sections)} sections")

    def _run_pack_preflight_checks(self):
        """Run pack-specific preflight checks."""
        preflight_checks = self.pack.get("filters", {}).get("preflight", [])

        if not preflight_checks:
            print("  (no pack-specific checks defined)")
            return

        for check in preflight_checks:
            # These would need actual implementation based on check type
            # For now, log them as info
            self.results.append(CheckResult(
                id=check.get("id", "CUSTOM_CHECK"),
                name=check.get("name", "Custom Check"),
                status=CheckStatus.SKIP,
                severity=Severity(check.get("severity", "info")),
                message=f"Check defined but not implemented: {check.get('condition', '')}"
            ))
            print(f"  ~ {check.get('name', 'Custom check')}: defined but not implemented")

    def estimate_cost(self) -> Dict:
        """
        Estimate the cost of running the workflow.
        Not dollars - operational cost: task count, MCP calls, time budget.
        """
        # Get sheet set from pack
        permit_skeleton = self.pack.get("sheets", {}).get("sets", {}).get("permitSkeleton", [])

        # Count tasks by type
        sheet_count = len(permit_skeleton)
        floor_plan_sheets = [s for s in permit_skeleton if s.get("viewType") == "FloorPlan"]
        schedule_sheets = [s for s in permit_skeleton if s.get("viewType") == "Schedule"]
        elevation_sheets = [s for s in permit_skeleton if s.get("viewType") in ("Elevation", "InteriorElevation")]

        # Estimate task counts
        create_sheet_tasks = sheet_count
        create_view_tasks = len(floor_plan_sheets)  # Views created for floor plans
        place_viewport_tasks = len(floor_plan_sheets)  # Viewports placed
        create_schedule_tasks = len(schedule_sheets)
        export_tasks = 2  # sheet_list + door_schedule always

        total_tasks = (create_sheet_tasks + create_view_tasks +
                      place_viewport_tasks + create_schedule_tasks + export_tasks)

        # Estimate MCP calls (each task = 1-3 MCP calls typically)
        # Sheet creation: 1 call
        # View creation: 3 calls (create + scale + crop)
        # Viewport: 1 call
        # Schedule: 2 calls (create + add fields)
        # Export: 2 calls each
        mcp_calls = (create_sheet_tasks * 1 +
                    create_view_tasks * 3 +
                    place_viewport_tasks * 1 +
                    create_schedule_tasks * 2 +
                    export_tasks * 2)

        # Cleanup calls (delete each artifact)
        cleanup_calls = create_sheet_tasks + create_view_tasks + create_schedule_tasks + place_viewport_tasks

        total_mcp_calls = mcp_calls + cleanup_calls

        # Estimate time (rough: 1-2 seconds per MCP call average)
        estimated_seconds = total_mcp_calls * 1.5
        estimated_minutes = estimated_seconds / 60

        # Budget limits (from Spine v0.2 defaults)
        max_steps = 30
        max_elapsed_ms = 300000  # 5 minutes

        cost = {
            "tasks": {
                "create_sheet": create_sheet_tasks,
                "create_view": create_view_tasks,
                "place_viewport": place_viewport_tasks,
                "create_schedule": create_schedule_tasks,
                "export": export_tasks,
                "cleanup": cleanup_calls,
                "workflow_total": total_tasks,
                "total": total_tasks + cleanup_calls
            },
            "mcp_calls": {
                "workflow": mcp_calls,
                "cleanup": cleanup_calls,
                "total": total_mcp_calls
            },
            "time_estimate": {
                "seconds": round(estimated_seconds),
                "minutes": round(estimated_minutes, 1),
                "display": f"~{round(estimated_minutes, 1)} min"
            },
            "budget": {
                "max_steps": max_steps,
                "max_elapsed_ms": max_elapsed_ms,
                "within_budget": total_tasks <= max_steps  # Workflow tasks only
            },
            "complexity": self._calculate_complexity(total_tasks, mcp_calls)  # Workflow only
        }

        return cost

    def _calculate_complexity(self, tasks: int, mcp_calls: int) -> str:
        """Categorize run complexity."""
        if tasks <= 10 and mcp_calls <= 30:
            return "LOW"
        elif tasks <= 20 and mcp_calls <= 60:
            return "MEDIUM"
        elif tasks <= 30 and mcp_calls <= 100:
            return "HIGH"
        else:
            return "VERY_HIGH"

    def _generate_summary(self) -> Dict:
        """Generate validation summary with readiness score."""
        # Count by status
        pass_count = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        warn_count = sum(1 for r in self.results if r.status == CheckStatus.WARN)
        fail_count = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        skip_count = sum(1 for r in self.results if r.status == CheckStatus.SKIP)

        # Check for blockers
        blockers = [r for r in self.results if r.status == CheckStatus.FAIL and r.severity == Severity.BLOCKER]

        # Calculate readiness score (simple weighted average)
        total_checks = len(self.results) - skip_count
        if total_checks > 0:
            score = (pass_count * 1.0 + warn_count * 0.5) / total_checks
        else:
            score = 0

        # Determine overall status
        if blockers:
            overall = "RED"
            emoji = "🔴"
        elif score >= 0.8:
            overall = "GREEN"
            emoji = "🟢"
        elif score >= 0.5:
            overall = "YELLOW"
            emoji = "🟡"
        else:
            overall = "RED"
            emoji = "🔴"

        summary = {
            "overall": overall,
            "score": round(score * 100),
            "counts": {
                "pass": pass_count,
                "warn": warn_count,
                "fail": fail_count,
                "skip": skip_count
            },
            "blockers": [{"id": b.id, "message": b.message, "remediation": b.remediation} for b in blockers],
            "project_data": self.project_data,
            "results": [
                {
                    "id": r.id,
                    "name": r.name,
                    "status": r.status.value,
                    "severity": r.severity.value,
                    "message": r.message
                }
                for r in self.results
            ]
        }

        # Print summary
        print("\n" + "=" * 60)
        print("PREFLIGHT SUMMARY")
        print("=" * 60)
        print(f"\n  Readiness: {emoji} {overall} ({summary['score']}%)")
        print(f"  Checks: {pass_count} pass, {warn_count} warn, {fail_count} fail")

        if blockers:
            print(f"\n  BLOCKERS ({len(blockers)}):")
            for b in blockers:
                print(f"    ✗ {b.message}")
                if b.remediation:
                    print(f"      → {b.remediation}")

        print("\n" + "=" * 60)

        return summary


def main():
    parser = argparse.ArgumentParser(description="Preflight validation for template packs")
    parser.add_argument('--pack', '-p', help='Path to resolved standards pack JSON')
    parser.add_argument('--sector', '-s', help='Sector module to auto-resolve and validate')
    parser.add_argument('--output', '-o', help='Output path for validation report')

    args = parser.parse_args()

    packs_dir = Path(__file__).parent

    # Load or resolve pack
    if args.pack:
        pack_path = Path(args.pack)
        if not pack_path.is_absolute():
            pack_path = packs_dir / pack_path
        with open(pack_path) as f:
            pack = json.load(f)
    elif args.sector:
        # Auto-resolve
        from pack_resolver import resolve_pack
        core_path = packs_dir / '_core' / 'standards.json'
        sector_path = packs_dir / args.sector / 'standards.json'
        pack = resolve_pack(core_path, sector_path)
    else:
        parser.error("Must provide --pack or --sector")

    # Run validation
    validator = PreflightValidator(pack)
    summary = validator.run_all_checks()

    # Save report if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nReport saved: {output_path}")

    # Return exit code based on result
    return 0 if summary["overall"] != "RED" else 1


if __name__ == '__main__':
    exit(main())
