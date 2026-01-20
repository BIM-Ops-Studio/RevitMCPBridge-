#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Source levels from 512 Clematis
levels = [
    {"name": "0", "elevation": -0.0006573950775272674},
    {"name": "Level 1", "elevation": 0.6660092715891395},
    {"name": "B.O. LEVEL 2", "elevation": 14.66600927158914},
    {"name": "Level 2", "elevation": 15.999342604922472},
    {"name": "B.O. LEVEL 3", "elevation": 29.3326759382556},
    {"name": "Level 3", "elevation": 29.83267593825581},
    {"name": "B.O. LEVEL 4", "elevation": 39.16600927158893},
    {"name": "Level 4", "elevation": 39.66600927158914},
    {"name": "B.O. LEVEL 5", "elevation": 48.99934260492246},
    {"name": "Level 5", "elevation": 49.49934260492246},
    {"name": "B.O. ROOF DECK", "elevation": 58.832675938255804},
    {"name": "ROOF DECK", "elevation": 59.332675938255804},
    {"name": "T.O. SLAB", "elevation": 63.49958058728168},
    {"name": "T.O. PARAPET (OLD HIDE THIS LEVEL)", "elevation": 65.332913920615},
    {"name": "T.O. BEAM", "elevation": 67.33282155841835}
]

# Switch to MFI project
print("Switching to MFI target project...")
result = call("setActiveDocument", {"documentName": "MF-project-test-3"})
print(f"Switch result: {result.get('success')}")
time.sleep(1)

# Create each level
print(f"\nCreating {len(levels)} levels...")
created = 0
failed = 0

for level in levels:
    time.sleep(0.3)  # Small delay between calls
    result = call("createLevel", {
        "name": level["name"],
        "elevation": level["elevation"]
    })
    if result.get("success"):
        created += 1
        print(f"  OK: {level['name']} at {level['elevation']:.2f}'")
    else:
        failed += 1
        error = result.get("error", "Unknown error")
        print(f"  FAIL: {level['name']}: {error}")

print(f"\nCreated {created}/{len(levels)} levels ({failed} failed)")
