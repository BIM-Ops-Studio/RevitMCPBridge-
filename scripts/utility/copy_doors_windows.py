#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Load the door/window data
print("Loading door/window data...")
with open("doors_windows_data.json", "r") as f:
    data = json.load(f)

doors = data.get("doors", [])
windows = data.get("windows", [])
print(f"Loaded {len(doors)} doors and {len(windows)} windows")

# Get door IDs
door_ids = [d["doorId"] for d in doors if d.get("doorId")]
window_ids = [w["windowId"] for w in windows if w.get("windowId")]

print(f"Door IDs: {len(door_ids)}")
print(f"Window IDs: {len(window_ids)}")

# Copy doors in batches
print("\nCopying doors...")
batch_size = 50
total_copied = 0

for i in range(0, len(door_ids), batch_size):
    batch = door_ids[i:i+batch_size]
    batch_num = i // batch_size + 1
    total_batches = (len(door_ids) + batch_size - 1) // batch_size

    time.sleep(5)

    result = call("copyElementsBetweenDocuments", {
        "sourceDocumentName": "512_CLEMATIS-2",
        "targetDocumentName": "MF-project-test-3",
        "elementIds": batch
    })

    if result.get("success"):
        copied = result.get("copiedCount", 0)
        total_copied += copied
        print(f"  Doors batch {batch_num}/{total_batches}: copied {copied}")
    else:
        print(f"  Doors batch {batch_num}/{total_batches}: Error - {result.get('error')}")

print(f"Total doors copied: {total_copied}")

# Copy windows in batches
print("\nCopying windows...")
window_copied = 0

for i in range(0, len(window_ids), batch_size):
    batch = window_ids[i:i+batch_size]
    batch_num = i // batch_size + 1
    total_batches = (len(window_ids) + batch_size - 1) // batch_size

    time.sleep(5)

    result = call("copyElementsBetweenDocuments", {
        "sourceDocumentName": "512_CLEMATIS-2",
        "targetDocumentName": "MF-project-test-3",
        "elementIds": batch
    })

    if result.get("success"):
        copied = result.get("copiedCount", 0)
        window_copied += copied
        print(f"  Windows batch {batch_num}/{total_batches}: copied {copied}")
    else:
        print(f"  Windows batch {batch_num}/{total_batches}: Error - {result.get('error')}")

print(f"Total windows copied: {window_copied}")
print(f"\n=== Total: {total_copied} doors, {window_copied} windows ===")
