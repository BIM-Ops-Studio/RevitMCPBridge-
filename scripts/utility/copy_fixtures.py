#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Categories to transfer (exact names from Revit)
categories = [
    ("Plumbing Fixtures", "Plumbing Fixtures"),
    ("Lighting Fixtures", "Lighting Fixtures"),
    ("Electrical Fixtures", "Electrical Fixtures"),
    ("Furniture", "Furniture"),
    ("Furniture Systems", "Furniture Systems"),
    ("Specialty Equipment", "Specialty Equipment"),
]

total_copied = 0

for cat_name, cat_key in categories:
    time.sleep(5)  # Delay at start of each category to avoid pipe congestion
    print(f"\nGetting {cat_name} from source...")

    result = call("getElements", {
        "category": cat_key,
        "includeTypes": True,
        "includeInstances": False
    })

    if not result.get("success"):
        print(f"  Error: {result.get('error')}")
        continue

    elements = result.get("elements", [])
    if not elements:
        print(f"  No {cat_name} found")
        continue

    # Get element IDs
    element_ids = [e["elementId"] for e in elements]
    print(f"  Found {len(element_ids)} {cat_name} types to copy")

    # Copy to target
    time.sleep(3)
    result = call("copyElementsBetweenDocuments", {
        "sourceDocumentName": "512_CLEMATIS-2",
        "targetDocumentName": "MF-project-test-3",
        "elementIds": element_ids
    })

    if result.get("success"):
        copied = result.get("copiedCount", 0)
        total_copied += copied
        print(f"  Copied {copied} {cat_name}")
    else:
        print(f"  Copy error: {result.get('error')}")

print(f"\nTotal fixtures copied: {total_copied}")
