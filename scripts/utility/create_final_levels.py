#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Final levels to create
levels = [
    {"name": "Level 2", "elevation": 15.999342604922472},
    {"name": "B.O. LEVEL 4", "elevation": 39.16600927158893},
    {"name": "Level 5", "elevation": 49.49934260492246},
    {"name": "ROOF DECK", "elevation": 59.332675938255804},
    {"name": "T.O. BEAM", "elevation": 67.33282155841835}
]

print(f"Creating {len(levels)} final levels...")
created = 0
failed = 0

for level in levels:
    time.sleep(2.0)  # 2 second delay between calls
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
