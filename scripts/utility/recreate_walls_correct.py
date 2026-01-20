#!/usr/bin/env python3
"""
Recreate walls with CORRECT 28'-8" depth (not 38').
This script deletes all existing walls and creates new ones.
"""

import json
import win32file
import time

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call_mcp(method, params=None):
    """Call MCP method via named pipe."""
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None, win32file.OPEN_EXISTING, 0, None
        )
        request = {"method": method, "params": params or {}}
        message = json.dumps(request) + '\n'
        win32file.WriteFile(handle, message.encode('utf-8'))

        response_data = b''
        while True:
            result, chunk = win32file.ReadFile(handle, 64 * 1024)
            response_data += chunk
            if b'\n' in chunk or len(chunk) == 0:
                break

        win32file.CloseHandle(handle)
        return json.loads(response_data.decode('utf-8').strip())
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_all_walls():
    """Delete all walls in the model."""
    print("\n=== STEP 1: Getting existing walls ===")
    result = call_mcp("getWalls")
    if not result.get("success"):
        print(f"Failed to get walls: {result.get('error')}")
        return False

    walls = result.get("walls", [])
    print(f"Found {len(walls)} walls to delete")

    if len(walls) == 0:
        print("No walls to delete")
        return True

    # Collect wall IDs
    wall_ids = []
    for w in walls:
        eid = w.get("elementId")
        if eid:
            wall_ids.append(eid)

    if wall_ids:
        print(f"Deleting {len(wall_ids)} walls...")
        result = call_mcp("deleteElements", {"elementIds": wall_ids})
        if result.get("success"):
            print(f"Deleted {result.get('deletedCount', 0)} walls")
        else:
            print(f"Delete failed: {result.get('error')}")
            return False

    return True


def create_wall(wall_def):
    """Create a single wall from definition."""
    start = wall_def["start"]
    end = wall_def["end"]

    params = {
        "startPoint": [start["x"], start["y"], start.get("z", 0.0)],
        "endPoint": [end["x"], end["y"], end.get("z", 0.0)],
        "levelId": wall_def.get("level_id", 30),
        "wallTypeId": wall_def.get("wall_type_id", 441515),
        "height": wall_def.get("height", 10.5)
    }

    result = call_mcp("createWallByPoints", params)
    return result


def create_all_walls():
    """Create all walls from the corrected spec."""

    # Corrected dimensions: 28'-8" (28.667') depth, not 38'
    DEPTH = 28.667  # CORRECTED from 38'
    GARAGE_WIDTH = 12.083  # 12'-1"
    GARAGE_DEPTH = 20.0    # 20'-0"
    BUILDING_WIDTH = 45.333  # 45'-4" (main building portion)

    print(f"\n=== CREATING WALLS WITH CORRECTED DIMENSIONS ===")
    print(f"Building Width: {BUILDING_WIDTH}' ({BUILDING_WIDTH:.3f})")
    print(f"Building Depth: {DEPTH}' (28'-8\") - CORRECTED FROM 38'")
    print(f"Garage: {GARAGE_WIDTH}' x {GARAGE_DEPTH}'")

    # Define exterior walls with CORRECT dimensions
    exterior_walls = [
        {
            "id": "EXT-001",
            "description": "South wall - Garage",
            "start": {"x": 0.0, "y": 0.0},
            "end": {"x": GARAGE_WIDTH, "y": 0.0},
            "wall_type_id": 441515,
            "level_id": 30,
            "height": 10.5
        },
        {
            "id": "EXT-002",
            "description": "South wall - Main building",
            "start": {"x": GARAGE_WIDTH, "y": 0.0},
            "end": {"x": BUILDING_WIDTH, "y": 0.0},
            "wall_type_id": 441515,
            "level_id": 30,
            "height": 10.5
        },
        {
            "id": "EXT-003",
            "description": "East wall",
            "start": {"x": BUILDING_WIDTH, "y": 0.0},
            "end": {"x": BUILDING_WIDTH, "y": DEPTH},
            "wall_type_id": 441515,
            "level_id": 30,
            "height": 10.5
        },
        {
            "id": "EXT-004",
            "description": "North wall",
            "start": {"x": BUILDING_WIDTH, "y": DEPTH},
            "end": {"x": 0.0, "y": DEPTH},
            "wall_type_id": 441515,
            "level_id": 30,
            "height": 10.5
        },
        {
            "id": "EXT-005",
            "description": "West wall - North portion",
            "start": {"x": 0.0, "y": DEPTH},
            "end": {"x": 0.0, "y": GARAGE_DEPTH},
            "wall_type_id": 441515,
            "level_id": 30,
            "height": 10.5
        },
        {
            "id": "EXT-006",
            "description": "West wall - Garage",
            "start": {"x": 0.0, "y": GARAGE_DEPTH},
            "end": {"x": 0.0, "y": 0.0},
            "wall_type_id": 441515,
            "level_id": 30,
            "height": 10.5
        }
    ]

    # Interior walls
    interior_walls = [
        {
            "id": "INT-001",
            "description": "Garage separation wall",
            "start": {"x": GARAGE_WIDTH, "y": 0.0},
            "end": {"x": GARAGE_WIDTH, "y": GARAGE_DEPTH},
            "wall_type_id": 441519,
            "level_id": 30,
            "height": 10.5
        }
    ]

    all_walls = exterior_walls + interior_walls
    created = 0
    failed = 0

    print(f"\n=== STEP 2: Creating {len(all_walls)} walls ===")

    for wall in all_walls:
        print(f"\nCreating {wall['id']}: {wall['description']}")
        print(f"  Start: ({wall['start']['x']:.3f}, {wall['start']['y']:.3f})")
        print(f"  End: ({wall['end']['x']:.3f}, {wall['end']['y']:.3f})")

        # Calculate length for verification
        dx = wall['end']['x'] - wall['start']['x']
        dy = wall['end']['y'] - wall['start']['y']
        length = (dx**2 + dy**2)**0.5
        print(f"  Length: {length:.3f}' ({int(length)}'-{int((length % 1) * 12)}\")")

        result = create_wall(wall)

        if result.get("success"):
            eid = result.get("elementId", "unknown")
            print(f"  SUCCESS - Element ID: {eid}")
            created += 1
        else:
            print(f"  FAILED: {result.get('error')}")
            failed += 1

        time.sleep(0.1)

    return created, failed


def verify_walls():
    """Verify created walls."""
    print("\n=== STEP 3: Verifying walls ===")
    result = call_mcp("getWalls")
    if result.get("success"):
        walls = result.get("walls", [])
        print(f"Total walls in model: {len(walls)}")

        # Find bounding box
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for w in walls:
            sp = w.get("startPoint", {})
            ep = w.get("endPoint", {})
            for p in [sp, ep]:
                x, y = p.get("x", 0), p.get("y", 0)
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)

        width = max_x - min_x
        depth = max_y - min_y

        print(f"\nBuilding Bounding Box:")
        print(f"  X: {min_x:.2f} to {max_x:.2f} (width: {width:.2f}')")
        print(f"  Y: {min_y:.2f} to {max_y:.2f} (depth: {depth:.2f}')")

        # Check against expected
        expected_depth = 28.667
        if abs(depth - expected_depth) < 0.5:
            print(f"\n  DEPTH CORRECT: {depth:.2f}' matches expected {expected_depth}'")
        else:
            print(f"\n  WARNING: Depth {depth:.2f}' does not match expected {expected_depth}'")

        return True
    else:
        print(f"Failed to verify: {result.get('error')}")
        return False


def main():
    print("=" * 60)
    print("RBCDC 1713 Wall Recreation - CORRECTED DIMENSIONS")
    print("Building depth: 28'-8\" (28.667') NOT 38'")
    print("=" * 60)

    # Step 1: Delete existing walls
    if not delete_all_walls():
        print("Failed to delete walls, aborting")
        return

    time.sleep(0.5)

    # Step 2: Create new walls
    created, failed = create_all_walls()

    print(f"\n=== SUMMARY ===")
    print(f"Walls created: {created}")
    print(f"Walls failed: {failed}")

    time.sleep(0.5)

    # Step 3: Verify
    verify_walls()

    print("\n" + "=" * 60)
    print("DONE - Check Revit to verify model")
    print("=" * 60)


if __name__ == "__main__":
    main()
