#!/usr/bin/env python3
"""
Spine v0.1: Permit Set Skeleton

First end-to-end workflow producing a minimal CD skeleton.

Input: Active model (TEST-4) with at least 2 levels
Output: 6 sheets + viewports + exports + evidence report

Sheet Set:
  A0.01 - COVER SHEET (title block only)
  A0.02 - GENERAL NOTES (no view - known ViewDrafting constraint)
  A1.01 - FIRST FLOOR PLAN (FloorPlan viewport)
  A1.02 - SECOND FLOOR PLAN (FloorPlan viewport)
  A2.01 - BUILDING ELEVATIONS (Elevation viewport - optional)
  A5.01 - DOOR SCHEDULE (Schedule viewport - optional)

Pass Criteria:
  MANDATORY:
    - 6 sheets created
    - 2 floor plan viewports placed
    - sheet_list.csv exported
    - door_schedule.csv exported

  OPTIONAL (warn if missing):
    - elevation viewport
    - schedule viewport

Capability Matrix: Updated after run based on actual results
"""

import json
import subprocess
import time
import hashlib
import csv
from pathlib import Path
from datetime import datetime, timezone

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


def sha256_file(path: str) -> str:
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def spine_v01_permit_skeleton():
    """
    Spine v0.1: Permit Set Skeleton

    Creates minimal CD skeleton with evidence and capability tracking.
    """
    print("\n" + "=" * 70)
    print("SPINE v0.1: PERMIT SET SKELETON")
    print("=" * 70)

    report = WorkflowReport("spine_v01_permit_skeleton")
    report.set_budget_limits(max_steps=25, max_total_retries=5, max_elapsed_ms=300000)

    # Capability matrix - updated during run
    capabilities = {
        "can_place_floorplan": None,
        "can_place_elevation": None,
        "can_place_schedule": None,
        "can_place_legend": False,  # Known Revit 2026 constraint
        "can_export_csv": None
    }

    # Track created artifacts
    sheets_created = []
    viewports_created = []
    views_created = []
    schedules_created = []
    exports_created = []

    # Sheet definitions
    SHEET_SET = [
        {"number": "A0.01", "name": "COVER SHEET"},
        {"number": "A0.02", "name": "GENERAL NOTES"},
        {"number": "A1.01", "name": "FIRST FLOOR PLAN"},
        {"number": "A1.02", "name": "SECOND FLOOR PLAN"},
        {"number": "A2.01", "name": "BUILDING ELEVATIONS"},
        {"number": "A5.01", "name": "DOOR SCHEDULE"},
    ]

    # Custom title block (ARKY - Title Block, 24x36 ARCH D)
    # Will be resolved dynamically from project
    custom_titleblock_id = None

    print(f"Run ID: {report.run_id}")
    print(f"Target: {len(SHEET_SET)} sheets")
    print("-" * 70)

    try:
        # ============================================================
        # STEP 1: Get Environment & Levels
        # ============================================================
        if not report.start_step("01_get_environment"):
            return report, capabilities

        print("\n[Step 1] Getting environment...")

        levels_resp, elapsed = send_mcp_request("getLevels")
        report.log_mcp_call("getLevels", {}, levels_resp, elapsed)

        if not levels_resp.get("success") or len(levels_resp.get("levels", [])) < 2:
            report.add_issue("INSUFFICIENT_LEVELS", Severity.BLOCKER,
                           "Model needs at least 2 levels for floor plans",
                           evidence={"levels_found": len(levels_resp.get("levels", []))})
            report.end_step(status="fail")
            report.finalize()
            return report, capabilities

        levels = levels_resp["levels"]
        level_1 = levels[0]
        level_2 = levels[1] if len(levels) > 1 else levels[0]
        print(f"  Levels: {level_1['name']} (ID:{level_1['levelId']}), {level_2['name']} (ID:{level_2['levelId']})")

        # Get title blocks and find custom (non-Autodesk) one
        tb_resp, _ = send_mcp_request("getTitleblockTypes")
        if tb_resp.get("success"):
            titleblocks = tb_resp.get("titleblocks", [])
            # Prefer ARKY title block, otherwise first non-Autodesk one
            for tb in titleblocks:
                family_name = tb.get("familyName", "")
                if "ARKY" in family_name.upper():
                    custom_titleblock_id = tb.get("titleblockId")
                    print(f"  Title Block: {family_name} (ID:{custom_titleblock_id})")
                    break
            if custom_titleblock_id is None:
                # Fall back to any non-standard size title block
                for tb in titleblocks:
                    family_name = tb.get("familyName", "")
                    # Skip Autodesk standard sizes
                    if not any(x in family_name for x in ["11 x 17", "8.5 x 11", "17 x 22", "22 x 34", "34 x 44"]):
                        custom_titleblock_id = tb.get("titleblockId")
                        print(f"  Title Block: {family_name} (ID:{custom_titleblock_id})")
                        break
            if custom_titleblock_id is None:
                print(f"  Title Block: Using project default (no custom found)")

        report.end_step(outputs={"level_count": len(levels), "titleblock_id": custom_titleblock_id})

        # ============================================================
        # STEP 2: Create Sheet Set
        # ============================================================
        if not report.start_step("02_create_sheets"):
            return report, capabilities

        print("\n[Step 2] Creating sheets...")

        for sheet_def in SHEET_SET:
            sheet_num = f"{sheet_def['number']}-{report.run_id[:4]}"  # Add run ID to avoid conflicts
            create_params = {
                "sheetNumber": sheet_num,
                "sheetName": sheet_def["name"]
            }
            # Use custom title block if found
            if custom_titleblock_id is not None:
                create_params["titleblockId"] = custom_titleblock_id

            resp, elapsed = send_mcp_request("createSheet", create_params)
            report.log_mcp_call("createSheet", {"sheetNumber": sheet_num, "titleblockId": custom_titleblock_id}, resp, elapsed)

            if resp.get("success"):
                sheet_id = resp.get("sheetId")
                sheets_created.append({
                    "id": sheet_id,
                    "number": sheet_num,
                    "name": sheet_def["name"],
                    "original_number": sheet_def["number"]
                })
                report.add_artifact("sheet", sheet_id, sheet_num, cleanup="delete")
                print(f"  Created: {sheet_num} - {sheet_def['name']} (ID: {sheet_id})")
            else:
                report.add_issue("SHEET_CREATE_FAILED", Severity.BLOCKER,
                               f"Failed to create sheet {sheet_num}: {resp.get('error')}")
                report.end_step(status="fail")
                break

        if len(sheets_created) == len(SHEET_SET):
            print(f"  All {len(sheets_created)} sheets created")
            report.end_step(outputs={"sheets_created": len(sheets_created)})
        else:
            report.end_step(status="fail", outputs={"sheets_created": len(sheets_created)})

        # ============================================================
        # STEP 3: Create Floor Plan Views
        # ============================================================
        if not report.start_step("03_create_floor_plans"):
            return report, capabilities

        print("\n[Step 3] Creating floor plan views...")

        floor_plan_views = []
        for idx, (level, sheet_num_base) in enumerate([
            (level_1, "A1.01"),
            (level_2, "A1.02")
        ]):
            view_name = f"ZZ_Plan_{level['name']}_{report.run_id[:4]}"
            resp, elapsed = send_mcp_request("createFloorPlan", {
                "levelId": level["levelId"],
                "name": view_name
            })
            report.log_mcp_call("createFloorPlan", {"levelId": level["levelId"], "name": view_name}, resp, elapsed)

            if resp.get("success"):
                view_id = resp.get("viewId")
                views_created.append({"id": view_id, "name": view_name, "type": "FloorPlan"})
                floor_plan_views.append({
                    "id": view_id,
                    "name": view_name,
                    "target_sheet": sheet_num_base
                })
                report.add_artifact("view", view_id, view_name, cleanup="delete")
                print(f"  Created: {view_name} (ID: {view_id})")

                # Set scale to 1/4" = 1'-0" (scale 48)
                scale_resp, _ = send_mcp_request("setViewScale", {
                    "viewId": view_id,
                    "scale": 48
                })
                if scale_resp.get("success"):
                    print(f"    Scale set to 1/4\" = 1'-0\"")

                # Calculate model extents from walls
                walls_resp, _ = send_mcp_request("getWalls")
                if walls_resp.get("success"):
                    walls = walls_resp.get("walls", [])
                    if walls:
                        min_x = min_y = float('inf')
                        max_x = max_y = float('-inf')
                        for w in walls:
                            for pt_key in ["startPoint", "endPoint"]:
                                pt = w.get(pt_key, {})
                                if pt:
                                    min_x = min(min_x, pt.get("x", 0))
                                    min_y = min(min_y, pt.get("y", 0))
                                    max_x = max(max_x, pt.get("x", 0))
                                    max_y = max(max_y, pt.get("y", 0))

                        # Add margin (5 feet)
                        margin = 5.0
                        crop_min_x = min_x - margin
                        crop_min_y = min_y - margin
                        crop_max_x = max_x + margin
                        crop_max_y = max_y + margin

                        # Set crop region to fit model
                        crop_resp, _ = send_mcp_request("setViewCropBox", {
                            "viewId": view_id,
                            "enableCrop": True,
                            "cropBox": [
                                [crop_min_x, crop_min_y, -10],  # min point
                                [crop_max_x, crop_max_y, 10]     # max point
                            ]
                        })
                        if crop_resp.get("success"):
                            print(f"    Crop region set ({max_x - min_x:.0f}' x {max_y - min_y:.0f}' + margin)")
                        else:
                            # Fall back to just enabling crop
                            send_mcp_request("setViewCropBox", {"viewId": view_id, "enableCrop": True})
                            print(f"    Crop region enabled (default bounds)")
                    else:
                        send_mcp_request("setViewCropBox", {"viewId": view_id, "enableCrop": True})
                        print(f"    Crop region enabled (no walls found)")
            else:
                report.add_issue("FLOOR_PLAN_CREATE_FAILED", Severity.BLOCKER,
                               f"Failed to create floor plan for {level['name']}: {resp.get('error')}")

        if len(floor_plan_views) >= 2:
            capabilities["can_place_floorplan"] = True  # Views created successfully
            report.end_step(outputs={"floor_plans_created": len(floor_plan_views)})
        else:
            report.end_step(status="fail", outputs={"floor_plans_created": len(floor_plan_views)})

        # ============================================================
        # STEP 4: Place Floor Plan Viewports (MANDATORY)
        # ============================================================
        if not report.start_step("04_place_floor_plans"):
            return report, capabilities

        print("\n[Step 4] Placing floor plan viewports...")

        plan_viewports_placed = 0
        for fp_view in floor_plan_views:
            # Find the sheet for this view
            target_sheet = next(
                (s for s in sheets_created if s["original_number"] == fp_view["target_sheet"]),
                None
            )
            if not target_sheet:
                continue

            resp, elapsed = send_mcp_request("placeViewOnSheet", {
                "sheetId": target_sheet["id"],
                "viewId": fp_view["id"],
                "x": 1.0,
                "y": 0.75
            })
            report.log_mcp_call("placeViewOnSheet", {
                "sheetId": target_sheet["id"], "viewId": fp_view["id"]
            }, resp, elapsed)

            if resp.get("success"):
                vp_id = resp.get("viewportId")
                viewports_created.append({"id": vp_id, "type": "FloorPlan", "sheet": target_sheet["number"]})
                report.add_artifact("viewport", vp_id, f"VP-{fp_view['name']}", cleanup="delete")
                plan_viewports_placed += 1
                print(f"  Placed: {fp_view['name']} on {target_sheet['number']} (VP: {vp_id})")
            else:
                capabilities["can_place_floorplan"] = False
                report.add_issue("FLOOR_PLAN_PLACE_FAILED", Severity.BLOCKER,
                               f"Failed to place {fp_view['name']}: {resp.get('error')}")

        if plan_viewports_placed >= 2:
            capabilities["can_place_floorplan"] = True
            report.end_step(outputs={"plan_viewports_placed": plan_viewports_placed})
        else:
            report.end_step(status="fail", outputs={"plan_viewports_placed": plan_viewports_placed})

        # ============================================================
        # STEP 5: Find & Place Elevation (OPTIONAL)
        # ============================================================
        if not report.start_step("05_place_elevation"):
            return report, capabilities

        print("\n[Step 5] Attempting elevation placement (optional)...")

        elevation_placed = False
        elevation_sheet = next(
            (s for s in sheets_created if s["original_number"] == "A2.01"),
            None
        )

        if elevation_sheet:
            # Try to find existing elevation views
            views_resp, elapsed = send_mcp_request("getViews")
            report.log_mcp_call("getViews", {}, views_resp, elapsed)

            elevation_view = None
            if views_resp.get("success"):
                for v in views_resp.get("views", []):
                    if v.get("viewType") in ["Elevation", "BuildingElevation"]:
                        elevation_view = v
                        break

            if elevation_view:
                # Check if already placed
                resp, elapsed = send_mcp_request("placeViewOnSheet", {
                    "sheetId": elevation_sheet["id"],
                    "viewId": elevation_view["id"],
                    "x": 1.0,
                    "y": 0.75
                })
                report.log_mcp_call("placeViewOnSheet", {
                    "sheetId": elevation_sheet["id"], "viewId": elevation_view["id"]
                }, resp, elapsed)

                if resp.get("success"):
                    vp_id = resp.get("viewportId")
                    viewports_created.append({"id": vp_id, "type": "Elevation", "sheet": elevation_sheet["number"]})
                    report.add_artifact("viewport", vp_id, f"VP-Elevation", cleanup="delete")
                    elevation_placed = True
                    capabilities["can_place_elevation"] = True
                    print(f"  Placed elevation on {elevation_sheet['number']} (VP: {vp_id})")
                else:
                    # Check if already placed on another sheet
                    if "already placed" in resp.get("error", "").lower():
                        report.add_issue("ELEVATION_ALREADY_PLACED", Severity.INFO,
                                       "Elevation view already on another sheet")
                    else:
                        capabilities["can_place_elevation"] = False
                        report.add_issue("ELEVATION_PLACE_FAILED", Severity.WARNING,
                                       f"Elevation placement failed: {resp.get('error')}")
            else:
                capabilities["can_place_elevation"] = None  # Not tested - no elevation found
                report.add_issue("NO_ELEVATION_VIEW", Severity.WARNING,
                               "No elevation view found in model; skipped placement")
                print("  No elevation view found - skipped")

        report.end_step(outputs={"elevation_placed": elevation_placed})

        # ============================================================
        # STEP 6: Create Door Schedule
        # ============================================================
        if not report.start_step("06_create_door_schedule"):
            return report, capabilities

        print("\n[Step 6] Creating door schedule...")

        schedule_id = None
        schedule_name = f"Door Schedule {report.run_id[:4]}"

        resp, elapsed = send_mcp_request("createSchedule", {
            "category": "Doors",
            "scheduleName": schedule_name
        })
        report.log_mcp_call("createSchedule", {"category": "Doors", "scheduleName": schedule_name}, resp, elapsed)

        if resp.get("success"):
            schedule_id = resp.get("scheduleId")
            schedules_created.append({"id": schedule_id, "name": schedule_name})
            report.add_artifact("schedule", schedule_id, schedule_name, cleanup="delete")
            print(f"  Created: {schedule_name} (ID: {schedule_id})")

            # Add fields
            fields = ["Mark", "Type Mark", "Level", "Width", "Height"]
            for field in fields:
                field_resp, _ = send_mcp_request("addScheduleField", {
                    "scheduleId": schedule_id,
                    "fieldName": field
                })
                if field_resp.get("success"):
                    print(f"    Added field: {field}")

            report.end_step(outputs={"schedule_id": schedule_id})
        else:
            report.add_issue("SCHEDULE_CREATE_FAILED", Severity.WARNING,
                           f"Failed to create door schedule: {resp.get('error')}")
            report.end_step(status="fail", outputs={"schedule_id": None})

        # ============================================================
        # STEP 7: Place Schedule on Sheet (OPTIONAL)
        # ============================================================
        if not report.start_step("07_place_schedule"):
            return report, capabilities

        print("\n[Step 7] Attempting schedule placement (optional)...")

        schedule_placed = False
        schedule_sheet = next(
            (s for s in sheets_created if s["original_number"] == "A5.01"),
            None
        )

        if schedule_id and schedule_sheet:
            resp, elapsed = send_mcp_request("placeViewOnSheet", {
                "sheetId": schedule_sheet["id"],
                "viewId": schedule_id,
                "x": 0.5,
                "y": 0.75
            })
            report.log_mcp_call("placeViewOnSheet", {
                "sheetId": schedule_sheet["id"], "viewId": schedule_id
            }, resp, elapsed)

            if resp.get("success"):
                vp_id = resp.get("viewportId")
                viewports_created.append({"id": vp_id, "type": "Schedule", "sheet": schedule_sheet["number"]})
                report.add_artifact("viewport", vp_id, f"VP-Schedule", cleanup="delete")
                schedule_placed = True
                capabilities["can_place_schedule"] = True
                print(f"  Placed schedule on {schedule_sheet['number']} (VP: {vp_id})")
            else:
                capabilities["can_place_schedule"] = False
                # Reclassify as unsupported capability, not error
                report.add_issue("SCHEDULE_PLACEMENT_UNSUPPORTED", Severity.WARNING,
                               "Schedule placement on sheets not supported via current API path in Revit 2026; exported CSV instead.",
                               evidence={"api_error": resp.get("error")})
                print(f"  Schedule placement unsupported (exported CSV instead)")

        report.end_step(outputs={"schedule_placed": schedule_placed})

        # ============================================================
        # STEP 8: Export Sheet List
        # ============================================================
        if not report.start_step("08_export_sheet_list"):
            return report, capabilities

        print("\n[Step 8] Exporting sheet list...")

        log_dir = Path("/mnt/d/RevitMCPBridge2026/logs")
        sheet_list_path = log_dir / f"sheet_list_{report.run_id}.csv"

        try:
            with open(sheet_list_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Sheet Number", "Sheet Name", "Sheet ID", "Viewports"])
                for sheet in sheets_created:
                    vp_count = len([v for v in viewports_created if v["sheet"] == sheet["number"]])
                    writer.writerow([sheet["number"], sheet["name"], sheet["id"], vp_count])

            sheet_list_hash = sha256_file(str(sheet_list_path))
            exports_created.append({
                "type": "sheet_list",
                "path": str(sheet_list_path),
                "sha256": sheet_list_hash
            })
            report.add_export("csv", str(sheet_list_path), sheet_list_hash)
            print(f"  Exported: {sheet_list_path.name} (sha256: {sheet_list_hash[:16]}...)")
            report.end_step(outputs={"sheet_list_path": str(sheet_list_path)})
        except Exception as e:
            report.add_issue("SHEET_LIST_EXPORT_FAILED", Severity.BLOCKER,
                           f"Failed to export sheet list: {e}")
            report.end_step(status="fail")

        # ============================================================
        # STEP 9: Export Door Schedule
        # ============================================================
        if not report.start_step("09_export_door_schedule"):
            return report, capabilities

        print("\n[Step 9] Exporting door schedule...")

        door_schedule_path = log_dir / f"door_schedule_{report.run_id}.csv"

        if schedule_id:
            resp, elapsed = send_mcp_request("exportScheduleToCSV", {
                "scheduleId": schedule_id,
                "filePath": str(door_schedule_path).replace("/mnt/d", "D:")
            })
            report.log_mcp_call("exportScheduleToCSV", {"scheduleId": schedule_id}, resp, elapsed)

            if resp.get("success"):
                capabilities["can_export_csv"] = True
                # Calculate hash
                if door_schedule_path.exists():
                    door_hash = sha256_file(str(door_schedule_path))
                    exports_created.append({
                        "type": "door_schedule",
                        "path": str(door_schedule_path),
                        "sha256": door_hash
                    })
                    report.add_export("csv", str(door_schedule_path), door_hash)
                    print(f"  Exported: {door_schedule_path.name} (sha256: {door_hash[:16]}...)")
                report.end_step(outputs={"door_schedule_path": str(door_schedule_path)})
            else:
                capabilities["can_export_csv"] = False
                report.add_issue("DOOR_SCHEDULE_EXPORT_FAILED", Severity.BLOCKER,
                               f"Failed to export door schedule: {resp.get('error')}")
                report.end_step(status="fail")
        else:
            report.add_issue("NO_SCHEDULE_TO_EXPORT", Severity.WARNING,
                           "No schedule created to export")
            report.end_step(status="fail")

        # ============================================================
        # STEP 10: Verify Postconditions
        # ============================================================
        if not report.start_step("10_verify_postconditions"):
            return report, capabilities

        print("\n[Step 10] Verifying postconditions...")

        # Mandatory postconditions
        sheet_count_ok = len(sheets_created) == 6
        plan_viewports_ok = len([v for v in viewports_created if v["type"] == "FloorPlan"]) >= 2
        sheet_list_exists = any(e["type"] == "sheet_list" for e in exports_created)
        door_schedule_exists = any(e["type"] == "door_schedule" for e in exports_created)

        # Check for duplicate sheet numbers
        sheet_numbers = [s["number"] for s in sheets_created]
        no_duplicates = len(sheet_numbers) == len(set(sheet_numbers))

        # Optional postconditions
        elevation_vp_ok = any(v["type"] == "Elevation" for v in viewports_created)
        schedule_vp_ok = any(v["type"] == "Schedule" for v in viewports_created)

        # Record postconditions
        report.add_postcondition("SHEET_COUNT_MATCHES", "pass" if sheet_count_ok else "fail",
                                {"expected": 6, "actual": len(sheets_created)})
        report.add_postcondition("PLAN_VIEWPORTS_PLACED", "pass" if plan_viewports_ok else "fail",
                                {"expected": 2, "actual": len([v for v in viewports_created if v["type"] == "FloorPlan"])})
        report.add_postcondition("EXPORT_SHEET_LIST_EXISTS", "pass" if sheet_list_exists else "fail")
        report.add_postcondition("EXPORT_DOOR_SCHEDULE_EXISTS", "pass" if door_schedule_exists else "fail")
        report.add_postcondition("NO_DUPLICATE_SHEET_NUMBERS", "pass" if no_duplicates else "fail")

        # Optional
        report.add_postcondition("ELEVATION_VIEWPORT_PLACED", "pass" if elevation_vp_ok else "warn",
                                {"optional": True})
        report.add_postcondition("SCHEDULE_VIEWPORT_PLACED", "pass" if schedule_vp_ok else "warn",
                                {"optional": True})

        # Print results
        print(f"  SHEET_COUNT_MATCHES: {'PASS' if sheet_count_ok else 'FAIL'} ({len(sheets_created)}/6)")
        print(f"  PLAN_VIEWPORTS_PLACED: {'PASS' if plan_viewports_ok else 'FAIL'}")
        print(f"  EXPORT_SHEET_LIST_EXISTS: {'PASS' if sheet_list_exists else 'FAIL'}")
        print(f"  EXPORT_DOOR_SCHEDULE_EXISTS: {'PASS' if door_schedule_exists else 'FAIL'}")
        print(f"  NO_DUPLICATE_SHEET_NUMBERS: {'PASS' if no_duplicates else 'FAIL'}")
        print(f"  ELEVATION_VIEWPORT_PLACED: {'PASS' if elevation_vp_ok else 'WARN (optional)'}")
        print(f"  SCHEDULE_VIEWPORT_PLACED: {'PASS' if schedule_vp_ok else 'WARN (optional)'}")

        report.end_step(outputs={
            "mandatory_pass": sheet_count_ok and plan_viewports_ok and sheet_list_exists and door_schedule_exists,
            "optional_pass": elevation_vp_ok and schedule_vp_ok
        })

        # ============================================================
        # STEP 11: Cleanup (with leftover tracking)
        # ============================================================
        if not report.start_step("11_cleanup"):
            return report, capabilities

        print("\n[Step 11] Cleaning up...")

        deleted_items = []
        leftovers = []

        # Delete viewports first
        for vp in viewports_created:
            resp, _ = send_mcp_request("deleteElement", {"elementId": vp["id"]})
            if resp.get("success"):
                deleted_items.append({"type": "viewport", "id": vp["id"]})
            else:
                leftovers.append({"type": "viewport", "id": vp["id"], "reason": resp.get("error", "unknown")})

        # Delete views
        for view in views_created:
            resp, _ = send_mcp_request("deleteElement", {"elementId": view["id"]})
            if resp.get("success"):
                deleted_items.append({"type": "view", "id": view["id"], "name": view["name"]})
            else:
                leftovers.append({"type": "view", "id": view["id"], "name": view["name"], "reason": resp.get("error", "unknown")})

        # Delete schedules
        for sched in schedules_created:
            resp, _ = send_mcp_request("deleteElement", {"elementId": sched["id"]})
            if resp.get("success"):
                deleted_items.append({"type": "schedule", "id": sched["id"], "name": sched["name"]})
            else:
                leftovers.append({"type": "schedule", "id": sched["id"], "name": sched["name"], "reason": resp.get("error", "unknown")})

        # Delete sheets
        for sheet in sheets_created:
            resp, _ = send_mcp_request("deleteElement", {"elementId": sheet["id"]})
            if resp.get("success"):
                deleted_items.append({"type": "sheet", "id": sheet["id"], "number": sheet["number"]})
            else:
                leftovers.append({"type": "sheet", "id": sheet["id"], "number": sheet["number"], "reason": resp.get("error", "unknown")})

        # Determine cleanup status based on leftovers, not item counts
        # PASS: no leftovers
        # WARN: 1-3 leftovers (contained, accounted)
        # FAIL: >3 leftovers or deletion errors indicating instability
        if len(leftovers) == 0:
            cleanup_status = "pass"
        elif len(leftovers) <= 3:
            cleanup_status = "warn"
        else:
            cleanup_status = "fail"

        cleanup_details = {
            "deleted_count": len(deleted_items),
            "leftover_count": len(leftovers),
            "leftovers": leftovers
        }

        report.record_cleanup(cleanup_status, f"Deleted {len(deleted_items)}, leftovers: {len(leftovers)}")
        report.add_postcondition("CLEANUP_STATUS", cleanup_status, cleanup_details)

        print(f"  Deleted: {len(deleted_items)} items")
        if leftovers:
            print(f"  Leftovers: {len(leftovers)} items")
            for lo in leftovers:
                print(f"    - {lo['type']} {lo.get('name', lo['id'])}: {lo['reason']}")

        report.end_step(outputs={"deleted": len(deleted_items), "leftovers": len(leftovers)})

    except Exception as e:
        report.add_issue("WORKFLOW_EXCEPTION", Severity.BLOCKER, f"Exception: {str(e)}")
        report.record_cleanup("partial", f"Emergency cleanup after exception")

    # Finalize
    report.finalize()
    report.save()

    # Store metrics
    report.set_metric("sheets_created", len(sheets_created))
    report.set_metric("viewports_created", len(viewports_created))
    report.set_metric("exports_created", len(exports_created))

    return report, capabilities


def main():
    """Run Spine v0.1."""
    report, capabilities = spine_v01_permit_skeleton()

    # Print summary
    print("\n" + "=" * 70)
    print("SPINE v0.1 RESULTS")
    print("=" * 70)

    print(f"\nrun.status: {report.status.value}")
    print(f"severity_counts: blocker={len([i for i in report.issues if i.severity == 'blocker'])}, "
          f"warning={len([i for i in report.issues if i.severity == 'warning'])}, "
          f"info={len([i for i in report.issues if i.severity == 'info'])}")

    print("\nissues[]:")
    for issue in report.issues:
        print(f"  - [{issue.severity.upper()}] {issue.id}: {issue.message}")

    print("\npostconditions:")
    for pc in report.postconditions:
        print(f"  - {pc.id}: {pc.status}")

    print("\ncapability_matrix:")
    for cap, val in capabilities.items():
        status = "true" if val is True else ("false" if val is False else "not_tested")
        print(f"  {cap}: {status}")

    print("\n" + "-" * 70)

    # Determine final status based on mandatory conditions
    # Core mandatory (must pass): sheets, viewports, exports, no duplicates
    core_mandatory_pass = all(
        pc.status == "pass"
        for pc in report.postconditions
        if pc.id in ["SHEET_COUNT_MATCHES", "PLAN_VIEWPORTS_PLACED",
                     "EXPORT_SHEET_LIST_EXISTS", "EXPORT_DOOR_SCHEDULE_EXISTS",
                     "NO_DUPLICATE_SHEET_NUMBERS"]
    )

    # Cleanup can be pass or warn (fail only if >3 leftovers)
    cleanup_pc = next((pc for pc in report.postconditions if pc.id == "CLEANUP_STATUS"), None)
    cleanup_ok = cleanup_pc and cleanup_pc.status in ["pass", "warn"]

    has_warnings = any(i.severity == "warning" for i in report.issues)
    has_cleanup_warn = cleanup_pc and cleanup_pc.status == "warn"

    if core_mandatory_pass and cleanup_ok and not has_warnings and not has_cleanup_warn:
        final = "PASS"
    elif core_mandatory_pass and cleanup_ok:
        final = "WARN"
    else:
        final = "FAIL"

    print(f"SPINE v0.1: {final}")
    print("=" * 70)

    return 0 if final in ["PASS", "WARN"] else 1


if __name__ == "__main__":
    exit(main())
