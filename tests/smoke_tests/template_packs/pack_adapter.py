#!/usr/bin/env python3
"""
Pack Adapter - Converts resolved template packs to Spine v0.2 format.

The new template pack system (v2) has a different schema than what Spine v0.2 expects.
This adapter bridges the gap, allowing Spine to work with both old and new packs.

Usage:
    from pack_adapter import adapt_pack_for_spine

    # Load resolved pack
    with open('resolved/resolved_multifamily.json') as f:
        resolved = json.load(f)

    # Convert to Spine v0.2 format
    spine_standards = adapt_pack_for_spine(resolved)
"""

from typing import Dict, Any


def adapt_pack_for_spine(resolved_pack: Dict) -> Dict:
    """
    Convert a resolved template pack (v2) to Spine v0.2 standards format (v1).

    Args:
        resolved_pack: A resolved pack from pack_resolver.py

    Returns:
        Standards dict in the format Spine v0.2 expects
    """
    identity = resolved_pack.get("identity", {})
    sheets = resolved_pack.get("sheets", {})
    views = resolved_pack.get("views", {})
    crop_strategy = resolved_pack.get("cropStrategy", {})
    level_mapping = resolved_pack.get("levelMapping", {})
    capabilities = resolved_pack.get("capabilities", {})
    title_blocks = resolved_pack.get("titleBlocks", {})

    # Extract scales from view templates
    view_templates = views.get("templates", {})
    scales = {}
    for template_name, template_def in view_templates.items():
        if "scale" in template_def:
            # Map template names to scale keys
            scale_key = _map_template_to_scale_key(template_name)
            if scale_key:
                scales[scale_key] = template_def["scale"]

    # Ensure default scales
    scales.setdefault("floorPlan", 48)
    scales.setdefault("ceilingPlan", 48)
    scales.setdefault("elevation", 48)
    scales.setdefault("section", 48)
    scales.setdefault("detail", 12)
    scales.setdefault("siteplan", 240)

    # Build sheet set in v1 format
    permit_skeleton = sheets.get("sets", {}).get("permitSkeleton", [])
    full_cd = sheets.get("sets", {}).get("fullCD", [])

    # Convert sheet definitions
    sheet_set = {
        "permitSkeleton": [_adapt_sheet_def(s) for s in permit_skeleton],
        "fullCD": [_adapt_sheet_def(s) for s in full_cd] if full_cd else []
    }

    # Build title block config
    title_block = {
        "preferredPatterns": title_blocks.get("preferredPatterns", []),
        "excludePatterns": title_blocks.get("excludePatterns", ["Autodesk", "11 x 17", "8.5 x 11"]),
        "fallbackSize": title_blocks.get("fallbackSize", "24x36")
    }

    # Build naming config
    naming = {
        "viewPrefix": identity.get("viewPrefix", "ZZ_"),
        "schedulePattern": "{Category} Schedule",
        "sheetNumberSuffix": sheets.get("numberingSuffix", "-{run_id:4}")
    }

    # Build v1 standards pack
    spine_standards = {
        "$schema": "standards-pack-v1",
        "name": identity.get("name", "Unknown"),
        "description": identity.get("description", ""),
        "version": identity.get("version", "1.0.0"),
        "firm": identity.get("firm", ""),
        "projectType": identity.get("projectType", "Unknown"),

        "titleBlock": title_block,

        "sheetSize": {
            "width": 36,  # Default ARCH D
            "height": 24,
            "units": "inches"
        },

        "scales": scales,

        "cropStrategy": {
            "method": crop_strategy.get("method", "model_extents"),
            "marginFeet": crop_strategy.get("marginFeet", 5.0),
            "enabled": crop_strategy.get("enabled", True)
        },

        "sheetSet": sheet_set,

        "naming": naming,

        "levelMapping": {
            "patterns": level_mapping.get("patterns", {
                "level1": ["Level 1", "L1", "First Floor", "Ground"],
                "level2": ["Level 2", "L2", "Second Floor"],
                "roof": ["Roof", "T.O. Roof", "Roof Level"]
            })
        },

        "capabilities": {
            "fallbacks": capabilities.get("fallbacks", {
                "scheduleViewport": "export_csv",
                "legendViewport": "skip_with_warning",
                "missingElevation": "create_or_skip"
            })
        },

        # Preserve v2-specific data for future use
        "_v2_source": {
            "resolvedFrom": identity.get("resolvedFrom", {}),
            "resolvedAt": identity.get("resolvedAt", ""),
            "schedules": resolved_pack.get("schedules", {}),
            "filters": resolved_pack.get("filters", {}),
            "sectorSpecific": resolved_pack.get("sectorSpecific", {})
        }
    }

    return spine_standards


def _map_template_to_scale_key(template_name: str) -> str:
    """Map view template names to scale dictionary keys."""
    mapping = {
        "floorPlan": "floorPlan",
        "floor_plan": "floorPlan",
        "reflectedCeiling": "ceilingPlan",
        "ceilingPlan": "ceilingPlan",
        "ceiling_plan": "ceilingPlan",
        "elevation": "elevation",
        "interiorElevation": "elevation",
        "section": "section",
        "wallSection": "section",
        "buildingSection": "section",
        "detail": "detail",
        "siteplan": "siteplan",
        "sitePlan": "siteplan",
        "enlargedPlan": "detail",  # Enlarged plans use detail scale
    }
    return mapping.get(template_name, "")


def _adapt_sheet_def(sheet: Dict) -> Dict:
    """Convert a v2 sheet definition to v1 format."""
    result = {
        "number": sheet.get("number", ""),
        "name": sheet.get("name", "")
    }

    # Map viewType
    view_type = sheet.get("viewType")
    if view_type:
        result["viewType"] = view_type

    # Map level/levelRole
    level = sheet.get("level") or sheet.get("levelRole")
    if level is not None:
        result["level"] = level

    # Map category
    category = sheet.get("category")
    if category:
        result["category"] = category

    # Map optional
    if sheet.get("optional"):
        result["optional"] = True

    # Map unit (for duplex/townhouse)
    unit = sheet.get("unit")
    if unit:
        result["unit"] = unit

    # Map content type
    content = sheet.get("content")
    if content:
        result["content"] = content

    return result


def is_v2_pack(pack: Dict) -> bool:
    """Check if a pack is v2 format (resolved template pack)."""
    # V2 packs have identity.resolvedFrom or $schema containing v2
    if pack.get("identity", {}).get("resolvedFrom"):
        return True
    if "v2" in pack.get("$schema", "").lower():
        return True
    if pack.get("sheets", {}).get("sets"):  # V2 structure
        return True
    return False


def load_and_adapt(pack_path: str) -> Dict:
    """Load a pack file and adapt it if needed."""
    import json
    from pathlib import Path

    with open(pack_path) as f:
        pack = json.load(f)

    if is_v2_pack(pack):
        return adapt_pack_for_spine(pack)
    else:
        # Already v1 format
        return pack


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python pack_adapter.py <resolved_pack.json>")
        sys.exit(1)

    pack_path = Path(sys.argv[1])
    if not pack_path.exists():
        print(f"ERROR: Pack not found: {pack_path}")
        sys.exit(1)

    with open(pack_path) as f:
        resolved = json.load(f)

    if is_v2_pack(resolved):
        adapted = adapt_pack_for_spine(resolved)
        print(json.dumps(adapted, indent=2))
    else:
        print(f"Pack is already v1 format, no adaptation needed")
        print(json.dumps(resolved, indent=2))
