#!/usr/bin/env python3
"""
Rule Comparison Framework
=========================
Compares extracted rules across multiple projects to identify:
- Universal rules (apply to all projects)
- Project-type-specific rules (apply to certain building types)
- Firm-specific rules (unique to a firm's practice)

Usage:
    python compare_project_rules.py
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def load_extracted_projects(base_dir: Path) -> list:
    """Load all extracted project JSON files."""
    projects = []
    for json_file in base_dir.glob("*-raw.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                data["source_file"] = str(json_file)
                projects.append(data)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    return projects

def classify_project_type(project: dict) -> str:
    """Classify project type based on extracted data."""
    room_analysis = project.get("room_analysis", {})

    # Multi-family indicators
    bedroom_count = room_analysis.get("Bedroom", {}).get("count", 0)
    unit_count = sum(1 for v in room_analysis.values() if v.get("count", 0) > 10)

    if bedroom_count > 50:
        return "multi-family"
    elif bedroom_count >= 3 and bedroom_count <= 10:
        return "single-family"
    elif room_analysis.get("Office", {}).get("count", 0) > 5:
        return "commercial-office"
    else:
        return "unknown"

def compare_rule_presence(projects: list) -> dict:
    """Compare which rules appear across projects."""
    rule_presence = defaultdict(list)

    for project in projects:
        project_name = project.get("project_name", "Unknown")
        project_type = classify_project_type(project)

        for rule in project.get("proposed_rules", []):
            rule_id = rule.get("id")
            rule_presence[rule_id].append({
                "project": project_name,
                "type": project_type,
                "confidence": rule.get("confidence"),
                "evidence": rule.get("evidence"),
            })

    return dict(rule_presence)

def classify_rules(rule_presence: dict, total_projects: int) -> dict:
    """Classify rules as universal, type-specific, or firm-specific."""
    classifications = {
        "universal": [],
        "type_specific": [],
        "firm_specific": [],
        "insufficient_data": [],
    }

    for rule_id, occurrences in rule_presence.items():
        presence_ratio = len(occurrences) / total_projects

        if total_projects < 3:
            classifications["insufficient_data"].append({
                "rule_id": rule_id,
                "occurrences": len(occurrences),
                "note": "Need more projects for accurate classification",
            })
        elif presence_ratio >= 0.8:
            classifications["universal"].append({
                "rule_id": rule_id,
                "presence": f"{len(occurrences)}/{total_projects}",
                "confidence": "HIGH",
            })
        elif presence_ratio >= 0.5:
            # Check if type-specific
            project_types = [o["type"] for o in occurrences]
            unique_types = set(project_types)

            if len(unique_types) == 1:
                classifications["type_specific"].append({
                    "rule_id": rule_id,
                    "applies_to": list(unique_types)[0],
                    "presence": f"{len(occurrences)}/{total_projects}",
                })
            else:
                classifications["universal"].append({
                    "rule_id": rule_id,
                    "presence": f"{len(occurrences)}/{total_projects}",
                    "confidence": "MEDIUM",
                })
        else:
            classifications["firm_specific"].append({
                "rule_id": rule_id,
                "occurrences": len(occurrences),
                "projects": [o["project"] for o in occurrences],
            })

    return classifications

def generate_comparison_report(
    projects: list,
    rule_presence: dict,
    classifications: dict
) -> str:
    """Generate markdown comparison report."""
    timestamp = datetime.now().strftime("%Y-%m-%d")

    report = f"""# Rule Comparison Analysis

**Generated:** {timestamp}
**Projects Analyzed:** {len(projects)}

---

## Projects Included

| Project | Type | Rooms | Views | Sheets |
|---------|------|-------|-------|--------|
"""
    for p in projects:
        stats = p.get("statistics", {})
        report += f"| {p.get('project_name', 'Unknown')} | {classify_project_type(p)} | {stats.get('rooms', 0)} | {stats.get('views', 0)} | {stats.get('sheets', 0)} |\n"

    report += """
---

## Rule Classification Summary

"""

    if classifications.get("universal"):
        report += "### ✅ Universal Rules (Apply to All Projects)\n\n"
        report += "| Rule | Presence | Confidence |\n"
        report += "|------|----------|------------|\n"
        for r in classifications["universal"]:
            report += f"| {r['rule_id']} | {r['presence']} | {r.get('confidence', 'N/A')} |\n"
        report += "\n"

    if classifications.get("type_specific"):
        report += "### 🏢 Type-Specific Rules\n\n"
        report += "| Rule | Applies To | Presence |\n"
        report += "|------|------------|----------|\n"
        for r in classifications["type_specific"]:
            report += f"| {r['rule_id']} | {r['applies_to']} | {r['presence']} |\n"
        report += "\n"

    if classifications.get("firm_specific"):
        report += "### 🏛️ Firm/Project-Specific Rules\n\n"
        report += "| Rule | Found In |\n"
        report += "|------|----------|\n"
        for r in classifications["firm_specific"]:
            report += f"| {r['rule_id']} | {', '.join(r['projects'])} |\n"
        report += "\n"

    if classifications.get("insufficient_data"):
        report += "### ⚠️ Insufficient Data\n\n"
        report += "*Need more projects to accurately classify these rules:*\n\n"
        for r in classifications["insufficient_data"]:
            report += f"- {r['rule_id']} (found in {r['occurrences']} project(s))\n"
        report += "\n"

    report += """---

## Rule Details by ID

"""
    for rule_id, occurrences in rule_presence.items():
        report += f"### {rule_id}\n\n"
        report += "| Project | Type | Confidence |\n"
        report += "|---------|------|------------|\n"
        for o in occurrences:
            report += f"| {o['project']} | {o['type']} | {o['confidence']} |\n"
        report += "\n"

    report += """---

## Recommendations

"""
    if len(projects) < 3:
        report += """### 🔴 Need More Data

To accurately classify rules as universal vs. specific, extract from at least:
- 1 more multi-family project
- 1 single-family residential project
- 1 commercial/healthcare project

This will enable statistical comparison across building types.
"""
    else:
        report += """### ✅ Sufficient Data for Initial Analysis

Consider:
1. Validating universal rules with user feedback
2. Testing type-specific rules on new projects of that type
3. Documenting firm-specific rules as firm standards
"""

    return report

def main():
    base_dir = Path(__file__).parent.parent / "extracted-projects"

    print("=" * 60)
    print("RULE COMPARISON FRAMEWORK")
    print("=" * 60)

    # Load projects
    print("\nLoading extracted projects...")
    projects = load_extracted_projects(base_dir)
    print(f"  Found {len(projects)} projects")

    if not projects:
        print("\nNo extracted projects found!")
        print(f"Run extract_project_patterns.py first to create project extractions.")
        return

    # Compare rules
    print("\nComparing rules across projects...")
    rule_presence = compare_rule_presence(projects)
    print(f"  Found {len(rule_presence)} unique rules")

    # Classify rules
    print("\nClassifying rules...")
    classifications = classify_rules(rule_presence, len(projects))

    # Generate report
    report = generate_comparison_report(projects, rule_presence, classifications)

    # Save report
    output_file = base_dir / "rule-comparison-analysis.md"
    with open(output_file, "w") as f:
        f.write(report)

    print(f"\nReport saved to: {output_file}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Projects analyzed: {len(projects)}")
    print(f"  Universal rules: {len(classifications.get('universal', []))}")
    print(f"  Type-specific rules: {len(classifications.get('type_specific', []))}")
    print(f"  Firm-specific rules: {len(classifications.get('firm_specific', []))}")
    print(f"  Insufficient data: {len(classifications.get('insufficient_data', []))}")

    return report

if __name__ == "__main__":
    main()
