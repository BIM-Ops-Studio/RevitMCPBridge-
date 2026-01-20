"""
Execute DD Package Workflow Autonomously
Creates complete Design Development deliverable
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient
import json

def main():
    print("=" * 80)
    print("EXECUTING DD PACKAGE WORKFLOW - AUTONOMOUS MODE")
    print("=" * 80)
    print()

    client = RevitClient()

    print("Starting autonomous DD package creation...")
    print("This will execute 30+ tasks automatically:")
    print("  - Verify project setup")
    print("  - Create floor plan views")
    print("  - Tag all rooms and doors")
    print("  - Create schedules")
    print("  - Check building code compliance")
    print("  - Organize sheet set")
    print("  - Run quality control")
    print()
    print("Watch your Revit model as I work...")
    print()

    # Execute the workflow
    result = client.send_request("executeWorkflow", {
        "workflowType": "DD_Package",
        "projectType": "SmallCommercial",
        "buildingCode": "IBC_2024"
    })

    print("=" * 80)

    if not result.get("success"):
        print("[ERROR] Workflow execution failed")
        print(f"Error: {result.get('error', 'Unknown error')}")
        return False

    # Show results
    print("[SUCCESS] DD PACKAGE COMPLETED!")
    print("=" * 80)
    print()

    workflow_id = result.get("workflowId")
    tasks_completed = result.get("tasksCompleted", 0)
    decisions_made = result.get("decisionsMade", 0)
    execution_time = result.get("executionTime", 0)

    print("EXECUTION SUMMARY:")
    print(f"  Workflow ID: {workflow_id}")
    print(f"  Tasks Completed: {tasks_completed}")
    print(f"  Autonomous Decisions: {decisions_made}")
    print(f"  Execution Time: {execution_time:.2f} seconds")
    print()

    # Get detailed status
    print("Getting detailed workflow status...")
    status_result = client.send_request("getWorkflowStatus", {
        "workflowId": workflow_id
    })

    if status_result.get("success"):
        completed = status_result.get("completedTasks", [])
        decisions = status_result.get("decisionsMade", [])

        if completed:
            print()
            print("COMPLETED TASKS:")
            for i, task in enumerate(completed[:15], 1):
                print(f"  {i}. {task}")
            if len(completed) > 15:
                print(f"  ... and {len(completed) - 15} more tasks")

        if decisions:
            print()
            print("AUTONOMOUS DECISIONS MADE:")
            for i, decision in enumerate(decisions[:10], 1):
                if isinstance(decision, dict):
                    print(f"  {i}. {decision.get('task', 'N/A')}")
                    print(f"     -> {decision.get('decision', 'N/A')}")
                else:
                    print(f"  {i}. {decision}")
            if len(decisions) > 10:
                print(f"  ... and {len(decisions) - 10} more decisions")

    print()
    print("=" * 80)
    print("CHECK YOUR REVIT PROJECT FOR:")
    print("  - Tagged floor plans")
    print("  - Room, door, and window schedules")
    print("  - Organized sheet set")
    print("  - Code compliance verification")
    print("=" * 80)

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
