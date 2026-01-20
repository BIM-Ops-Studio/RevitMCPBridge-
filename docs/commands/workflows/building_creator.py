"""
Building Creator - Create complete building shells from parameters

Usage:
    python building_creator.py

Or as module:
    from workflows.building_creator import create_simple_house
    create_simple_house(width=30, depth=40, height=10)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.revit_mcp import RevitMCP, RevitMCPError
import time


def create_rectangular_building(
    width: float,
    depth: float,
    wall_height: float,
    level_id: int = None,
    wall_type_id: int = None,
    origin_x: float = 0,
    origin_y: float = 0
) -> dict:
    """
    Create a rectangular building shell with 4 walls.

    Args:
        width: Building width (X direction) in feet
        depth: Building depth (Y direction) in feet
        wall_height: Wall height in feet
        level_id: Level to place walls on (uses first level if None)
        wall_type_id: Wall type to use (uses first available if None)
        origin_x: X coordinate of bottom-left corner
        origin_y: Y coordinate of bottom-left corner

    Returns:
        dict with created wall IDs and summary
    """
    revit = RevitMCP()

    # Get level if not specified
    if level_id is None:
        levels = revit.get_levels()
        if not levels:
            raise RevitMCPError("No levels found in project")
        level_id = levels[0]["id"]
        print(f"Using level: {levels[0]['name']}")

    # Get wall type if not specified
    if wall_type_id is None:
        wall_types = revit.get_wall_types()
        if wall_types:
            # Try to find "Generic - 8\"" or similar basic wall
            for wt in wall_types:
                if "generic" in wt.get("name", "").lower():
                    wall_type_id = wt["id"]
                    print(f"Using wall type: {wt['name']}")
                    break
            if wall_type_id is None:
                wall_type_id = wall_types[0]["id"]
                print(f"Using wall type: {wall_types[0]['name']}")

    # Define wall endpoints
    walls_data = [
        {"name": "South", "start": (origin_x, origin_y), "end": (origin_x + width, origin_y)},
        {"name": "East", "start": (origin_x + width, origin_y), "end": (origin_x + width, origin_y + depth)},
        {"name": "North", "start": (origin_x + width, origin_y + depth), "end": (origin_x, origin_y + depth)},
        {"name": "West", "start": (origin_x, origin_y + depth), "end": (origin_x, origin_y)},
    ]

    results = {"walls": [], "success": True, "errors": []}

    for wall_data in walls_data:
        try:
            result = revit.create_wall(
                start=wall_data["start"],
                end=wall_data["end"],
                height=wall_height,
                level_id=level_id,
                wall_type_id=wall_type_id
            )
            wall_id = result.get("wallId") or result.get("result", {}).get("wallId")
            results["walls"].append({
                "name": wall_data["name"],
                "id": wall_id,
                "start": wall_data["start"],
                "end": wall_data["end"]
            })
            print(f"  Created {wall_data['name']} wall: ID {wall_id}")
            time.sleep(0.1)
        except RevitMCPError as e:
            results["errors"].append(f"{wall_data['name']}: {str(e)}")
            results["success"] = False

    results["summary"] = f"Created {len(results['walls'])} walls, {len(results['errors'])} errors"
    return results


def create_simple_house(
    width: float = 30,
    depth: float = 40,
    wall_height: float = 10,
    num_floors: int = 1,
    floor_height: float = 10
) -> dict:
    """
    Create a simple house with multiple floors.

    Args:
        width: House width in feet
        depth: House depth in feet
        wall_height: Wall height per floor in feet
        num_floors: Number of floors
        floor_height: Height between floor levels

    Returns:
        dict with all created elements
    """
    revit = RevitMCP()
    results = {"floors": [], "total_walls": 0}

    levels = revit.get_levels()
    if not levels:
        raise RevitMCPError("No levels found")

    # Sort levels by elevation
    levels_sorted = sorted(levels, key=lambda x: x.get("elevation", 0))

    for floor_num in range(num_floors):
        if floor_num >= len(levels_sorted):
            print(f"Warning: Not enough levels for floor {floor_num + 1}")
            break

        level = levels_sorted[floor_num]
        print(f"\nCreating floor {floor_num + 1} on level: {level['name']}")

        floor_result = create_rectangular_building(
            width=width,
            depth=depth,
            wall_height=wall_height,
            level_id=level["id"]
        )

        results["floors"].append({
            "floor": floor_num + 1,
            "level": level["name"],
            "walls": floor_result["walls"]
        })
        results["total_walls"] += len(floor_result["walls"])

    print(f"\n=== COMPLETE ===")
    print(f"Created {results['total_walls']} walls across {len(results['floors'])} floors")

    return results


def create_l_shaped_building(
    main_width: float,
    main_depth: float,
    wing_width: float,
    wing_depth: float,
    wall_height: float,
    level_id: int = None
) -> dict:
    """
    Create an L-shaped building.

    Args:
        main_width: Width of main section
        main_depth: Depth of main section
        wing_width: Width of wing section
        wing_depth: Depth of wing section
        wall_height: Wall height
        level_id: Level ID (optional)

    Returns:
        dict with created walls
    """
    revit = RevitMCP()

    if level_id is None:
        levels = revit.get_levels()
        level_id = levels[0]["id"]

    # L-shape walls (main + wing, no duplicate walls)
    walls = [
        # Main section
        {"start": (0, 0), "end": (main_width, 0)},  # South
        {"start": (main_width, 0), "end": (main_width, wing_depth)},  # East lower
        {"start": (main_width, wing_depth), "end": (main_width + wing_width, wing_depth)},  # Wing south
        {"start": (main_width + wing_width, wing_depth), "end": (main_width + wing_width, main_depth)},  # Wing east
        {"start": (main_width + wing_width, main_depth), "end": (0, main_depth)},  # North
        {"start": (0, main_depth), "end": (0, 0)},  # West
    ]

    results = {"walls": [], "success": True}

    for i, wall in enumerate(walls):
        try:
            result = revit.create_wall(
                start=wall["start"],
                end=wall["end"],
                height=wall_height,
                level_id=level_id
            )
            wall_id = result.get("wallId") or result.get("result", {}).get("wallId")
            results["walls"].append({"id": wall_id, **wall})
            print(f"  Wall {i + 1}: ID {wall_id}")
            time.sleep(0.1)
        except RevitMCPError as e:
            print(f"  Wall {i + 1} failed: {e}")
            results["success"] = False

    return results


if __name__ == "__main__":
    print("=== BUILDING CREATOR ===\n")

    # Example: Create a simple 30x40 building
    print("Creating 30' x 40' rectangular building...")
    result = create_rectangular_building(
        width=30,
        depth=40,
        wall_height=10
    )

    print(f"\nResult: {result['summary']}")
