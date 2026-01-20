"""
Execute DD Package Workflow
Creates complete Design Development deliverable autonomously
"""

import json
import sys
from pathlib import Path

# Add the revit-mcp-server to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "revit-mcp-server"))

from revit_mcp_server.revit_client import RevitClient


def main():
    print("=" * 80)
    print("EXECUTING DD PACKAGE WORKFLOW")
    print("=" * 80)
    print()

    # Connect to Revit
    print("🔌 Connecting to Revit MCP Server...")
    client = RevitClient()

    try:
        client.connect()
        print("✅ Connected successfully\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    # Get current project info
    print("📋 Checking current project...")
    project_info = client.send_request("getProjectInfo", {})

    if project_info.get("success"):
        info = project_info.get("projectInfo", {})
        print(f"   Project: {info.get('ProjectName', 'Unnamed Project')}")
        print(f"   Number: {info.get('ProjectNumber', 'N/A')}")
        print(f"   Address: {info.get('ProjectAddress', 'N/A')}")
        print()

    # Execute DD Package workflow
    print("🚀 Starting DD Package Workflow...")
    print("   This will autonomously:")
    print("   - Verify project setup")
    print("   - Create floor plan views")
    print("   - Tag all rooms and doors")
    print("   - Create schedules")
    print("   - Check building code compliance")
    print("   - Organize sheet set")
    print("   - Run quality control")
    print()

    result = client.send_request("executeWorkflow", {
        "workflowType": "DD_Package",
        "projectType": "SmallCommercial",
        "buildingCode": "IBC_2024"
    })

    print("=" * 80)

    if not result.get("success"):
        error = result.get("error", "Unknown error")
        print(f"❌ WORKFLOW FAILED")
        print(f"   Error: {error}")
        print()

        if "No active document" in error:
            print("   Note: Make sure you have a Revit project open")
        elif "No rooms found" in error or "No elements" in error:
            print("   Note: The project needs rooms, walls, and doors for DD package")

        print("=" * 80)
        return False

    # Success - show results
    print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()

    workflow_id = result.get("workflowId")
    tasks_completed = result.get("tasksCompleted", 0)
    decisions_made = result.get("decisionsMade", 0)
    execution_time = result.get("executionTime", 0)

    print(f"📊 EXECUTION SUMMARY:")
    print(f"   Workflow ID: {workflow_id}")
    print(f"   Tasks Completed: {tasks_completed}")
    print(f"   Autonomous Decisions Made: {decisions_made}")
    print(f"   Execution Time: {execution_time:.2f} seconds")
    print()

    # Get detailed status
    print("📝 Getting detailed workflow status...")
    status_result = client.send_request("getWorkflowStatus", {
        "workflowId": workflow_id
    })

    if status_result.get("success"):
        # Get the status - might be nested or direct
        status = status_result

        # Handle if there's a nested "status" key
        if "status" in status_result and isinstance(status_result["status"], (dict, str)):
            status = status_result["status"]

        # Handle if status is returned as string (JSON)
        if isinstance(status, str):
            try:
                status = json.loads(status)
            except:
                status = {}

        completed_tasks = status.get("completedTasks", [])
        decisions = status.get("decisionsMade", [])

        print(f"   Status: {status.get('status')}")
        print(f"   Current Phase: {status.get('currentPhase')}")
        print()

        if completed_tasks:
            print("   ✓ Completed Tasks:")
            for task in completed_tasks[:10]:  # Show first 10
                print(f"     - {task}")
            if len(completed_tasks) > 10:
                print(f"     ... and {len(completed_tasks) - 10} more")
            print()

        if decisions:
            print("   🤖 Autonomous Decisions Made:")
            for decision in decisions[:5]:  # Show first 5
                if isinstance(decision, dict):
                    print(f"     - {decision.get('task', 'N/A')}: {decision.get('decision', 'N/A')}")
            if len(decisions) > 5:
                print(f"     ... and {len(decisions) - 5} more decisions")
            print()

    print("=" * 80)
    print("🎉 DD PACKAGE COMPLETE!")
    print("   Check your Revit project for:")
    print("   - Tagged floor plans")
    print("   - Room, door, and window schedules")
    print("   - Organized sheet set")
    print("   - Code compliance verification")
    print("=" * 80)
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
