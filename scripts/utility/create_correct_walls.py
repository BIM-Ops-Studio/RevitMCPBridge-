#!/usr/bin/env python3
"""
Create correct exterior walls for RBCDC 1713 2-Story Prototype.
Based on verified PDF dimensions:
- Building width: 52'-4" (52.333 feet)
- Building depth: 28'-8" (28.667 feet) - CRITICAL FIX from 38'
- Garage: 11'-4" x 20'-0"
"""

import json
import win32file
import time

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# VERIFIED DIMENSIONS FROM PDF
BUILDING_WIDTH = 52.333  # 52'-4"
BUILDING_DEPTH = 28.667  # 28'-8" - CORRECTED from previous 38'
GARAGE_WIDTH = 11.333    # 11'-4"
GARAGE_DEPTH = 20.0      # 20'-0"

# Wall types
EXTERIOR_TYPE_ID = 441515
INTERIOR_TYPE_ID = 441519

# Level
LEVEL_1_ID = 30
LEVEL_2_ID = 311


def call_mcp(method, params=None):
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


def create_wall(wall_id, description, start, end, wall_type_id, level_id, height=10.0):
    """Create a single wall with verification."""
    print(f"\n=== {wall_id}: {description} ===")
    print(f"  Start: ({start[0]:.3f}, {start[1]:.3f}, {start[2]:.3f})")
    print(f"  End:   ({end[0]:.3f}, {end[1]:.3f}, {end[2]:.3f})")

    # Calculate expected length
    import math
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    expected_length = math.sqrt(dx*dx + dy*dy)
    print(f"  Expected length: {expected_length:.3f} ft")

    result = call_mcp("createWallByPoints", {
        "startPoint": list(start),
        "endPoint": list(end),
        "levelId": level_id,
        "wallTypeId": wall_type_id,
        "height": height,
        "structural": False
    })

    if result.get("success"):
        print(f"  [OK] Created: Wall ID {result.get('wallId')}")
        return result.get('wallId')
    else:
        print(f"  [FAIL] {result.get('error')}")
        return None


def main():
    print("=" * 60)
    print("RBCDC 1713 - CORRECT EXTERIOR WALLS")
    print("=" * 60)
    print(f"\nBuilding Dimensions:")
    print(f"  Width: {BUILDING_WIDTH}' (52'-4\")")
    print(f"  Depth: {BUILDING_DEPTH}' (28'-8\") - CORRECTED")
    print(f"  Garage: {GARAGE_WIDTH}' x {GARAGE_DEPTH}'")

    # Test MCP connection
    result = call_mcp("getLevels")
    if not result.get("success"):
        print(f"\nMCP Error: {result.get('error')}")
        return
    print("\nMCP Connection OK")

    created_walls = []

    # ============================================================
    # 1ST FLOOR EXTERIOR WALLS (Counter-clockwise from SW corner)
    # ============================================================
    print("\n" + "=" * 60)
    print("1ST FLOOR EXTERIOR WALLS")
    print("=" * 60)

    # EXT-001: South wall - Garage portion
    wid = create_wall(
        "EXT-001", "South wall - Garage",
        (0.0, 0.0, 0.0),
        (GARAGE_WIDTH, 0.0, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_1_ID
    )
    if wid: created_walls.append(wid)

    # EXT-002: South wall - Main building
    wid = create_wall(
        "EXT-002", "South wall - Main building",
        (GARAGE_WIDTH, 0.0, 0.0),
        (BUILDING_WIDTH, 0.0, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_1_ID
    )
    if wid: created_walls.append(wid)

    # EXT-003: East wall
    wid = create_wall(
        "EXT-003", "East wall",
        (BUILDING_WIDTH, 0.0, 0.0),
        (BUILDING_WIDTH, BUILDING_DEPTH, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_1_ID
    )
    if wid: created_walls.append(wid)

    # EXT-004: North wall
    wid = create_wall(
        "EXT-004", "North wall",
        (BUILDING_WIDTH, BUILDING_DEPTH, 0.0),
        (0.0, BUILDING_DEPTH, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_1_ID
    )
    if wid: created_walls.append(wid)

    # EXT-005: West wall - North portion (above garage)
    wid = create_wall(
        "EXT-005", "West wall - North portion",
        (0.0, BUILDING_DEPTH, 0.0),
        (0.0, GARAGE_DEPTH, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_1_ID
    )
    if wid: created_walls.append(wid)

    # EXT-006: West wall - Garage
    wid = create_wall(
        "EXT-006", "West wall - Garage",
        (0.0, GARAGE_DEPTH, 0.0),
        (0.0, 0.0, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_1_ID
    )
    if wid: created_walls.append(wid)

    # INT-001: Garage east wall (separation)
    wid = create_wall(
        "INT-001", "Garage separation wall",
        (GARAGE_WIDTH, 0.0, 0.0),
        (GARAGE_WIDTH, GARAGE_DEPTH, 0.0),
        INTERIOR_TYPE_ID, LEVEL_1_ID
    )
    if wid: created_walls.append(wid)

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created {len(created_walls)} walls successfully")
    print(f"Wall IDs: {created_walls}")

    # Verify by getting walls
    result = call_mcp("getWalls")
    if result.get("success"):
        walls = result.get("walls", [])
        print(f"\nVerification: {len(walls)} walls in model")

        # Check dimensions
        total_south = sum(w["length"] for w in walls if abs(w["startPoint"]["y"]) < 0.1 and abs(w["endPoint"]["y"]) < 0.1)
        total_north = sum(w["length"] for w in walls if abs(w["startPoint"]["y"] - BUILDING_DEPTH) < 0.1 and abs(w["endPoint"]["y"] - BUILDING_DEPTH) < 0.1)

        print(f"\nSouth wall total length: {total_south:.3f}' (expected: {BUILDING_WIDTH:.3f}')")
        print(f"North wall total length: {total_north:.3f}' (expected: {BUILDING_WIDTH:.3f}')")


if __name__ == "__main__":
    main()
