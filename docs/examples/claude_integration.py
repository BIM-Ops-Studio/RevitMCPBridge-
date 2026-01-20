"""
Example: Claude AI Integration with RevitMCPBridge2026

This example shows how Claude Code can interact with Revit
through the MCP bridge, demonstrating:
1. Natural language to MCP method translation
2. Context-aware operations
3. Learning from corrections
4. Autonomous goal execution

Note: This is a conceptual example showing the integration pattern.
In practice, Claude Code calls these methods directly via MCP.
"""

import json
import win32pipe
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'


class RevitMCPClient:
    """Simple MCP client for Revit interaction"""

    def __init__(self):
        self.pipe = None
        self.context = {}

    def connect(self):
        self.pipe = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        return self

    def call(self, method, params=None):
        params = params or {}
        request = json.dumps({"method": method, "params": params})
        win32file.WriteFile(self.pipe, request.encode())
        response = win32file.ReadFile(self.pipe, 65536)[1]
        return json.loads(response.decode())

    def get_context(self):
        """Get current project context (Level 2+ feature)"""
        return self.call("getProjectContext")

    def smart_execute(self, action, **kwargs):
        """Execute with intelligence (Level 3+ feature)"""
        return self.call("smartExecute", {
            "action": action,
            "parameters": kwargs
        })

    def execute_goal(self, goal_type, **params):
        """Execute autonomous goal (Level 5 feature)"""
        return self.call("executeGoal", {
            "goalType": goal_type,
            "parameters": params
        })


def example_natural_language_workflow():
    """
    Example: How Claude translates natural language to MCP calls

    User says: "Create a 20x15 foot room with a door on the south wall"

    Claude's process:
    1. Parse intent: create room, specific size, door placement
    2. Get project context (levels, wall types)
    3. Calculate wall coordinates
    4. Create walls, place door, create room
    5. Verify result
    """
    print("Natural Language Workflow Example")
    print("=" * 60)
    print("User: 'Create a 20x15 foot room with a door on the south wall'")
    print()

    client = RevitMCPClient().connect()

    # Step 1: Get project context
    print("Step 1: Getting project context...")
    context = client.call("getProjectInfo")
    print(f"  Project: {context.get('projectName', 'Unknown')}")

    levels = client.call("getLevels")
    level_id = levels.get("levels", [{}])[0].get("levelId")
    print(f"  Using Level ID: {level_id}")

    # Step 2: Get available types
    print("\nStep 2: Finding appropriate types...")
    wall_types = client.call("getWallTypes")
    wall_type = wall_types.get("wallTypes", [{}])[0]
    print(f"  Wall type: {wall_type.get('name')}")

    door_types = client.call("getDoorTypes")
    door_type = door_types.get("doorTypes", [{}])[0]
    print(f"  Door type: {door_type.get('name')}")

    # Step 3: Calculate geometry
    print("\nStep 3: Calculating geometry...")
    room_width = 20  # feet
    room_depth = 15  # feet
    origin_x, origin_y = 0, 0  # Could offset from existing geometry

    walls = [
        {"name": "South", "start": (origin_x, origin_y),
         "end": (origin_x + room_width, origin_y)},
        {"name": "East", "start": (origin_x + room_width, origin_y),
         "end": (origin_x + room_width, origin_y + room_depth)},
        {"name": "North", "start": (origin_x + room_width, origin_y + room_depth),
         "end": (origin_x, origin_y + room_depth)},
        {"name": "West", "start": (origin_x, origin_y + room_depth),
         "end": (origin_x, origin_y)},
    ]

    for wall in walls:
        print(f"  {wall['name']} wall: {wall['start']} -> {wall['end']}")

    # Step 4: Create walls
    print("\nStep 4: Creating walls...")
    created_walls = {}

    for wall in walls:
        result = client.call("createWall", {
            "startX": wall["start"][0],
            "startY": wall["start"][1],
            "endX": wall["end"][0],
            "endY": wall["end"][1],
            "levelId": level_id,
            "wallTypeId": wall_type.get("typeId"),
            "height": 10.0
        })

        if result.get("success"):
            created_walls[wall["name"]] = result.get("wallId")
            print(f"  {wall['name']} wall created: {result.get('wallId')}")
        else:
            print(f"  {wall['name']} wall FAILED: {result.get('error')}")

    # Step 5: Place door on south wall
    print("\nStep 5: Placing door on south wall...")
    if "South" in created_walls:
        result = client.call("placeDoor", {
            "wallId": created_walls["South"],
            "doorTypeId": door_type.get("typeId"),
            "x": origin_x + room_width / 2,  # Center of wall
            "y": origin_y,
            "levelId": level_id
        })

        if result.get("success"):
            print(f"  Door placed: {result.get('doorId')}")
        else:
            print(f"  Door FAILED: {result.get('error')}")

    # Step 6: Create room
    print("\nStep 6: Creating room...")
    result = client.call("createRoom", {
        "levelId": level_id,
        "x": origin_x + room_width / 2,
        "y": origin_y + room_depth / 2
    })

    if result.get("success"):
        room_id = result.get("roomId")
        print(f"  Room created: {room_id}")

        # Name the room
        client.call("setParameter", {
            "elementId": room_id,
            "parameterName": "Name",
            "value": "Office"
        })
        print("  Room named: Office")

    # Step 7: Verify
    print("\nStep 7: Verifying result...")
    for wall_name, wall_id in created_walls.items():
        result = client.call("verifyElement", {"elementId": wall_id})
        status = "OK" if result.get("exists") else "MISSING"
        print(f"  {wall_name} wall: {status}")

    print("\nComplete! Room created successfully.")


def example_autonomous_goal():
    """
    Example: Level 5 Autonomous Goal Execution

    Instead of step-by-step commands, give a high-level goal
    and let the system figure out the details.
    """
    print("\n" + "=" * 60)
    print("Autonomous Goal Example")
    print("=" * 60)
    print("User: 'Document this model with floor plans and a door schedule'")
    print()

    client = RevitMCPClient().connect()

    # Use Level 5 autonomous execution
    result = client.execute_goal("document_model",
        includeFloorPlans=True,
        includeSchedules=["Doors", "Windows"],
        createSheets=True,
        sheetPattern="A-{level}.{sequence}"
    )

    if result.get("success"):
        task_id = result.get("taskId")
        print(f"Goal submitted as task: {task_id}")
        print("\nThe system will autonomously:")
        print("  1. Analyze existing views")
        print("  2. Create missing floor plan views")
        print("  3. Create door and window schedules")
        print("  4. Create sheets with proper numbering")
        print("  5. Place views and schedules on sheets")
        print("  6. Verify all placements")
        print("  7. Report any issues and attempt to fix them")

        # The system handles errors automatically
        print("\nIf errors occur, the system will:")
        print("  - Retry with corrected parameters")
        print("  - Learn from the correction")
        print("  - Apply learning to future operations")
    else:
        print(f"Goal submission failed: {result.get('error')}")


def example_learning_from_correction():
    """
    Example: Level 3 Learning from Corrections

    When an operation fails or produces wrong results,
    the system learns and improves.
    """
    print("\n" + "=" * 60)
    print("Learning from Corrections Example")
    print("=" * 60)

    client = RevitMCPClient().connect()

    # Record a correction
    print("Storing correction for future use...")
    result = client.call("storeCorrection", {
        "method": "placeDoor",
        "issue": "Door placed 6 inches from wall end",
        "correction": "Minimum offset from wall end should be 4 inches",
        "originalParams": {"x": 0.5, "y": 0, "wallId": 123},
        "correctedParams": {"x": 0.33, "y": 0, "wallId": 123}
    })

    if result.get("success"):
        print(f"Correction stored (ID: {result.get('correctionId')})")

    # Later, when placing doors, the system checks for relevant corrections
    print("\nNext time placing a door near wall end...")
    print("System will automatically apply learned offset.")

    # Get relevant corrections for a method
    result = client.call("getMethodCorrections", {"method": "placeDoor"})
    corrections = result.get("corrections", [])
    print(f"\nFound {len(corrections)} corrections for placeDoor method")


if __name__ == "__main__":
    try:
        example_natural_language_workflow()
        example_autonomous_goal()
        example_learning_from_correction()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. Revit 2026 is running")
        print("  2. A project is open")
        print("  3. RevitMCPBridge add-in is loaded")
