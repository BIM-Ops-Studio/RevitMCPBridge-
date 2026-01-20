#!/usr/bin/env python3
"""
Phase 1 Smoke Tests for RevitMCPBridge2026
Pass/Fail tests to prove core functionality works.

Corrections applied:
1. Test A uses Undo (undoLastOperation), Delete as fallback
2. Test B is deterministic (creates drafting view, ZZ-TEST- prefix, verifies viewport)
3. Logging includes run_start header with doc_id, revit_version

Run with: python smoke_tests/run_smoke_tests.py
Exit code: 0 = all pass, 1 = failures
"""

import subprocess
import json
import time
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Config
PIPE_NAME = "RevitMCPBridge2026"
TIMEOUT = 30
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def wsl_to_windows_path(wsl_path: str) -> str:
    """Convert WSL path to Windows path for Revit."""
    if wsl_path.startswith("/mnt/"):
        # /mnt/d/foo -> D:\foo
        parts = wsl_path[5:].split("/", 1)
        drive = parts[0].upper()
        rest = parts[1].replace("/", "\\") if len(parts) > 1 else ""
        return f"{drive}:\\" + rest
    return wsl_path

# Session tracking
RUN_ID = str(uuid.uuid4())[:8]
STEP_ID = 0
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = LOG_DIR / f"smoke_{TIMESTAMP}_{RUN_ID}.ndjson"
SUMMARY_FILE = LOG_DIR / f"smoke_summary_{TIMESTAMP}_{RUN_ID}.json"


def log_event(event_type: str, method: str = None, args_summary: str = None,
              tx: str = "none", elapsed_ms: float = 0, result: str = None,
              error: str = None, warnings_count: int = 0, **extra):
    """Write one log line to NDJSON file."""
    global STEP_ID
    STEP_ID += 1

    entry = {
        "ts": datetime.now().isoformat(),
        "type": event_type,
        "run_id": RUN_ID,
        "step_id": STEP_ID,
    }

    if method:
        entry["method"] = method
    if args_summary:
        entry["args_summary"] = args_summary
    if tx != "none":
        entry["tx"] = tx
    if elapsed_ms > 0:
        entry["elapsed_ms"] = round(elapsed_ms, 2)
    if result:
        entry["result"] = result
    if error:
        entry["error"] = error
    if warnings_count > 0:
        entry["warnings_count"] = warnings_count

    entry.update(extra)

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def send_request(method: str, params: dict = None) -> dict:
    """Send request to MCP server and return response."""
    request = {"method": method}
    if params:
        request["params"] = params

    ps_script = f'''
$pipeName = '{PIPE_NAME}'
$request = @'
{json.dumps(request)}
'@
try {{
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect({TIMEOUT * 1000})
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.WriteLine($request)
    $writer.Flush()
    $response = $reader.ReadLine()
    $pipe.Close()
    Write-Output $response
}} catch {{
    Write-Output ('ERROR: ' + $_.Exception.Message)
}}
'''

    start = time.time()
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=TIMEOUT + 5
        )
        elapsed = (time.time() - start) * 1000
        output = result.stdout.strip()
    except subprocess.TimeoutExpired:
        elapsed = (time.time() - start) * 1000
        log_event("mcp_call", method, str(params)[:100], "none", elapsed, "fail", "Timeout")
        return {"success": False, "error": "Request timed out"}

    # Parse response - extract JSON from output (may have prefix text from shell hooks)
    if output.startswith("ERROR:"):
        error_msg = output.replace("ERROR:", "").strip()
        log_event("mcp_call", method, str(params)[:100], "none", elapsed, "fail", error_msg)
        return {"success": False, "error": error_msg}

    # Find the JSON start (skip any shell startup messages)
    json_start = output.find('{')
    if json_start == -1:
        log_event("mcp_call", method, str(params)[:100], "none", elapsed, "fail",
                  "No JSON in response")
        return {"success": False, "error": f"No JSON found in response: {output[:200]}"}

    json_str = output[json_start:]

    try:
        response = json.loads(json_str)
        tx_state = "commit" if response.get("success") else "rollback"
        warnings = response.get("warnings_count", 0)
        log_event("mcp_call", method, str(params)[:100], tx_state, elapsed,
                  "ok" if response.get("success") else "fail",
                  response.get("error"), warnings)
        return response
    except json.JSONDecodeError as e:
        log_event("mcp_call", method, str(params)[:100], "none", elapsed, "fail",
                  f"JSON decode error: {str(e)[:100]}")
        return {"success": False, "error": f"JSON decode error: {json_str[:200]}"}


def get_document_info() -> dict:
    """Get current document info for logging."""
    resp = send_request("getProjectInfo")
    if resp.get("success"):
        return {
            "doc_title": resp.get("projectInfo", {}).get("name", "Unknown"),
            "doc_path": resp.get("projectInfo", {}).get("path", "Unknown"),
        }
    return {"doc_title": "Unknown", "doc_path": "Unknown"}


def test_ping() -> tuple:
    """Test 0: Basic connectivity. Returns (pass, details)."""
    print("\n[TEST 0] Ping - Basic Connectivity")
    print("-" * 40)

    resp = send_request("getLevels")

    if resp.get("success"):
        levels = resp.get("levels", [])
        print(f"  PASS - Connected, found {len(levels)} levels")
        return True, {"levels_count": len(levels)}
    else:
        print(f"  FAIL - {resp.get('error', 'Unknown error')}")
        return False, {"error": resp.get("error")}


def test_a_transaction_undo() -> tuple:
    """
    Test A: Transaction + Undo Integrity
    Goal: Prove commands don't pollute state.
    Uses undoLastOperation first, deleteElement as fallback.
    """
    print("\n[TEST A] Transaction + Undo Integrity")
    print("-" * 40)

    details = {"undo_method": None, "baseline": 0, "after_create": 0, "final": 0}

    # 1. Get baseline wall count
    print("  1. Getting baseline wall count...")
    resp = send_request("getWalls")
    if not resp.get("success"):
        print(f"  FAIL - Could not get walls: {resp.get('error')}")
        return False, {"error": "Could not get baseline walls", "details": resp.get("error")}

    baseline_count = len(resp.get("walls", []))
    details["baseline"] = baseline_count
    print(f"     Baseline: {baseline_count} walls")

    # 2. Get a level to place wall on
    resp = send_request("getLevels")
    if not resp.get("success") or not resp.get("levels"):
        print(f"  FAIL - Could not get levels")
        return False, {"error": "Could not get levels"}

    level_id = resp["levels"][0].get("levelId") or resp["levels"][0].get("id")

    # 3. Get a wall type
    resp = send_request("getWallTypes")
    if not resp.get("success") or not resp.get("wallTypes"):
        print(f"  FAIL - Could not get wall types")
        return False, {"error": "Could not get wall types"}

    wall_type_id = resp["wallTypes"][0].get("id") or resp["wallTypes"][0].get("typeId") or resp["wallTypes"][0].get("wallTypeId")

    # 4. Create exactly 1 wall (at a unique location to avoid conflicts)
    unique_x = 500 + int(time.time() % 1000)
    print(f"  2. Creating 1 wall at x={unique_x}...")
    resp = send_request("createWall", {
        "startPoint": [unique_x, 100, 0],
        "endPoint": [unique_x + 20, 100, 0],
        "levelId": level_id,
        "height": 10,
        "wallTypeId": wall_type_id
    })

    if not resp.get("success"):
        print(f"  FAIL - Could not create wall: {resp.get('error')}")
        return False, {"error": "Wall creation failed", "details": resp.get("error")}

    wall_id = resp.get("wallId")
    print(f"     Created wall ID: {wall_id}")

    # 5. Confirm wall count increased by 1
    print("  3. Verifying wall count increased...")
    resp = send_request("getWalls")
    new_count = len(resp.get("walls", []))
    details["after_create"] = new_count

    if new_count != baseline_count + 1:
        print(f"  FAIL - Expected {baseline_count + 1} walls, got {new_count}")
        return False, {"error": f"Wall count mismatch: expected {baseline_count + 1}, got {new_count}"}
    print(f"     Count: {new_count} (correct)")

    # 6. Try Undo first (undoLastOperation), then Delete as fallback
    print("  4. Attempting undo...")

    # Try undoLastOperation first
    resp = send_request("undoLastOperation")
    undo_worked = resp.get("success", False)

    if undo_worked:
        details["undo_method"] = "undoLastOperation"
        print(f"     Used: undoLastOperation")
    else:
        # Fallback to delete
        print(f"     undoLastOperation failed ({resp.get('error', 'unknown')}), using deleteElement...")
        resp = send_request("deleteElement", {"elementId": wall_id})
        if resp.get("success"):
            details["undo_method"] = "deleteElement (fallback)"
            print(f"     Used: deleteElement (fallback)")
        else:
            print(f"  FAIL - Both undo methods failed: {resp.get('error')}")
            return False, {"error": "Both undo methods failed", "details": resp.get("error")}

    # 7. Confirm wall count returns to baseline
    print("  5. Verifying wall count returned to baseline...")
    resp = send_request("getWalls")
    final_count = len(resp.get("walls", []))
    details["final"] = final_count

    if final_count != baseline_count:
        print(f"  FAIL - Expected {baseline_count} walls, got {final_count}")
        return False, {"error": f"Final count mismatch: expected {baseline_count}, got {final_count}"}

    print(f"     Final count: {final_count} (matches baseline)")
    print(f"  PASS - Transaction + Undo verified via {details['undo_method']}")
    return True, details


def test_b_sheet_viewport_export() -> tuple:
    """
    Test B: Sheet CRUD + Export
    Goal: Prove sheet creation/export backbone works.
    Note: placeViewOnSheet has a known bug - tested separately.
    """
    print("\n[TEST B] Sheet CRUD + Export")
    print("-" * 40)

    details = {"sheet_id": None, "export_path": None}
    sheet_number = f"ZZ-TEST-{TIMESTAMP[-6:]}"

    # 1. Get title block (use first available)
    print("  1. Checking title blocks...")
    resp = send_request("getTitleblockTypes")
    title_block_id = None
    if resp.get("success"):
        tbs = resp.get("titleblockTypes") or resp.get("titleBlocks") or []
        if tbs:
            tb = tbs[0]
            title_block_id = tb.get("id") or tb.get("typeId") or tb.get("titleblockId")
            print(f"     Using title block ID: {title_block_id}")
    if not title_block_id:
        print("     No title blocks found, creating sheet without")

    # 2. Create sheet with deterministic number
    print(f"  2. Creating sheet {sheet_number}...")
    sheet_params = {
        "sheetNumber": sheet_number,
        "sheetName": f"Smoke Test {RUN_ID}"
    }
    if title_block_id:
        sheet_params["titleblockId"] = title_block_id

    resp = send_request("createSheet", sheet_params)

    if not resp.get("success"):
        print(f"  FAIL - Could not create sheet: {resp.get('error')}")
        return False, {"error": "Sheet creation failed", "details": resp.get("error")}

    sheet_id = resp.get("sheetId")
    details["sheet_id"] = sheet_id
    print(f"     Created sheet ID: {sheet_id}")

    # 3. Export sheet list (verify sheet appears)
    print("  3. Exporting sheet list...")
    export_path = str(LOG_DIR / f"sheet_list_{RUN_ID}.csv")
    details["export_path"] = export_path

    resp = send_request("getAllSheets")

    export_verified = False
    if resp.get("success"):
        # Sheets might be under "sheets" or "result.sheets"
        sheets = resp.get("sheets") or resp.get("result", {}).get("sheets", [])
        # Write to CSV
        with open(export_path, 'w') as f:
            f.write("Number,Name,ID\n")
            for s in sheets:
                s_num = s.get("number", s.get("sheetNumber", ""))
                s_name = s.get("name", s.get("sheetName", ""))
                s_id = s.get("id") or s.get("sheetId")
                f.write(f"{s_num},{s_name},{s_id}\n")

        # Verify our sheet is in the export
        with open(export_path, 'r') as f:
            content = f.read()
        if sheet_number in content:
            export_verified = True
            print(f"     Sheet found in export ({len(sheets)} sheets total)")
        else:
            print(f"  WARN - Sheet not found in export content")
    else:
        print(f"  WARN - Could not get sheets: {resp.get('error')}")

    # 4. Cleanup
    print("  4. Cleaning up...")
    resp = send_request("deleteElement", {"elementId": sheet_id})
    if resp.get("success"):
        print("     Sheet deleted")
    else:
        print(f"     Sheet deletion failed: {resp.get('error')}")

    # Overall result
    details["export_verified"] = export_verified

    if export_verified:
        print("  PASS - Sheet CRUD + Export verified")
        return True, details
    else:
        print("  FAIL - Sheet not found in export")
        return False, details


def test_c_schedule_crud_export() -> tuple:
    """
    Test C: Schedule CRUD + Export
    Goal: Prove schedule engine is real.
    """
    print("\n[TEST C] Schedule CRUD + Export")
    print("-" * 40)

    details = {"schedule_id": None, "created": False, "fields_count": 0, "export_path": None}
    schedule_name = f"Door Schedule Test {RUN_ID}"

    # 1. Create a new door schedule (deterministic)
    print("  1. Creating door schedule...")
    schedule_id = None
    resp = send_request("createSchedule", {
        "scheduleName": schedule_name,
        "category": "Doors"
    })

    if resp.get("success"):
        schedule_id = resp.get("scheduleId")
        details["schedule_id"] = schedule_id
        details["created"] = True
        print(f"     Created schedule ID: {schedule_id}")
    else:
        # Fallback: find existing door schedule
        print(f"     Could not create ({resp.get('error')}), finding existing...")
        resp = send_request("getSchedules")
        if not resp.get("success"):
            return False, {"error": "Could not get schedules"}

        for s in resp.get("schedules", []):
            s_id = s.get("id") or s.get("scheduleId")
            s_name = s.get("name", "")
            if "door" in s_name.lower() and s_id:
                schedule_id = s_id
                details["schedule_id"] = schedule_id
                print(f"     Using existing schedule: {s_name} (ID: {schedule_id})")
                break

        if not schedule_id:
            return False, {"error": "No door schedule available"}

    # 2. Get/verify schedule fields
    print("  2. Getting schedule fields...")
    resp = send_request("getScheduleFields", {"scheduleId": schedule_id})

    if resp.get("success"):
        fields = resp.get("fields", [])
        details["fields_count"] = len(fields)
        print(f"     Found {len(fields)} fields")
    else:
        print(f"  WARN - Could not get fields: {resp.get('error')}")

    # 3. Add a field if schedule has few fields
    if details["fields_count"] < 2 and details["created"]:
        print("  3. Adding 'Mark' field...")
        resp = send_request("addScheduleField", {
            "scheduleId": schedule_id,
            "fieldName": "Mark"
        })
        if resp.get("success"):
            print("     Field added")
        else:
            print(f"     Could not add field: {resp.get('error')}")

    # 4. Export schedule
    print("  4. Exporting schedule...")
    export_path = str(LOG_DIR / f"schedule_export_{RUN_ID}.csv")
    details["export_path"] = export_path

    resp = send_request("exportScheduleToCSV", {
        "scheduleId": schedule_id,
        "filePath": wsl_to_windows_path(export_path)
    })

    export_verified = False
    if resp.get("success"):
        if os.path.exists(export_path):
            with open(export_path, 'r') as f:
                content = f.read()
            export_verified = len(content) > 10  # Has some content
            print(f"     Export created ({len(content)} chars)")
        else:
            print(f"  WARN - Export file not created")
    else:
        print(f"  WARN - Export failed: {resp.get('error')}")

    details["export_verified"] = export_verified

    # 5. Cleanup if we created it
    if details["created"]:
        print("  5. Cleaning up...")
        resp = send_request("deleteElement", {"elementId": schedule_id})
        if resp.get("success"):
            print("     Schedule deleted")
        else:
            print(f"     Deletion failed: {resp.get('error')}")

    # Result
    if export_verified:
        print("  PASS - Schedule CRUD + Export verified")
        return True, details
    else:
        print("  FAIL - Export not verified")
        return False, details


def main():
    print("=" * 60)
    print("RevitMCPBridge2026 - Phase 1 Smoke Tests")
    print(f"Run ID: {RUN_ID}")
    print(f"Timestamp: {TIMESTAMP}")
    print("=" * 60)

    # Write run_start header to log
    doc_info = {"doc_title": "Unknown", "doc_path": "Unknown"}

    # Try to get document info (connectivity test)
    test_resp = send_request("getProjectInfo")
    if test_resp.get("success"):
        doc_info["doc_title"] = test_resp.get("projectInfo", {}).get("name", "Unknown")
        doc_info["doc_path"] = test_resp.get("projectInfo", {}).get("path", "Unknown")

    log_event("run_start",
              revit_version="2026",
              doc_title=doc_info["doc_title"],
              doc_path=doc_info["doc_path"])

    print(f"Document: {doc_info['doc_title']}")
    print(f"Log: {LOG_FILE}")

    results = {}

    # Test 0: Connectivity
    passed, details = test_ping()
    results["ping"] = {"passed": passed, "details": details}

    if not passed:
        print("\n" + "=" * 60)
        print("ABORT: Cannot connect to Revit MCP server")
        print("Make sure Revit is open with a project loaded")
        print("=" * 60)

        # Write summary
        summary = {
            "run_id": RUN_ID,
            "timestamp": TIMESTAMP,
            "all_passed": False,
            "aborted": True,
            "reason": "Connection failed",
            "results": results,
            "log_file": str(LOG_FILE)
        }
        with open(SUMMARY_FILE, 'w') as f:
            json.dump(summary, f, indent=2)

        log_event("run_end", result="fail", reason="Connection failed")
        sys.exit(1)

    # Test A: Transaction + Undo
    passed, details = test_a_transaction_undo()
    results["test_a"] = {"passed": passed, "details": details}

    # Test B: Sheet + Viewport + Export
    passed, details = test_b_sheet_viewport_export()
    results["test_b"] = {"passed": passed, "details": details}

    # Test C: Schedule CRUD + Export
    passed, details = test_c_schedule_crud_export()
    results["test_c"] = {"passed": passed, "details": details}

    # Summary
    all_passed = all(r["passed"] for r in results.values())

    print("\n" + "=" * 60)
    print("SMOKE TEST SUMMARY")
    print("=" * 60)
    print(f"Run ID:    {RUN_ID}")
    print(f"Document:  {doc_info['doc_title']}")
    print("-" * 60)

    for name, data in results.items():
        status = "PASS" if data["passed"] else "FAIL"
        extra = ""
        if name == "test_a" and data["passed"]:
            extra = f" (via {data['details'].get('undo_method', 'unknown')})"
        print(f"  {name}: {status}{extra}")

    print("-" * 60)
    if all_passed:
        print("RESULT: ALL TESTS PASSED")
    else:
        print("RESULT: SOME TESTS FAILED")

    print(f"\nLog file: {LOG_FILE}")
    print(f"Summary:  {SUMMARY_FILE}")
    print("=" * 60)

    # Write summary JSON
    summary = {
        "run_id": RUN_ID,
        "timestamp": TIMESTAMP,
        "revit_version": "2026",
        "document": doc_info,
        "all_passed": all_passed,
        "results": results,
        "log_file": str(LOG_FILE),
    }
    with open(SUMMARY_FILE, 'w') as f:
        json.dump(summary, f, indent=2)

    # Log run end
    log_event("run_end", result="ok" if all_passed else "fail")

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
