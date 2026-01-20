#!/usr/bin/env python3
from mcp_call import call
import json

# Get walls from current Revit model
print("Getting wall instances from Revit...")
result = call("getWalls", {})

if not result.get("success"):
    print(f"Error: {result.get('error')}")
    exit(1)

walls = result.get("walls", [])
print(f"Found {len(walls)} wall instances")

# Print all walls with coordinates
for w in walls:
    sp = w.get('startPoint', {})
    ep = w.get('endPoint', {})
    wall_id = w.get('id', 'N/A')
    print(f'Wall {wall_id}: ({sp.get("x",0):.2f}, {sp.get("y",0):.2f}) -> ({ep.get("x",0):.2f}, {ep.get("y",0):.2f})')

# Save full data to file for inspection
with open("wall_data.json", "w") as f:
    json.dump(result, f, indent=2)
print("\nFull data saved to wall_data.json")
