#!/usr/bin/env python3
"""
Deterministic Wall Creation from JSON Specification

This script reads wall definitions from a JSON spec file and creates
them in Revit using EXACT coordinates. No AI inference - purely deterministic.

Pipeline: PDF -> JSON spec (human-verified) -> This script -> Revit API
"""

import json
import sys
import math
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call_mcp(method, params=None):
    """Call MCP method via named pipe"""
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None, win32file.OPEN_EXISTING, 0, None
        )
        request = {"method": method, "params": params or {}}
        message = json.dumps(request) + '\n'
        win32file.WriteFile(handle, message.encode('utf-8'))

        response_data = b''
        while True:
            result, chunk = win32file.ReadFile(handle, 64 * 1024)
            response_data += chunk
            if b'\n' in chunk or len(chunk) == 0:
                break

        win32file.CloseHandle(handle)
        return json.loads(response_data.decode('utf-8').strip())
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_length(start, end):
    """Calculate wall length from coordinates"""
    dx = end["x"] - start["x"]
    dy = end["y"] - start["y"]
    return math.sqrt(dx*dx + dy*dy)


def verify_wall(wall_def):
    """Verify wall definition before creation"""
    start = wall_def["start"]
    end = wall_def["end"]
    expected_length = wall_def["length_feet"]
    calculated = calculate_length(start, end)

    tolerance = 0.01  # 0.01 feet = ~1/8 inch
    if abs(calculated - expected_length) > tolerance:
        return False, f"Length mismatch: expected {expected_length:.3f}, calculated {calculated:.3f}"
    return True, "OK"


def create_wall(wall_def, dry_run=False):
    """Create a single wall from specification"""
    wall_id = wall_def["id"]
    description = wall_def["description"]
    start = wall_def["start"]
    end = wall_def["end"]
    wall_type_id = wall_def["wall_type_id"]
    level_id = wall_def["level_id"]
    height = wall_def["height"]

    # Verify before creation
    valid, msg = verify_wall(wall_def)
    if not valid:
        return {"success": False, "error": f"Verification failed: {msg}", "wall_id": wall_id}

    # Print what we're creating
    print(f"\n{'='*60}")
    print(f"WALL: {wall_id}")
    print(f"Description: {description}")
    print(f"Start: ({start['x']:.3f}, {start['y']:.3f}, {start['z']:.3f})")
    print(f"End: ({end['x']:.3f}, {end['y']:.3f}, {end['z']:.3f})")
    print(f"Expected Length: {wall_def['length_feet']:.3f} ft ({wall_def['length_string']})")
    print(f"Calculated Length: {calculate_length(start, end):.3f} ft")
    print(f"Verification: PASS")
    print(f"Wall Type ID: {wall_type_id}")
    print(f"Level ID: {level_id}")

    if dry_run:
        print(f"[DRY RUN - Not creating wall]")
        return {"success": True, "dry_run": True, "wall_id": wall_id}

    # Create wall via MCP
    result = call_mcp("createWallByPoints", {
        "startPoint": [start["x"], start["y"], start["z"]],
        "endPoint": [end["x"], end["y"], end["z"]],
        "wallTypeId": wall_type_id,
        "levelId": level_id,
        "height": height
    })

    if result.get("success"):
        print(f"CREATED: Element ID {result.get('wallId')}")
    else:
        print(f"FAILED: {result.get('error')}")

    return result


def delete_all_walls():
    """Delete all existing walls"""
    print("\n" + "="*60)
    print("DELETING ALL EXISTING WALLS")
    print("="*60)

    # Get all walls
    result = call_mcp("getWalls")
    if not result.get("success"):
        print(f"Error getting walls: {result.get('error')}")
        return False

    walls = result.get("walls", [])
    if not walls:
        print("No walls to delete")
        return True

    wall_ids = [w["wallId"] for w in walls]
    print(f"Found {len(wall_ids)} walls to delete: {wall_ids}")

    # Delete them
    result = call_mcp("deleteElements", {"elementIds": wall_ids})
    if result.get("success"):
        print(f"Deleted {result.get('deletedCount')} walls")
        return True
    else:
        print(f"Delete failed: {result.get('error')}")
        return False


def main():
    # Load specification
    spec_file = "rbcdc_1713_spec.json"
    if len(sys.argv) > 1:
        spec_file = sys.argv[1]

    print(f"Loading specification from: {spec_file}")

    with open(spec_file, 'r') as f:
        spec = json.load(f)

    print(f"\nProject: {spec['project']['name']}")
    print(f"Sheet: {spec['project']['sheet']}")
    print(f"Coordinate Origin: {spec['coordinate_system']['origin']}")

    # Check for --dry-run flag
    dry_run = "--dry-run" in sys.argv
    delete_first = "--delete" in sys.argv or not dry_run

    if dry_run:
        print("\n*** DRY RUN MODE - No walls will be created ***")

    # Delete existing walls if requested
    if delete_first and not dry_run:
        if not delete_all_walls():
            print("Failed to delete walls - aborting")
            return

    # Create exterior walls first
    print("\n" + "="*60)
    print("CREATING EXTERIOR WALLS")
    print("="*60)

    exterior_walls = spec.get("first_floor_exterior_walls", [])
    for wall_def in exterior_walls:
        result = create_wall(wall_def, dry_run)
        if not result.get("success") and not result.get("dry_run"):
            print(f"\nERROR creating {wall_def['id']} - stopping")
            break

    # Create interior walls
    print("\n" + "="*60)
    print("CREATING INTERIOR WALLS")
    print("="*60)

    interior_walls = spec.get("first_floor_interior_walls", [])
    for wall_def in interior_walls:
        result = create_wall(wall_def, dry_run)
        if not result.get("success") and not result.get("dry_run"):
            print(f"\nERROR creating {wall_def['id']} - stopping")
            break

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Exterior walls: {len(exterior_walls)}")
    print(f"Interior walls: {len(interior_walls)}")
    print(f"Total: {len(exterior_walls) + len(interior_walls)}")

    # Verification checks
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    checks = spec.get("verification_checks", {})
    for check, expected in checks.items():
        print(f"  {check}: {expected}")


if __name__ == "__main__":
    main()
