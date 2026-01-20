#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Remaining levels to create
levels = [
    {"name": "Level 1", "elevation": 0.6660092715891395},
    {"name": "B.O. LEVEL 2", "elevation": 14.66600927158914},
    {"name": "Level 2", "elevation": 15.999342604922472},
    {"name": "Level 3", "elevation": 29.83267593825581},
    {"name": "B.O. LEVEL 4", "elevation": 39.16600927158893},
    {"name": "Level 4", "elevation": 39.66600927158914},
    {"name": "Level 5", "elevation": 49.49934260492246},
    {"name": "B.O. ROOF DECK", "elevation": 58.832675938255804},
    {"name": "ROOF DECK", "elevation": 59.332675938255804},
    {"name": "T.O. PARAPET", "elevation": 65.332913920615},
    {"name": "T.O. BEAM", "elevation": 67.33282155841835}
]

print(f"Creating {len(levels)} remaining levels...")
created = 0
failed = 0

for level in levels:
    time.sleep(1.0)  # 1 second delay between calls
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
