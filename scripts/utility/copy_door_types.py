#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Get door types from source
print("Getting door type IDs from source (512 Clematis)...")
result = call("getDoorTypes", {})
if not result.get("success"):
    print(f"Error getting door types: {result.get('error')}")
    exit(1)

door_types = result.get("doorTypes", [])
door_type_ids = [dt["typeId"] for dt in door_types]
print(f"Found {len(door_type_ids)} door types to copy")

# Copy in batches
batch_size = 20
total_copied = 0

for i in range(0, len(door_type_ids), batch_size):
    batch = door_type_ids[i:i+batch_size]
    batch_num = i // batch_size + 1
    print(f"\nCopying batch {batch_num} ({len(batch)} door types)...")

    time.sleep(5)  # 5 second delay between batches

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

print(f"\nTotal door types copied: {total_copied}/{len(door_type_ids)}")
