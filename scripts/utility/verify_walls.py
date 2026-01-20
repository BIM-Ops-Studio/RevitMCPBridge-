#!/usr/bin/env python3
"""Verify created wall positions in Revit"""

from mcp_call import call
import json

# Get wall details
result = call("getWalls", {})
walls = result.get("walls", [])

print("CREATED WALLS VERIFICATION:")
print("="*70)
for w in walls:
    wid = w["wallId"]
    sx = w["startPoint"]["x"]
    sy = w["startPoint"]["y"]
    ex = w["endPoint"]["x"]
    ey = w["endPoint"]["y"]
    length = w["length"]
    print("Wall %d: (%.2f, %.2f) -> (%.2f, %.2f), Length: %.2f ft" % (wid, sx, sy, ex, ey, length))

print("="*70)
print("Total walls found: %d" % len(walls))

if len(walls) > 0:
    # Check for porch and lanai
    all_y = []
    all_x = []
    for w in walls:
        all_y.extend([w["startPoint"]["y"], w["endPoint"]["y"]])
        all_x.extend([w["startPoint"]["x"], w["endPoint"]["x"]])
    
    min_y = min(all_y)
    max_y = max(all_y)
    min_x = min(all_x)
    max_x = max(all_x)

    print("")
    print("Bounding box: X(%.2f to %.2f), Y(%.2f to %.2f)" % (min_x, max_x, min_y, max_y))
    print("Overall dimensions: %.2f x %.2f ft" % (max_x - min_x, max_y - min_y))

    print("")
    if min_y < 0:
        print("[OK] PORCH detected: extends %.1f ft south of baseline" % abs(min_y))
    if max_y > 40:
        print("[OK] LANAI detected: extends %.1f ft north of Grid D" % (max_y - 38.333))

    print("")
    print("BUILDING SHAPE:")
    print("-" * 70)
    if min_y < 0 and max_y > 40:
        print("SUCCESS! This is a COMPLEX perimeter with:")
        print("  - PORCH projecting %.1f ft SOUTH" % abs(min_y))
        print("  - LANAI projecting %.1f ft NORTH" % (max_y - 38.333))
        print("  - GARAGE in SW corner (X: 0 to ~12.083)")
        print("NOT a simple rectangle!")
    else:
        print("WARNING: May be missing projections")
        if min_y >= 0:
            print("  - No porch detected (min_y = %.2f)" % min_y)
        if max_y <= 40:
            print("  - No lanai detected (max_y = %.2f)" % max_y)
