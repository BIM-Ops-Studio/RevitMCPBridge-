"""
Quick Start Examples - Common tasks with RevitMCPBridge

Run this file to test your connection and see examples:
    python quick_start.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.revit_mcp import RevitMCP, RevitMCPError


def test_connection():
    """Test connection to Revit."""
    print("Testing connection to Revit...")
    revit = RevitMCP()

    try:
        levels = revit.get_levels()
        print(f"  SUCCESS! Found {len(levels)} levels")
        return True
    except RevitMCPError as e:
        print(f"  FAILED: {e}")
        return False


def example_get_project_info():
    """Get basic project information."""
    print("\n=== PROJECT INFO ===")
    revit = RevitMCP()

    try:
        info = revit.get_project_info()
        result = info.get("result", info)
        print(f"  Project Name: {result.get('projectName', 'N/A')}")
        print(f"  Project Number: {result.get('projectNumber', 'N/A')}")
        print(f"  Client: {result.get('clientName', 'N/A')}")
        print(f"  Address: {result.get('address', 'N/A')}")
    except RevitMCPError as e:
        print(f"  Error: {e}")


def example_list_levels():
    """List all levels in the project."""
    print("\n=== LEVELS ===")
    revit = RevitMCP()

    levels = revit.get_levels()
    for level in sorted(levels, key=lambda x: x.get("elevation", 0)):
        print(f"  {level.get('name'):<20} Elev: {level.get('elevation', 0):>8.2f}'  ID: {level.get('id')}")


def example_list_wall_types():
    """List available wall types."""
    print("\n=== WALL TYPES ===")
    revit = RevitMCP()

    wall_types = revit.get_wall_types()
    print(f"  Found {len(wall_types)} wall types:")
    for wt in wall_types[:10]:
        print(f"    - {wt.get('name')} (ID: {wt.get('id')})")
    if len(wall_types) > 10:
        print(f"    ... and {len(wall_types) - 10} more")


def example_list_views():
    """List all views by type."""
    print("\n=== VIEWS ===")
    revit = RevitMCP()

    views = revit.get_views()

    # Group by type
    by_type = {}
    for view in views:
        vtype = view.get("viewType", "Unknown")
        if vtype not in by_type:
            by_type[vtype] = []
        by_type[vtype].append(view.get("name", "Unnamed"))

    for vtype, names in sorted(by_type.items()):
        print(f"  {vtype}: {len(names)}")


def example_list_sheets():
    """List all sheets."""
    print("\n=== SHEETS ===")
    revit = RevitMCP()

    sheets = revit.get_sheets()
    print(f"  Found {len(sheets)} sheets:")
    for sheet in sorted(sheets, key=lambda x: x.get("sheetNumber", "")):
        print(f"    {sheet.get('sheetNumber', '?'):<10} {sheet.get('sheetName', 'Unnamed')}")


def example_create_wall():
    """Example: Create a single wall."""
    print("\n=== CREATE WALL EXAMPLE ===")
    revit = RevitMCP()

    # Get first level
    levels = revit.get_levels()
    if not levels:
        print("  No levels found!")
        return

    level = levels[0]
    print(f"  Using level: {level.get('name')}")

    # Create a 20' wall
    result = revit.create_wall(
        start=(0, 0),
        end=(20, 0),
        height=10,
        level_id=level["id"]
    )

    wall_id = result.get("wallId") or result.get("result", {}).get("wallId")
    print(f"  Created wall ID: {wall_id}")


def example_active_view():
    """Get and set active view."""
    print("\n=== ACTIVE VIEW ===")
    revit = RevitMCP()

    result = revit.get_active_view()
    view_info = result.get("result", result)
    print(f"  Current view: {view_info.get('viewName')} ({view_info.get('viewType')})")


def run_all_examples():
    """Run all read-only examples."""
    if not test_connection():
        print("\nCannot connect to Revit. Make sure Revit is open and MCP Bridge is running.")
        return

    example_get_project_info()
    example_list_levels()
    example_list_wall_types()
    example_list_views()
    example_list_sheets()
    example_active_view()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_examples()
