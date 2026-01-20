"""
Sheet Automation - Create and populate sheets automatically

Usage:
    python sheet_automation.py

Or as module:
    from workflows.sheet_automation import create_sheet_set
    create_sheet_set("A", ["Floor Plans", "Elevations", "Sections"])
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.revit_mcp import RevitMCP, RevitMCPError
from typing import List, Dict, Optional, Tuple
import time


# Standard sheet numbering patterns
SHEET_PATTERNS = {
    "architectural": {
        "prefix": "A",
        "categories": [
            ("0", "General"),
            ("1", "Floor Plans"),
            ("2", "Elevations"),
            ("3", "Sections"),
            ("4", "Details"),
            ("5", "Schedules"),
            ("6", "Interior Elevations"),
            ("7", "Ceiling Plans"),
        ]
    },
    "structural": {
        "prefix": "S",
        "categories": [
            ("1", "Plans"),
            ("2", "Elevations"),
            ("3", "Details"),
            ("4", "Schedules"),
        ]
    },
    "mep": {
        "prefix": "M",
        "categories": [
            ("1", "Mechanical Plans"),
            ("2", "Plumbing Plans"),
            ("3", "Electrical Plans"),
        ]
    }
}


def create_sheet_set(
    discipline: str = "architectural",
    categories: Optional[List[str]] = None,
    start_number: int = 1
) -> Dict:
    """
    Create a set of sheets based on discipline patterns.

    Args:
        discipline: "architectural", "structural", or "mep"
        categories: Optional list of specific categories to create
        start_number: Starting sheet number within category

    Returns:
        dict with created sheets
    """
    revit = RevitMCP()

    pattern = SHEET_PATTERNS.get(discipline, SHEET_PATTERNS["architectural"])
    prefix = pattern["prefix"]

    results = {"sheets": [], "errors": []}

    for cat_num, cat_name in pattern["categories"]:
        if categories and cat_name not in categories:
            continue

        sheet_number = f"{prefix}{cat_num}0{start_number}"
        sheet_name = cat_name.upper()

        try:
            result = revit.create_sheet(
                number=sheet_number,
                name=sheet_name
            )
            sheet_id = result.get("sheetId") or result.get("result", {}).get("sheetId")
            results["sheets"].append({
                "number": sheet_number,
                "name": sheet_name,
                "id": sheet_id
            })
            print(f"  Created: {sheet_number} - {sheet_name}")
            time.sleep(0.1)
        except RevitMCPError as e:
            results["errors"].append(f"{sheet_number}: {str(e)}")
            print(f"  Failed: {sheet_number} - {e}")

    return results


def create_custom_sheets(sheets: List[Dict]) -> Dict:
    """
    Create custom sheets from a list of definitions.

    Args:
        sheets: List of dicts with "number" and "name" keys

    Example:
        sheets = [
            {"number": "A101", "name": "FIRST FLOOR PLAN"},
            {"number": "A102", "name": "SECOND FLOOR PLAN"},
        ]
        create_custom_sheets(sheets)
    """
    revit = RevitMCP()
    results = {"sheets": [], "errors": []}

    for sheet in sheets:
        try:
            result = revit.create_sheet(
                number=sheet["number"],
                name=sheet["name"]
            )
            sheet_id = result.get("sheetId") or result.get("result", {}).get("sheetId")
            results["sheets"].append({**sheet, "id": sheet_id})
            print(f"  Created: {sheet['number']} - {sheet['name']}")
            time.sleep(0.1)
        except RevitMCPError as e:
            results["errors"].append(f"{sheet['number']}: {str(e)}")

    return results


def place_views_on_sheet(
    sheet_id: int,
    views: List[Dict],
    grid_cols: int = 2,
    margin: float = 0.5,
    spacing: float = 0.3
) -> Dict:
    """
    Place multiple views on a sheet in a grid layout.

    Args:
        sheet_id: Target sheet ID
        views: List of dicts with "view_id" key
        grid_cols: Number of columns in grid
        margin: Margin from sheet edge (feet)
        spacing: Spacing between views (feet)

    Returns:
        dict with placement results
    """
    revit = RevitMCP()
    results = {"viewports": [], "errors": []}

    # Calculate positions (assuming 24x36 ARCH D sheet)
    sheet_width = 3.0  # feet (36 inches)
    sheet_height = 2.0  # feet (24 inches)

    usable_width = sheet_width - (2 * margin)
    usable_height = sheet_height - (2 * margin)

    col_width = (usable_width - (spacing * (grid_cols - 1))) / grid_cols
    row_height = 0.8  # Approximate view height

    for i, view_data in enumerate(views):
        col = i % grid_cols
        row = i // grid_cols

        x = margin + (col * (col_width + spacing)) + (col_width / 2)
        y = sheet_height - margin - (row * (row_height + spacing)) - (row_height / 2)

        try:
            result = revit.place_view_on_sheet(
                sheet_id=sheet_id,
                view_id=view_data["view_id"],
                location=(x, y)
            )
            viewport_id = result.get("viewportId") or result.get("result", {}).get("viewportId")
            results["viewports"].append({
                "view_id": view_data["view_id"],
                "viewport_id": viewport_id,
                "location": (x, y)
            })
            print(f"  Placed view {view_data['view_id']} at ({x:.2f}, {y:.2f})")
            time.sleep(0.1)
        except RevitMCPError as e:
            results["errors"].append(f"View {view_data['view_id']}: {str(e)}")

    return results


def auto_populate_sheets(view_type_mapping: Optional[Dict] = None) -> Dict:
    """
    Automatically place views on matching sheets.

    Default mapping:
        - Floor Plan views -> A1xx sheets
        - Elevation views -> A2xx sheets
        - Section views -> A3xx sheets
    """
    revit = RevitMCP()

    if view_type_mapping is None:
        view_type_mapping = {
            "FloorPlan": "A1",
            "Elevation": "A2",
            "Section": "A3",
            "CeilingPlan": "A7",
        }

    # Get all views and sheets
    views = revit.get_views()
    sheets = revit.get_sheets()

    results = {"placements": [], "skipped": []}

    # Group sheets by prefix
    sheet_by_prefix = {}
    for sheet in sheets:
        number = sheet.get("number", "")
        prefix = number[:2] if len(number) >= 2 else ""
        if prefix not in sheet_by_prefix:
            sheet_by_prefix[prefix] = []
        sheet_by_prefix[prefix].append(sheet)

    # Place views on matching sheets
    for view in views:
        view_type = view.get("viewType", "")
        view_name = view.get("name", "")
        view_id = view.get("id")

        # Skip templates and schedules
        if view.get("isTemplate") or view_type == "Schedule":
            continue

        # Find matching sheet prefix
        sheet_prefix = view_type_mapping.get(view_type)
        if not sheet_prefix:
            results["skipped"].append(f"{view_name} ({view_type}): No matching sheet type")
            continue

        # Find available sheet
        available_sheets = sheet_by_prefix.get(sheet_prefix, [])
        if not available_sheets:
            results["skipped"].append(f"{view_name}: No {sheet_prefix}xx sheets found")
            continue

        # Place on first available sheet
        target_sheet = available_sheets[0]
        try:
            result = revit.place_view_on_sheet(
                sheet_id=target_sheet["id"],
                view_id=view_id,
                location=(1.5, 1.0)  # Center-ish
            )
            results["placements"].append({
                "view": view_name,
                "sheet": target_sheet.get("number"),
                "success": True
            })
            print(f"  {view_name} -> {target_sheet.get('number')}")
        except RevitMCPError as e:
            results["placements"].append({
                "view": view_name,
                "sheet": target_sheet.get("number"),
                "success": False,
                "error": str(e)
            })

        time.sleep(0.1)

    return results


def list_sheets_summary() -> None:
    """Print a summary of all sheets in the project."""
    revit = RevitMCP()
    sheets = revit.get_sheets()

    print(f"\n=== SHEETS IN PROJECT ({len(sheets)}) ===\n")

    # Group by discipline
    by_discipline = {}
    for sheet in sheets:
        number = sheet.get("number", "?")
        prefix = number[0] if number else "?"
        if prefix not in by_discipline:
            by_discipline[prefix] = []
        by_discipline[prefix].append(sheet)

    for prefix in sorted(by_discipline.keys()):
        discipline_sheets = by_discipline[prefix]
        print(f"{prefix} Series ({len(discipline_sheets)} sheets):")
        for sheet in sorted(discipline_sheets, key=lambda x: x.get("number", "")):
            print(f"  {sheet.get('number'):<10} {sheet.get('name', 'Unnamed')}")
        print()


if __name__ == "__main__":
    print("=== SHEET AUTOMATION ===\n")

    # List current sheets
    list_sheets_summary()

    # Example: Create architectural sheet set
    # print("\nCreating architectural sheets...")
    # result = create_sheet_set("architectural")
    # print(f"\nCreated {len(result['sheets'])} sheets")
