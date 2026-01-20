#!/usr/bin/env python3
"""
Project Profiler - Step 0 for Adaptive Spine

Fingerprints a Revit project and generates a profile JSON.
Run this before spine workflows to detect:
- Levels and their roles
- Available title blocks (with preference matching)
- Model extents
- Existing views (reusable vs create new)
- Capability matrix
- Missing prerequisites

Usage:
    python project_profiler.py [--standards ARKY_SFH_v1]
"""

import json
import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime, timezone


def send_mcp_request(method: str, params: dict = None, timeout: int = 30) -> dict:
    """Send MCP request. Returns response dict."""
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


def load_standards_pack(pack_name: str) -> dict:
    """Load a standards pack JSON file."""
    standards_dir = Path(__file__).parent / "standards"
    pack_path = standards_dir / f"{pack_name}.json"

    if pack_path.exists():
        with open(pack_path) as f:
            return json.load(f)
    return None


def profile_levels(standards: dict = None) -> dict:
    """Profile levels in the project."""
    resp = send_mcp_request("getLevels")

    if not resp.get("success"):
        return {"detected": [], "count": 0, "error": resp.get("error")}

    levels = resp.get("levels", [])
    level_mapping = standards.get("levelMapping", {}).get("patterns", {}) if standards else {}

    detected = []
    for level in levels:
        level_info = {
            "id": level.get("levelId"),
            "name": level.get("name"),
            "elevation": level.get("elevation", 0.0),
            "mappedRole": None
        }

        # Try to map level to a role
        name_lower = level.get("name", "").lower()
        for role, patterns in level_mapping.items():
            if any(p.lower() in name_lower or name_lower in p.lower() for p in patterns):
                level_info["mappedRole"] = role
                break

        detected.append(level_info)

    # Sort by elevation
    detected.sort(key=lambda x: x["elevation"])

    return {
        "detected": detected,
        "count": len(detected),
        "hasRoof": any("roof" in (l.get("mappedRole") or "") for l in detected)
    }


def profile_title_blocks(standards: dict = None) -> dict:
    """Profile available title blocks."""
    resp = send_mcp_request("getTitleblockTypes")

    if not resp.get("success"):
        return {"available": [], "selected": None, "error": resp.get("error")}

    titleblocks = resp.get("titleblocks", [])
    tb_prefs = standards.get("titleBlock", {}) if standards else {}
    preferred_patterns = tb_prefs.get("preferredPatterns", [])
    exclude_patterns = tb_prefs.get("excludePatterns", [])

    available = []
    selected = None

    for tb in titleblocks:
        name = tb.get("familyName", "")
        is_autodesk = any(x in name for x in ["11 x 17", "8.5 x 11", "17 x 22", "22 x 34", "34 x 44"])

        tb_info = {
            "id": tb.get("titleblockId"),
            "name": name,
            "isAutodesk": is_autodesk
        }
        available.append(tb_info)

        # Check if this matches preferences
        if selected is None:
            excluded = any(ex.lower() in name.lower() for ex in exclude_patterns)
            if not excluded:
                for pref in preferred_patterns:
                    if pref.lower() in name.lower():
                        selected = {
                            "id": tb.get("titleblockId"),
                            "name": name,
                            "reason": f"Matched pattern '{pref}' from standards pack"
                        }
                        break

    # If no preference matched, pick first non-Autodesk
    if selected is None:
        for tb in available:
            if not tb["isAutodesk"]:
                selected = {
                    "id": tb["id"],
                    "name": tb["name"],
                    "reason": "First non-Autodesk title block"
                }
                break

    # Ultimate fallback
    if selected is None and available:
        selected = {
            "id": available[0]["id"],
            "name": available[0]["name"],
            "reason": "Default (first available)"
        }

    return {"available": available, "selected": selected}


def profile_model_extents() -> dict:
    """Calculate model extents from walls."""
    resp = send_mcp_request("getWalls")

    if not resp.get("success"):
        return {"error": resp.get("error")}

    walls = resp.get("walls", [])
    if not walls:
        return {"error": "No walls found", "sizeFeet": {"width": 0, "depth": 0, "height": 0}}

    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')

    for w in walls:
        for pt_key in ["startPoint", "endPoint"]:
            pt = w.get(pt_key, {})
            if pt:
                min_x = min(min_x, pt.get("x", 0))
                min_y = min(min_y, pt.get("y", 0))
                min_z = min(min_z, pt.get("z", 0))
                max_x = max(max_x, pt.get("x", 0))
                max_y = max(max_y, pt.get("y", 0))
                max_z = max(max_z, pt.get("z", 0))

        # Also consider wall height
        height = w.get("height", 0)
        base_z = w.get("startPoint", {}).get("z", 0)
        max_z = max(max_z, base_z + height)

    return {
        "min": {"x": round(min_x, 2), "y": round(min_y, 2), "z": round(min_z, 2)},
        "max": {"x": round(max_x, 2), "y": round(max_y, 2), "z": round(max_z, 2)},
        "sizeFeet": {
            "width": round(max_x - min_x, 2),
            "depth": round(max_y - min_y, 2),
            "height": round(max_z - min_z, 2)
        },
        "calculatedFrom": "walls"
    }


def profile_existing_views() -> dict:
    """Profile existing views in the project."""
    resp = send_mcp_request("getViews")

    if not resp.get("success"):
        return {"floorPlans": [], "elevations": [], "sections": [], "schedules": [], "error": resp.get("error")}

    views = resp.get("views", [])

    floor_plans = []
    elevations = []
    sections = []
    schedules = []

    for v in views:
        view_type = v.get("viewType", "")
        view_info = {
            "id": v.get("viewId"),
            "name": v.get("name", ""),
            "canReuse": not v.get("name", "").startswith("ZZ_")  # Don't reuse our generated views
        }

        if "FloorPlan" in view_type:
            view_info["level"] = v.get("levelName", "")
            floor_plans.append(view_info)
        elif "Elevation" in view_type:
            elevations.append(view_info)
        elif "Section" in view_type:
            sections.append(view_info)
        elif "Schedule" in view_type:
            schedules.append(view_info)

    return {
        "floorPlans": floor_plans,
        "elevations": elevations,
        "sections": sections,
        "schedules": schedules
    }


def profile_existing_sheets() -> dict:
    """Profile existing sheets in the project."""
    resp = send_mcp_request("getAllSheets")

    if not resp.get("success"):
        return {"count": 0, "error": resp.get("error")}

    sheets = resp.get("sheets", [])

    # Detect numbering pattern
    numbering_pattern = None
    if sheets:
        numbers = [s.get("sheetNumber", "") for s in sheets]
        if any("." in n and n.count(".") >= 2 for n in numbers):
            numbering_pattern = "dot-category"  # A1.0.1 style
        elif any("-" in n for n in numbers):
            numbering_pattern = "dash-suffix"  # A1.01-xxxx style
        else:
            numbering_pattern = "standard"  # A101 style

    return {
        "count": len(sheets),
        "numberingPattern": numbering_pattern,
        "lastNumber": sheets[-1].get("sheetNumber") if sheets else None
    }


def infer_project_type(levels: dict, extents: dict) -> str:
    """Infer project type from profile data."""
    level_count = levels.get("count", 0)
    footprint = extents.get("sizeFeet", {})
    width = footprint.get("width", 0)
    depth = footprint.get("depth", 0)
    area = width * depth

    if level_count >= 3 or area > 10000:
        return "Multifamily"
    elif level_count == 2 and area > 3000:
        return "Duplex"
    else:
        return "SFH"


def generate_recommendations(profile: dict, standards: dict = None) -> dict:
    """Generate recommendations based on profile."""
    project_type = infer_project_type(profile["levels"], profile["modelExtents"])

    recommendations = {
        "standardsPack": f"ARKY_{project_type}_v1",
        "sheetSet": "permitSkeleton",
        "notes": []
    }

    levels = profile["levels"]
    if levels["count"] == 1:
        recommendations["notes"].append("Single-level model - simpler sheet set")
    elif levels["count"] == 2:
        recommendations["notes"].append(f"{levels['count']}-level model suitable for {project_type} workflow")
    else:
        recommendations["notes"].append(f"{levels['count']}-level model - consider full CD sheet set")

    tb = profile["titleBlocks"]["selected"]
    if tb:
        recommendations["notes"].append(f"Custom title block '{tb['name']}' available")

    extents = profile["modelExtents"]["sizeFeet"]
    recommendations["notes"].append(
        f"Model extents suggest {extents['width']:.0f}' x {extents['depth']:.0f}' building footprint"
    )

    views = profile["existingViews"]
    if not views.get("elevations"):
        recommendations["notes"].append("No elevation views exist - will need to create or skip")

    return recommendations


def identify_missing_prerequisites(profile: dict, standards: dict = None) -> list:
    """Identify missing prerequisites for the workflow."""
    missing = []

    views = profile["existingViews"]
    if not views.get("elevations"):
        missing.append("No elevation views exist - will need to create or skip")

    if not views.get("schedules"):
        missing.append("No schedules exist - will create during workflow")

    levels = profile["levels"]
    if levels["count"] < 2 and standards:
        sheet_set = standards.get("sheetSet", {}).get("permitSkeleton", [])
        level2_sheets = [s for s in sheet_set if s.get("level") == 2 and not s.get("optional")]
        if level2_sheets:
            missing.append("Only 1 level found but sheet set requires Level 2")

    return missing


def profile_project(standards_pack_name: str = None) -> dict:
    """Generate complete project profile."""
    print("=" * 60)
    print("PROJECT PROFILER - Step 0")
    print("=" * 60)

    # Load standards pack if specified
    standards = None
    if standards_pack_name:
        standards = load_standards_pack(standards_pack_name)
        if standards:
            print(f"Loaded standards pack: {standards_pack_name}")
        else:
            print(f"Warning: Standards pack '{standards_pack_name}' not found")

    print("\n[1/6] Profiling levels...")
    levels = profile_levels(standards)
    print(f"  Found {levels['count']} levels")

    print("\n[2/6] Profiling title blocks...")
    title_blocks = profile_title_blocks(standards)
    selected_tb = title_blocks.get("selected", {})
    print(f"  Selected: {selected_tb.get('name', 'None')} ({selected_tb.get('reason', '')})")

    print("\n[3/6] Calculating model extents...")
    extents = profile_model_extents()
    size = extents.get("sizeFeet", {})
    print(f"  Size: {size.get('width', 0):.0f}' x {size.get('depth', 0):.0f}' x {size.get('height', 0):.0f}'")

    print("\n[4/6] Profiling existing views...")
    views = profile_existing_views()
    print(f"  Floor plans: {len(views.get('floorPlans', []))}")
    print(f"  Elevations: {len(views.get('elevations', []))}")
    print(f"  Sections: {len(views.get('sections', []))}")

    print("\n[5/6] Profiling existing sheets...")
    sheets = profile_existing_sheets()
    print(f"  Sheets: {sheets['count']}")

    print("\n[6/6] Generating recommendations...")

    # Build profile
    profile = {
        "$schema": "project-profile-v1",
        "projectName": "Unknown",  # Would need project info API
        "profiledAt": datetime.now(timezone.utc).isoformat(),
        "profileVersion": "1.0.0",
        "environment": {
            "revitVersion": "2026.2",
            "mcpBridgeVersion": "1.0.0"
        },
        "levels": levels,
        "titleBlocks": title_blocks,
        "modelExtents": extents,
        "existingViews": views,
        "existingSheets": sheets,
        "capabilityMatrix": {
            "can_place_floorplan": True,
            "can_place_elevation": "not_tested",
            "can_place_schedule": False,
            "can_place_legend": False,
            "can_export_csv": True
        }
    }

    profile["missingPrerequisites"] = identify_missing_prerequisites(profile, standards)
    profile["recommendations"] = generate_recommendations(profile, standards)

    print(f"  Recommended pack: {profile['recommendations']['standardsPack']}")
    for note in profile['recommendations']['notes']:
        print(f"  - {note}")

    return profile


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Profile a Revit project")
    parser.add_argument("--standards", "-s", help="Standards pack name (e.g., ARKY_SFH_v1)")
    parser.add_argument("--output", "-o", help="Output profile path")
    args = parser.parse_args()

    profile = profile_project(args.standards)

    # Save profile
    if args.output:
        output_path = Path(args.output)
    else:
        profiles_dir = Path(__file__).parent / "profiles"
        profiles_dir.mkdir(exist_ok=True)
        output_path = profiles_dir / f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Profile saved: {output_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
