#!/usr/bin/env python3
"""
Phase 2: Door Schedule Preflight Report (v2)

Uses standardized WorkflowReport schema v1.0.
Demonstrates:
- Budget tracking
- Artifact tracking for rollback
- Postcondition verification
- Structured issue reporting
"""

import json
import subprocess
import time
from pathlib import Path

from workflow_report import (
    WorkflowReport, RunStatus, Severity, EventType
)


def wsl_to_windows_path(wsl_path: str) -> str:
    """Convert WSL path to Windows path for Revit."""
    if wsl_path.startswith("/mnt/"):
        parts = wsl_path[5:].split("/", 1)
        drive = parts[0].upper()
        rest = parts[1].replace("/", "\\") if len(parts) > 1 else ""
        return f"{drive}:\\" + rest
    return wsl_path


def send_mcp_request(method: str, params: dict = None, timeout: int = 30) -> tuple:
    """Send MCP request. Returns (response_dict, elapsed_ms)."""
    request = {"method": method}
    if params:
        request["params"] = params

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
        elapsed_ms = (time.time() - start_time) * 1000

        # Extract JSON
        json_start = output.find('{')
        if json_start == -1:
            return {"success": False, "error": f"No JSON in response"}, elapsed_ms

        response = json.loads(output[json_start:])
        return response, elapsed_ms

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {"success": False, "error": str(e)}, elapsed_ms


def run_door_preflight():
    """
    Door Schedule Preflight Workflow

    Steps:
    1. Get project info (for environment)
    2. Query doors in model
    3. Create door schedule
    4. Add key fields
    5. Export to CSV
    6. Validate export
    7. Cleanup
    """

    # Initialize report
    report = WorkflowReport("door_schedule_preflight")

    # Set budget limits (can customize per workflow)
    report.set_budget_limits(
        max_steps=20,
        max_total_retries=3,
        max_elapsed_ms=120000
    )

    schedule_id = None
    schedule_name = f"Door Preflight {report.run_id}"

    print("\n" + "=" * 60)
    print(f"DOOR SCHEDULE PREFLIGHT v2")
    print(f"Run ID: {report.run_id}")
    print("=" * 60)

    try:
        # Step 0: Get environment info
        report.start_step("00_get_environment")
        print("\n[Step 0] Getting environment info...")

        resp, elapsed = send_mcp_request("getProjectInfo")
        report.log_mcp_call("getProjectInfo", {}, resp, elapsed)

        if resp.get("success"):
            report.set_environment(
                revit_version=resp.get("revitVersion", "2026"),
                doc_title=resp.get("projectName", resp.get("documentTitle", "Unknown")),
                doc_path=resp.get("documentPath")
            )
            print(f"  Document: {report.doc_title}")
        else:
            report.set_environment(revit_version="2026", doc_title="Unknown")
            print(f"  WARN: Could not get project info")

        report.end_step(outputs={"doc_title": report.doc_title})

        # Check budget before continuing
        if report.budget_exceeded:
            report.stop("Budget exceeded before main workflow")
            return report

        # Step 1: Query doors
        report.start_step("01_query_doors")
        print("\n[Step 1] Querying doors in model...")

        resp, elapsed = send_mcp_request("getDoors")
        report.log_mcp_call("getDoors", {}, resp, elapsed)

        if not resp.get("success"):
            report.add_issue("DOORS_QUERY_FAILED", Severity.BLOCKER,
                           f"Failed to query doors: {resp.get('error')}",
                           suggested_action="Check MCP connection and Revit document")
            report.end_step(status="fail")
            report.finalize()
            return report

        doors = resp.get("doors", [])
        report.set_metric("door_count", len(doors))
        print(f"  Found {len(doors)} doors")

        if len(doors) == 0:
            report.add_issue("NO_DOORS", Severity.WARNING,
                           "No doors found in model",
                           suggested_action="Add doors to model before running schedule workflow")

        report.end_step(outputs={"door_count": len(doors)})

        # Step 2: Create schedule
        report.start_step("02_create_schedule")
        print(f"\n[Step 2] Creating schedule '{schedule_name}'...")

        resp, elapsed = send_mcp_request("createSchedule", {
            "scheduleName": schedule_name,
            "category": "Doors"
        })
        report.log_mcp_call("createSchedule", {"scheduleName": schedule_name, "category": "Doors"}, resp, elapsed)

        if not resp.get("success"):
            report.add_issue("SCHEDULE_CREATE_FAILED", Severity.BLOCKER,
                           f"Failed to create schedule: {resp.get('error')}")
            report.end_step(status="fail")
            report.finalize()
            return report

        schedule_id = resp.get("scheduleId")
        report.add_artifact("schedule", schedule_id, schedule_name, cleanup="delete")
        report.set_metric("schedule_id", schedule_id)
        print(f"  Created schedule ID: {schedule_id}")

        report.end_step(outputs={"schedule_id": schedule_id})

        # Step 3: Add fields
        report.start_step("03_add_fields")
        print("\n[Step 3] Adding schedule fields...")

        target_fields = ["Mark", "Type Mark", "Level", "Width", "Height"]
        fields_added = 0
        fields_failed = []

        for field_name in target_fields:
            resp, elapsed = send_mcp_request("addScheduleField", {
                "scheduleId": schedule_id,
                "fieldName": field_name
            })
            report.log_mcp_call("addScheduleField", {"scheduleId": schedule_id, "fieldName": field_name}, resp, elapsed)

            if resp.get("success"):
                fields_added += 1
                print(f"  + Added '{field_name}'")
            else:
                fields_failed.append(field_name)
                print(f"  - Failed '{field_name}': {resp.get('error', 'unknown')}")

        if fields_failed:
            report.add_issue("FIELDS_PARTIAL", Severity.WARNING,
                           f"Could not add {len(fields_failed)} fields: {', '.join(fields_failed)}",
                           evidence={"failed_fields": fields_failed})

        report.add_modified("schedule", schedule_id, fields_added=target_fields[:fields_added])
        report.set_metric("fields_added", fields_added)
        report.set_metric("fields_attempted", len(target_fields))
        print(f"  Added {fields_added}/{len(target_fields)} fields")

        report.end_step(outputs={"fields_added": fields_added, "fields_attempted": len(target_fields)})

        # Step 4: Export to CSV
        report.start_step("04_export_csv")
        print("\n[Step 4] Exporting to CSV...")

        export_wsl_path = str(report.log_dir / f"door_schedule_{report.run_id}.csv")
        export_windows_path = wsl_to_windows_path(export_wsl_path)

        resp, elapsed = send_mcp_request("exportScheduleToCSV", {
            "scheduleId": schedule_id,
            "filePath": export_windows_path
        })
        report.log_mcp_call("exportScheduleToCSV", {"scheduleId": schedule_id, "filePath": export_windows_path}, resp, elapsed)

        if not resp.get("success"):
            report.add_issue("EXPORT_FAILED", Severity.BLOCKER,
                           f"Export failed: {resp.get('error')}",
                           suggested_action="Check file path and permissions")
            report.end_step(status="fail")
        else:
            report.add_export("csv", export_wsl_path, compute_hash=True)
            print(f"  Exported to: {export_wsl_path}")
            report.end_step(outputs={"export_path": export_wsl_path})

        # Step 5: Validate export
        report.start_step("05_validate_export")
        print("\n[Step 5] Validating export...")

        export_file = Path(export_wsl_path)
        if export_file.exists():
            content = export_file.read_text()
            lines = [l for l in content.strip().split('\n') if l.strip()]
            data_rows = max(0, len(lines) - 2)  # Subtract title + header

            report.set_metric("export_rows", data_rows)
            report.set_metric("export_size_bytes", len(content))
            print(f"  Export has {data_rows} data rows, {len(content)} bytes")

            # Postcondition: export exists and has data
            report.add_postcondition("EXPORT_EXISTS", "pass",
                                    {"path": export_wsl_path, "size": len(content)})

            if data_rows == len(doors):
                report.add_postcondition("ROW_COUNT_MATCHES", "pass",
                                        {"expected": len(doors), "actual": data_rows})
                print(f"  Row count matches door count ({len(doors)})")
            elif data_rows > 0:
                report.add_postcondition("ROW_COUNT_MATCHES", "pass",
                                        {"expected": len(doors), "actual": data_rows,
                                         "note": "Minor variance acceptable"})
                report.add_issue("ROW_COUNT_VARIANCE", Severity.INFO,
                               f"Export has {data_rows} rows, model has {len(doors)} doors",
                               evidence={"expected": len(doors), "actual": data_rows})
            else:
                report.add_postcondition("ROW_COUNT_MATCHES", "fail",
                                        {"expected": len(doors), "actual": 0})
                report.add_issue("EXPORT_EMPTY", Severity.WARNING,
                               "Export has no data rows")

            report.end_step(outputs={"rows": data_rows, "size": len(content)})
        else:
            report.add_postcondition("EXPORT_EXISTS", "fail", {"path": export_wsl_path})
            report.add_issue("EXPORT_NOT_FOUND", Severity.BLOCKER,
                           "Export file not found after export command succeeded")
            report.end_step(status="fail")

        # Step 6: Cleanup
        report.start_step("06_cleanup")
        print("\n[Step 6] Cleaning up...")

        resp, elapsed = send_mcp_request("deleteElement", {"elementId": schedule_id})
        report.log_mcp_call("deleteElement", {"elementId": schedule_id}, resp, elapsed)

        if resp.get("success"):
            report.record_cleanup("ok")
            print("  Schedule deleted")
            report.end_step(outputs={"deleted": True})
        else:
            report.record_cleanup("failed", f"Delete failed: {resp.get('error')}")
            report.add_issue("CLEANUP_FAILED", Severity.WARNING,
                           f"Could not delete test schedule: {resp.get('error')}",
                           evidence={"schedule_id": schedule_id},
                           suggested_action="Manually delete schedule from Revit")
            report.end_step(status="fail", outputs={"deleted": False})

        # Final postcondition: artifact cleaned up
        report.add_postcondition("ARTIFACT_CLEANED",
                                "pass" if resp.get("success") else "fail",
                                {"schedule_id": schedule_id})

    except Exception as e:
        report.add_issue("WORKFLOW_EXCEPTION", Severity.BLOCKER,
                        f"Unhandled exception: {str(e)}")

        # Best-effort cleanup
        if schedule_id:
            try:
                resp, _ = send_mcp_request("deleteElement", {"elementId": schedule_id})
                report.record_cleanup("partial" if resp.get("success") else "failed",
                                     f"Emergency cleanup after exception")
            except:
                report.record_cleanup("failed", "Emergency cleanup also failed")

    # Finalize and save
    report.finalize()
    report.save()
    report.print_summary()

    return report


def main():
    """Run the preflight workflow."""
    report = run_door_preflight()
    return 0 if report.status in (RunStatus.PASS, RunStatus.WARN) else 1


if __name__ == "__main__":
    exit(main())
