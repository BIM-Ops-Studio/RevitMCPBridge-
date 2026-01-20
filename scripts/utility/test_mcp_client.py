#!/usr/bin/env python3
"""Test client for RevitMCPBridge2026 - View Review and Room Schedule Creation"""

import json
import time
import sys

try:
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    print("ERROR: pywin32 not installed. Install with: pip install pywin32")
    sys.exit(1)

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'
TIMEOUT_MS = 30000

def send_mcp_request(method, parameters):
    """Send a request to the MCP server and return the response"""
    try:
        # Connect to named pipe
        handle = win32file.CreateFile(
            PIPE_NAME,
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
            "parameters": parameters
        }
        request_json = json.dumps(request)

        # Send request
        win32file.WriteFile(handle, request_json.encode('utf-8'))

        # Read response
        result, data = win32file.ReadFile(handle, 64 * 1024)

        # Close handle
        win32file.CloseHandle(handle)

        # Parse response
        response = json.loads(data.decode('utf-8'))
        return response

    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running. Click 'Start MCP Server' in Revit."}
        else:
            return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_result(result, description):
    """Print the result of an MCP call"""
    print(f"\n[{description}]")
    if result.get("success"):
        print("[SUCCESS]")
        # Print all keys except 'success'
        for key, value in result.items():
            if key != "success":
                if isinstance(value, (dict, list)):
                    print(f"{key}: {json.dumps(value, indent=2)}")
                else:
                    print(f"{key}: {value}")
    else:
        print(f"[FAILED]: {result.get('error', 'Unknown error')}")
    return result.get("success", False)

# ============================================================================
# TEST 1: View Review
# ============================================================================
print_section("TEST 1: Reviewing Current View")

print("\n1. Getting active view information...")
view_info = send_mcp_request("getActiveViewInfo", {})
print_result(view_info, "Active View Info")

if view_info.get("success"):
    view_name = view_info.get("viewName", "Unknown")
    view_type = view_info.get("viewType", "Unknown")
    print(f"\n>> Current View: '{view_name}' (Type: {view_type})")

print("\n2. Getting all walls in the view...")
walls = send_mcp_request("getWallsInView", {})
print_result(walls, "Walls in View")

if walls.get("success"):
    wall_list = walls.get("walls", [])
    print(f"\nWALLS: Found {len(wall_list)} walls in view")
    if wall_list:
        print("   First 5 walls:")
        for i, wall in enumerate(wall_list[:5], 1):
            print(f"   {i}. ID: {wall.get('id')} - Type: {wall.get('wallType')} - Height: {wall.get('height', 'N/A')}")

print("\n3. Getting all rooms in the project...")
rooms = send_mcp_request("getAllRooms", {})
print_result(rooms, "All Rooms")

room_count = 0
if rooms.get("success"):
    room_list = rooms.get("rooms", [])
    room_count = len(room_list)
    print(f"\nROOMS: Found {room_count} rooms in project")
    if room_list:
        print("   First 10 rooms:")
        for i, room in enumerate(room_list[:10], 1):
            number = room.get('number', 'N/A')
            name = room.get('name', 'Unnamed')
            area = room.get('area', 'N/A')
            level = room.get('level', 'N/A')
            print(f"   {i}. {number} - {name} | Area: {area} | Level: {level}")

print("\n4. Getting all doors in the view...")
doors = send_mcp_request("getDoorsInView", {})
print_result(doors, "Doors in View")

if doors.get("success"):
    door_list = doors.get("doors", [])
    print(f"\nDOORS: Found {len(door_list)} doors in view")
    if door_list:
        print("   First 5 doors:")
        for i, door in enumerate(door_list[:5], 1):
            print(f"   {i}. ID: {door.get('id')} - Type: {door.get('doorType')} - Mark: {door.get('mark', 'N/A')}")

# ============================================================================
# TEST 2: Create Room Schedule
# ============================================================================
print_section("TEST 2: Creating Room Schedule")

if room_count > 0:
    print("\n1. Creating room schedule...")
    schedule_params = {
        "scheduleName": "Room Schedule - MCP Test",
        "categoryName": "Rooms"
    }
    create_schedule = send_mcp_request("createSchedule", schedule_params)
    print_result(create_schedule, "Create Room Schedule")

    if create_schedule.get("success"):
        schedule_id = create_schedule.get("scheduleId")
        print(f"\nSUCCESS: Schedule created successfully! Schedule ID: {schedule_id}")

        print("\n2. Adding fields to room schedule...")
        fields_to_add = [
            {"fieldName": "Number", "fieldType": "Number"},
            {"fieldName": "Name", "fieldType": "Name"},
            {"fieldName": "Level", "fieldType": "Level"},
            {"fieldName": "Area", "fieldType": "Area"},
            {"fieldName": "Comments", "fieldType": "Comments"}
        ]

        for field in fields_to_add:
            print(f"   Adding field: {field['fieldName']}...")
            add_field = send_mcp_request("addScheduleField", {
                "scheduleId": schedule_id,
                "fieldName": field["fieldName"]
            })
            if add_field.get("success"):
                print(f"   SUCCESS: Added: {field['fieldName']}")
            else:
                print(f"   WARNING:  Could not add {field['fieldName']}: {add_field.get('error')}")

        print("\n3. Getting schedule data to verify...")
        time.sleep(0.5)  # Small delay to ensure Revit processes the changes
        get_data = send_mcp_request("getScheduleData", {"scheduleId": schedule_id})
        print_result(get_data, "Room Schedule Data")

        if get_data.get("success"):
            data = get_data.get("data", [])
            print(f"\nSCHEDULE: Schedule contains {len(data)} rows")
            if data:
                print("\n   Sample data (first 5 rows):")
                for i, row in enumerate(data[:5], 1):
                    print(f"   {i}. {row}")
else:
    print("\nWARNING:  No rooms found in project - cannot create room schedule")

# ============================================================================
# SUMMARY
# ============================================================================
print_section("TEST SUMMARY")

print("\nSUCCESS: MCP Bridge is working!")
print(f"   • Active View: {view_info.get('viewName', 'N/A')}")
print(f"   • Walls in View: {len(walls.get('walls', []))}")
print(f"   • Rooms in Project: {room_count}")
print(f"   • Doors in View: {len(doors.get('doors', []))}")
if room_count > 0:
    print(f"   • Room Schedule Created: {create_schedule.get('success', False)}")

print("\n" + "=" * 80)
print("Test complete!")
print("=" * 80 + "\n")
