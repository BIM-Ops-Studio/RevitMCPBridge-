#!/usr/bin/env python3
"""
State Assessment - Analyze current project state vs standards

These analyzers understand what's already done vs missing,
enabling gap-based planning (only do what's needed).

Usage:
    from state_assessment import StateAssessor

    assessor = StateAssessor(standards_pack)
    state = assessor.assess_all()
    gaps = assessor.find_gaps(state)
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

# Import canonical sheet contract
from sheet_contract import compare_sheets, get_missing_sheet_numbers


class CoverageLevel(Enum):
    NONE = "none"        # 0%
    PARTIAL = "partial"  # 1-89%
    GOOD = "good"        # 90-99%
    COMPLETE = "complete"  # 100%


@dataclass
class SheetAnalysis:
    """Analysis of sheet set coverage."""
    existing_sheets: List[Dict]
    expected_sheets: List[Dict]
    missing_sheets: List[Dict]
    extra_sheets: List[Dict]
    naming_issues: List[Dict]
    coverage_percent: float
    sheet_coverage: Dict = field(default_factory=dict)  # Canonical contract data

    @property
    def coverage_level(self) -> CoverageLevel:
        if self.coverage_percent == 0:
            return CoverageLevel.NONE
        elif self.coverage_percent < 90:
            return CoverageLevel.PARTIAL
        elif self.coverage_percent < 100:
            return CoverageLevel.GOOD
        else:
            return CoverageLevel.COMPLETE


@dataclass
class ViewAnalysis:
    """Analysis of view coverage."""
    floor_plans: Dict[str, Dict]  # level -> view info
    missing_plans: List[str]      # levels without plans
    wrong_scale_views: List[Dict]
    wrong_template_views: List[Dict]
    orphan_views: List[Dict]      # views not on any sheet
    elevation_count: int
    section_count: int


@dataclass
class TagAnalysis:
    """Analysis of tag coverage."""
    doors: Dict[str, Any]    # {total, tagged, untagged, coverage_pct, untagged_ids}
    windows: Dict[str, Any]
    rooms: Dict[str, Any]

    @property
    def overall_coverage(self) -> float:
        total = (self.doors.get("total", 0) +
                self.windows.get("total", 0) +
                self.rooms.get("total", 0))
        if total == 0:
            return 100.0
        tagged = (self.doors.get("tagged", 0) +
                 self.windows.get("tagged", 0) +
                 self.rooms.get("tagged", 0))
        return (tagged / total) * 100


@dataclass
class ScheduleAnalysis:
    """Analysis of schedule completeness."""
    existing_schedules: List[Dict]
    required_schedules: List[str]
    missing_schedules: List[str]
    field_coverage: Dict[str, Dict]  # schedule -> {required, present, missing}
    duplicate_marks: Dict[str, List]  # category -> list of duplicate marks


@dataclass
class DimensionAnalysis:
    """Basic dimension presence analysis."""
    has_overall_dims: bool
    plans_with_dims: int
    plans_without_dims: int
    total_dim_count: int


@dataclass
class ProjectState:
    """Complete state assessment of a project."""
    sheets: SheetAnalysis
    views: ViewAnalysis
    tags: TagAnalysis
    schedules: ScheduleAnalysis
    dimensions: DimensionAnalysis
    timestamp: str
    model_name: str = ""


def send_mcp_request(method: str, params: dict = None, timeout: int = 60) -> dict:
    """Send MCP request to RevitMCPBridge."""
    request = {"method": method}
    if params:
        request["params"] = params

    try:
        # Use larger buffer size and timeout for large responses
        cmd = [
            "powershell.exe", "-Command",
            f'''
            $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
            $pipe.Connect({timeout * 1000})
            $writer = New-Object System.IO.StreamWriter($pipe)
            $reader = New-Object System.IO.StreamReader($pipe)
            $writer.WriteLine('{json.dumps(request).replace("'", "''")}')
            $writer.Flush()
            # Read full response
            $response = $reader.ReadLine()
            $pipe.Close()
            # Output just the JSON (skip any prefix output)
            $jsonStart = $response.IndexOf('{{')
            if ($jsonStart -ge 0) {{ Write-Output $response.Substring($jsonStart) }}
            else {{ Write-Output $response }}
            '''
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)
        output = result.stdout.strip()

        # Find JSON start (skip any shell prefix messages)
        json_start = output.find('{')
        if json_start == -1:
            return {"success": False, "error": f"No JSON in response: {output[:200]}"}

        json_str = output[json_start:]

        # Try to parse - if fails, it might be truncated
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Response might be truncated, try to salvage partial data
            return {"success": False, "error": f"JSON parse error: {str(e)[:100]}", "partial": json_str[:500]}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class StateAssessor:
    """Assesses current project state against standards pack."""

    def __init__(self, standards_pack: Dict):
        self.standards = standards_pack
        self.permit_skeleton = self._get_permit_skeleton()

    def _get_permit_skeleton(self) -> List[Dict]:
        """Get permit skeleton from standards."""
        # Handle both v1 and v2 formats
        if "sheets" in self.standards and "sets" in self.standards["sheets"]:
            # v2 format
            return self.standards["sheets"]["sets"].get("permitSkeleton", [])
        elif "sheetSet" in self.standards:
            # v1 format
            return self.standards["sheetSet"].get("permitSkeleton", [])
        return []

    def assess_all(self) -> ProjectState:
        """Run all assessments and return complete state."""
        return ProjectState(
            sheets=self.analyze_sheets(),
            views=self.analyze_views(),
            tags=self.analyze_tags(),
            schedules=self.analyze_schedules(),
            dimensions=self.analyze_dimensions(),
            timestamp=datetime.now().isoformat()
        )

    def analyze_sheets(self) -> SheetAnalysis:
        """Analyze sheet set coverage using canonical contract."""
        # Get existing sheets from MCP
        resp = send_mcp_request("getAllSheets")
        if resp.get("success"):
            result = resp.get("result", resp)
            existing = result.get("sheets", [])
        else:
            existing = []

        # Use canonical comparison from sheet_contract
        expected = self.permit_skeleton
        sheet_coverage = compare_sheets(existing, expected)

        # Convert to legacy format for backwards compatibility
        missing = [{"number": n} for n in sheet_coverage["missing_numbers"]]
        extra = [{"sheetNumber": n} for n in sheet_coverage["extra_numbers"]]

        return SheetAnalysis(
            existing_sheets=existing,
            expected_sheets=expected,
            missing_sheets=missing,
            extra_sheets=extra,
            naming_issues=sheet_coverage["naming_issues"],
            coverage_percent=sheet_coverage["coverage_percent"],
            sheet_coverage=sheet_coverage  # Canonical contract data
        )

    def analyze_views(self, verbose: bool = False) -> ViewAnalysis:
        """Analyze view coverage and configuration using filtered queries."""
        # Get levels first
        level_resp = send_mcp_request("getLevels")
        if level_resp.get("success"):
            levels = level_resp.get("levels", [])
        else:
            levels = []

        # Filter to relevant levels (not T.O., roof, parapet, etc.)
        skip_patterns = ["t.o.", "b.o.", "roof", "parapet", "beam", "slab"]
        relevant_levels = [l for l in levels
                         if not any(skip in l.get("name", "").lower() for skip in skip_patterns)]

        # Query ONLY floor plan views (not all 2000+ views) - server-side filtering
        floor_plans = {}
        floor_plan_resp = send_mcp_request("getViews", {"viewType": "FloorPlan"}, timeout=60)
        if floor_plan_resp.get("success"):
            result = floor_plan_resp.get("result", floor_plan_resp)
            fp_views = result.get("views", [])
            if verbose:
                print(f"    [DEBUG] FloorPlan views: {len(fp_views)}")

            # Match floor plans to levels
            for view in fp_views:
                view_name = view.get("name", "")
                view_level = view.get("level", "")

                for level in relevant_levels:
                    level_name = level.get("name", "")
                    if (view_level and level_name.lower() == view_level.lower()) or \
                       (level_name.lower() in view_name.lower()):
                        floor_plans[level_name] = view
                        break
        elif verbose:
            print(f"    [DEBUG] FloorPlan query failed: {floor_plan_resp.get('error', 'unknown')[:100]}")

        # Query ONLY elevation views
        elevations = []
        elev_resp = send_mcp_request("getViews", {"viewType": "Elevation"}, timeout=60)
        if elev_resp.get("success"):
            result = elev_resp.get("result", elev_resp)
            elevations = result.get("views", [])
            if verbose:
                print(f"    [DEBUG] Elevation views: {len(elevations)}")

        # Query ONLY section views
        sections = []
        sect_resp = send_mcp_request("getViews", {"viewType": "Section"}, timeout=60)
        if sect_resp.get("success"):
            result = sect_resp.get("result", sect_resp)
            sections = result.get("views", [])
            if verbose:
                print(f"    [DEBUG] Section views: {len(sections)}")

        # Find missing plans
        missing_plans = []
        for level in relevant_levels:
            level_name = level.get("name", "")
            if level_name not in floor_plans:
                missing_plans.append(level_name)

        # Check scales (compare to standards)
        expected_scale = self.standards.get("scales", {}).get("floorPlan", 48)
        wrong_scale = []
        for level_name, view in floor_plans.items():
            view_scale = view.get("scale", 0)
            if view_scale and view_scale != expected_scale:
                wrong_scale.append({
                    "view": view.get("name"),
                    "current_scale": view_scale,
                    "expected_scale": expected_scale
                })

        return ViewAnalysis(
            floor_plans=floor_plans,
            missing_plans=missing_plans,
            wrong_scale_views=wrong_scale,
            wrong_template_views=[],  # Would need template comparison
            orphan_views=[],  # Would need sheet-view mapping
            elevation_count=len(elevations),
            section_count=len(sections)
        )

    def analyze_tags(self) -> TagAnalysis:
        """Analyze tag coverage for doors, windows, rooms."""

        def get_tag_coverage(category: str) -> Dict:
            # Get all elements of category - handle result-wrapped responses
            resp = send_mcp_request("getElementsByCategory", {"category": category})
            if resp.get("success"):
                result = resp.get("result", resp)
                elements = result.get("elements", [])
            else:
                elements = []
            total = len(elements)

            # For now, we can't directly query if tagged
            # Return placeholder - real implementation needs getTaggedElements method
            # Estimate based on Mark parameter being filled
            tagged = 0
            untagged_ids = []

            for elem in elements:
                # Check if Mark parameter is filled (proxy for being tagged)
                mark = elem.get("mark", elem.get("Mark", ""))
                if mark:
                    tagged += 1
                else:
                    untagged_ids.append(elem.get("id"))

            coverage = (tagged / total * 100) if total > 0 else 100

            return {
                "total": total,
                "tagged": tagged,
                "untagged": total - tagged,
                "coverage_pct": round(coverage, 1),
                "untagged_ids": untagged_ids[:10]  # Limit to first 10
            }

        return TagAnalysis(
            doors=get_tag_coverage("Doors"),
            windows=get_tag_coverage("Windows"),
            rooms=get_tag_coverage("Rooms")
        )

    def analyze_schedules(self) -> ScheduleAnalysis:
        """Analyze schedule completeness."""
        # Get existing schedules - handle result-wrapped responses
        resp = send_mcp_request("getSchedules")
        if resp.get("success"):
            result = resp.get("result", resp)
            existing = result.get("schedules", [])
        else:
            existing = []

        existing_names = [s.get("name", "").lower() for s in existing]

        # Determine required schedules from standards
        required = []
        schedule_defs = self.standards.get("schedules", {}).get("definitions", {})
        for sched_name, sched_def in schedule_defs.items():
            required.append(sched_def.get("category", sched_name))

        # Default required if not specified
        if not required:
            required = ["Door", "Window", "Room"]

        # Find missing
        missing = []
        for req in required:
            found = any(req.lower() in name for name in existing_names)
            if not found:
                missing.append(req)

        # Check field coverage for existing schedules
        field_coverage = {}
        for sched in existing:
            sched_name = sched.get("name", "")
            # Would need getScheduleFields method for detailed analysis
            field_coverage[sched_name] = {
                "status": "exists",
                "field_count": sched.get("fieldCount", 0)
            }

        # Check for duplicate marks
        duplicate_marks = {}
        for category in ["Doors", "Windows"]:
            resp = send_mcp_request("getElementsByCategory", {"category": category})
            if resp.get("success"):
                result = resp.get("result", resp)
                elements = result.get("elements", [])
            else:
                elements = []

            marks = {}
            for elem in elements:
                mark = elem.get("mark", "")
                if mark:
                    if mark not in marks:
                        marks[mark] = []
                    marks[mark].append(elem.get("id"))

            duplicates = {mark: ids for mark, ids in marks.items() if len(ids) > 1}
            if duplicates:
                duplicate_marks[category] = duplicates

        return ScheduleAnalysis(
            existing_schedules=existing,
            required_schedules=required,
            missing_schedules=missing,
            field_coverage=field_coverage,
            duplicate_marks=duplicate_marks
        )

    def analyze_dimensions(self) -> DimensionAnalysis:
        """Basic dimension presence check."""
        # Get dimension count - handle result-wrapped responses
        resp = send_mcp_request("getElementsByCategory", {"category": "Dimensions"})
        if resp.get("success"):
            result = resp.get("result", resp)
            dims = result.get("elements", [])
        else:
            dims = []
        total_dims = len(dims)

        # Get floor plan views
        view_resp = send_mcp_request("getViews")
        if view_resp.get("success"):
            result = view_resp.get("result", view_resp)
            views = result.get("views", [])
        else:
            views = []
        floor_plans = [v for v in views if "FloorPlan" in v.get("viewType", "")]

        # For now, can't easily check which views have dimensions
        # This would require getViewDimensions or similar method
        plans_with_dims = 0 if total_dims == 0 else len(floor_plans)  # Rough estimate
        plans_without_dims = len(floor_plans) - plans_with_dims

        return DimensionAnalysis(
            has_overall_dims=total_dims > 0,
            plans_with_dims=plans_with_dims,
            plans_without_dims=plans_without_dims,
            total_dim_count=total_dims
        )

    def find_gaps(self, state: ProjectState) -> Dict[str, List]:
        """
        Find gaps between current state and standards.
        Returns task suggestions to close gaps.
        """
        gaps = {
            "sheets": [],
            "views": [],
            "tags": [],
            "schedules": [],
            "parameters": []
        }

        # Sheet gaps
        for sheet in state.sheets.missing_sheets:
            if not sheet.get("optional"):
                gaps["sheets"].append({
                    "type": "create_sheet",
                    "number": sheet.get("number"),
                    "name": sheet.get("name"),
                    "priority": "required"
                })

        # View gaps
        for level_name in state.views.missing_plans:
            gaps["views"].append({
                "type": "create_floor_plan",
                "level": level_name,
                "priority": "required"
            })

        # Tag gaps
        if state.tags.doors.get("coverage_pct", 100) < 100:
            gaps["tags"].append({
                "type": "tag_doors",
                "count": state.tags.doors.get("untagged", 0),
                "priority": "required" if state.tags.doors.get("coverage_pct", 100) < 90 else "recommended"
            })

        if state.tags.windows.get("coverage_pct", 100) < 100:
            gaps["tags"].append({
                "type": "tag_windows",
                "count": state.tags.windows.get("untagged", 0),
                "priority": "recommended"
            })

        if state.tags.rooms.get("coverage_pct", 100) < 100:
            gaps["tags"].append({
                "type": "tag_rooms",
                "count": state.tags.rooms.get("untagged", 0),
                "priority": "required"  # Room tags are critical
            })

        # Schedule gaps
        for sched in state.schedules.missing_schedules:
            gaps["schedules"].append({
                "type": "create_schedule",
                "category": sched,
                "priority": "required"
            })

        # Duplicate mark issues
        for category, duplicates in state.schedules.duplicate_marks.items():
            for mark, ids in duplicates.items():
                gaps["parameters"].append({
                    "type": "fix_duplicate_mark",
                    "category": category,
                    "mark": mark,
                    "element_count": len(ids),
                    "priority": "blocker"
                })

        return gaps

    def generate_report(self, state: ProjectState, gaps: Dict) -> Dict:
        """Generate human-readable assessment report."""
        # Count gaps by priority
        blockers = []
        required = []
        recommended = []

        for category, gap_list in gaps.items():
            for gap in gap_list:
                if gap.get("priority") == "blocker":
                    blockers.append(gap)
                elif gap.get("priority") == "required":
                    required.append(gap)
                else:
                    recommended.append(gap)

        # Calculate completion as percentage of expected items that exist
        # (not counting items that exceed expectations)
        expected_sheet_count = len([s for s in state.sheets.expected_sheets if not s.get("optional")])
        matched_sheet_count = expected_sheet_count - len(state.sheets.missing_sheets)
        expected_plan_count = len(state.views.floor_plans) + len(state.views.missing_plans)
        actual_plan_count = len(state.views.floor_plans)

        total_expected = expected_sheet_count + max(expected_plan_count, 1)
        total_matched = matched_sheet_count + actual_plan_count
        completion = (total_matched / total_expected * 100) if total_expected > 0 else 100
        completion = min(completion, 100)  # Cap at 100%

        return {
            "summary": {
                "completion_percent": round(completion, 1),
                "ready_for_permit": len(blockers) == 0 and state.sheets.coverage_percent >= 80,
                "blocker_count": len(blockers),
                "required_count": len(required),
                "recommended_count": len(recommended)
            },
            "sheets": {
                "coverage": state.sheets.coverage_percent,
                "existing": len(state.sheets.existing_sheets),
                "expected": len(state.sheets.expected_sheets),
                "missing": len(state.sheets.missing_sheets)
            },
            "views": {
                "floor_plans": len(state.views.floor_plans),
                "missing_plans": len(state.views.missing_plans),
                "elevations": state.views.elevation_count,
                "sections": state.views.section_count
            },
            "tags": {
                "door_coverage": state.tags.doors.get("coverage_pct", 100),
                "window_coverage": state.tags.windows.get("coverage_pct", 100),
                "room_coverage": state.tags.rooms.get("coverage_pct", 100),
                "overall_coverage": state.tags.overall_coverage
            },
            "schedules": {
                "existing": len(state.schedules.existing_schedules),
                "required": len(state.schedules.required_schedules),
                "missing": len(state.schedules.missing_schedules),
                "duplicate_marks": sum(len(v) for v in state.schedules.duplicate_marks.values())
            },
            "blockers": blockers,
            "required_tasks": required,
            "recommended_tasks": recommended
        }


def main():
    """CLI for state assessment."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Assess project state against standards")
    parser.add_argument("--sector", "-t", required=True, help="Sector module")
    parser.add_argument("--output", "-o", help="Output report path")
    args = parser.parse_args()

    # Load standards - add template_packs to path
    base_dir = Path(__file__).parent
    if str(base_dir / "template_packs") not in sys.path:
        sys.path.insert(0, str(base_dir / "template_packs"))
    from pack_resolver import resolve_pack

    core_path = base_dir / "template_packs" / "_core" / "standards.json"
    sector_path = base_dir / "template_packs" / args.sector / "standards.json"

    if not sector_path.exists():
        print(f"ERROR: Sector '{args.sector}' not found")
        return 1

    resolved = resolve_pack(core_path, sector_path)

    # Run assessment
    print("\n" + "=" * 60)
    print("STATE ASSESSMENT")
    print("=" * 60)
    print(f"Sector: {args.sector}")
    print("-" * 60)

    assessor = StateAssessor(resolved)

    # Test MCP connection first
    print("\n[1/5] Testing MCP connection...")
    test_resp = send_mcp_request("getLevels")
    if test_resp.get("success"):
        print(f"  ✓ MCP connected - {len(test_resp.get('levels', []))} levels")
    else:
        print(f"  ✗ MCP failed: {test_resp.get('error', 'unknown')}")
        return 1

    print("\n[2/5] Analyzing sheets...")
    sheets_analysis = assessor.analyze_sheets()
    print(f"  Found {len(sheets_analysis.existing_sheets)} sheets")

    print("\n[3/5] Analyzing views (this may take a moment for large models)...")
    views_analysis = assessor.analyze_views(verbose=True)
    print(f"  Found {len(views_analysis.floor_plans)} floor plans, {views_analysis.elevation_count} elevations")

    print("\n[4/5] Analyzing tags...")
    tags_analysis = assessor.analyze_tags()
    print(f"  Doors: {tags_analysis.doors.get('total', 0)}, Windows: {tags_analysis.windows.get('total', 0)}")

    print("\n[5/5] Analyzing schedules...")
    schedules_analysis = assessor.analyze_schedules()
    print(f"  Found {len(schedules_analysis.existing_schedules)} schedules")

    # Assemble state
    state = ProjectState(
        sheets=sheets_analysis,
        views=views_analysis,
        tags=tags_analysis,
        schedules=schedules_analysis,
        dimensions=assessor.analyze_dimensions(),
        timestamp=datetime.now().isoformat()
    )
    gaps = assessor.find_gaps(state)
    report = assessor.generate_report(state, gaps)

    # Print summary
    print(f"\n[SHEETS]")
    print(f"  Coverage: {report['sheets']['coverage']}%")
    print(f"  Existing: {report['sheets']['existing']}, Missing: {report['sheets']['missing']}")

    print(f"\n[VIEWS]")
    print(f"  Floor Plans: {report['views']['floor_plans']}")
    print(f"  Missing Plans: {report['views']['missing_plans']}")
    print(f"  Elevations: {report['views']['elevations']}, Sections: {report['views']['sections']}")

    print(f"\n[TAGS]")
    print(f"  Doors: {report['tags']['door_coverage']}%")
    print(f"  Windows: {report['tags']['window_coverage']}%")
    print(f"  Rooms: {report['tags']['room_coverage']}%")

    print(f"\n[SCHEDULES]")
    print(f"  Existing: {report['schedules']['existing']}")
    print(f"  Missing: {report['schedules']['missing']}")
    print(f"  Duplicate Marks: {report['schedules']['duplicate_marks']}")

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"  Completion: {report['summary']['completion_percent']}%")
    print(f"  Ready for Permit: {'Yes' if report['summary']['ready_for_permit'] else 'No'}")
    print(f"  Blockers: {report['summary']['blocker_count']}")
    print(f"  Required Tasks: {report['summary']['required_count']}")
    print(f"  Recommended: {report['summary']['recommended_count']}")

    if report["blockers"]:
        print(f"\n  BLOCKERS:")
        for b in report["blockers"]:
            print(f"    - {b['type']}: {b}")

    print("=" * 60)

    # Save report
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved: {output_path}")

    return 0 if report["summary"]["ready_for_permit"] else 1


if __name__ == "__main__":
    sys.exit(main())
