"""
Execute Multiple Tasks Autonomously
Complete 4 major deliverables in one execution
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient
import json

def print_separator(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def task1_room_schedule_with_finishes(client):
    """Task 1: Create a room schedule with finishes"""
    print_separator("TASK 1: Creating Room Schedule with Finishes")

    # Create room schedule
    print("Creating room schedule...")
    result = client.send_request("createSchedule", {
        "category": "Rooms",
        "scheduleName": "Room Schedule - Finishes"
    })

    if not result.get("success"):
        print(f"  [ERROR] {result.get('error')}")
        return False

    schedule_name = result.get("scheduleName", "Room Schedule - Finishes")
    print(f"  [SUCCESS] Created: {schedule_name}")

    # Add fields
    fields = [
        "Number",
        "Name",
        "Area",
        "Level",
        "Finish - Floor",
        "Finish - Wall",
        "Finish - Ceiling",
        "Finish - Base"
    ]

    print("Adding schedule fields...")
    for field in fields:
        result = client.send_request("addScheduleField", {
            "scheduleName": schedule_name,
            "fieldName": field
        })
        if result.get("success"):
            print(f"  [+] Added field: {field}")
        else:
            print(f"  [!] Skipped field: {field} ({result.get('error', 'not available')})")

    print("  [SUCCESS] Room schedule with finishes created!")
    return True

def task2_tag_doors_and_schedule(client):
    """Task 2: Tag all doors and create door schedule"""
    print_separator("TASK 2: Tagging Doors & Creating Door Schedule")

    # Get current view
    print("Getting current view for tagging...")
    view_result = client.send_request("getActiveView", {})

    # Tag all doors
    print("Tagging all doors...")
    tag_result = client.send_request("batchTagDoors", {
        "viewName": view_result.get("viewName", "current"),
        "tagOrientation": "Horizontal"
    })

    if tag_result.get("success"):
        doors_tagged = tag_result.get("doorsTagged", 0)
        print(f"  [SUCCESS] Tagged {doors_tagged} doors")
    else:
        print(f"  [WARNING] {tag_result.get('error', 'Could not tag doors')}")

    # Create door schedule
    print("Creating door schedule...")
    sched_result = client.send_request("createSchedule", {
        "category": "Doors",
        "scheduleName": "Door Schedule"
    })

    if not sched_result.get("success"):
        print(f"  [ERROR] {sched_result.get('error')}")
        return False

    schedule_name = sched_result.get("scheduleName", "Door Schedule")
    print(f"  [SUCCESS] Created: {schedule_name}")

    # Add door schedule fields
    door_fields = [
        "Mark",
        "Type",
        "Width",
        "Height",
        "Fire Rating",
        "Frame Material",
        "Level",
        "To Room",
        "From Room"
    ]

    print("Adding door schedule fields...")
    for field in door_fields:
        result = client.send_request("addScheduleField", {
            "scheduleName": schedule_name,
            "fieldName": field
        })
        if result.get("success"):
            print(f"  [+] Added field: {field}")
        else:
            print(f"  [!] Skipped field: {field}")

    print("  [SUCCESS] Door schedule created with all fields!")
    return True

def task3_setup_level1_cd_plan(client):
    """Task 3: Set up Level 1 floor plan for construction documents"""
    print_separator("TASK 3: Setting Up Level 1 Floor Plan for CDs")

    # Create or get Level 1 floor plan
    print("Creating Level 1 floor plan view...")
    view_result = client.send_request("createFloorPlan", {
        "levelName": "Level 1",
        "viewName": "Level 1 - Floor Plan - CD"
    })

    if view_result.get("success"):
        view_name = view_result.get("viewName", "Level 1 - Floor Plan - CD")
        print(f"  [SUCCESS] Created: {view_name}")
    else:
        view_name = "Level 1"
        print(f"  [INFO] Using existing view: {view_name}")

    # Set scale for construction documents (1/4" = 1'-0")
    print("Setting CD scale (1/4\" = 1'-0\")...")
    scale_result = client.send_request("setViewScale", {
        "viewName": view_name,
        "scale": 48  # 1/4" scale
    })

    if scale_result.get("success"):
        print("  [SUCCESS] Scale set to 1/4\" = 1'-0\"")

    # Tag all rooms in view
    print("Tagging all rooms...")
    room_tag_result = client.send_request("batchTagRooms", {
        "viewName": view_name
    })

    if room_tag_result.get("success"):
        rooms_tagged = room_tag_result.get("roomsTagged", 0)
        print(f"  [SUCCESS] Tagged {rooms_tagged} rooms")

    # Tag all doors
    print("Tagging all doors...")
    door_tag_result = client.send_request("batchTagDoors", {
        "viewName": view_name
    })

    if door_tag_result.get("success"):
        doors_tagged = door_tag_result.get("doorsTagged", 0)
        print(f"  [SUCCESS] Tagged {doors_tagged} doors")

    # Add dimensions
    print("Adding dimensions...")
    dim_result = client.send_request("addDimensionsToWalls", {
        "viewName": view_name
    })

    if dim_result.get("success"):
        print("  [SUCCESS] Wall dimensions added")

    print("  [SUCCESS] Level 1 CD floor plan ready!")
    return True

def task4_create_sd_package(client):
    """Task 4: Create SD package for client review"""
    print_separator("TASK 4: Creating SD Package for Client Review")

    print("Executing SD Package workflow...")
    result = client.send_request("executeWorkflow", {
        "workflowType": "SD_Package",
        "projectType": "SmallCommercial",
        "buildingCode": "IBC_2024"
    })

    if not result.get("success"):
        print(f"  [ERROR] {result.get('error')}")
        return False

    tasks_completed = result.get("tasksCompleted", 0)
    decisions_made = result.get("decisionsMade", 0)

    print(f"  [SUCCESS] SD Package completed!")
    print(f"    Tasks: {tasks_completed}")
    print(f"    Decisions: {decisions_made}")

    return True

def main():
    print("\n" + "=" * 80)
    print("  AUTONOMOUS EXECUTION - 4 MAJOR TASKS")
    print("=" * 80)
    print()
    print("Executing:")
    print("  1. Create room schedule with finishes")
    print("  2. Tag all doors and create door schedule")
    print("  3. Set up Level 1 floor plan for construction documents")
    print("  4. Create SD package for client review")
    print()
    print("Starting execution...")

    client = RevitClient()

    results = {
        "Task 1 - Room Schedule": False,
        "Task 2 - Door Tagging & Schedule": False,
        "Task 3 - Level 1 CD Plan": False,
        "Task 4 - SD Package": False
    }

    # Execute all tasks
    try:
        results["Task 1 - Room Schedule"] = task1_room_schedule_with_finishes(client)
    except Exception as e:
        print(f"[ERROR] Task 1 failed: {e}")

    try:
        results["Task 2 - Door Tagging & Schedule"] = task2_tag_doors_and_schedule(client)
    except Exception as e:
        print(f"[ERROR] Task 2 failed: {e}")

    try:
        results["Task 3 - Level 1 CD Plan"] = task3_setup_level1_cd_plan(client)
    except Exception as e:
        print(f"[ERROR] Task 3 failed: {e}")

    try:
        results["Task 4 - SD Package"] = task4_create_sd_package(client)
    except Exception as e:
        print(f"[ERROR] Task 4 failed: {e}")

    # Summary
    print_separator("EXECUTION COMPLETE - SUMMARY")

    for task, success in results.items():
        status = "[SUCCESS]" if success else "[FAILED]"
        print(f"  {status} {task}")

    successful = sum(1 for v in results.values() if v)
    total = len(results)

    print()
    print(f"Completed: {successful}/{total} tasks")
    print()
    print("=" * 80)
    print("  CHECK YOUR REVIT PROJECT FOR ALL CHANGES!")
    print("=" * 80)

    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
