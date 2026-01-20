#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Step 1: Switch to target and get type/level mappings
print("Switching to target document...")
result = call("setActiveDocument", {"documentName": "MF-project-test-3"})
if not result.get("success"):
    print(f"Error switching: {result.get('error')}")
    exit(1)
print("Switched to MF-project-test-3")

time.sleep(3)

# Get wall types in target
print("Getting wall types in target...")
result = call("getWallTypes", {})
if not result.get("success"):
    print(f"Error getting wall types: {result.get('error')}")
    exit(1)

target_wall_types = {wt["name"]: wt["wallTypeId"] for wt in result.get("wallTypes", [])}
print(f"Found {len(target_wall_types)} wall types in target")

time.sleep(3)

# Get levels in target
print("Getting levels in target...")
result = call("getLevels", {})
if not result.get("success"):
    print(f"Error getting levels: {result.get('error')}")
    exit(1)

target_levels = {lvl["name"]: lvl["levelId"] for lvl in result.get("levels", [])}
print(f"Found {len(target_levels)} levels in target")

# Step 2: Load source wall data
print("\nLoading source wall data...")
with open("wall_data.json", "r") as f:
    source_data = json.load(f)

source_walls = source_data.get("walls", [])
print(f"Loaded {len(source_walls)} walls from source")

# Step 3: Transform walls for target
print("\nTransforming wall data...")
target_walls = []
skipped = {"no_type": 0, "no_level": 0}

for wall in source_walls:
    wall_type_name = wall.get("wallType")
    base_level_name = wall.get("baseLevel")

    # Map to target IDs
    wall_type_id = target_wall_types.get(wall_type_name)
    level_id = target_levels.get(base_level_name)

    if not wall_type_id:
        skipped["no_type"] += 1
        continue
    if not level_id:
        skipped["no_level"] += 1
        continue

    start = wall.get("startPoint", {})
    end = wall.get("endPoint", {})

    target_walls.append({
        "startPoint": [start.get("x", 0), start.get("y", 0), 0],  # Z at 0 for level base
        "endPoint": [end.get("x", 0), end.get("y", 0), 0],
        "levelId": level_id,
        "wallTypeId": wall_type_id,
        "height": wall.get("height", 10.0)
    })

print(f"Transformed {len(target_walls)} walls")
print(f"Skipped: {skipped['no_type']} (no matching type), {skipped['no_level']} (no matching level)")

# Step 4: Create walls in batches
print("\nCreating walls in target...")
batch_size = 50
total_created = 0
total_failed = 0

for i in range(0, len(target_walls), batch_size):
    batch = target_walls[i:i+batch_size]
    batch_num = i // batch_size + 1
    total_batches = (len(target_walls) + batch_size - 1) // batch_size

    time.sleep(5)  # Delay between batches

    result = call("batchCreateWalls", {"walls": batch})

    if result.get("success"):
        created = result.get("createdCount", 0)
        failed = result.get("failedCount", 0)
        total_created += created
        total_failed += failed
        print(f"  Batch {batch_num}/{total_batches}: created {created}, failed {failed}")
    else:
        print(f"  Batch {batch_num}/{total_batches}: Error - {result.get('error')}")

print(f"\n=== Total walls created: {total_created} ===")
print(f"=== Total walls failed: {total_failed} ===")
