#!/usr/bin/env python3
"""
Filtered Queries - Query only what the pack needs, not everything

Solves the large-model problem by:
1. Querying views by type (floor plans only, elevations only)
2. Querying views by sheet placement
3. Never requesting "all views" on models with 1000+

Each query is small enough to fit in subprocess buffer.
"""

import json
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import canonical sheet contract
from sheet_contract import compare_sheets


def send_mcp_request(method: str, params: dict = None, timeout: int = 60) -> dict:
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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)
        output = result.stdout.strip()

        json_start = output.find('{')
        if json_start == -1:
            return {"success": False, "error": f"No JSON in response"}

        json_str = output[json_start:]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON parse error: {str(e)[:100]}"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@dataclass
class PackTargets:
    """What the pack expects us to find/create."""
    expected_sheets: List[Dict]  # From pack's permitSkeleton
    expected_levels: List[str]   # Levels that should have floor plans
    required_schedules: List[str]  # Schedule categories required
    tag_categories: List[str]    # Categories that need tags


class FilteredQueries:
    """
    Query only what the pack needs, not the entire model.

    This avoids the subprocess buffer overflow on large models
    by making targeted, small queries instead of "get everything."
    """

    def __init__(self, pack_targets: PackTargets):
        self.targets = pack_targets

    def get_sheet_coverage(self) -> Dict[str, Any]:
        """
        Get sheets relevant to the pack only.

        Uses canonical sheet_contract.compare_sheets() for consistent identity.
        """
        resp = send_mcp_request("getAllSheets")
        if not resp.get("success"):
            return {"success": False, "error": resp.get("error")}

        result = resp.get("result", resp)
        all_sheets = result.get("sheets", [])

        # Use canonical comparison from sheet_contract
        sheet_coverage = compare_sheets(all_sheets, self.targets.expected_sheets)

        # Return in expected format with canonical data embedded
        return {
            "success": True,
            "total_in_model": len(all_sheets),
            "expected_by_pack": len(self.targets.expected_sheets),
            "matches": list(sheet_coverage["existing_by_number"].keys()),
            "missing": sheet_coverage["missing_numbers"],  # Canonical missing list
            "coverage_percent": sheet_coverage["coverage_percent"],
            "sheet_coverage": sheet_coverage  # Full canonical contract
        }

    def get_floor_plan_coverage(self) -> Dict[str, Any]:
        """
        Get floor plans for expected levels only.

        Uses viewType filter to query only FloorPlan views (not all 2000+ views).
        Then matches to relevant levels.
        """
        # First get levels
        level_resp = send_mcp_request("getLevels")
        if not level_resp.get("success"):
            return {"success": False, "error": level_resp.get("error")}

        levels = level_resp.get("levels", [])
        level_names = [l.get("name", "") for l in levels]

        # Filter to levels we care about (not T.O., B.O., etc.)
        relevant_levels = []
        skip_patterns = ["t.o.", "b.o.", "parapet", "beam", "slab", "roof"]
        for name in level_names:
            if not any(skip in name.lower() for skip in skip_patterns):
                relevant_levels.append(name)

        # Query ONLY floor plan views (not all views) - uses server-side filtering
        floor_plan_resp = send_mcp_request("getViews", {"viewType": "FloorPlan"}, timeout=60)

        floor_plans_found = {}
        views_data = []

        if floor_plan_resp.get("success"):
            result = floor_plan_resp.get("result", floor_plan_resp)
            views_data = result.get("views", [])

            # Match floor plans to levels
            for view in views_data:
                view_name = view.get("name", "")
                view_level = view.get("level", "")

                # Match by level name or by view name containing level name
                for level_name in relevant_levels:
                    if (view_level and level_name.lower() == view_level.lower()) or \
                       (level_name.lower() in view_name.lower()):
                        if level_name not in floor_plans_found:
                            floor_plans_found[level_name] = []
                        floor_plans_found[level_name].append({
                            "id": view.get("id"),
                            "name": view_name,
                            "scale": view.get("scale", 0)
                        })

        # Find levels without floor plans
        missing_levels = [l for l in relevant_levels if l not in floor_plans_found]

        return {
            "success": True,
            "total_levels": len(levels),
            "relevant_levels": len(relevant_levels),
            "floor_plans_found": len(floor_plans_found),
            "total_floor_plan_views": len(views_data),
            "levels_with_plans": list(floor_plans_found.keys()),
            "levels_without_plans": missing_levels,
            "floor_plans": floor_plans_found,
            "coverage_percent": round(len(floor_plans_found) / len(relevant_levels) * 100, 1) if relevant_levels else 100.0
        }

    def get_schedule_coverage(self) -> Dict[str, Any]:
        """
        Check for required schedules only.

        The schedule list is typically small (<100), so this is safe to query fully.
        We then filter to what the pack requires.
        """
        resp = send_mcp_request("getSchedules")
        if not resp.get("success"):
            return {"success": False, "error": resp.get("error")}

        result = resp.get("result", resp)
        schedules = result.get("schedules", [])
        schedule_names = [s.get("name", "").lower() for s in schedules]

        # Check for required schedules
        coverage = {
            "success": True,
            "total_in_model": len(schedules),
            "required_by_pack": self.targets.required_schedules,
            "found": [],
            "missing": []
        }

        for required in self.targets.required_schedules:
            # Fuzzy match: "Door" matches "Door Schedule", "DOOR SCHEDULE - COMMON AREAS", etc.
            found = any(required.lower() in name for name in schedule_names)
            if found:
                coverage["found"].append(required)
            else:
                coverage["missing"].append(required)

        return coverage

    def get_tag_coverage(self) -> Dict[str, Any]:
        """
        Check tag coverage for required categories.

        Uses specific methods: getDoors, getWindows, getRooms
        Each returns manageable data with Mark values.
        """
        # Map category names to MCP methods and response keys
        category_methods = {
            "Doors": ("getDoors", "doors", "doorCount"),
            "Windows": ("getWindows", "windows", "windowCount"),
            "Rooms": ("getRooms", "rooms", "roomCount")
        }

        results = {}

        for category in self.targets.tag_categories:
            if category not in category_methods:
                results[category] = {"total": 0, "error": f"Unknown category: {category}"}
                continue

            method, items_key, count_key = category_methods[category]
            elem_resp = send_mcp_request(method, timeout=90)

            if elem_resp.get("success"):
                # Handle both direct and result-wrapped responses
                data = elem_resp.get("result", elem_resp)
                elements = data.get(items_key, [])
                total = data.get(count_key, len(elements))

                # Check Mark parameter as proxy for "tagged"
                # Doors/Windows have "mark", Rooms have "number" (room number is their "mark")
                if category == "Rooms":
                    with_mark = sum(1 for e in elements
                                   if e.get("number") and str(e.get("number")).strip())
                    # Also check for proper names (not "Room" or blank)
                    valid_names = sum(1 for e in elements
                                     if e.get("name") and
                                     e.get("name").strip().lower() not in ["room", "unnamed", ""])
                    results[category] = {
                        "total": total,
                        "with_number": with_mark,
                        "with_valid_name": valid_names,
                        "coverage_percent": round(with_mark / total * 100, 1) if total > 0 else 100.0,
                        "name_valid_percent": round(valid_names / total * 100, 1) if total > 0 else 100.0
                    }
                else:
                    with_mark = sum(1 for e in elements
                                   if e.get("mark") and str(e.get("mark")).strip()
                                   and str(e.get("mark")).strip() != "00")  # "00" is often a placeholder
                    results[category] = {
                        "total": total,
                        "with_mark": with_mark,
                        "coverage_percent": round(with_mark / total * 100, 1) if total > 0 else 100.0
                    }
            else:
                results[category] = {
                    "total": 0,
                    "error": elem_resp.get("error", "Query failed")
                }

        return {
            "success": True,
            "categories": results
        }

    def run_all(self) -> Dict[str, Any]:
        """Run all filtered queries and return combined results."""
        return {
            "sheets": self.get_sheet_coverage(),
            "floor_plans": self.get_floor_plan_coverage(),
            "schedules": self.get_schedule_coverage(),
            "tags": self.get_tag_coverage()
        }


def test_with_multifamily():
    """Test filtered queries with multifamily pack targets."""
    # Define what multifamily pack expects
    targets = PackTargets(
        expected_sheets=[
            {"number": "G0.01", "name": "COVER SHEET"},
            {"number": "G0.02", "name": "CODE ANALYSIS"},
            {"number": "G0.03", "name": "LIFE SAFETY PLAN"},
            {"number": "A1.0.1", "name": "FLOOR PLAN - LEVEL 1"},
            {"number": "A1.0.2", "name": "FLOOR PLAN - LEVEL 2"},
            {"number": "A1.0.3", "name": "FLOOR PLAN - LEVEL 3"},
            {"number": "A2.0.1", "name": "ELEVATIONS NORTH/SOUTH"},
            {"number": "A2.0.2", "name": "ELEVATIONS EAST/WEST"},
            {"number": "A5.0.1", "name": "DOOR SCHEDULE"},
            {"number": "A5.0.2", "name": "WINDOW SCHEDULE"},
        ],
        expected_levels=["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"],
        required_schedules=["Door", "Window", "Room"],
        tag_categories=["Doors", "Windows", "Rooms"]
    )

    queries = FilteredQueries(targets)

    print("\n" + "=" * 60)
    print("FILTERED QUERIES TEST (pack-driven)")
    print("=" * 60)

    # Sheets
    print("\n[1] Sheet Coverage")
    sheets = queries.get_sheet_coverage()
    if sheets.get("success"):
        print(f"  Model sheets: {sheets['total_in_model']}")
        print(f"  Pack expects: {sheets['expected_by_pack']}")
        print(f"  Matched: {len(sheets['matches'])}")
        print(f"  Missing: {sheets['missing']}")
        print(f"  Coverage: {sheets['coverage_percent']}%")
    else:
        print(f"  ERROR: {sheets.get('error')}")

    # Schedules
    print("\n[2] Schedule Coverage")
    schedules = queries.get_schedule_coverage()
    if schedules.get("success"):
        print(f"  Model schedules: {schedules['total_in_model']}")
        print(f"  Required: {schedules['required_by_pack']}")
        print(f"  Found: {schedules['found']}")
        print(f"  Missing: {schedules['missing']}")
    else:
        print(f"  ERROR: {schedules.get('error')}")

    # Tags
    print("\n[3] Tag Coverage")
    tags = queries.get_tag_coverage()
    if tags.get("success"):
        for cat, data in tags["categories"].items():
            if "error" in data:
                print(f"  {cat}: ERROR - {data['error']}")
            else:
                print(f"  {cat}: {data['total']} total, {data['coverage_percent']}% with Mark")
    else:
        print(f"  ERROR: {tags.get('error')}")

    # Floor plans (now with real data!)
    print("\n[4] Floor Plan Coverage")
    plans = queries.get_floor_plan_coverage()
    if plans.get("success"):
        print(f"  Total levels: {plans.get('total_levels')}")
        print(f"  Relevant levels: {plans.get('relevant_levels')}")
        print(f"  Floor plans found: {plans.get('floor_plans_found')}")
        print(f"  Total floor plan views: {plans.get('total_floor_plan_views')}")
        print(f"  Coverage: {plans.get('coverage_percent')}%")
        if plans.get('levels_without_plans'):
            print(f"  Missing plans for: {plans.get('levels_without_plans')}")
    else:
        print(f"  ERROR: {plans.get('error')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_with_multifamily()
