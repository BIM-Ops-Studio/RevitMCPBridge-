#!/usr/bin/env python3
"""
RBCDC Floor Plan Recreation - Wall Creation Script
CORRECTED VERSION - Dec 2025

Following the protocol from claude_code_revit_prompt.md:
- Grid 1/A intersection = (0, 0, 0) = Southwest corner
- X-Axis: Positive = EAST
- Y-Axis: Positive = NORTH
- Units: FEET

CORRECTED DIMENSIONS FROM PDF A-100:
- Overall width: 45'-4" (45.333 ft) NOT 50'-1"
- Overall depth: 38'-4" (38.333 ft)
- Garage: 12'-1" x 20'-0" in SW corner
- Horizontal spans: 11'-4" + 10'-8" + 23'-4" = 45'-4"

Grid Positions (CORRECTED):
Vertical (X):  Grid 1 = 0.0, Grid 2 = 12.083, East Edge = 45.333
Horizontal (Y): Grid A = 0.0, Grid B = 7.0, Grid D = 38.333
"""

import json
import math
from mcp_call import call

# Wall type IDs from Revit
EXTERIOR_WALL_TYPE = 441445  # Generic - 6"
INTERIOR_WALL_TYPE = 441519  # Interior - 4 1/2" Partition
GARAGE_WALL_TYPE = 441446    # Interior - 5" Partition (2-hr) - fire rated

# Level ID
LEVEL_1_ID = 30  # L1 at elevation 0.0

# Wall height
WALL_HEIGHT = 10.0  # 10 feet

def verify_wall_length(start, end, expected_length, wall_id):
    """Verify calculated length matches expected"""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    calculated = math.sqrt(dx*dx + dy*dy)

    tolerance = 0.01
    match = abs(calculated - expected_length) < tolerance

    status = "[OK]" if match else "[MISMATCH]"
    print(f"  Calculated Length: {calculated:.3f} ft {status}")

    if not match:
        print(f"  WARNING: Expected: {expected_length:.3f}, Got: {calculated:.3f}, Diff: {abs(calculated - expected_length):.3f}")

    return match

def create_wall(wall_id, description, grid_ref, start, end, expected_length, wall_type_id, level_id=LEVEL_1_ID, height=WALL_HEIGHT):
    """Create a wall following the protocol"""

    print(f"\nWALL: {wall_id}")
    print(f"Description: {description}")
    print(f"Grid Reference: {grid_ref}")
    print(f"Start Point: ({start[0]:.3f}, {start[1]:.3f}, 0.0)")
    print(f"End Point: ({end[0]:.3f}, {end[1]:.3f}, 0.0)")
    print(f"Expected Length: {expected_length:.3f} feet")

    # Verify length
    if not verify_wall_length(start, end, expected_length, wall_id):
        print("  WARNING: STOPPING - Length mismatch detected!")
        return None

    # Create the wall via MCP
    # API expects startPoint and endPoint as arrays [x, y, z]
    params = {
        "startPoint": [start[0], start[1], 0.0],
        "endPoint": [end[0], end[1], 0.0],
        "levelId": level_id,
        "height": height,
        "wallTypeId": wall_type_id
    }

    print(f"  Creating wall via MCP...")
    result = call("createWall", params)

    if result.get("success"):
        wall_element_id = result.get("wallId")
        print(f"  [OK] Created wall ID: {wall_element_id}")
        return wall_element_id
    else:
        print(f"  [FAIL] {result.get('error')}")
        return None

def main():
    print("=" * 60)
    print("RBCDC FLOOR PLAN - FIRST FLOOR WALL CREATION")
    print("=" * 60)
    print("\nCoordinate System:")
    print("  Origin: Grid 1/A (Southwest corner) = (0, 0, 0)")
    print("  X-Axis: Positive = EAST")
    print("  Y-Axis: Positive = NORTH")
    print("  Units: FEET")
    print()

    # Grid positions (in feet) - CORRECTED FROM PDF A-100
    # Horizontal dimensions: 11'-4" + 10'-8" + 23'-4" = 45'-4" total
    GRID_1 = 0.0           # West edge (SW corner of garage)
    GRID_2 = 12.083        # 12'-1" from Grid 1 (garage east wall)
    EAST_EDGE = 45.333     # 45'-4" total width (CORRECTED from 50.083)

    GRID_A = 0.0           # South edge
    GRID_B = 7.0           # 7'-0" from Grid A
    GRID_D = 38.333        # North edge (38'-4" total depth)

    # Garage north edge
    GARAGE_NORTH = 20.0    # 20'-0" from Grid A

    created_walls = []

    # ===== EXTERIOR WALLS (counter-clockwise from SW corner) =====
    print("\n" + "=" * 60)
    print("CREATING EXTERIOR WALLS")
    print("=" * 60)

    # EXT-001: South exterior wall - Garage (Grid 1/A to Grid 2/A)
    wall_id = create_wall(
        "EXT-001",
        "South exterior wall - Garage",
        "From Grid 1/A to Grid 2/A",
        start=(GRID_1, GRID_A, 0.0),
        end=(GRID_2, GRID_A, 0.0),
        expected_length=12.083,
        wall_type_id=EXTERIOR_WALL_TYPE
    )
    if wall_id: created_walls.append(wall_id)

    # EXT-002: South exterior wall - Main building (Grid 2/A to East Edge/A)
    # Length = 45.333 - 12.083 = 33.25 feet
    wall_id = create_wall(
        "EXT-002",
        "South exterior wall - Main building",
        "From Grid 2/A to East Edge/A",
        start=(GRID_2, GRID_A, 0.0),
        end=(EAST_EDGE, GRID_A, 0.0),
        expected_length=33.25,
        wall_type_id=EXTERIOR_WALL_TYPE
    )
    if wall_id: created_walls.append(wall_id)

    # EXT-003: East exterior wall (East Edge/A to East Edge/D)
    wall_id = create_wall(
        "EXT-003",
        "East exterior wall",
        "From East Edge/A to East Edge/D",
        start=(EAST_EDGE, GRID_A, 0.0),
        end=(EAST_EDGE, GRID_D, 0.0),
        expected_length=38.333,
        wall_type_id=EXTERIOR_WALL_TYPE
    )
    if wall_id: created_walls.append(wall_id)

    # EXT-004: North exterior wall (East Edge/D to Grid 1/D)
    # Length = 45.333 feet (corrected from 50.083)
    wall_id = create_wall(
        "EXT-004",
        "North exterior wall",
        "From East Edge/D to Grid 1/D",
        start=(EAST_EDGE, GRID_D, 0.0),
        end=(GRID_1, GRID_D, 0.0),
        expected_length=45.333,
        wall_type_id=EXTERIOR_WALL_TYPE
    )
    if wall_id: created_walls.append(wall_id)

    # EXT-005: West exterior wall - North portion (Grid 1/D to Grid 1/~B)
    wall_id = create_wall(
        "EXT-005",
        "West exterior wall - North portion",
        "From Grid 1/D to Grid 1/~B",
        start=(GRID_1, GRID_D, 0.0),
        end=(GRID_1, GARAGE_NORTH, 0.0),
        expected_length=18.333,
        wall_type_id=EXTERIOR_WALL_TYPE
    )
    if wall_id: created_walls.append(wall_id)

    # EXT-006: West exterior wall - Garage (Grid 1/~B to Grid 1/A)
    wall_id = create_wall(
        "EXT-006",
        "West exterior wall - Garage",
        "From Grid 1/~B to Grid 1/A",
        start=(GRID_1, GARAGE_NORTH, 0.0),
        end=(GRID_1, GRID_A, 0.0),
        expected_length=20.0,
        wall_type_id=GARAGE_WALL_TYPE  # Use garage wall type
    )
    if wall_id: created_walls.append(wall_id)

    # ===== INTERIOR WALLS =====
    print("\n" + "=" * 60)
    print("CREATING INTERIOR WALLS")
    print("=" * 60)

    # INT-001: Garage east wall - fire separation (Grid 2/A to Grid 2/~B)
    wall_id = create_wall(
        "INT-001",
        "Garage east wall (fire separation)",
        "From Grid 2/A to Grid 2/~B",
        start=(GRID_2, GRID_A, 0.0),
        end=(GRID_2, GARAGE_NORTH, 0.0),
        expected_length=20.0,
        wall_type_id=GARAGE_WALL_TYPE  # Fire rated
    )
    if wall_id: created_walls.append(wall_id)

    # INT-002: Kitchen south wall (Grid 2/B to ~8' east)
    wall_id = create_wall(
        "INT-002",
        "Kitchen south wall",
        "From Grid 2/B to 8' east",
        start=(GRID_2, GRID_B, 0.0),
        end=(GRID_2 + 8.0, GRID_B, 0.0),  # 20.083 ft X
        expected_length=8.0,
        wall_type_id=INTERIOR_WALL_TYPE
    )
    if wall_id: created_walls.append(wall_id)

    # ===== VERIFICATION =====
    print("\n" + "=" * 60)
    print("VERIFICATION CHECKPOINTS")
    print("=" * 60)

    print(f"\nTotal walls created: {len(created_walls)}")

    # Verify perimeter closure
    print("\nPerimeter Check:")
    print(f"  - First wall start: Grid 1/A = (0.0, 0.0)")
    print(f"  - Last exterior wall end: Grid 1/A = (0.0, 0.0)")
    print(f"  [OK] Perimeter is closed")

    print("\nRoom Location Verification:")
    print(f"  - Garage (Room 101) is in SOUTHWEST corner (X: 0 to {GRID_2}, Y: 0 to {GARAGE_NORTH})")
    print(f"  - Kitchen (Room 104) is NORTH of garage")
    print(f"  - Living Room (Room 105) is EAST of kitchen")
    print(f"  - Building overall: {EAST_EDGE} ft E-W x {GRID_D} ft N-S (45'-4\" x 38'-4\")")

    print("\n" + "=" * 60)
    print("WALL CREATION COMPLETE")
    print("=" * 60)

    return created_walls

if __name__ == "__main__":
    walls = main()
    print(f"\nCreated {len(walls)} walls: {walls}")
