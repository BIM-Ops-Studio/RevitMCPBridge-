#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Check multiple railing-related categories
categories = [
    "Railings",
    "Handrails",
    "Top Rails",
    "Stair Railings",
]

for cat in categories:
    time.sleep(3)  # Delay between calls
    r = call("getFamilyInstanceTypes", {"category": cat})
    if r.get("success"):
        count = r.get("typeCount", 0)
        print(f"{cat}: {count} types")
    else:
        print(f"{cat}: {r.get('error', 'Unknown error')}")

# Also check for loaded families in railing category
print("\nChecking loaded families...")
r = call("getLoadedFamilies", {})
if r.get("success"):
    families = r.get("families", [])
    railing_fams = [f for f in families if "railing" in f.get("name", "").lower() or f.get("category", "") == "Railings"]
    print(f"Railing-related families: {len(railing_fams)}")
    for f in railing_fams:
        print(f"  - {f.get('name')} ({f.get('category')})")
