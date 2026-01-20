#!/usr/bin/env python3
"""
Rule Classifier
===============
Takes validated rules and generates executable logic for the CIPS system.
Transforms human-validated patterns into code that can be applied automatically.

Usage:
    python rule_classifier.py

Input: validated-rules.json (user-approved rules)
Output: executable-rules.json (ready for CIPS integration)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class RuleClassifier:
    """Classifies and codifies validated rules."""

    def __init__(self):
        self.rule_templates = {
            "UNIT_ENLARGED_PLANS": self._codify_unit_enlarged_plans,
            "TYPICAL_FLOOR_GROUPING": self._codify_typical_floor_grouping,
            "LIFE_SAFETY_PLANS": self._codify_life_safety_plans,
            "SECTION_ORGANIZATION": self._codify_section_organization,
            "DETAIL_ORGANIZATION": self._codify_detail_organization,
            "COMMON_AREA_RESTROOMS": self._codify_common_area_restrooms,
            "ADA_DOCUMENTATION": self._codify_ada_documentation,
        }

    def codify_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a validated rule to executable format."""
        rule_id = rule.get("id")

        if rule_id in self.rule_templates:
            return self.rule_templates[rule_id](rule)
        else:
            return self._codify_generic(rule)

    def _codify_unit_enlarged_plans(self, rule: Dict) -> Dict:
        """Generate executable logic for unit enlarged plans."""
        return {
            "rule_id": "UNIT_ENLARGED_PLANS",
            "category": "sheet_generation",
            "trigger": {
                "conditions": [
                    {"field": "project_type", "operator": "in", "value": ["multi-family", "apartment", "condo"]},
                    {"field": "unique_unit_types", "operator": ">", "value": 1},
                ],
                "logic": "AND"
            },
            "action": {
                "type": "create_sheets",
                "template": {
                    "sheet_series": "A-9",
                    "naming_pattern": "ENLARGED {unit_type} FLR. PLN.",
                    "per_item": "unique_unit_type",
                },
                "view_requirements": [
                    {"view_type": "FloorPlan", "scope": "unit_boundary", "scale": "1/4\" = 1'-0\""},
                    {"view_type": "CeilingPlan", "scope": "unit_boundary", "scale": "1/4\" = 1'-0\""},
                ],
            },
            "mcp_methods": [
                "createSheet",
                "createFloorPlan",
                "placeViewOnSheet",
            ],
            "validation": {
                "check": "Each unique unit type has corresponding A-9.x sheet",
                "auto_fix": False,
            }
        }

    def _codify_typical_floor_grouping(self, rule: Dict) -> Dict:
        """Generate executable logic for typical floor grouping."""
        return {
            "rule_id": "TYPICAL_FLOOR_GROUPING",
            "category": "sheet_organization",
            "trigger": {
                "conditions": [
                    {"field": "identical_floor_count", "operator": ">=", "value": 2},
                ],
                "logic": "AND"
            },
            "action": {
                "type": "group_floors",
                "template": {
                    "naming_pattern": "{start_floor} THRU {end_floor} LVL. {view_type}",
                    "single_sheet": True,
                },
                "detection": {
                    "similarity_threshold": 0.95,
                    "compare_elements": ["walls", "doors", "windows", "rooms"],
                },
            },
            "mcp_methods": [
                "getFloorPlansByLevel",
                "compareViewContent",
                "createSheet",
            ],
            "validation": {
                "check": "Identical floors share single sheet",
                "auto_fix": False,
            }
        }

    def _codify_life_safety_plans(self, rule: Dict) -> Dict:
        """Generate executable logic for life safety plans."""
        return {
            "rule_id": "LIFE_SAFETY_PLANS",
            "category": "code_compliance",
            "trigger": {
                "conditions": [
                    {"field": "building_height", "operator": ">", "value": 3, "unit": "stories"},
                    {"field": "occupancy_type", "operator": "in", "value": ["assembly", "institutional", "high-rise"]},
                ],
                "logic": "OR"
            },
            "action": {
                "type": "create_sheets",
                "template": {
                    "sheet_series": "A-0.1",
                    "naming_pattern": "{floor_name} LIFE SAFETY PLAN",
                    "per_item": "unique_floor_or_group",
                },
                "required_elements": [
                    "exit_paths",
                    "fire_ratings",
                    "egress_distances",
                    "occupant_loads",
                    "exit_signage",
                ],
            },
            "mcp_methods": [
                "createSheet",
                "duplicateView",
                "setViewTemplate",
                "addAnnotation",
            ],
            "validation": {
                "check": "Each unique floor (or typical group) has life safety plan",
                "auto_fix": False,
            }
        }

    def _codify_section_organization(self, rule: Dict) -> Dict:
        """Generate executable logic for section organization."""
        return {
            "rule_id": "SECTION_ORGANIZATION",
            "category": "view_organization",
            "trigger": {
                "conditions": [
                    {"field": "project_phase", "operator": ">=", "value": "DD"},
                ],
                "logic": "AND"
            },
            "action": {
                "type": "organize_sections",
                "rules": {
                    "building_sections": {
                        "sheet_series": "A-4",
                        "criteria": "cuts_through_entire_building",
                        "typical_count": "2-4",
                        "orientations": ["longitudinal", "transverse"],
                    },
                    "wall_sections": {
                        "sheet_series": "A-5",
                        "criteria": "details_specific_assembly",
                        "per_item": "wall_type_or_condition",
                    },
                },
            },
            "mcp_methods": [
                "createSection",
                "createSheet",
                "placeViewOnSheet",
            ],
            "validation": {
                "check": "Building sections on A-4.x, wall sections on A-5.x",
                "auto_fix": True,
            }
        }

    def _codify_detail_organization(self, rule: Dict) -> Dict:
        """Generate executable logic for detail organization."""
        return {
            "rule_id": "DETAIL_ORGANIZATION",
            "category": "sheet_organization",
            "trigger": {
                "conditions": [
                    {"field": "project_phase", "operator": ">=", "value": "CD"},
                ],
                "logic": "AND"
            },
            "action": {
                "type": "organize_details",
                "categories": {
                    "roof": {"sheet_series": "A-2.6", "keywords": ["roof", "parapet", "flashing"]},
                    "stair_elevator": {"sheet_series": "A-6", "keywords": ["stair", "elevator", "ramp"]},
                    "door": {"sheet_series": "A-7.2", "keywords": ["door", "frame", "hardware"]},
                    "window": {"sheet_series": "A-8.2", "keywords": ["window", "glazing", "storefront"]},
                    "partition": {"sheet_series": "A-10", "keywords": ["partition", "casework", "millwork"]},
                },
            },
            "mcp_methods": [
                "getDraftingViews",
                "moveViewToSheet",
                "createSheet",
            ],
            "validation": {
                "check": "Details organized by element type on appropriate sheets",
                "auto_fix": True,
            }
        }

    def _codify_common_area_restrooms(self, rule: Dict) -> Dict:
        """Generate executable logic for common area restrooms."""
        return {
            "rule_id": "COMMON_AREA_RESTROOMS",
            "category": "enlarged_plans",
            "trigger": {
                "conditions": [
                    {"field": "has_common_restrooms", "operator": "==", "value": True},
                    {"field": "restroom_is_public", "operator": "==", "value": True},
                ],
                "logic": "AND"
            },
            "action": {
                "type": "create_enlarged_plan",
                "template": {
                    "sheet_series": "A-9",
                    "naming_pattern": "ENLARGED RESTROOM FLOOR PLAN",
                },
                "required_elements": [
                    "fixture_layout",
                    "partition_details",
                    "ada_clearances",
                    "door_swings",
                ],
            },
            "mcp_methods": [
                "createFloorPlan",
                "setCropRegion",
                "createSheet",
                "placeViewOnSheet",
            ],
            "validation": {
                "check": "Common/public restrooms have enlarged plans",
                "auto_fix": False,
            }
        }

    def _codify_ada_documentation(self, rule: Dict) -> Dict:
        """Generate executable logic for ADA documentation."""
        return {
            "rule_id": "ADA_DOCUMENTATION",
            "category": "code_compliance",
            "trigger": {
                "conditions": [
                    {"field": "has_public_areas", "operator": "==", "value": True},
                    {"field": "occupancy_type", "operator": "not_in", "value": ["single-family"]},
                ],
                "logic": "AND"
            },
            "action": {
                "type": "create_sheets",
                "template": {
                    "sheet_series": "A-0",
                    "naming_pattern": "ADA NOTES & DETAILS",
                },
                "standard_content": [
                    "accessibility_notes",
                    "clearance_diagrams",
                    "fixture_mounting_heights",
                    "signage_requirements",
                ],
            },
            "mcp_methods": [
                "createSheet",
                "importDraftingViews",
                "addTextNote",
            ],
            "validation": {
                "check": "ADA documentation sheets exist for public buildings",
                "auto_fix": False,
            }
        }

    def _codify_generic(self, rule: Dict) -> Dict:
        """Generate generic executable format for unknown rules."""
        return {
            "rule_id": rule.get("id", "UNKNOWN"),
            "category": "custom",
            "trigger": {
                "conditions": [
                    {"field": "custom", "operator": "custom", "value": rule.get("condition", "")},
                ],
                "logic": "AND"
            },
            "action": {
                "type": "custom",
                "description": rule.get("action", ""),
            },
            "mcp_methods": [],
            "validation": {
                "check": "Manual validation required",
                "auto_fix": False,
            }
        }


def load_validated_rules(base_dir: Path) -> List[Dict]:
    """Load user-validated rules from JSON files."""
    rules = []

    # First check for explicit validated-rules.json
    validated_file = base_dir / "validated-rules.json"
    if validated_file.exists():
        with open(validated_file) as f:
            data = json.load(f)
            return data.get("rules", [])

    # Otherwise, aggregate from raw extractions (treating HIGH confidence as validated)
    for json_file in base_dir.glob("*-raw.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                for rule in data.get("proposed_rules", []):
                    if rule.get("confidence") == "HIGH":
                        rules.append(rule)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    return rules


def main():
    base_dir = Path(__file__).parent.parent / "extracted-projects"

    print("=" * 60)
    print("RULE CLASSIFIER")
    print("=" * 60)

    # Load validated rules
    print("\nLoading validated rules...")
    rules = load_validated_rules(base_dir)
    print(f"  Found {len(rules)} validated rules")

    if not rules:
        print("\nNo validated rules found!")
        print("Either:")
        print("  1. Create validated-rules.json with approved rules")
        print("  2. Or ensure *-raw.json files have HIGH confidence rules")
        return

    # Classify and codify rules
    classifier = RuleClassifier()
    executable_rules = []

    print("\nCodifying rules...")
    for rule in rules:
        codified = classifier.codify_rule(rule)
        executable_rules.append(codified)
        print(f"  ✓ {rule.get('id', 'UNKNOWN')}")

    # Save executable rules
    output = {
        "generated_at": datetime.now().isoformat(),
        "source": "rule_classifier.py",
        "total_rules": len(executable_rules),
        "rules": executable_rules,
    }

    output_file = base_dir / "executable-rules.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nExecutable rules saved to: {output_file}")

    # Generate summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    categories = {}
    for rule in executable_rules:
        cat = rule.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\nRules by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # List MCP methods needed
    all_methods = set()
    for rule in executable_rules:
        all_methods.update(rule.get("mcp_methods", []))

    print(f"\nMCP methods required: {len(all_methods)}")
    for method in sorted(all_methods):
        print(f"  - {method}")

    return output


if __name__ == "__main__":
    main()
