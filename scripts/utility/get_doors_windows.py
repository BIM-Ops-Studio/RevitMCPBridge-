#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Switch back to source
print("Switching to source document...")
result = call("setActiveDocument", {"documentName": "512_CLEMATIS-2"})
if not result.get("success"):
    print(f"Error switching: {result.get('error')}")
    exit(1)
print("Switched to 512 Clematis")

time.sleep(3)

# Get doors from schedule
print("\nGetting door schedule...")
result = call("getDoorSchedule", {})
if not result.get("success"):
    print(f"Error getting doors: {result.get('error')}")
    doors = []
else:
    doors = result.get("doors", [])
    print(f"Found {len(doors)} doors")

time.sleep(3)

# Get windows from schedule
print("Getting window schedule...")
result = call("getWindowSchedule", {})
if not result.get("success"):
    print(f"Error getting windows: {result.get('error')}")
    windows = []
else:
    windows = result.get("windows", [])
    print(f"Found {len(windows)} windows")

# Show sample structures
if doors:
    print("\nSample door structure:")
    print(json.dumps(doors[0], indent=2))

if windows:
    print("\nSample window structure:")
    print(json.dumps(windows[0], indent=2))

# Save data
data = {"doors": doors, "windows": windows}
with open("doors_windows_data.json", "w") as f:
    json.dump(data, f, indent=2)
print(f"\nSaved {len(doors)} doors and {len(windows)} windows to doors_windows_data.json")
