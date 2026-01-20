#!/usr/bin/env python3
"""
Smoke Test F: Viewport Placement

Deterministic test for placeViewOnSheet functionality.

Workflow:
1. Create sheet (unique ZZ-TEST-* number)
2. Create drafting view (unique ZZ_DRAFT_* name)
3. Place view on sheet at fixed point
4. Verify viewport exists
5. Cleanup (delete viewport, view, sheet)

Pass criteria:
- No exceptions
- Viewport exists and references correct view + sheet
- Cleanup ok
"""

import json
import subprocess
import time
from pathlib import Path

from workflow_report import WorkflowReport, RunStatus, Severity


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

        json_start = output.find('{')
        if json_start == -1:
            return {"success": False, "error": "No JSON in response"}, elapsed_ms

        response = json.loads(output[json_start:])
        return response, elapsed_ms

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {"success": False, "error": str(e)}, elapsed_ms


def test_f_viewport_placement():
    """
    Smoke Test F: Viewport Placement

    Tests the complete flow of placing a view on a sheet.
    """
    print("\n" + "=" * 60)
    print("SMOKE TEST F: Viewport Placement")
    print("=" * 60)

    report = WorkflowReport("test_f_viewport_placement")

    # Set reasonable budgets
    report.set_budget_limits(max_steps=15, max_total_retries=3)

    # Track artifacts for cleanup
    sheet_id = None
    view_id = None
    viewport_id = None

    # Unique identifiers
    timestamp = report.run_id
    sheet_number = f"ZZ-TEST-{timestamp}"
    view_name = f"ZZ_DRAFT_{timestamp}"

    print(f"Run ID: {report.run_id}")
    print(f"Sheet: {sheet_number}")
    print(f"View: {view_name}")
    print("-" * 60)

    try:
        # Step 1: Create sheet
        if not report.start_step("01_create_sheet"):
            return report

        print("\n[Step 1] Creating sheet...")
        resp, elapsed = send_mcp_request("createSheet", {
            "sheetNumber": sheet_number,
            "sheetName": f"Viewport Test {timestamp}"
        })
        report.log_mcp_call("createSheet", {"sheetNumber": sheet_number}, resp, elapsed)

        if not resp.get("success"):
            report.add_issue("SHEET_CREATE_FAILED", Severity.BLOCKER,
                           f"Failed to create sheet: {resp.get('error')}")
            report.end_step(status="fail")
            report.finalize()
            return report

        sheet_id = resp.get("sheetId")
        report.add_artifact("sheet", sheet_id, sheet_number, cleanup="delete")
        report.set_metric("sheet_id", sheet_id)
        print(f"  Created sheet ID: {sheet_id}")
        report.end_step(outputs={"sheet_id": sheet_id})

        # Step 2: Create floor plan view (floor plans reliably place on sheets)
        if not report.start_step("02_create_floor_plan"):
            return report

        print("\n[Step 2] Creating floor plan view...")
        # First get a level to create the floor plan on
        levels_resp, _ = send_mcp_request("getLevels")
        if not levels_resp.get("success") or not levels_resp.get("levels"):
            report.add_issue("NO_LEVELS", Severity.BLOCKER, "No levels found in model")
            report.end_step(status="fail")
        else:
            level_id = levels_resp["levels"][0]["levelId"]
            resp, elapsed = send_mcp_request("createFloorPlan", {
                "levelId": level_id,
                "name": view_name
            })
            report.log_mcp_call("createFloorPlan", {"levelId": level_id, "name": view_name}, resp, elapsed)

            if not resp.get("success"):
                report.add_issue("VIEW_CREATE_FAILED", Severity.BLOCKER,
                               f"Failed to create floor plan: {resp.get('error')}")
                report.end_step(status="fail")
                # Continue to cleanup
            else:
                view_id = resp.get("viewId")
                report.add_artifact("view", view_id, view_name, cleanup="delete")
                report.set_metric("view_id", view_id)
                print(f"  Created view ID: {view_id}")
                report.end_step(outputs={"view_id": view_id})

        # Step 3: Place view on sheet
        if view_id and not report.is_stopped:
            if not report.start_step("03_place_view"):
                return report

            print("\n[Step 3] Placing view on sheet...")
            # Use fixed point in sheet coordinates (feet)
            resp, elapsed = send_mcp_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "x": 1.0,
                "y": 0.5
            })
            report.log_mcp_call("placeViewOnSheet", {
                "sheetId": sheet_id, "viewId": view_id, "x": 1.0, "y": 0.5
            }, resp, elapsed)

            if not resp.get("success"):
                report.add_issue("VIEWPORT_PLACE_FAILED", Severity.BLOCKER,
                               f"Failed to place view: {resp.get('error')}",
                               evidence={
                                   "sheetId": sheet_id,
                                   "viewId": view_id,
                                   "viewName": resp.get("viewName"),
                                   "viewType": resp.get("viewType"),
                                   "sheetNumber": resp.get("sheetNumber")
                               })
                report.end_step(status="fail")
            else:
                viewport_id = resp.get("viewportId")
                report.add_artifact("viewport", viewport_id, f"VP-{view_name}", cleanup="delete")
                report.set_metric("viewport_id", viewport_id)
                print(f"  Created viewport ID: {viewport_id}")
                report.end_step(outputs={"viewport_id": viewport_id})

        # Step 4: Verify viewport exists
        if viewport_id and not report.is_stopped:
            if not report.start_step("04_verify_viewport"):
                return report

            print("\n[Step 4] Verifying viewport...")

            # Get viewports on sheet
            resp, elapsed = send_mcp_request("getViewportsOnSheet", {
                "sheetId": sheet_id
            })
            report.log_mcp_call("getViewportsOnSheet", {"sheetId": sheet_id}, resp, elapsed)

            verified = False
            if resp.get("success"):
                viewports = resp.get("viewports", [])
                for vp in viewports:
                    vp_id = vp.get("viewportId") or vp.get("id")
                    vp_view_id = vp.get("viewId")
                    if vp_id == viewport_id or vp_view_id == view_id:
                        verified = True
                        print(f"  Viewport verified: ID={vp_id}, ViewID={vp_view_id}")
                        break

                if not verified and len(viewports) > 0:
                    # Maybe different ID format - check if any viewport references our view
                    for vp in viewports:
                        if vp.get("viewId") == view_id:
                            verified = True
                            print(f"  Viewport verified via viewId match")
                            break

            report.add_postcondition("VIEWPORT_EXISTS", "pass" if verified else "fail",
                                    {"viewport_id": viewport_id, "verified": verified})

            if verified:
                print("  VERIFIED - Viewport exists on sheet")
                report.end_step(outputs={"verified": True})
            else:
                report.add_issue("VIEWPORT_NOT_FOUND", Severity.WARNING,
                               "Viewport created but not found in sheet viewport list",
                               evidence={"viewport_id": viewport_id, "viewports": viewports if resp.get("success") else []})
                report.end_step(status="fail", outputs={"verified": False})

        # Step 5: Cleanup
        if not report.start_step("05_cleanup"):
            return report

        print("\n[Step 5] Cleaning up...")
        cleanup_ok = True
        cleanup_notes = []

        # Delete viewport first (if exists)
        if viewport_id:
            resp, elapsed = send_mcp_request("deleteElement", {"elementId": viewport_id})
            report.log_mcp_call("deleteElement", {"elementId": viewport_id}, resp, elapsed)
            if resp.get("success"):
                print(f"  Deleted viewport {viewport_id}")
                cleanup_notes.append(f"viewport {viewport_id} deleted")
            else:
                print(f"  Failed to delete viewport: {resp.get('error')}")
                cleanup_notes.append(f"viewport delete failed: {resp.get('error')}")
                cleanup_ok = False

        # Delete view
        if view_id:
            resp, elapsed = send_mcp_request("deleteElement", {"elementId": view_id})
            report.log_mcp_call("deleteElement", {"elementId": view_id}, resp, elapsed)
            if resp.get("success"):
                print(f"  Deleted view {view_id}")
                cleanup_notes.append(f"view {view_id} deleted")
            else:
                print(f"  Failed to delete view: {resp.get('error')}")
                cleanup_notes.append(f"view delete failed: {resp.get('error')}")
                cleanup_ok = False

        # Delete sheet
        if sheet_id:
            resp, elapsed = send_mcp_request("deleteElement", {"elementId": sheet_id})
            report.log_mcp_call("deleteElement", {"elementId": sheet_id}, resp, elapsed)
            if resp.get("success"):
                print(f"  Deleted sheet {sheet_id}")
                cleanup_notes.append(f"sheet {sheet_id} deleted")
            else:
                print(f"  Failed to delete sheet: {resp.get('error')}")
                cleanup_notes.append(f"sheet delete failed: {resp.get('error')}")
                cleanup_ok = False

        report.record_cleanup("ok" if cleanup_ok else "partial", "; ".join(cleanup_notes))
        report.add_postcondition("CLEANUP_STATUS", "pass" if cleanup_ok else "fail")
        report.end_step(outputs={"cleanup_ok": cleanup_ok})

    except Exception as e:
        report.add_issue("WORKFLOW_EXCEPTION", Severity.BLOCKER, f"Exception: {str(e)}")

        # Emergency cleanup
        for artifact in report.artifacts_created:
            try:
                send_mcp_request("deleteElement", {"elementId": int(artifact.id)})
            except:
                pass
        report.record_cleanup("partial", f"Emergency cleanup after exception: {e}")

    # Finalize
    report.finalize()
    report.save()
    report.print_summary()

    return report


def main():
    """Run Smoke Test F."""
    report = test_f_viewport_placement()

    # Print key results
    print("\n" + "=" * 60)
    print("TEST F RESULTS")
    print("=" * 60)
    print(f"Status:         {report.status.value}")
    print(f"Stopped Reason: {report.stopped_reason}")
    print(f"Cleanup:        {report.cleanup_status}")

    # Check if viewport was successfully placed and verified
    viewport_postcond = next((p for p in report.postconditions if p.id == "VIEWPORT_EXISTS"), None)
    if viewport_postcond:
        print(f"Viewport:       {viewport_postcond.status}")

    print("-" * 60)
    passed = report.status in (RunStatus.PASS, RunStatus.WARN)
    print(f"TEST F: {'PASS' if passed else 'FAIL'}")
    print("=" * 60)

    return 0 if passed else 1


if __name__ == "__main__":
    exit(main())
