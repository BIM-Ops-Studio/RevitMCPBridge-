"""
Simplified 1st Floor Shell Builder
Uses batchCreateWalls for simpler wall creation
"""

import win32file
import json

def send_mcp_command(method, parameters):
    """Send command to Revit MCP Bridge"""
    try:
        h = win32file.CreateFile(
            r'\\.\pipe\RevitMCPBridge2026',
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        request = (json.dumps({"method": method, "parameters": parameters}) + "\n").encode()
        win32file.WriteFile(h, request)

        _, data = win32file.ReadFile(h, 64*1024)
        win32file.CloseHandle(h)

        result = json.loads(data.decode())
        return result
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}

def main():
    print("="*70)
    print("SIMPLIFIED 1ST FLOOR SHELL - PDF TO REVIT TEST")
    print("="*70)

    # Get levels
    print("\n[1/2] Getting levels...")
    levels_result = send_mcp_command("getLevels", {})

    if not levels_result.get("success"):
        print(f"ERROR: {levels_result.get('error')}")
        return

    levels = levels_result.get("levels", [])
    level = levels[0] if levels else None

    if not level:
        print("ERROR: No levels found")
        return

    level_id = level.get('levelId')
    print(f"[OK] Using level: {level.get('name')} (ID: {level_id})")

    # Create walls using batch method
    # Building: 45'-4" x 28'-8" (45.333' x 28.667')
    print("\n[2/2] Creating rectangular building shell...")
    print("Dimensions: 45'-4\" x 28'-8\"")

    walls_data = {
        "walls": [
            # South wall (front)
            {
                "startPoint": [0, 0, 0],
                "endPoint": [45.333, 0, 0],
                "levelId": level_id,
                "height": 10.0
            },
            # East wall
            {
                "startPoint": [45.333, 0, 0],
                "endPoint": [45.333, 28.667, 0],
                "levelId": level_id,
                "height": 10.0
            },
            # North wall (back)
            {
                "startPoint": [45.333, 28.667, 0],
                "endPoint": [0, 28.667, 0],
                "levelId": level_id,
                "height": 10.0
            },
            # West wall
            {
                "startPoint": [0, 28.667, 0],
                "endPoint": [0, 0, 0],
                "levelId": level_id,
                "height": 10.0
            }
        ]
    }

    result = send_mcp_command("batchCreateWalls", walls_data)

    if result.get("success"):
        created = result.get("successCount", 0)
        failed = result.get("failedCount", 0)
        print(f"\n[OK] Walls created: {created}")
        if failed > 0:
            print(f"[WARNING] Walls failed: {failed}")
            errors = result.get("errors", [])
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
    else:
        print(f"\n[FAILED] {result.get('error')}")

    print("\n" + "="*70)
    print("Next: Check Revit 3D view to verify the rectangular shell")
    print("="*70)

if __name__ == "__main__":
    main()
