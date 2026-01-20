#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Categories to transfer
categories = [
    "Plumbing Fixtures",
    "Lighting Fixtures",
    "Electrical Fixtures",
    "Furniture",
    "Specialty Equipment",
]

total_copied = 0

for category in categories:
    time.sleep(5)  # Delay between categories

    # Get family types for this category
    print(f"\nGetting {category} types from source...")
    result = call("getFamilyInstanceTypes", {"category": category})

    if not result.get("success"):
        print(f"  Error: {result.get('error')}")
        continue

    family_types = result.get("familyTypes", [])
    type_ids = [t["typeId"] for t in family_types if t.get("typeId")]

    if not type_ids:
        print(f"  No {category} types found")
        continue

    print(f"  Found {len(type_ids)} types to copy")

    # Copy in batches
    batch_size = 20
    cat_copied = 0

    for i in range(0, len(type_ids), batch_size):
        batch = type_ids[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(type_ids) + batch_size - 1) // batch_size

        time.sleep(3)  # Delay between batches

        result = call("copyElementsBetweenDocuments", {
            "sourceDocumentName": "512_CLEMATIS-2",
            "targetDocumentName": "MF-project-test-3",
            "elementIds": batch
        })

        if result.get("success"):
            copied = result.get("copiedCount", 0)
            cat_copied += copied
            print(f"  Batch {batch_num}/{total_batches}: copied {copied} types")
        else:
            print(f"  Batch {batch_num}/{total_batches}: Error - {result.get('error')}")

    total_copied += cat_copied
    print(f"  {category} total: {cat_copied} types copied")

print(f"\n=== Total fixture types copied: {total_copied} ===")
