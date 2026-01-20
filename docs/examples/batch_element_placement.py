"""
Example: Batch element placement using RevitMCPBridge2026

This example demonstrates:
1. Batch wall creation
2. Batch door placement
3. Error handling and verification
4. Using the validation methods

Prerequisites:
- Revit 2026 running with RevitMCPBridge loaded
- A project with at least one level
"""

import json
import win32pipe
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'


def connect():
    return win32file.CreateFile(
        PIPE_NAME,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None,
        win32file.OPEN_EXISTING,
        0, None
    )


def call_mcp(pipe, method, params=None):
    params = params or {}
    request = json.dumps({"method": method, "params": params})
    win32file.WriteFile(pipe, request.encode())
    response = win32file.ReadFile(pipe, 65536)[1]
    return json.loads(response.decode())


def main():
    print("Batch Element Placement Example")
    print("=" * 60)

    pipe = connect()
    print("Connected to MCP server\n")

    # Get the first level
    result = call_mcp(pipe, "getLevels")
    if not result.get("success") or not result.get("levels"):
        print("Error: No levels found")
        return

    level = result["levels"][0]
    level_id = level.get("levelId")
    print(f"Using level: {level.get('name')} (ID: {level_id})")

    # Get wall types
    result = call_mcp(pipe, "getWallTypes")
    wall_types = result.get("wallTypes", [])
    if not wall_types:
        print("Error: No wall types found")
        return

    wall_type_id = wall_types[0].get("typeId")
    print(f"Using wall type: {wall_types[0].get('name')}")

    # Define a simple rectangular room (20' x 15')
    walls_to_create = [
        {"startX": 0, "startY": 0, "endX": 20, "endY": 0},    # Bottom
        {"startX": 20, "startY": 0, "endX": 20, "endY": 15},   # Right
        {"startX": 20, "startY": 15, "endX": 0, "endY": 15},   # Top
        {"startX": 0, "startY": 15, "endX": 0, "endY": 0},     # Left
    ]

    # Add common parameters
    for wall in walls_to_create:
        wall["levelId"] = level_id
        wall["wallTypeId"] = wall_type_id
        wall["height"] = 10.0

    print(f"\nCreating {len(walls_to_create)} walls...")

    # Method 1: Individual wall creation
    created_walls = []
    for i, wall_params in enumerate(walls_to_create):
        result = call_mcp(pipe, "createWall", wall_params)

        if result.get("success"):
            wall_id = result.get("wallId")
            created_walls.append(wall_id)
            print(f"  Wall {i+1}: Created (ID: {wall_id})")
        else:
            print(f"  Wall {i+1}: FAILED - {result.get('error')}")

    print(f"\nCreated {len(created_walls)} walls")

    # Verify the walls exist
    print("\nVerifying walls...")
    for wall_id in created_walls:
        result = call_mcp(pipe, "verifyElement", {"elementId": wall_id})
        if result.get("exists"):
            print(f"  Wall {wall_id}: Verified")
        else:
            print(f"  Wall {wall_id}: NOT FOUND!")

    # Place doors in the walls
    print("\n" + "-" * 60)
    print("Placing doors...")

    # Get door types
    result = call_mcp(pipe, "getDoorTypes")
    door_types = result.get("doorTypes", [])
    if not door_types:
        print("No door types available")
        return

    door_type_id = door_types[0].get("typeId")
    print(f"Using door type: {door_types[0].get('name')}")

    # Place a door in the bottom wall (first wall)
    if created_walls:
        result = call_mcp(pipe, "placeDoor", {
            "wallId": created_walls[0],  # Bottom wall
            "doorTypeId": door_type_id,
            "x": 10,  # Center of 20' wall
            "y": 0,
            "levelId": level_id
        })

        if result.get("success"):
            door_id = result.get("doorId")
            print(f"Door placed successfully (ID: {door_id})")

            # Tag the door
            result = call_mcp(pipe, "tagDoor", {
                "doorId": door_id
            })
            if result.get("success"):
                print("Door tagged")
        else:
            print(f"Door placement failed: {result.get('error')}")

    # Method 2: Batch wall creation (more efficient)
    print("\n" + "=" * 60)
    print("Method 2: Batch Creation")
    print("=" * 60)

    # Define another room offset from the first
    offset_x = 30  # 30' to the right of first room

    batch_walls = [
        {"startX": offset_x, "startY": 0, "endX": offset_x + 20, "endY": 0,
         "levelId": level_id, "wallTypeId": wall_type_id, "height": 10.0},
        {"startX": offset_x + 20, "startY": 0, "endX": offset_x + 20, "endY": 15,
         "levelId": level_id, "wallTypeId": wall_type_id, "height": 10.0},
        {"startX": offset_x + 20, "startY": 15, "endX": offset_x, "endY": 15,
         "levelId": level_id, "wallTypeId": wall_type_id, "height": 10.0},
        {"startX": offset_x, "startY": 15, "endX": offset_x, "endY": 0,
         "levelId": level_id, "wallTypeId": wall_type_id, "height": 10.0},
    ]

    result = call_mcp(pipe, "createWallBatch", {"walls": batch_walls})

    if result.get("success"):
        batch_walls = result.get("createdWalls", [])
        failed = result.get("failedCount", 0)
        print(f"Batch created {len(batch_walls)} walls, {failed} failed")
    else:
        print(f"Batch creation failed: {result.get('error')}")

    # Create a room in each enclosed area
    print("\nCreating rooms...")

    room_locations = [
        {"x": 10, "y": 7.5},  # Center of first room
        {"x": offset_x + 10, "y": 7.5},  # Center of second room
    ]

    for i, loc in enumerate(room_locations):
        result = call_mcp(pipe, "createRoom", {
            "levelId": level_id,
            "x": loc["x"],
            "y": loc["y"]
        })

        if result.get("success"):
            room_id = result.get("roomId")
            print(f"  Room {i+1} created (ID: {room_id})")

            # Set room name
            call_mcp(pipe, "setParameter", {
                "elementId": room_id,
                "parameterName": "Name",
                "value": f"Room {i+1}"
            })
        else:
            print(f"  Room {i+1} failed: {result.get('error')}")

    print("\nDone!")


if __name__ == "__main__":
    main()
