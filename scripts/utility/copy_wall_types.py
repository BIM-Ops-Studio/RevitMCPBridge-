#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Get wall types from source first
print("Getting wall type IDs from source (512 Clematis)...")
result = call("getWallTypes", {})
if not result.get("success"):
    print(f"Error getting wall types: {result.get('error')}")
    exit(1)

wall_types = result.get("wallTypes", [])
wall_type_ids = [wt["wallTypeId"] for wt in wall_types]
print(f"Found {len(wall_type_ids)} wall types to copy")

# Copy in batches to avoid timeouts
batch_size = 20
total_copied = 0

for i in range(0, len(wall_type_ids), batch_size):
    batch = wall_type_ids[i:i+batch_size]
    batch_num = i // batch_size + 1
    print(f"\nCopying batch {batch_num} ({len(batch)} wall types)...")

    time.sleep(2)  # Wait before each batch

    result = call("copyElementsBetweenDocuments", {
        "sourceDocumentName": "512_CLEMATIS-2",
        "targetDocumentName": "MF-project-test-3",
        "elementIds": batch
    })

    if result.get("success"):
        copied = result.get("copiedCount", 0)
        total_copied += copied
        print(f"  Copied {copied} types")
    else:
        print(f"  Error: {result.get('error')}")

print(f"\nTotal copied: {total_copied}/{len(wall_type_ids)}")
