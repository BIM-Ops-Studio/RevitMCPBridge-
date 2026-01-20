"""
Example: Create a complete sheet set using RevitMCPBridge2026

This example demonstrates:
1. Connecting to the MCP server
2. Getting project views
3. Creating sheets
4. Placing views on sheets
5. Using Level 5 autonomous goal execution

Prerequisites:
- Revit 2026 running with RevitMCPBridge loaded
- A project with floor plan views
"""

import json
import win32pipe
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'


def connect():
    """Connect to MCP server"""
    return win32file.CreateFile(
        PIPE_NAME,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None,
        win32file.OPEN_EXISTING,
        0, None
    )


def call_mcp(pipe, method, params=None):
    """Call an MCP method and return the result"""
    params = params or {}
    request = json.dumps({"method": method, "params": params})
    win32file.WriteFile(pipe, request.encode())
    response = win32file.ReadFile(pipe, 65536)[1]
    return json.loads(response.decode())


def main():
    print("Connecting to RevitMCPBridge2026...")
    pipe = connect()
    print("Connected!\n")

    # Method 1: Manual sheet creation
    print("=" * 60)
    print("Method 1: Manual Sheet Creation")
    print("=" * 60)

    # Get all floor plan views
    result = call_mcp(pipe, "getAllViews")
    if not result.get("success"):
        print(f"Error: {result.get('error')}")
        return

    views = result.get("views", [])
    floor_plans = [v for v in views if v.get("viewType") == "FloorPlan"]
    print(f"Found {len(floor_plans)} floor plan views")

    # Get title block types
    result = call_mcp(pipe, "getTitleBlockTypes")
    title_blocks = result.get("titleBlocks", [])
    if title_blocks:
        title_block_id = title_blocks[0].get("typeId")
        print(f"Using title block: {title_blocks[0].get('name')}")
    else:
        print("No title blocks found!")
        return

    # Create a sheet for each floor plan
    created_sheets = []
    for i, view in enumerate(floor_plans[:3]):  # Limit to 3 for demo
        sheet_number = f"A-{101 + i}"
        sheet_name = f"Floor Plan - {view.get('name')}"

        print(f"\nCreating sheet: {sheet_number} - {sheet_name}")

        result = call_mcp(pipe, "createSheet", {
            "sheetNumber": sheet_number,
            "sheetName": sheet_name,
            "titleBlockId": title_block_id
        })

        if result.get("success"):
            sheet_id = result.get("sheetId")
            created_sheets.append({
                "sheetId": sheet_id,
                "viewId": view.get("viewId")
            })
            print(f"  Created sheet ID: {sheet_id}")

            # Place the view on the sheet
            result = call_mcp(pipe, "placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view.get("viewId"),
                "x": 1.5,  # Center of sheet (feet from origin)
                "y": 1.0
            })

            if result.get("success"):
                print(f"  Placed view on sheet")
            else:
                print(f"  Error placing view: {result.get('error')}")
        else:
            print(f"  Error: {result.get('error')}")

    print(f"\nCreated {len(created_sheets)} sheets")

    # Method 2: Autonomous goal execution (Level 5)
    print("\n" + "=" * 60)
    print("Method 2: Autonomous Goal Execution (Level 5)")
    print("=" * 60)

    # Use the executeGoal method for autonomous execution
    print("\nExecuting autonomous sheet set creation...")

    result = call_mcp(pipe, "executeGoal", {
        "goalType": "create_sheet_set",
        "parameters": {
            "viewTypes": ["FloorPlan", "Section"],
            "sheetPattern": "A-{level}.{sequence}",
            "titleBlockName": "E1 30x42 Horizontal"
        }
    })

    if result.get("success"):
        task_id = result.get("taskId")
        print(f"Goal submitted, task ID: {task_id}")

        # Check if task needs approval
        if result.get("requiresApproval"):
            print("\nTask requires approval. Approving...")
            result = call_mcp(pipe, "approveTask", {"taskId": task_id})

        # Wait for completion (in real use, you'd poll)
        print("Task is executing autonomously...")
        print("The AI will automatically:")
        print("  - Analyze available views")
        print("  - Create sheets with intelligent numbering")
        print("  - Place views optimally")
        print("  - Handle any errors automatically")
    else:
        print(f"Error: {result.get('error')}")

    print("\nDone!")


if __name__ == "__main__":
    main()
