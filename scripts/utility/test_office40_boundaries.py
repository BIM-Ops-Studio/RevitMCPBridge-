"""
Test script to modify Office 40 room boundaries
Connects to RevitMCPBridge2026 named pipe and modifies wall location lines
"""

import json
import struct

def send_command(pipe_name, method, params):
    """Send a command to the named pipe and get response"""
    import win32pipe
    import win32file
    import pywintypes

    pipe_path = f"\\\\.\\pipe\\{pipe_name}"

    try:
        # Connect to the pipe
        handle = win32file.CreateFile(
            pipe_path,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        # Prepare request
        request = {
            "method": method,
            "params": params
        }

        request_json = json.dumps(request) + "\n"
        request_bytes = request_json.encode('utf-8')

        # Send request
        win32file.WriteFile(handle, request_bytes)

        # Read response
        result = win32file.ReadFile(handle, 64*1024)
        response_data = result[1].decode('utf-8').strip()

        # Close handle
        win32file.CloseHandle(handle)

        return json.loads(response_data)

    except pywintypes.error as e:
        print(f"Pipe error: {e}")
        return {"success": False, "error": str(e)}

def main():
    pipe_name = "RevitMCPBridge2026"

    print("=" * 60)
    print("Office 40 Room Boundary Test")
    print("=" * 60)

    # Step 1: Get all rooms to find Office 40
    print("\n[1/4] Finding Office 40...")
    rooms_response = send_command(pipe_name, "getRooms", {})

    if not rooms_response.get("success"):
        print(f"❌ Failed to get rooms: {rooms_response.get('error')}")
        return

    rooms = rooms_response.get("result", {}).get("rooms", [])
    office_40 = None

    for room in rooms:
        if room.get("number") == "40" or room.get("name") == "Office 40":
            office_40 = room
            break

    if not office_40:
        print("❌ Office 40 not found!")
        print(f"Available rooms: {[f\"{r.get('number')} - {r.get('name')}\" for r in rooms[:10]]}")
        return

    print(f"✅ Found Office 40:")
    print(f"   - Room ID: {office_40.get('id')}")
    print(f"   - Name: {office_40.get('name')}")
    print(f"   - Number: {office_40.get('number')}")
    print(f"   - Area: {office_40.get('area')} sq ft")

    # Step 2: Get room info with boundaries
    print(f"\n[2/4] Getting Office 40 boundary information...")
    room_info = send_command(pipe_name, "getRoomInfo", {"roomId": str(office_40.get('id'))})

    if not room_info.get("success"):
        print(f"❌ Failed: {room_info.get('error')}")
        return

    print(f"✅ Room has {len(room_info.get('result', {}).get('boundaries', []))} boundary loops")

    # Step 3: Get walls in current view
    print(f"\n[3/4] Getting walls in current view...")
    walls_response = send_command(pipe_name, "getWallsInView", {})

    if not walls_response.get("success"):
        print(f"❌ Failed: {walls_response.get('error')}")
        return

    walls = walls_response.get("result", {}).get("walls", [])
    print(f"✅ Found {len(walls)} walls in view")

    # Step 4: Modify wall properties
    print(f"\n[4/4] Modifying wall location lines...")
    print("\nFor this test, we'll modify the first 3 walls as examples:")
    print("  - Wall 1: Finish Face Exterior (for hallway/curtain wall)")
    print("  - Wall 2: Finish Face Interior (for demising wall)")
    print("  - Wall 3: Core Centerline (for interior partition)")

    if len(walls) < 3:
        print(f"⚠️  Only {len(walls)} walls available")

    test_configs = [
        {"locationLine": "FinishFaceExterior", "roomBounding": True},
        {"locationLine": "FinishFaceInterior", "roomBounding": True},
        {"locationLine": "CoreCenterline", "roomBounding": True}
    ]

    for i, config in enumerate(test_configs[:len(walls)]):
        wall = walls[i]
        wall_id = wall.get("id")

        print(f"\n  Wall {i+1} (ID: {wall_id}):")
        print(f"    Setting locationLine = {config['locationLine']}")

        result = send_command(pipe_name, "modifyWallProperties", {
            "wallId": str(wall_id),
            **config
        })

        if result.get("success"):
            modified = result.get("result", {}).get("modified", [])
            print(f"    ✅ Success! Modified: {', '.join(modified)}")
        else:
            print(f"    ❌ Failed: {result.get('error')}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check Office 40 in Revit - room boundaries should be updated")
    print("2. Use Room tool to verify area calculation")
    print("3. Adjust more walls as needed using the same approach")

if __name__ == "__main__":
    try:
        import win32file
        import win32pipe
        import pywintypes
    except ImportError:
        print("❌ Missing pywin32. Install with: pip install pywin32")
        exit(1)

    main()
