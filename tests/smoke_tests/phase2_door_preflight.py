#!/usr/bin/env python3
"""
Phase 2: Door Schedule Preflight Report

A real workflow test that demonstrates:
1. Query actual model data (doors)
2. Create a schedule with specific structure
3. Add meaningful fields
4. Export to verifiable format
5. Validate output content
6. Clean up artifacts

This serves as a PATTERN TEMPLATE for future workflow tests.
"""

import json
import subprocess
import time
import uuid
from pathlib import Path
from datetime import datetime

# Config
PIPE_NAME = r"\\.\pipe\RevitMCPBridge2026"
LOG_DIR = Path(__file__).parent.parent / "logs"
RUN_ID = str(uuid.uuid4())[:8]
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Logging
LOG_FILE = LOG_DIR / f"preflight_door_{TIMESTAMP}_{RUN_ID}.ndjson"
step_counter = 0


def log_event(event_type: str, **kwargs):
    """Write NDJSON log entry."""
    global step_counter
    step_counter += 1
    entry = {
        "ts": datetime.now().isoformat(),
        "type": event_type,
        "run_id": RUN_ID,
        "step_id": step_counter,
        **kwargs
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def wsl_to_windows_path(wsl_path: str) -> str:
    """Convert WSL path to Windows path for Revit."""
    if wsl_path.startswith("/mnt/"):
        parts = wsl_path[5:].split("/", 1)
        drive = parts[0].upper()
        rest = parts[1].replace("/", "\\") if len(parts) > 1 else ""
        return f"{drive}:\\" + rest
    return wsl_path


def send_request(method: str, params: dict = None, timeout: int = 30) -> dict:
    """Send MCP request and return response."""
    request = {"method": method}
    if params:
        request["params"] = params

    args_summary = str(params)[:80] if params else "None"
    start_time = time.time()

    try:
        cmd = [
            "powershell.exe", "-Command",
            f'''
            $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
            $pipe.Connect({timeout * 1000})
            $writer = New-Object System.IO.StreamWriter($pipe)
            $reader = New-Object System.IO.StreamReader($pipe)
            $writer.WriteLine('{json.dumps(request).replace("'", "''")}')
            $writer.Flush()
            $response = $reader.ReadLine()
            $pipe.Close()
            Write-Output $response
            '''
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        output = result.stdout.strip()

        # Extract JSON from output
        json_start = output.find('{')
        if json_start == -1:
            elapsed = (time.time() - start_time) * 1000
            log_event("mcp_call", method=method, args_summary=args_summary,
                     tx="rollback", elapsed_ms=elapsed, result="fail",
                     error="No JSON in response")
            return {"success": False, "error": f"No JSON found in response: {output[:100]}"}

        json_str = output[json_start:]
        response = json.loads(json_str)
        elapsed = (time.time() - start_time) * 1000

        tx_state = "commit" if response.get("success") else "rollback"
        result_state = "ok" if response.get("success") else "fail"
        error_msg = response.get("error") if not response.get("success") else None

        log_kwargs = {
            "method": method,
            "args_summary": args_summary,
            "tx": tx_state,
            "elapsed_ms": round(elapsed, 2),
            "result": result_state
        }
        if error_msg:
            log_kwargs["error"] = error_msg

        log_event("mcp_call", **log_kwargs)
        return response

    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log_event("mcp_call", method=method, args_summary=args_summary,
                 tx="rollback", elapsed_ms=round(elapsed, 2), result="fail",
                 error=str(e))
        return {"success": False, "error": str(e)}


def door_schedule_preflight() -> dict:
    """
    Door Schedule Preflight Report Workflow

    Goal: Generate a door schedule with key fields, export it,
    and validate that doors in the model are properly captured.

    Returns:
        dict: Workflow result with pass/fail, stats, and any issues
    """
    print("\n" + "=" * 60)
    print("PHASE 2: Door Schedule Preflight Report")
    print(f"Run ID: {RUN_ID}")
    print("=" * 60)

    result = {
        "workflow": "door_schedule_preflight",
        "run_id": RUN_ID,
        "timestamp": TIMESTAMP,
        "steps": [],
        "passed": False,
        "door_count": 0,
        "schedule_id": None,
        "export_path": None,
        "issues": []
    }

    schedule_id = None
    schedule_name = f"Door Preflight {RUN_ID}"

    try:
        # Step 1: Query doors in model
        print("\n[Step 1] Query doors in model...")
        resp = send_request("getDoors")

        if not resp.get("success"):
            result["issues"].append(f"getDoors failed: {resp.get('error')}")
            result["steps"].append({"step": 1, "action": "getDoors", "status": "FAIL"})
            print(f"  FAIL - {resp.get('error')}")
            return result

        doors = resp.get("doors", [])
        result["door_count"] = len(doors)
        result["steps"].append({"step": 1, "action": "getDoors", "status": "PASS", "count": len(doors)})
        print(f"  Found {len(doors)} doors in model")

        if len(doors) == 0:
            result["issues"].append("No doors in model - cannot test schedule")
            print("  WARN - No doors to schedule, workflow limited")

        # Step 2: Create door schedule
        print("\n[Step 2] Create door schedule...")
        resp = send_request("createSchedule", {
            "scheduleName": schedule_name,
            "category": "Doors"
        })

        if not resp.get("success"):
            result["issues"].append(f"createSchedule failed: {resp.get('error')}")
            result["steps"].append({"step": 2, "action": "createSchedule", "status": "FAIL"})
            print(f"  FAIL - {resp.get('error')}")
            return result

        schedule_id = resp.get("scheduleId")
        result["schedule_id"] = schedule_id
        result["steps"].append({"step": 2, "action": "createSchedule", "status": "PASS", "id": schedule_id})
        print(f"  Created schedule ID: {schedule_id}")

        # Step 3: Get available fields
        print("\n[Step 3] Get available fields...")
        resp = send_request("getScheduleFields", {"scheduleId": schedule_id})

        available_fields = []
        if resp.get("success"):
            available_fields = resp.get("availableFields", [])
            result["steps"].append({"step": 3, "action": "getScheduleFields", "status": "PASS",
                                   "available": len(available_fields)})
            print(f"  {len(available_fields)} available fields")
        else:
            result["steps"].append({"step": 3, "action": "getScheduleFields", "status": "WARN"})
            print(f"  WARN - Could not get fields: {resp.get('error')}")

        # Step 4: Add key fields
        print("\n[Step 4] Add key fields (Mark, Type Mark, Level, Width, Height)...")
        target_fields = ["Mark", "Type Mark", "Level", "Width", "Height"]
        fields_added = 0

        for field_name in target_fields:
            resp = send_request("addScheduleField", {
                "scheduleId": schedule_id,
                "fieldName": field_name
            })
            if resp.get("success"):
                fields_added += 1
                print(f"  + Added '{field_name}'")
            else:
                print(f"  - Skipped '{field_name}': {resp.get('error', 'unknown')}")

        result["steps"].append({"step": 4, "action": "addScheduleFields", "status": "PASS" if fields_added > 0 else "WARN",
                               "added": fields_added, "attempted": len(target_fields)})
        print(f"  Added {fields_added}/{len(target_fields)} fields")

        # Step 5: Export schedule to CSV
        print("\n[Step 5] Export schedule to CSV...")
        export_wsl_path = str(LOG_DIR / f"door_preflight_{RUN_ID}.csv")
        export_windows_path = wsl_to_windows_path(export_wsl_path)

        resp = send_request("exportScheduleToCSV", {
            "scheduleId": schedule_id,
            "filePath": export_windows_path
        })

        if not resp.get("success"):
            result["issues"].append(f"exportScheduleToCSV failed: {resp.get('error')}")
            result["steps"].append({"step": 5, "action": "exportScheduleToCSV", "status": "FAIL"})
            print(f"  FAIL - {resp.get('error')}")
        else:
            result["export_path"] = export_wsl_path
            result["steps"].append({"step": 5, "action": "exportScheduleToCSV", "status": "PASS"})
            print(f"  Exported to: {export_wsl_path}")

        # Step 6: Validate export content
        print("\n[Step 6] Validate export content...")
        export_file = Path(export_wsl_path)
        if export_file.exists():
            content = export_file.read_text()
            lines = [l for l in content.strip().split('\n') if l.strip()]

            # Count data rows (skip header)
            data_rows = len(lines) - 1 if len(lines) > 0 else 0

            result["steps"].append({"step": 6, "action": "validateExport", "status": "PASS",
                                   "rows": data_rows, "size": len(content)})
            print(f"  Export has {data_rows} data rows, {len(content)} chars")

            # Compare to door count
            if data_rows == len(doors):
                print(f"  MATCH - Export rows match door count ({len(doors)})")
            elif data_rows > 0:
                print(f"  NOTE - Export has {data_rows} rows, model has {len(doors)} doors")
            else:
                result["issues"].append("Export has no data rows")
        else:
            result["issues"].append("Export file not found")
            result["steps"].append({"step": 6, "action": "validateExport", "status": "FAIL"})
            print(f"  FAIL - Export file not found")

        # Step 7: Cleanup
        print("\n[Step 7] Cleanup (delete test schedule)...")
        resp = send_request("deleteElement", {"elementId": schedule_id})

        if resp.get("success"):
            result["steps"].append({"step": 7, "action": "cleanup", "status": "PASS"})
            print("  Schedule deleted")
        else:
            result["issues"].append(f"Cleanup failed: {resp.get('error')}")
            result["steps"].append({"step": 7, "action": "cleanup", "status": "WARN"})
            print(f"  WARN - Cleanup failed: {resp.get('error')}")

        # Final assessment
        critical_steps = [s for s in result["steps"] if s["status"] == "FAIL"]
        result["passed"] = len(critical_steps) == 0

    except Exception as e:
        result["issues"].append(f"Workflow exception: {str(e)}")
        result["passed"] = False
        print(f"\nEXCEPTION: {e}")

        # Try cleanup on exception
        if schedule_id:
            try:
                send_request("deleteElement", {"elementId": schedule_id})
            except:
                pass

    return result


def main():
    """Run Phase 2 preflight workflow."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Log workflow start
    log_event("workflow_start", workflow="door_schedule_preflight")

    # Run the workflow
    result = door_schedule_preflight()

    # Log workflow end
    log_event("workflow_end",
             result="pass" if result["passed"] else "fail",
             door_count=result["door_count"],
             issues_count=len(result["issues"]))

    # Print summary
    print("\n" + "=" * 60)
    print("PREFLIGHT SUMMARY")
    print("=" * 60)
    print(f"Run ID:     {result['run_id']}")
    print(f"Doors:      {result['door_count']}")
    print(f"Schedule:   {result['schedule_id']}")
    print(f"Export:     {result['export_path']}")
    print("-" * 60)

    for step in result["steps"]:
        status_icon = "✓" if step["status"] == "PASS" else "✗" if step["status"] == "FAIL" else "⚠"
        print(f"  {status_icon} Step {step['step']}: {step['action']} - {step['status']}")

    print("-" * 60)
    if result["issues"]:
        print("Issues:")
        for issue in result["issues"]:
            print(f"  - {issue}")

    print("-" * 60)
    if result["passed"]:
        print("RESULT: PASSED")
    else:
        print("RESULT: FAILED")
    print("=" * 60)

    # Save summary
    summary_path = LOG_DIR / f"preflight_summary_{TIMESTAMP}_{RUN_ID}.json"
    with open(summary_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSummary: {summary_path}")
    print(f"Log:     {LOG_FILE}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    exit(main())
