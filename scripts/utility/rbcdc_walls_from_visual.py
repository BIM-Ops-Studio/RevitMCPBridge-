#!/usr/bin/env python3
"""
RBCDC 1st Floor Plan - Wall Definition from Visual Analysis

Based on reading the actual floor plan quadrants, here's what I see:

ORIENTATION (architectural convention):
- North is UP on the drawing
- Grid lines A,B,C,D run EAST-WEST (horizontal on drawing)
- Grid lines 1,2,3,4,5 run NORTH-SOUTH (vertical on drawing)

COORDINATE SYSTEM:
- Origin (0,0) = Grid 1/A intersection (southwest corner of GARAGE)
- X-axis = EAST (positive to the right)
- Y-axis = NORTH (positive upward)
- Units = FEET

FROM THE QUADRANT IMAGES:

GRID POSITIONS (reading dimensions from drawings):
- Grid 1: X = 0 (west edge)
- Grid 2: X = 7'-0" = 7.0 (from dimension "7'-0"" between grids 1-2)
- Actually looking more carefully...

Let me re-read the dimensions from the quadrants:

North-West quadrant shows:
- "4'-0"" and "9'-8"" dimensions at top
- Grid lines A, B, C visible
- "7'-0"" dimension on left side between grids 1 and 2
- KITCHEN (104, 204 SF) with "8'-0"" width

Center-West quadrant shows:
- GARAGE (101, 242 SF) with "12'-1"" dimension at bottom
- "20'-0"" dimension for garage depth (north-south)
- UTILITY RM (102, 44 SF)
- PANTRY (103)
- Grid lines 3, 4, 5 visible
- "45'-4"" overall dimension on left

Center-East quadrant shows:
- DINING RM (106, 100 SF)
- CLOSET (108, 68 SF)
- PORCH (EX-1, 54 SF) with "10'-4"" and "5'-4"" dimensions
- Stairs going UP

North-East quadrant shows:
- REAR LANAI (EX-2, 110 SF) with "8'-0"" and "6'-0"" dimensions
- LIVING RM (105, 144 SF)
- "15'-0"" and "16'-0"" dimensions for lanai

So the building is approximately:
- 45'-4" north-south (from Grid A to Grid D plus lanai)
- About 34'-0" east-west (main building width)
"""

from mcp_call import call
import json

# Wall type IDs from Revit
EXTERIOR_WALL = 441445  # Generic - 6"
INTERIOR_WALL = 441519  # Interior - 4 1/2" Partition
GARAGE_WALL = 441446    # Interior - 5" Partition (2-hr)

LEVEL_1 = 30
HEIGHT = 10.0

def create_wall(name, start, end, wall_type=EXTERIOR_WALL):
    """Create a single wall via MCP"""
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
# GRID POSITIONS from visual analysis
# ================================================================
# Reading from the quadrant images:

# VERTICAL GRIDS (X positions, west to east):
# The garage is 12'-1" wide (from dimension string)
# Looking at the grid bubbles and dimensions...

G1 = 0.0       # West edge - left side of garage
G2 = 12.083    # 12'-1" from G1 (garage width)
# Additional grids exist but main building structure uses G1-G2 for west portion

# HORIZONTAL GRIDS (Y positions, south to north):
GA = 0.0       # South edge (Grid A)
GB = 7.0       # 7'-0" from GA (dimension visible in drawings)
GC = 20.0      # Approximate - need to verify
GD = 34.0      # North edge of main building

# LANAI extends north from main building
LANAI_NORTH = GD + 7.0   # Approx 7' extension = 41.0

# PORCH extends south from main building
PORCH_SOUTH = -5.33      # 5'-4" south of Grid A

# Overall building width (east-west)
BUILDING_EAST = 34.0     # East edge (approximate)

print("=" * 60)
print("RBCDC FLOOR PLAN - FROM VISUAL QUADRANT ANALYSIS")
print("=" * 60)
print("\nThis script defines walls based on reading the actual")
print("floor plan images quadrant by quadrant.")
print("\nGrid positions:")
print(f"  G1 (west) = {G1}")
print(f"  G2 = {G2}")
print(f"  GA (south) = {GA}")
print(f"  GB = {GB}")
print(f"  GC = {GC}")
print(f"  GD (north main) = {GD}")
print(f"  Lanai north = {LANAI_NORTH}")
print(f"  Porch south = {PORCH_SOUTH}")
print(f"  Building east = {BUILDING_EAST}")

walls = []

# ================================================================
# EXTERIOR PERIMETER
# Tracing counter-clockwise from southwest corner
# ================================================================

print("\n" + "=" * 60)
print("EXTERIOR PERIMETER WALLS")
print("=" * 60)

# The exterior shape from the quadrants appears to be:
# - Main rectangle with LANAI bump at northwest
# - PORCH at south-center (but it's under roof, may not be exterior wall)

# SOUTH WALL
# From southwest corner going east along Grid A
# PORCH is recessed, so south wall has a notch

# West portion of south (garage face)
w = create_wall("EXT-S1: South - West/Garage", (G1, GA), (G2, GA))
if w: walls.append(w)

# Continue east - need to determine porch location
# From quadrants: PORCH is roughly centered, about 10'-4" wide
PORCH_WEST = 15.0   # Approximate
PORCH_EAST = 25.0   # Approximate

w = create_wall("EXT-S2: South - Center-West", (G2, GA), (PORCH_WEST, GA))
if w: walls.append(w)

# Porch is recessed into the building (covered entry)
# Skip the porch opening for now, continue to east

w = create_wall("EXT-S3: South - Center-East", (PORCH_EAST, GA), (BUILDING_EAST, GA))
if w: walls.append(w)

# EAST WALL
w = create_wall("EXT-E1: East Wall", (BUILDING_EAST, GA), (BUILDING_EAST, GD))
if w: walls.append(w)

# NORTH WALL (with LANAI)
# North wall has lanai bump-out at the west end

# East portion of north
LANAI_EAST = 16.0  # Lanai extends from about G1 to here

w = create_wall("EXT-N1: North - East of Lanai", (BUILDING_EAST, GD), (LANAI_EAST, GD))
if w: walls.append(w)

# Lanai east wall going north
w = create_wall("EXT-N2: Lanai East", (LANAI_EAST, GD), (LANAI_EAST, LANAI_NORTH))
if w: walls.append(w)

# Lanai north wall
w = create_wall("EXT-N3: Lanai North", (LANAI_EAST, LANAI_NORTH), (G1, LANAI_NORTH))
if w: walls.append(w)

# Lanai west wall going south
w = create_wall("EXT-N4: Lanai West", (G1, LANAI_NORTH), (G1, GD))
if w: walls.append(w)

# WEST WALL
w = create_wall("EXT-W1: West Wall", (G1, GD), (G1, GA))
if w: walls.append(w)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Exterior walls created: {len(walls)}")
print(f"Wall IDs: {walls}")

print("\nNOTE: This is the EXTERIOR SHELL only.")
print("Interior walls need to be added separately.")
print("Dimensions are approximate - need refinement from actual PDF measurements.")
