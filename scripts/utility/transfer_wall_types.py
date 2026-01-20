#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Step 1: Get wall types from source (512 Clematis)
print("Switching to source project...")
result = call("setActiveDocument", {"documentName": "512_CLEMATIS-2"})
print(f"Switch: {result.get('success')}")
time.sleep(1)

print("Getting wall types from source...")
result = call("getWallTypes", {})
if not result.get("success"):
    print(f"Error: {result.get('error')}")
    exit(1)

wall_types = result.get("wallTypes", [])
print(f"Found {len(wall_types)} wall types")

# Get the element IDs
wall_type_ids = [wt["id"] for wt in wall_types]

# Step 2: Copy wall types to target
print("\nCopying wall types to MF-project-test-3...")
time.sleep(1)

result = call("copyElementsBetweenDocuments", {
    "sourceDocumentName": "512_CLEMATIS-2",
    "targetDocumentName": "MF-project-test-3",
    "elementIds": wall_type_ids
})

if result.get("success"):
    print(f"Successfully copied {result.get('copiedCount')} wall types")
else:
    print(f"Error: {result.get('error')}")

print(json.dumps(result, indent=2))
