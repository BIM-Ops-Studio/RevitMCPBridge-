"""
Model Audit - Extract and report on model contents

Usage:
    python model_audit.py

Or as module:
    from extraction.model_audit import full_audit
    report = full_audit()
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.revit_mcp import RevitMCP, RevitMCPError
from typing import Dict, List, Optional
from datetime import datetime
import json


def count_elements() -> Dict:
    """Count elements by category."""
    revit = RevitMCP()

    counts = {
        "walls": 0,
        "doors": 0,
        "windows": 0,
        "rooms": 0,
        "levels": 0,
        "views": 0,
        "sheets": 0,
    }

    try:
        walls = revit.get_walls()
        counts["walls"] = len(walls)
    except:
        pass

    try:
        levels = revit.get_levels()
        counts["levels"] = len(levels)
    except:
        pass

    try:
        rooms = revit.get_rooms()
        counts["rooms"] = len(rooms)
    except:
        pass

    try:
        views = revit.get_views()
        counts["views"] = len(views)
    except:
        pass

    try:
        sheets = revit.get_sheets()
        counts["sheets"] = len(sheets)
    except:
        pass

    return counts


def get_wall_summary() -> Dict:
    """Get summary of wall types and lengths."""
    revit = RevitMCP()

    walls = revit.get_walls()
    wall_types = revit.get_wall_types()

    # Create type lookup
    type_names = {wt["id"]: wt.get("name", "Unknown") for wt in wall_types}

    # Group walls by type
    by_type = {}
    total_length = 0

    for wall in walls:
        type_id = wall.get("typeId")
        type_name = type_names.get(type_id, f"Type {type_id}")
        length = wall.get("length", 0)

        if type_name not in by_type:
            by_type[type_name] = {"count": 0, "total_length": 0}

        by_type[type_name]["count"] += 1
        by_type[type_name]["total_length"] += length
        total_length += length

    return {
        "total_walls": len(walls),
        "total_length_ft": round(total_length, 1),
        "by_type": by_type
    }


def get_room_summary() -> Dict:
    """Get summary of rooms."""
    revit = RevitMCP()

    rooms = revit.get_rooms()

    total_area = 0
    by_level = {}

    for room in rooms:
        area = room.get("area", 0)
        level = room.get("level", "Unknown")

        total_area += area

        if level not in by_level:
            by_level[level] = {"count": 0, "total_area": 0}

        by_level[level]["count"] += 1
        by_level[level]["total_area"] += area

    return {
        "total_rooms": len(rooms),
        "total_area_sf": round(total_area, 0),
        "by_level": by_level,
        "rooms": [{"name": r.get("name"), "number": r.get("number"), "area": r.get("area")} for r in rooms]
    }


def get_view_summary() -> Dict:
    """Get summary of views by type."""
    revit = RevitMCP()

    views = revit.get_views()

    by_type = {}
    templates = 0

    for view in views:
        view_type = view.get("viewType", "Unknown")

        if view.get("isTemplate"):
            templates += 1
            continue

        if view_type not in by_type:
            by_type[view_type] = []

        by_type[view_type].append(view.get("name", "Unnamed"))

    return {
        "total_views": len(views),
        "templates": templates,
        "by_type": {k: {"count": len(v), "names": v[:5]} for k, v in by_type.items()}
    }


def get_sheet_summary() -> Dict:
    """Get summary of sheets."""
    revit = RevitMCP()

    sheets = revit.get_sheets()

    by_discipline = {}

    for sheet in sheets:
        number = sheet.get("number", "")
        prefix = number[0] if number else "?"

        discipline_map = {
            "A": "Architectural",
            "S": "Structural",
            "M": "Mechanical",
            "E": "Electrical",
            "P": "Plumbing",
            "G": "General",
        }
        discipline = discipline_map.get(prefix, f"Other ({prefix})")

        if discipline not in by_discipline:
            by_discipline[discipline] = []

        by_discipline[discipline].append({
            "number": number,
            "name": sheet.get("name", "Unnamed")
        })

    return {
        "total_sheets": len(sheets),
        "by_discipline": {k: {"count": len(v), "sheets": v} for k, v in by_discipline.items()}
    }


def full_audit(output_file: Optional[str] = None) -> Dict:
    """
    Perform a full model audit.

    Args:
        output_file: Optional path to save JSON report

    Returns:
        Complete audit report dict
    """
    revit = RevitMCP()

    print("=== MODEL AUDIT ===\n")

    report = {
        "timestamp": datetime.now().isoformat(),
        "project_info": {},
        "element_counts": {},
        "walls": {},
        "rooms": {},
        "views": {},
        "sheets": {}
    }

    # Project info
    print("Getting project info...")
    try:
        info = revit.get_project_info()
        report["project_info"] = info.get("result", info)
    except:
        report["project_info"] = {"error": "Could not retrieve"}

    # Element counts
    print("Counting elements...")
    report["element_counts"] = count_elements()

    # Wall summary
    print("Analyzing walls...")
    try:
        report["walls"] = get_wall_summary()
    except Exception as e:
        report["walls"] = {"error": str(e)}

    # Room summary
    print("Analyzing rooms...")
    try:
        report["rooms"] = get_room_summary()
    except Exception as e:
        report["rooms"] = {"error": str(e)}

    # View summary
    print("Analyzing views...")
    try:
        report["views"] = get_view_summary()
    except Exception as e:
        report["views"] = {"error": str(e)}

    # Sheet summary
    print("Analyzing sheets...")
    try:
        report["sheets"] = get_sheet_summary()
    except Exception as e:
        report["sheets"] = {"error": str(e)}

    # Print summary
    print("\n" + "=" * 50)
    print("AUDIT SUMMARY")
    print("=" * 50)

    counts = report["element_counts"]
    print(f"\nElement Counts:")
    print(f"  Levels:  {counts.get('levels', 'N/A')}")
    print(f"  Walls:   {counts.get('walls', 'N/A')}")
    print(f"  Rooms:   {counts.get('rooms', 'N/A')}")
    print(f"  Views:   {counts.get('views', 'N/A')}")
    print(f"  Sheets:  {counts.get('sheets', 'N/A')}")

    if "walls" in report and "total_length_ft" in report["walls"]:
        print(f"\nWalls:")
        print(f"  Total Length: {report['walls']['total_length_ft']} ft")
        print(f"  Wall Types: {len(report['walls'].get('by_type', {}))}")

    if "rooms" in report and "total_area_sf" in report["rooms"]:
        print(f"\nRooms:")
        print(f"  Total Area: {report['rooms']['total_area_sf']} SF")

    if "sheets" in report and "by_discipline" in report["sheets"]:
        print(f"\nSheets by Discipline:")
        for disc, data in report["sheets"]["by_discipline"].items():
            print(f"  {disc}: {data['count']}")

    # Save to file if requested
    if output_file:
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {output_file}")

    return report


def quick_stats() -> None:
    """Print quick statistics about the model."""
    counts = count_elements()

    print("\n=== QUICK STATS ===")
    for category, count in counts.items():
        print(f"  {category.capitalize()}: {count}")


if __name__ == "__main__":
    # Run full audit
    report = full_audit()

    # Optionally save to file
    # report = full_audit(output_file="model_audit.json")
