#!/usr/bin/env python3
"""
Sheet Contract - Single source of truth for sheet identity

All modules (state_assessment, filtered_queries, pack_assessor, gap_planner)
MUST use these functions. No parallel implementations.

Canonical key = normalized sheet number (NOT sheet name)
"""

import re
from typing import Dict, List, Any


def normalize_sheet_number(raw: str) -> str:
    """
    Canonical sheet key: trim, collapse spaces, uppercase.

    Examples:
        "G0.01" -> "G0.01"
        "  a1.0.1  " -> "A1.0.1"
        "A1.01 " -> "A1.01"
    """
    return " ".join((raw or "").strip().upper().split())


def extract_sheet_number(raw: str) -> str:
    """
    Extract sheet number, stripping suffixes like "A1.01-FLOOR PLAN".

    Handles:
        "A1.01-FLOOR PLAN" -> "A1.01"
        "A1-01" -> "A1-01" (dash is part of number)
        "CVR" -> "CVR"
        "ALS.1.1" -> "ALS.1.1"
    """
    s = (raw or "").strip()
    if not s:
        return ""

    # If there's a dash followed by letters (not digits), treat as suffix separator
    # e.g., "A1.01-FLOOR PLAN" -> "A1.01"
    # but keep "A1-01" intact (dash followed by digits)
    m = re.match(r"^(.+?)-\s*[A-Za-z].*$", s)
    if m:
        s = m.group(1)

    return s


def build_existing_index(existing_sheets: List[Dict]) -> Dict[str, Dict]:
    """
    Build canonical index from MCP getAllSheets response.

    Args:
        existing_sheets: List of sheet dicts from MCP
            Each has: id, sheetNumber, sheetName, viewCount, placedViews

    Returns:
        Dict keyed by normalized sheet number:
        {
            "G0.01": {"id": 123, "number": "G0.01", "raw_number": "G0.01", "name": "COVER SHEET"},
            ...
        }
    """
    idx = {}
    for s in existing_sheets:
        raw_num = s.get("sheetNumber", "")
        extracted = extract_sheet_number(raw_num)
        key = normalize_sheet_number(extracted)
        if not key:
            continue
        idx[key] = {
            "id": s.get("id"),
            "number": key,
            "raw_number": raw_num,
            "name": (s.get("sheetName") or "").strip(),
            "view_count": s.get("viewCount", 0),
        }
    return idx


def build_expected_index(expected_sheets: List[Dict]) -> Dict[str, Dict]:
    """
    Build canonical index from pack's permitSkeleton.

    Args:
        expected_sheets: List from pack, each has: number, name, optional (bool)

    Returns:
        Dict keyed by normalized sheet number:
        {
            "G0.01": {"number": "G0.01", "name": "COVER SHEET", "optional": False},
            ...
        }
    """
    idx = {}
    for e in expected_sheets:
        raw_num = e.get("number", "")
        key = normalize_sheet_number(raw_num)
        if not key:
            continue
        idx[key] = {
            "number": key,
            "name": (e.get("name") or "").strip(),
            "optional": e.get("optional", False)
        }
    return idx


def compare_sheets(existing_sheets: List[Dict], expected_sheets: List[Dict]) -> Dict[str, Any]:
    """
    Single comparison function used by ALL modules.

    Returns sheet_coverage dict - the canonical data contract.

    Args:
        existing_sheets: Raw list from MCP getAllSheets
        expected_sheets: List from pack's permitSkeleton

    Returns:
        {
            "existing_by_number": {key: {...}, ...},
            "expected_by_number": {key: {...}, ...},
            "missing_numbers": ["A5.0.2", ...],  # Expected but not found
            "extra_numbers": ["Z9.99", ...],      # Found but not expected
            "coverage_percent": 90.0,
            "naming_issues": []
        }
    """
    existing_by = build_existing_index(existing_sheets)
    expected_by = build_expected_index(expected_sheets)

    # Find missing (expected but not in existing)
    missing = [n for n in expected_by.keys() if n not in existing_by]

    # Find extra (in existing but not expected)
    extra = [n for n in existing_by.keys() if n not in expected_by]

    # Calculate coverage (only count required sheets, not optional)
    required_expected = {k: v for k, v in expected_by.items() if not v.get("optional")}
    required_count = len(required_expected)

    if required_count > 0:
        matched = sum(1 for k in required_expected.keys() if k in existing_by)
        coverage = round(matched / required_count * 100.0, 1)
    else:
        coverage = 100.0

    # Check for naming issues
    naming_issues = []
    for key, data in existing_by.items():
        name = data.get("name", "")
        if not name or name.lower() in ["unnamed", "sheet"]:
            naming_issues.append({
                "number": key,
                "issue": "Missing or invalid name"
            })

    return {
        "existing_by_number": existing_by,
        "expected_by_number": expected_by,
        "missing_numbers": missing,
        "extra_numbers": extra,
        "coverage_percent": coverage,
        "naming_issues": naming_issues
    }


# Convenience functions for consumers

def get_missing_sheet_numbers(sheet_coverage: Dict) -> List[str]:
    """Get list of sheet numbers that need to be created."""
    return sheet_coverage.get("missing_numbers", [])


def sheet_exists(sheet_coverage: Dict, sheet_number: str) -> bool:
    """Check if a sheet number already exists in the model."""
    key = normalize_sheet_number(sheet_number)
    return key in sheet_coverage.get("existing_by_number", {})


def get_existing_sheet(sheet_coverage: Dict, sheet_number: str) -> Dict:
    """Get existing sheet data by number, or empty dict if not found."""
    key = normalize_sheet_number(sheet_number)
    return sheet_coverage.get("existing_by_number", {}).get(key, {})
