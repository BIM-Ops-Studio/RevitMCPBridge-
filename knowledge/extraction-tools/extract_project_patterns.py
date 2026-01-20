#!/usr/bin/env python3
"""
Project Pattern Extractor
=========================
Extracts patterns from currently open Revit project via MCP.
Generates proposed rules with confidence scores for user validation.

Usage:
    python extract_project_patterns.py [project_name]

If project_name not provided, will query from Revit.
"""

import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# MCP communication
MCP_PIPE_CMD = r'powershell.exe -Command "$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(\".\", \"RevitMCPBridge2026\", [System.IO.Pipes.PipeDirection]::InOut); $pipeClient.Connect(5000); $writer = New-Object System.IO.StreamWriter($pipeClient); $reader = New-Object System.IO.StreamReader($pipeClient); $writer.WriteLine(\"{METHOD_JSON}\"); $writer.Flush(); $response = $reader.ReadLine(); Write-Output $response; $pipeClient.Close()"'

def call_mcp(method: str, params: dict = None) -> dict:
    """Call MCP method and return JSON response."""
    request = {"method": method, "params": params or {}}
    request_json = json.dumps(request).replace('"', '\\"')
    cmd = MCP_PIPE_CMD.replace("{METHOD_JSON}", request_json)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
        if result.stdout.strip():
            return json.loads(result.stdout.strip())
    except Exception as e:
        print(f"Error calling {method}: {e}")
    return {"success": False, "error": "MCP call failed"}

def extract_rooms(doc_data: dict) -> list:
    """Extract room data."""
    result = call_mcp("getRooms")
    if result.get("success"):
        return result.get("rooms", [])
    return []

def extract_views(doc_data: dict) -> list:
    """Extract view data."""
    result = call_mcp("getViews")
    if result.get("success"):
        return result.get("result", {}).get("views", [])
    return []

def extract_sheets(doc_data: dict) -> list:
    """Extract sheet data."""
    result = call_mcp("getAllSheets")
    if result.get("success"):
        return result.get("result", {}).get("sheets", [])
    return []

def extract_firm_from_titleblock() -> dict:
    """
    Extract firm name from titleblock family names.

    Key insight: Titleblock families are named by the design firm that created them.
    Pattern: TITLEBLOCK_{FIRM}_{SIZE}_{VARIANT}

    Example: TITLEBLOCK_SOP_36x24_2018 -> Firm is "SOP"

    The folder structure shows CLIENT organization, not the architect.
    This is the authoritative source for firm identification.
    """
    result = call_mcp("getLoadedFamilies")
    if not result.get("success"):
        return {"firm": "unknown", "titleblocks": [], "note": "Could not query families"}

    families = result.get("families", [])

    # Filter for titleblock families
    titleblock_families = [
        f for f in families
        if f.get("category", "").lower() == "title blocks"
    ]

    if not titleblock_families:
        return {"firm": "unknown", "titleblocks": [], "note": "No titleblock families found"}

    # Parse titleblock names to find firm prefix
    firm_prefixes = []
    for tb in titleblock_families:
        name = tb.get("name", "")
        # Parse TITLEBLOCK_{FIRM}_{SIZE} pattern
        if name.upper().startswith("TITLEBLOCK_"):
            parts = name.split("_")
            if len(parts) >= 2:
                # Second part is typically the firm abbreviation
                firm_candidate = parts[1]
                # Skip generic names like SCHEMATIC, SKETCH, etc.
                if firm_candidate.upper() not in ["SCHEMATIC", "SKETCH", "STANDARD"]:
                    firm_prefixes.append(firm_candidate)

    # Find most common firm prefix (main CD titleblock)
    firm = "unknown"
    if firm_prefixes:
        from collections import Counter
        prefix_counts = Counter(firm_prefixes)
        firm = prefix_counts.most_common(1)[0][0]

    return {
        "firm": firm,
        "titleblocks": [tb.get("name") for tb in titleblock_families],
        "note": f"Identified from titleblock naming pattern"
    }

def classify_room_type(name: str) -> str:
    """Classify room by name."""
    name = name.upper()
    mappings = [
        (["KITCHEN", "KIT"], "Kitchen"),
        (["BATH", "RR", "RESTROOM", "TOILET"], "Bathroom"),
        (["BED", "BEDROOM", "BR"], "Bedroom"),
        (["LIVING", "GREAT", "FAMILY"], "Living"),
        (["OFFICE"], "Office"),
        (["CLOSET", "W.I.C", "WIC"], "Closet"),
        (["UTILITY", "MECH", "ELEC", "LAUNDRY"], "Utility"),
        (["LOBBY", "CORRIDOR", "HALL"], "Circulation"),
        (["STAIR"], "Stair"),
        (["BALCONY", "TERRACE", "PATIO"], "Balcony"),
        (["GARAGE"], "Garage"),
        (["DINING"], "Dining"),
    ]
    for keywords, room_type in mappings:
        if any(kw in name for kw in keywords):
            return room_type
    return "Other"

def classify_sheet_category(sheet_number: str) -> str:
    """Classify sheet by number prefix."""
    num = sheet_number.upper()
    categories = {
        "A-0": "A-0: General/Index",
        "A-1": "A-1: Site",
        "A-2": "A-2: Plans/RCP",
        "A-3": "A-3: Elevations",
        "A-4": "A-4: Building Sections",
        "A-5": "A-5: Wall Sections",
        "A-6": "A-6: Vertical Circulation",
        "A-7": "A-7: Schedules",
        "A-8": "A-8: Windows/Finishes",
        "A-9": "A-9: Enlarged Plans",
        "A-10": "A-10: Details",
        "LP": "LP: Landscape",
        "C": "C: Civil",
        "S": "S: Structural",
        "M": "M: Mechanical",
        "E": "E: Electrical",
        "P": "P: Plumbing",
    }
    for prefix, category in categories.items():
        if num.startswith(prefix):
            return category
    return "Other"

def analyze_room_patterns(rooms: list) -> dict:
    """Analyze room distribution patterns."""
    room_types = defaultdict(list)

    for room in rooms:
        name = room.get("name", "")
        area = room.get("area", 0)
        room_type = classify_room_type(name)
        room_types[room_type].append({
            "name": name,
            "area": area,
            "level": room.get("level", ""),
        })

    analysis = {}
    for rtype, rlist in room_types.items():
        areas = [r["area"] for r in rlist if r["area"] > 0]
        analysis[rtype] = {
            "count": len(rlist),
            "avg_area": sum(areas) / len(areas) if areas else 0,
            "min_area": min(areas) if areas else 0,
            "max_area": max(areas) if areas else 0,
            "samples": [r["name"] for r in rlist[:5]],
        }

    return analysis

def analyze_view_patterns(views: list) -> dict:
    """Analyze view type distribution."""
    view_types = defaultdict(list)

    for view in views:
        vtype = view.get("viewType", "Unknown")
        view_types[vtype].append({
            "name": view.get("name", ""),
            "scale": view.get("scale"),
            "level": view.get("level"),
        })

    analysis = {}
    for vtype, vlist in view_types.items():
        analysis[vtype] = {
            "count": len(vlist),
            "samples": [v["name"] for v in vlist[:5]],
        }

    return analysis

def analyze_sheet_patterns(sheets: list) -> dict:
    """Analyze sheet organization patterns."""
    categories = defaultdict(list)

    for sheet in sheets:
        num = sheet.get("sheetNumber", "")
        name = sheet.get("sheetName", "")
        category = classify_sheet_category(num)
        categories[category].append({
            "number": num,
            "name": name,
            "viewCount": sheet.get("viewCount", 0),
        })

    analysis = {}
    for cat, slist in categories.items():
        analysis[cat] = {
            "count": len(slist),
            "sheets": [{"num": s["number"], "name": s["name"]} for s in slist],
        }

    return analysis

def detect_sheet_numbering_pattern(sheets: list) -> str:
    """Detect sheet numbering pattern style."""
    numbers = [s.get("sheetNumber", "") for s in sheets]

    # Check for dot patterns (A-2.1, A-2.2)
    dot_pattern = sum(1 for n in numbers if "." in n)
    dash_pattern = sum(1 for n in numbers if "-" in n)
    simple_pattern = sum(1 for n in numbers if n.isalnum())

    if dot_pattern > len(numbers) * 0.5:
        return "Dot-decimal (A-2.1, A-2.2)"
    elif dash_pattern > len(numbers) * 0.5:
        return "Dash-separated (A-2-1)"
    else:
        return "Simple alphanumeric (A201)"

def generate_proposed_rules(
    room_analysis: dict,
    view_analysis: dict,
    sheet_analysis: dict,
    project_name: str
) -> list:
    """Generate proposed rules from analysis."""
    rules = []

    # Rule: Unit Enlarged Plans (for multi-family)
    enlarged_sheets = [
        s for cat, data in sheet_analysis.items()
        if "A-9" in cat
        for s in data.get("sheets", [])
    ]
    if enlarged_sheets:
        rules.append({
            "id": "UNIT_ENLARGED_PLANS",
            "name": "Unit Enlarged Plans",
            "condition": "project_type = 'multi-family' AND unit_types > 1",
            "action": "Create enlarged floor plan for each unique unit type",
            "details": {
                "sheet_series": "A-9.x",
                "scale": "Larger than overall floor plan",
                "includes": ["Floor plan", "RCP callout"],
            },
            "evidence": [f"{s['num']}: {s['name']}" for s in enlarged_sheets[:6]],
            "confidence": "HIGH" if len(enlarged_sheets) >= 3 else "MEDIUM",
            "validation_needed": [
                "Confirm: Each distinct unit type gets its own sheet",
                "Scale used for enlarged plans?",
                "What triggers a 'distinct' unit?",
            ],
        })

    # Rule: Life Safety Plans
    life_safety_sheets = [
        s for cat, data in sheet_analysis.items()
        for s in data.get("sheets", [])
        if "LIFE SAFETY" in s.get("name", "").upper()
    ]
    if life_safety_sheets:
        rules.append({
            "id": "LIFE_SAFETY_PLANS",
            "name": "Life Safety Plans",
            "condition": "building_height > 3_stories OR occupancy = assembly/institutional",
            "action": "Create life safety plan for each unique floor",
            "details": {
                "sheet_series": "A-0.1x",
                "shows": ["Exit paths", "Fire ratings", "Egress distances"],
            },
            "evidence": [f"{s['num']}: {s['name']}" for s in life_safety_sheets],
            "confidence": "HIGH",
            "validation_needed": [
                "When is life safety required vs optional?",
                "What elements must appear?",
            ],
        })

    # Rule: Floor Plan Grouping (Typical Floors)
    floor_plan_sheets = [
        s for cat, data in sheet_analysis.items()
        if "Plans" in cat
        for s in data.get("sheets", [])
    ]
    typical_patterns = [s for s in floor_plan_sheets if "THRU" in s.get("name", "").upper()]
    if typical_patterns:
        rules.append({
            "id": "TYPICAL_FLOOR_GROUPING",
            "name": "Floor Plan Grouping (Typical Floors)",
            "condition": "Multiple identical floors exist",
            "action": "Combine typical floors on single sheet (e.g., '4TH THRU 11TH')",
            "details": {
                "reduces": "Sheet count",
                "note": "TYP. FLOORS or similar designation",
            },
            "evidence": [f"{s['num']}: {s['name']}" for s in typical_patterns],
            "confidence": "HIGH",
            "validation_needed": [
                "Threshold for 'typical' - how similar must floors be?",
                "When do you split vs. combine?",
            ],
        })

    # Rule: Building vs Wall Sections
    building_section_sheets = [
        s for cat, data in sheet_analysis.items()
        if "Building Section" in cat
        for s in data.get("sheets", [])
    ]
    wall_section_sheets = [
        s for cat, data in sheet_analysis.items()
        if "Wall Section" in cat
        for s in data.get("sheets", [])
    ]
    if building_section_sheets or wall_section_sheets:
        rules.append({
            "id": "SECTION_ORGANIZATION",
            "name": "Building Sections vs Wall Sections",
            "condition": "Project requires section documentation",
            "action": "Separate building sections (A-4.x) from wall sections (A-5.x)",
            "details": {
                "building_sections": {
                    "purpose": "Cut through entire building, show floor-to-floor relationships",
                    "typical_count": "2-4 (longitudinal + transverse)",
                },
                "wall_sections": {
                    "purpose": "Detail specific assembly conditions, show construction layers",
                    "typical_count": "Per wall type + special conditions",
                },
            },
            "evidence": {
                "building": [f"{s['num']}: {s['name']}" for s in building_section_sheets[:3]],
                "wall": [f"{s['num']}: {s['name']}" for s in wall_section_sheets[:3]],
            },
            "confidence": "HIGH",
            "validation_needed": [
                "What determines where building sections cut?",
                "Which wall conditions get dedicated sections?",
            ],
        })

    # Rule: Detail Organization
    detail_sheets = [
        s for cat, data in sheet_analysis.items()
        for s in data.get("sheets", [])
        if "DETAIL" in s.get("name", "").upper()
    ]
    if detail_sheets:
        rules.append({
            "id": "DETAIL_ORGANIZATION",
            "name": "Detail Organization by Element Type",
            "condition": "Project has construction details",
            "action": "Organize details by building element type",
            "details": {
                "categories": {
                    "Roof details": "A-2.6",
                    "Stair/elevator": "A-6.x",
                    "Door details": "A-7.2",
                    "Window details": "A-8.2",
                    "Partition/casework": "A-10.x",
                },
            },
            "evidence": [f"{s['num']}: {s['name']}" for s in detail_sheets[:6]],
            "confidence": "HIGH",
            "validation_needed": [
                "Is this CSI-based or custom organization?",
                "How do you decide typical vs specific detail?",
            ],
        })

    # Rule: Common Area Documentation
    bathroom_count = room_analysis.get("Bathroom", {}).get("count", 0)
    restroom_sheets = [
        s for cat, data in sheet_analysis.items()
        for s in data.get("sheets", [])
        if "RESTROOM" in s.get("name", "").upper()
    ]
    if restroom_sheets and bathroom_count > 10:
        rules.append({
            "id": "COMMON_AREA_RESTROOMS",
            "name": "Common Area Restroom Documentation",
            "condition": "Restroom = public/common (not in unit)",
            "action": "Create enlarged restroom plan",
            "details": {
                "sheet": "A-9.15 or similar",
                "includes": ["Fixture layout", "Partition details", "ADA clearances"],
                "note": "Unit bathrooms shown in unit enlarged plans",
            },
            "evidence": {
                "restroom_sheets": [f"{s['num']}: {s['name']}" for s in restroom_sheets],
                "total_bathrooms": bathroom_count,
            },
            "confidence": "MEDIUM",
            "validation_needed": [
                "Confirm: Only common restrooms get separate sheets",
                "Unit bathrooms covered by unit enlarged plans?",
            ],
        })

    return rules

def generate_report(
    project_name: str,
    room_analysis: dict,
    view_analysis: dict,
    sheet_analysis: dict,
    numbering_pattern: str,
    rules: list,
) -> str:
    """Generate markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d")

    report = f"""# {project_name} - Extracted Decision Rules

**Extracted:** {timestamp}

---

## Project Statistics

| Category | Count |
|----------|-------|
| Total Rooms | {sum(d['count'] for d in room_analysis.values())} |
| Total Views | {sum(d['count'] for d in view_analysis.values())} |
| Total Sheets | {sum(d['count'] for d in sheet_analysis.values())} |

### Room Distribution

| Room Type | Count | Avg Area |
|-----------|-------|----------|
"""
    for rtype, data in sorted(room_analysis.items(), key=lambda x: -x[1]['count']):
        report += f"| {rtype} | {data['count']} | {data['avg_area']:.0f} sf |\n"

    report += f"""
### Sheet Numbering Pattern
**Detected:** {numbering_pattern}

### Sheet Categories

| Category | Count |
|----------|-------|
"""
    for cat, data in sorted(sheet_analysis.items()):
        report += f"| {cat} | {data['count']} |\n"

    report += "\n---\n\n## PROPOSED RULES\n\n"

    for i, rule in enumerate(rules, 1):
        report += f"""### RULE {i}: {rule['name']}
**Status:** {'✅ VALIDATED' if rule['confidence'] == 'HIGH' else '⚠️ NEEDS VALIDATION'} ({rule['confidence']} confidence)

```
IF {rule['condition']}
THEN {rule['action']}
```

**Details:**
"""
        if isinstance(rule.get('details'), dict):
            for k, v in rule['details'].items():
                if isinstance(v, dict):
                    report += f"  - {k}:\n"
                    for k2, v2 in v.items():
                        report += f"    - {k2}: {v2}\n"
                else:
                    report += f"  - {k}: {v}\n"

        report += "\n**Evidence:**\n"
        evidence = rule.get('evidence', [])
        if isinstance(evidence, list):
            for e in evidence[:6]:
                report += f"- {e}\n"
        elif isinstance(evidence, dict):
            for ek, ev in evidence.items():
                report += f"- {ek}: {ev}\n"

        report += "\n**Your Validation Needed:**\n"
        for q in rule.get('validation_needed', []):
            report += f"- [ ] {q}\n"

        report += "\n---\n\n"

    report += """## NEXT STEPS

1. **You validate** these rules (confirm/reject/modify)
2. **I extract** from 2-3 more projects (different types)
3. **Compare** to find universal vs. project-specific rules
4. **Codify** validated rules into executable logic

"""
    return report

def main():
    print("=" * 60)
    print("PROJECT PATTERN EXTRACTOR")
    print("=" * 60)

    # Get project name from args or query
    project_name = sys.argv[1] if len(sys.argv) > 1 else "Unknown Project"

    print(f"\nExtracting patterns from: {project_name}")
    print("-" * 40)

    # Extract data
    print("Extracting firm from titleblock...")
    firm_info = extract_firm_from_titleblock()
    print(f"  Firm: {firm_info['firm']} ({firm_info['note']})")
    if firm_info['titleblocks']:
        print(f"  Titleblocks: {', '.join(firm_info['titleblocks'][:3])}")

    print("Extracting rooms...")
    rooms = extract_rooms({})
    print(f"  Found {len(rooms)} rooms")

    print("Extracting views...")
    views = extract_views({})
    print(f"  Found {len(views)} views")

    print("Extracting sheets...")
    sheets = extract_sheets({})
    print(f"  Found {len(sheets)} sheets")

    # Analyze patterns
    print("\nAnalyzing patterns...")
    room_analysis = analyze_room_patterns(rooms)
    view_analysis = analyze_view_patterns(views)
    sheet_analysis = analyze_sheet_patterns(sheets)
    numbering_pattern = detect_sheet_numbering_pattern(sheets)

    # Generate rules
    print("Generating proposed rules...")
    rules = generate_proposed_rules(
        room_analysis, view_analysis, sheet_analysis, project_name
    )
    print(f"  Generated {len(rules)} rules")

    # Generate report
    report = generate_report(
        project_name, room_analysis, view_analysis,
        sheet_analysis, numbering_pattern, rules
    )

    # Save report
    output_dir = Path(__file__).parent.parent / "extracted-projects"
    output_dir.mkdir(exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in project_name)
    safe_name = safe_name.lower().replace(" ", "-")
    output_file = output_dir / f"{safe_name}-rules.md"

    with open(output_file, "w") as f:
        f.write(report)

    print(f"\nReport saved to: {output_file}")
    print("=" * 60)

    # Also output raw data for further analysis
    raw_data = {
        "project_name": project_name,
        "firm": firm_info["firm"],
        "firm_note": firm_info["note"],
        "titleblock_families": firm_info["titleblocks"],
        "extracted_at": datetime.now().isoformat(),
        "statistics": {
            "rooms": len(rooms),
            "views": len(views),
            "sheets": len(sheets),
        },
        "room_analysis": room_analysis,
        "view_analysis": view_analysis,
        "sheet_analysis": sheet_analysis,
        "numbering_pattern": numbering_pattern,
        "proposed_rules": rules,
    }

    json_file = output_dir / f"{safe_name}-raw.json"
    with open(json_file, "w") as f:
        json.dump(raw_data, f, indent=2)

    print(f"Raw data saved to: {json_file}")

    return report

if __name__ == "__main__":
    main()
