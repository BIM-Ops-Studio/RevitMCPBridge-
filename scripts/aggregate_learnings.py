#!/usr/bin/env python3
"""
Aggregate Detail Library Extractions into Learning Summaries
=============================================================
Runs after extract_all_details.ps1 to consolidate extracted data
into structured knowledge files that Claude can reference.

Usage: python3 aggregate_learnings.py
"""

import os
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
EXTRACTIONS_DIR = Path("/mnt/d/RevitMCPBridge2026/knowledge/detail_library/extractions")
OUTPUT_DIR = Path("/mnt/d/RevitMCPBridge2026/knowledge/detail_library")

def load_all_extractions():
    """Load all extraction JSON files"""
    extractions = []

    if not EXTRACTIONS_DIR.exists():
        print(f"No extractions found at {EXTRACTIONS_DIR}")
        return []

    for category_dir in EXTRACTIONS_DIR.iterdir():
        if category_dir.is_dir():
            for json_file in category_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        data['category'] = category_dir.name
                        extractions.append(data)
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")

    return extractions


def aggregate_detail_components(extractions):
    """Aggregate all detail component families used"""
    components = defaultdict(lambda: {"count": 0, "files": [], "categories": set()})

    for ext in extractions:
        category = ext.get('category', 'Unknown')
        for comp in ext.get('detailComponents', []):
            if isinstance(comp, dict):
                name = comp.get('typeName') or comp.get('familyName', 'Unknown')
            else:
                name = str(comp)

            components[name]["count"] += 1
            components[name]["files"].append(ext.get('file', ''))
            components[name]["categories"].add(category)

    # Convert sets to lists for JSON
    result = {}
    for name, data in sorted(components.items(), key=lambda x: -x[1]["count"]):
        result[name] = {
            "usageCount": data["count"],
            "categories": list(data["categories"]),
            "exampleFiles": data["files"][:5]  # First 5 examples
        }

    return result


def aggregate_text_notes(extractions):
    """Aggregate all text notes/callouts used"""
    notes = defaultdict(lambda: {"count": 0, "categories": set()})

    for ext in extractions:
        category = ext.get('category', 'Unknown')
        for note in ext.get('textNotes', []):
            if note and isinstance(note, str) and len(note) > 2:
                # Normalize: uppercase, strip
                normalized = note.strip().upper()
                notes[normalized]["count"] += 1
                notes[normalized]["categories"].add(category)

    # Convert to list sorted by frequency
    result = []
    for note, data in sorted(notes.items(), key=lambda x: -x[1]["count"]):
        if data["count"] >= 2:  # Only include notes used 2+ times
            result.append({
                "text": note,
                "usageCount": data["count"],
                "categories": list(data["categories"])
            })

    return result[:200]  # Top 200 notes


def aggregate_line_styles(extractions):
    """Aggregate line styles used"""
    styles = defaultdict(lambda: {"count": 0, "categories": set()})

    for ext in extractions:
        category = ext.get('category', 'Unknown')
        for style in ext.get('lineStyles', []):
            if style:
                styles[style]["count"] += 1
                styles[style]["categories"].add(category)

    result = {}
    for style, data in sorted(styles.items(), key=lambda x: -x[1]["count"]):
        result[style] = {
            "usageCount": data["count"],
            "categories": list(data["categories"])
        }

    return result


def aggregate_by_category(extractions):
    """Summarize patterns per category"""
    categories = defaultdict(lambda: {
        "fileCount": 0,
        "totalComponents": 0,
        "totalTextNotes": 0,
        "commonComponents": defaultdict(int),
        "commonNotes": defaultdict(int)
    })

    for ext in extractions:
        cat = ext.get('category', 'Unknown')
        categories[cat]["fileCount"] += 1

        for comp in ext.get('detailComponents', []):
            name = comp.get('typeName', '') if isinstance(comp, dict) else str(comp)
            if name:
                categories[cat]["commonComponents"][name] += 1
                categories[cat]["totalComponents"] += 1

        for note in ext.get('textNotes', []):
            if note:
                categories[cat]["commonNotes"][note] += 1
                categories[cat]["totalTextNotes"] += 1

    # Convert to final format
    result = {}
    for cat, data in categories.items():
        # Get top 10 components and notes for this category
        top_components = sorted(data["commonComponents"].items(), key=lambda x: -x[1])[:10]
        top_notes = sorted(data["commonNotes"].items(), key=lambda x: -x[1])[:10]

        result[cat] = {
            "fileCount": data["fileCount"],
            "totalComponents": data["totalComponents"],
            "totalTextNotes": data["totalTextNotes"],
            "topComponents": [{"name": n, "count": c} for n, c in top_components],
            "topNotes": [{"text": n, "count": c} for n, c in top_notes]
        }

    return result


def generate_learning_summary(extractions, components, notes, styles, categories):
    """Generate human-readable summary"""
    summary = []
    summary.append("# Detail Library Learning Summary")
    summary.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    summary.append(f"Files Processed: {len(extractions)}")

    summary.append("\n## Overall Statistics")
    summary.append(f"- Unique Detail Components: {len(components)}")
    summary.append(f"- Unique Text Callouts: {len(notes)}")
    summary.append(f"- Line Styles Used: {len(styles)}")
    summary.append(f"- Categories: {len(categories)}")

    summary.append("\n## Most Used Detail Components")
    summary.append("| Component | Usage Count | Categories |")
    summary.append("|-----------|-------------|------------|")
    for name, data in list(components.items())[:20]:
        cats = ", ".join(data["categories"][:3])
        if len(data["categories"]) > 3:
            cats += "..."
        summary.append(f"| {name[:40]} | {data['usageCount']} | {cats} |")

    summary.append("\n## Most Common Callouts/Annotations")
    summary.append("| Text | Usage Count |")
    summary.append("|------|-------------|")
    for note in notes[:30]:
        text = note["text"][:60]
        summary.append(f"| {text} | {note['usageCount']} |")

    summary.append("\n## Line Styles")
    for style, data in styles.items():
        summary.append(f"- **{style}**: Used {data['usageCount']} times")

    summary.append("\n## By Category")
    for cat, data in sorted(categories.items(), key=lambda x: -x[1]["fileCount"]):
        summary.append(f"\n### {cat}")
        summary.append(f"- Files: {data['fileCount']}")
        summary.append(f"- Total Components: {data['totalComponents']}")
        if data['topComponents']:
            summary.append("- Key Components: " + ", ".join([c["name"] for c in data["topComponents"][:5]]))
        if data['topNotes']:
            summary.append("- Common Notes: " + ", ".join([n["text"][:30] for n in data["topNotes"][:3]]))

    return "\n".join(summary)


def main():
    print("=" * 60)
    print("AGGREGATING DETAIL LIBRARY LEARNINGS")
    print("=" * 60)

    # Load all extractions
    print("\n[1/6] Loading extractions...")
    extractions = load_all_extractions()
    print(f"      Loaded {len(extractions)} files")

    if not extractions:
        print("No extractions to process. Run extract_all_details.ps1 first.")
        return

    # Aggregate data
    print("\n[2/6] Aggregating detail components...")
    components = aggregate_detail_components(extractions)
    print(f"      Found {len(components)} unique components")

    print("\n[3/6] Aggregating text notes...")
    notes = aggregate_text_notes(extractions)
    print(f"      Found {len(notes)} common callouts")

    print("\n[4/6] Aggregating line styles...")
    styles = aggregate_line_styles(extractions)
    print(f"      Found {len(styles)} line styles")

    print("\n[5/6] Aggregating by category...")
    categories = aggregate_by_category(extractions)
    print(f"      Processed {len(categories)} categories")

    # Save aggregated data
    print("\n[6/6] Saving aggregated data...")

    # Components
    with open(OUTPUT_DIR / "learned_components.json", 'w') as f:
        json.dump(components, f, indent=2)
    print(f"      Saved: learned_components.json")

    # Notes/Callouts
    with open(OUTPUT_DIR / "learned_callouts.json", 'w') as f:
        json.dump(notes, f, indent=2)
    print(f"      Saved: learned_callouts.json")

    # Line Styles
    with open(OUTPUT_DIR / "learned_line_styles.json", 'w') as f:
        json.dump(styles, f, indent=2)
    print(f"      Saved: learned_line_styles.json")

    # Category breakdown
    with open(OUTPUT_DIR / "learned_by_category.json", 'w') as f:
        json.dump(categories, f, indent=2)
    print(f"      Saved: learned_by_category.json")

    # Human-readable summary
    summary = generate_learning_summary(extractions, components, notes, styles, categories)
    with open(OUTPUT_DIR / "learning_summary.md", 'w') as f:
        f.write(summary)
    print(f"      Saved: learning_summary.md")

    print("\n" + "=" * 60)
    print("AGGREGATION COMPLETE")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nFiles created:")
    print("  - learned_components.json    (detail families used)")
    print("  - learned_callouts.json      (standard annotations)")
    print("  - learned_line_styles.json   (line weights/styles)")
    print("  - learned_by_category.json   (patterns per category)")
    print("  - learning_summary.md        (human-readable report)")


if __name__ == "__main__":
    main()
