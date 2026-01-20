#!/usr/bin/env python3
"""
RBCDC Floor Plan - CORRECT EXTERIOR SHAPE from Visual Analysis
Based on CAREFULLY tracing the exterior perimeter from the PDF image

Looking at the 1ST FLOOR PLAN (left side of A-100 sheet):

The building shape is:
- Main rectangular body from Grid 1 to Grid 5 (east-west) and A to D (south-north)
- GARAGE in SW corner (Grid 1-2, A-B area)
- REAR LANAI projects WEST from Grid 1 (NOT north!) between grids B and C
- PORCH is at the SOUTH but it's an INSET/covered area, not a projection

Coordinate System:
- Origin: Grid 1/A intersection = SW corner of GARAGE
- X-Axis: Positive = EAST (right on image)
- Y-Axis: Positive = NORTH (up on image)
- Units: FEET
"""

from mcp_call import call
import json

# Wall type IDs
EXTERIOR_WALL = 441445  # Generic - 6"
INTERIOR_WALL = 441519  # Interior - 4 1/2" Partition
GARAGE_WALL = 441446    # Interior - 5" Partition (2-hr)

# Level ID
LEVEL_1 = 30

# Wall height
HEIGHT = 10.0

def create_wall(name, start, end, wall_type=EXTERIOR_WALL):
    """Create a single wall"""
    print(f"\n{name}")
    print(f"  ({start[0]:.2f}, {start[1]:.2f}) -> ({end[0]:.2f}, {end[1]:.2f})")

    result = call("createWall", {
        "startPoint": [start[0], start[1], 0.0],
        "endPoint": [end[0], end[1], 0.0],
        "levelId": LEVEL_1,
        "height": HEIGHT,
        "wallTypeId": wall_type
    })

    if result.get("success"):
        print(f"  [OK] Wall ID: {result.get('wallId')}")
        return result.get("wallId")
    else:
        print(f"  [FAIL] {result.get('error')}")
        return None

# ================================================================
# GRID POSITIONS - Read carefully from the PDF dimensions
# ================================================================
# Vertical grids (X positions) - from dimension strings at top:
G1 = 0.0        # West edge of garage
G2 = 12.083     # 12'-1" from G1
G3 = 27.083     # 15'-0" from G2 (total 27'-1")
G4 = 35.083     # 8'-0" from G3 (total 35'-1")
G5 = 50.083     # 15'-0" from G4 (total 50'-1")

# Horizontal grids (Y positions) - from dimension strings on left:
GA = 0.0        # South edge (baseline)
GB = 7.0        # 7'-0" from GA
GC = 24.667     # 17'-8" from GA (7' + 10'-8" = 17'-8")
GD = 38.333     # North edge of main building

# REAR LANAI projects NORTH from Grid D (top of building)
# Looking at the image: REAR LANAI (102, 133 SF) is at the TOP-LEFT
# It spans from about Grid 1 to Grid 2 (west side) and extends north beyond D

# Lanai dimensions (estimating from image):
LANAI_NORTH = GD + 7.0   # 7' north of Grid D = 45.33
LANAI_EAST = G2          # Lanai east edge at Grid 2 (12.083)

print("=" * 60)
print("RBCDC FLOOR PLAN - CORRECT EXTERIOR SHAPE")
print("=" * 60)

walls = []

# ================================================================
# EXTERIOR PERIMETER - Tracing counter-clockwise from SW corner
# Starting at Grid 1/A (SW corner)
# ================================================================

print("\n--- SOUTH WALL (along Grid A) ---")
# Full south wall from Grid 1 to Grid 5
w = create_wall("EXT-01: South Wall", (G1, GA), (G5, GA))
if w: walls.append(w)

print("\n--- EAST WALL (along Grid 5) ---")
# Full east wall from Grid A to Grid D
w = create_wall("EXT-02: East Wall", (G5, GA), (G5, GD))
if w: walls.append(w)

print("\n--- NORTH WALLS (with LANAI bump-out) ---")

# North wall - east section (Grid 5 to Grid 2, along Grid D)
w = create_wall("EXT-03: North - East of Lanai", (G5, GD), (LANAI_EAST, GD))
if w: walls.append(w)

# Lanai east wall - going north
w = create_wall("EXT-04: Lanai East Wall", (LANAI_EAST, GD), (LANAI_EAST, LANAI_NORTH))
if w: walls.append(w)

# Lanai north wall - going west
w = create_wall("EXT-05: Lanai North Wall", (LANAI_EAST, LANAI_NORTH), (G1, LANAI_NORTH))
if w: walls.append(w)

# Lanai west wall - going south (this is also the west wall of main building above D)
w = create_wall("EXT-06: Lanai West Wall", (G1, LANAI_NORTH), (G1, GD))
if w: walls.append(w)

print("\n--- WEST WALL (along Grid 1) ---")
# Full west wall from Grid D to Grid A
w = create_wall("EXT-07: West Wall", (G1, GD), (G1, GA))
if w: walls.append(w)

# ================================================================
# SUMMARY
# ================================================================
print("\n" + "=" * 60)
print("EXTERIOR PERIMETER COMPLETE")
print("=" * 60)
print(f"Total walls created: {len(walls)}")
print(f"Wall IDs: {walls}")
