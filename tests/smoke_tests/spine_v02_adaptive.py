#!/usr/bin/env python3
"""
Spine v0.2: Adaptive Permit Skeleton

Config-driven workflow that adapts to project context.

Inputs:
  - standards/<pack>.json (rules + defaults) [v1 format]
  - template_packs/resolved/<pack>.json [v2 format, auto-adapted]
  - profiles/<project>.profile.json (what's in the model)
  - CLI overrides (optional)

Outputs:
  - WorkflowReport (same schema as v0.1)
  - Exports (sheet_list.csv, door_schedule.csv)

Architecture:
  1. resolve(profile, standards) -> ResolvedConfig
  2. build_plan(resolved) -> list[Task]
  3. execute_task(task, ctx, report) -> success/fail
  4. verify_postconditions() -> pass/warn/fail

Usage:
  # Old format (v1 standards)
  python spine_v02_adaptive.py --standards ARKY_SFH_v1 [--profile profiles/TEST-4.profile.json]

  # New format (v2 template packs)
  python spine_v02_adaptive.py --pack resolved/resolved_multifamily.json [--profile ...]

  # Auto-resolve from sector
  python spine_v02_adaptive.py --sector multifamily [--firm ARKY] [--profile ...]
"""

import json
import subprocess
import time
import hashlib
import csv
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

from workflow_report import WorkflowReport, RunStatus, Severity


# =============================================================================
# MCP Communication
# =============================================================================

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

        return json.loads(output[json_start:]), elapsed_ms

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {"success": False, "error": str(e)}, elapsed_ms


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Task:
    """A single executable task in the workflow."""
    task_id: str
    task_type: str
    required: bool
    inputs: Dict[str, Any]
    prereqs: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ResolvedConfig:
    """Merged configuration from profile + standards."""
    # Identity
    run_id: str
    standards_pack: str
    project_type: str

    # Title Block
    titleblock_id: int
    titleblock_name: str

    # Sheet Size
    sheet_width: float
    sheet_height: float

    # Levels (role -> level info)
    level_map: Dict[str, Dict]  # {"L1": {"id": 30, "name": "Level 1"}, ...}

    # Scales by view type
    scales: Dict[str, int]

    # Crop settings
    crop_enabled: bool
    crop_margin_feet: float
    model_extents: Dict[str, float]  # min_x, min_y, max_x, max_y

    # Sheet set definition
    sheet_set: List[Dict]

    # Capabilities (what's supported at runtime)
    capabilities: Dict[str, Any]

    # Naming
    view_prefix: str
    sheet_suffix: str


# =============================================================================
# Step 1: Resolve Config
# =============================================================================

def resolve(profile: dict, standards: dict, run_id: str) -> ResolvedConfig:
    """
    Merge profile + standards into a single resolved config.
    Profile provides "what exists", standards provide "what we want".
    """

    # Title block: prefer profile's selected, fall back to standards preference
    tb_selected = profile.get("titleBlocks", {}).get("selected", {})
    titleblock_id = tb_selected.get("id", 0)
    titleblock_name = tb_selected.get("name", "Unknown")

    # Sheet size from standards
    sheet_size = standards.get("sheetSize", {})
    sheet_width = sheet_size.get("width", 36)
    sheet_height = sheet_size.get("height", 24)

    # Build level map from profile
    level_map = {}
    for level in profile.get("levels", {}).get("detected", []):
        role = level.get("mappedRole")
        if role:
            # Normalize role names (level1 -> L1)
            normalized = role.upper().replace("LEVEL", "L")
            level_map[normalized] = {
                "id": level.get("id"),
                "name": level.get("name"),
                "elevation": level.get("elevation", 0)
            }
        else:
            # Unmapped levels get generic names
            name = level.get("name", "")
            level_map[name] = {
                "id": level.get("id"),
                "name": name,
                "elevation": level.get("elevation", 0)
            }

    # Ensure L1 and L2 exist (map by elevation order if not already mapped)
    if "L1" not in level_map and "L2" not in level_map:
        levels_by_elev = sorted(
            profile.get("levels", {}).get("detected", []),
            key=lambda x: x.get("elevation", 0)
        )
        if len(levels_by_elev) >= 1:
            level_map["L1"] = {
                "id": levels_by_elev[0].get("id"),
                "name": levels_by_elev[0].get("name"),
                "elevation": levels_by_elev[0].get("elevation", 0)
            }
        if len(levels_by_elev) >= 2:
            level_map["L2"] = {
                "id": levels_by_elev[1].get("id"),
                "name": levels_by_elev[1].get("name"),
                "elevation": levels_by_elev[1].get("elevation", 0)
            }

    # Scales from standards
    scales = standards.get("scales", {
        "floorPlan": 48,
        "elevation": 48,
        "section": 48,
        "detail": 12
    })

    # Crop settings from standards
    crop_strategy = standards.get("cropStrategy", {})
    crop_enabled = crop_strategy.get("enabled", True)
    crop_margin = crop_strategy.get("marginFeet", 5.0)

    # Model extents from profile
    extents = profile.get("modelExtents", {})
    model_extents = {
        "min_x": extents.get("min", {}).get("x", 0),
        "min_y": extents.get("min", {}).get("y", 0),
        "max_x": extents.get("max", {}).get("x", 0),
        "max_y": extents.get("max", {}).get("y", 0)
    }

    # Sheet set from standards
    sheet_set = standards.get("sheetSet", {}).get("permitSkeleton", [])

    # Capabilities from profile + known constraints
    capabilities = profile.get("capabilityMatrix", {})
    # Override with known Revit 2026 constraints
    capabilities["can_place_schedule"] = False
    capabilities["can_place_legend"] = False

    # Naming from standards
    naming = standards.get("naming", {})
    view_prefix = naming.get("viewPrefix", "ZZ_")
    sheet_suffix = naming.get("sheetNumberSuffix", "-{run_id:4}").format(run_id=run_id[:4])

    return ResolvedConfig(
        run_id=run_id,
        standards_pack=standards.get("name", "unknown"),
        project_type=standards.get("projectType", "unknown"),
        titleblock_id=titleblock_id,
        titleblock_name=titleblock_name,
        sheet_width=sheet_width,
        sheet_height=sheet_height,
        level_map=level_map,
        scales=scales,
        crop_enabled=crop_enabled,
        crop_margin_feet=crop_margin,
        model_extents=model_extents,
        sheet_set=sheet_set,
        capabilities=capabilities,
        view_prefix=view_prefix,
        sheet_suffix=sheet_suffix
    )


# =============================================================================
# Step 2: Build Plan
# =============================================================================

def build_plan(resolved: ResolvedConfig) -> List[Task]:
    """
    Generate task list from resolved config.
    Tasks are ordered by dependency.
    Handles per-unit sheets (duplex/townhouse) by:
    - Reusing floor plan views across unit sheets for same level
    - Creating unique schedules per unit
    """
    tasks = []
    sheet_ids = {}  # Track sheet numbers -> task_ids for prereqs
    created_views = {}  # Track level -> view task_id to avoid duplicates
    created_schedules = {}  # Track (category, unit) -> schedule task_id

    # Phase 1: Create sheets
    for sheet_def in resolved.sheet_set:
        sheet_num = sheet_def["number"] + resolved.sheet_suffix
        task_id = f"create_sheet_{sheet_def['number'].replace('.', '_')}"

        tasks.append(Task(
            task_id=task_id,
            task_type="create_sheet",
            required=sheet_def.get("required", True),
            inputs={
                "sheetNumber": sheet_num,
                "sheetName": sheet_def["name"],
                "titleblockId": resolved.titleblock_id
            },
            postconditions=["SHEET_EXISTS"],
            description=f"Create sheet {sheet_num} - {sheet_def['name']}"
        ))
        sheet_ids[sheet_def["number"]] = task_id

    # Phase 2: Create views and place on sheets
    for sheet_def in resolved.sheet_set:
        content_type = sheet_def.get("content") or sheet_def.get("viewType")
        if not content_type or content_type == "titleblock_only":
            continue

        level_role = sheet_def.get("levelRole") or sheet_def.get("level")
        sheet_num = sheet_def["number"]
        sheet_task_id = sheet_ids.get(sheet_num)
        unit = sheet_def.get("unit")  # e.g., "A" or "B" for duplex

        if content_type in ("floorPlan", "FloorPlan"):
            # Resolve level
            level_key = f"L{level_role}" if isinstance(level_role, int) else str(level_role).upper()
            level_info = resolved.level_map.get(level_key)

            if not level_info:
                # Level not found - skip with warning (task will be marked optional)
                continue

            # View key includes unit if specified (Revit requires unique views per sheet)
            # For duplex: L1_A, L1_B create separate views; for SFH: just L1
            view_key = f"{level_key}_{unit}" if unit else level_key
            view_name = f"{resolved.view_prefix}Plan_{view_key}_{resolved.run_id[:4]}"

            # Check if we already created a view for this level+unit combo
            if view_key not in created_views:
                # Task: Create floor plan view
                create_view_task = Task(
                    task_id=f"create_floorplan_{view_key}",
                    task_type="create_floorplan",
                    required=sheet_def.get("required", True),
                    inputs={
                        "levelId": level_info["id"],
                        "name": view_name,
                        "scale": resolved.scales.get("floorPlan", 48),
                        "cropEnabled": resolved.crop_enabled,
                        "cropMargin": resolved.crop_margin_feet,
                        "modelExtents": resolved.model_extents,
                        "unit": unit  # Pass unit for future scope box support
                    },
                    prereqs=[],
                    postconditions=["VIEW_EXISTS"],
                    description=f"Create floor plan for {view_key}"
                )
                tasks.append(create_view_task)
                created_views[view_key] = {
                    "task_id": create_view_task.task_id,
                    "view_name": view_name
                }

            view_info = created_views[view_key]

            # Task: Place viewport on sheet
            place_task_id = f"place_floorplan_{view_key}"
            place_task = Task(
                task_id=place_task_id,
                task_type="place_viewport",
                required=sheet_def.get("required", True),
                inputs={
                    "sheetNumber": sheet_num + resolved.sheet_suffix,
                    "viewName": view_info["view_name"],
                    "x": 1.0,
                    "y": 0.5
                },
                prereqs=[sheet_task_id, view_info["task_id"]],
                postconditions=["VIEWPORT_PLACED"],
                description=f"Place {view_key} plan on {sheet_num}"
            )
            tasks.append(place_task)

        elif content_type in ("doorSchedule", "Schedule") and sheet_def.get("category") == "Doors":
            # For per-unit schedules, include unit in name; otherwise shared schedule
            sched_key = ("Doors", unit)

            if sched_key not in created_schedules:
                # Unique schedule name per unit (or shared if no unit)
                if unit:
                    schedule_name = f"Door Schedule {unit} {resolved.run_id[:4]}"
                    task_id_suffix = f"_{unit}"
                else:
                    schedule_name = f"Door Schedule {resolved.run_id[:4]}"
                    task_id_suffix = ""

                # Task: Create door schedule
                create_sched_task = Task(
                    task_id=f"create_door_schedule{task_id_suffix}",
                    task_type="create_schedule",
                    required=True,  # Schedule creation is required
                    inputs={
                        "category": "Doors",
                        "name": schedule_name,
                        "fields": ["Mark", "Type Mark", "Level", "Width", "Height"],
                        "unit": unit  # Pass unit for filtering if supported
                    },
                    prereqs=[],
                    postconditions=["SCHEDULE_EXISTS"],
                    description=f"Create door schedule{f' for Unit {unit}' if unit else ''}"
                )
                tasks.append(create_sched_task)
                created_schedules[sched_key] = {
                    "task_id": create_sched_task.task_id,
                    "schedule_name": schedule_name
                }

            sched_info = created_schedules[sched_key]

            # Task: Place schedule on sheet (optional - known to fail in Revit 2026)
            if resolved.capabilities.get("can_place_schedule", False):
                place_sched_task = Task(
                    task_id=f"place_door_schedule{f'_{unit}' if unit else ''}",
                    task_type="place_schedule",
                    required=False,  # Optional due to Revit 2026 constraint
                    inputs={
                        "sheetNumber": sheet_num + resolved.sheet_suffix,
                        "scheduleName": sched_info["schedule_name"],
                        "x": 1.5,
                        "y": 1.0
                    },
                    prereqs=[sheet_task_id, sched_info["task_id"]],
                    postconditions=["SCHEDULE_VIEWPORT_PLACED"],
                    description=f"Place door schedule on {sheet_num}"
                )
                tasks.append(place_sched_task)

        elif content_type in ("elevation", "Elevation"):
            # Task: Place existing elevation (if available)
            tasks.append(Task(
                task_id="place_elevation",
                task_type="place_elevation",
                required=False,  # Optional
                inputs={
                    "sheetNumber": sheet_num + resolved.sheet_suffix,
                    "x": 1.0,
                    "y": 0.5
                },
                prereqs=[sheet_task_id],
                postconditions=["ELEVATION_VIEWPORT_PLACED"],
                description=f"Place elevation on {sheet_num}"
            ))

    # Phase 3: Exports
    tasks.append(Task(
        task_id="export_sheet_list",
        task_type="export_csv",
        required=True,
        inputs={"exportType": "sheet_list"},
        prereqs=[],  # Can run after sheets created
        postconditions=["EXPORT_SHEET_LIST_EXISTS"],
        description="Export sheet list CSV"
    ))

    # Export door schedule(s) - prereqs depend on which schedules were created
    schedule_prereqs = [info["task_id"] for info in created_schedules.values()]
    if not schedule_prereqs:
        schedule_prereqs = []  # No schedules created (shouldn't happen)

    tasks.append(Task(
        task_id="export_door_schedule",
        task_type="export_csv",
        required=True,
        inputs={"exportType": "door_schedule"},
        prereqs=schedule_prereqs,
        postconditions=["EXPORT_DOOR_SCHEDULE_EXISTS"],
        description="Export door schedule CSV"
    ))

    return tasks


# =============================================================================
# Step 3: Task Executors
# =============================================================================

class ExecutionContext:
    """Shared context for task execution."""

    def __init__(self, resolved: ResolvedConfig, report: WorkflowReport):
        self.resolved = resolved
        self.report = report
        self.artifacts = {}  # task_id -> artifact info
        self.sheets = {}  # sheet_number -> sheet_id
        self.views = {}  # view_name -> view_id
        self.schedules = {}  # schedule_name -> schedule_id
        self.viewports = []  # list of viewport_ids


def execute_task(task: Task, ctx: ExecutionContext) -> bool:
    """
    Execute a single task. Returns True on success.
    Deterministic - does one thing, records result.
    """
    report = ctx.report
    resolved = ctx.resolved

    if task.task_type == "create_sheet":
        resp, elapsed = send_mcp_request("createSheet", task.inputs)
        report.log_mcp_call("createSheet", task.inputs, resp, elapsed)

        if resp.get("success"):
            sheet_id = resp.get("sheetId")
            ctx.sheets[task.inputs["sheetNumber"]] = sheet_id
            ctx.artifacts[task.task_id] = {"type": "sheet", "id": sheet_id}
            report.add_artifact("sheet", sheet_id, task.inputs["sheetNumber"], cleanup="delete")
            print(f"    Created: {task.inputs['sheetNumber']} (ID: {sheet_id})")
            return True
        else:
            print(f"    FAILED: {resp.get('error')}")
            return False

    elif task.task_type == "create_floorplan":
        # Create the view
        resp, elapsed = send_mcp_request("createFloorPlan", {
            "levelId": task.inputs["levelId"],
            "name": task.inputs["name"]
        })
        report.log_mcp_call("createFloorPlan", task.inputs, resp, elapsed)

        if not resp.get("success"):
            print(f"    FAILED: {resp.get('error')}")
            return False

        view_id = resp.get("viewId")
        ctx.views[task.inputs["name"]] = view_id
        ctx.artifacts[task.task_id] = {"type": "view", "id": view_id}
        report.add_artifact("view", view_id, task.inputs["name"], cleanup="delete")
        print(f"    Created: {task.inputs['name']} (ID: {view_id})")

        # Set scale
        scale_resp, _ = send_mcp_request("setViewScale", {
            "viewId": view_id,
            "scale": task.inputs.get("scale", 48)
        })
        if scale_resp.get("success"):
            print(f"      Scale: 1/{task.inputs.get('scale', 48)}\" = 1'-0\"")

        # Set crop region
        if task.inputs.get("cropEnabled"):
            extents = task.inputs.get("modelExtents", {})
            margin = task.inputs.get("cropMargin", 5.0)

            crop_resp, _ = send_mcp_request("setViewCropBox", {
                "viewId": view_id,
                "enableCrop": True,
                "cropBox": [
                    [extents.get("min_x", 0) - margin, extents.get("min_y", 0) - margin, -10],
                    [extents.get("max_x", 0) + margin, extents.get("max_y", 0) + margin, 10]
                ]
            })
            if crop_resp.get("success"):
                width = extents.get("max_x", 0) - extents.get("min_x", 0)
                height = extents.get("max_y", 0) - extents.get("min_y", 0)
                print(f"      Crop: {width:.0f}' x {height:.0f}' + {margin}' margin")

        return True

    elif task.task_type == "place_viewport":
        # Look up sheet and view IDs
        sheet_id = ctx.sheets.get(task.inputs["sheetNumber"])
        view_id = ctx.views.get(task.inputs["viewName"])

        if not sheet_id or not view_id:
            print(f"    SKIPPED: Sheet or view not found")
            return False

        resp, elapsed = send_mcp_request("placeViewOnSheet", {
            "sheetId": sheet_id,
            "viewId": view_id,
            "x": task.inputs.get("x", 1.0),
            "y": task.inputs.get("y", 0.5)
        })
        report.log_mcp_call("placeViewOnSheet", task.inputs, resp, elapsed)

        if resp.get("success"):
            viewport_id = resp.get("viewportId")
            ctx.viewports.append(viewport_id)
            ctx.artifacts[task.task_id] = {"type": "viewport", "id": viewport_id}
            report.add_artifact("viewport", viewport_id, f"VP-{task.inputs['viewName']}", cleanup="delete")
            print(f"    Placed: {task.inputs['viewName']} on {task.inputs['sheetNumber']} (VP: {viewport_id})")
            return True
        else:
            print(f"    FAILED: {resp.get('error')}")
            return False

    elif task.task_type == "create_schedule":
        resp, elapsed = send_mcp_request("createSchedule", {
            "category": task.inputs["category"],
            "scheduleName": task.inputs["name"]
        })
        report.log_mcp_call("createSchedule", task.inputs, resp, elapsed)

        if not resp.get("success"):
            print(f"    FAILED: {resp.get('error')}")
            return False

        schedule_id = resp.get("scheduleId")
        ctx.schedules[task.inputs["name"]] = schedule_id
        ctx.artifacts[task.task_id] = {"type": "schedule", "id": schedule_id}
        report.add_artifact("schedule", schedule_id, task.inputs["name"], cleanup="delete")
        print(f"    Created: {task.inputs['name']} (ID: {schedule_id})")

        # Add fields
        fields_added = []
        for field_name in task.inputs.get("fields", []):
            field_resp, _ = send_mcp_request("addScheduleField", {
                "scheduleId": schedule_id,
                "fieldName": field_name
            })
            if field_resp.get("success"):
                fields_added.append(field_name)

        if fields_added:
            print(f"      Fields: {', '.join(fields_added)}")

        return True

    elif task.task_type == "place_schedule":
        # Known to fail in Revit 2026 - handle gracefully
        sheet_id = ctx.sheets.get(task.inputs["sheetNumber"])
        schedule_id = ctx.schedules.get(task.inputs["scheduleName"])

        if not sheet_id or not schedule_id:
            print(f"    SKIPPED: Sheet or schedule not found")
            return False

        resp, elapsed = send_mcp_request("placeViewOnSheet", {
            "sheetId": sheet_id,
            "viewId": schedule_id,
            "x": task.inputs.get("x", 1.5),
            "y": task.inputs.get("y", 1.0)
        })
        report.log_mcp_call("placeViewOnSheet", task.inputs, resp, elapsed)

        if resp.get("success"):
            viewport_id = resp.get("viewportId")
            ctx.viewports.append(viewport_id)
            print(f"    Placed: {task.inputs['scheduleName']} (VP: {viewport_id})")
            return True
        else:
            # Expected failure - not an error
            print(f"    UNSUPPORTED: Schedule placement not available in Revit 2026")
            return False

    elif task.task_type == "place_elevation":
        # Check if elevation views exist in profile
        # For now, skip with warning
        print(f"    SKIPPED: No elevation views available")
        return False

    elif task.task_type == "export_csv":
        export_type = task.inputs["exportType"]

        if export_type == "sheet_list":
            # Export sheet list
            resp, _ = send_mcp_request("getAllSheets")
            if resp.get("success"):
                sheets = resp.get("sheets", [])
                filename = f"sheet_list_{resolved.run_id}.csv"
                filepath = Path(__file__).parent / filename

                with open(filepath, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Sheet Number", "Sheet Name", "View Count"])
                    for s in sheets:
                        writer.writerow([s.get("sheetNumber"), s.get("sheetName"), s.get("viewCount", 0)])

                # Calculate hash
                with open(filepath, "rb") as f:
                    sha = hashlib.sha256(f.read()).hexdigest()

                ctx.artifacts[task.task_id] = {"type": "export", "path": str(filepath), "sha256": sha}
                print(f"    Exported: {filename} (sha256: {sha[:16]}...)")
                return True

        elif export_type == "door_schedule":
            # Get schedule data
            schedule_id = list(ctx.schedules.values())[0] if ctx.schedules else None
            if not schedule_id:
                print(f"    SKIPPED: No schedule to export")
                return False

            resp, _ = send_mcp_request("getScheduleData", {"scheduleId": schedule_id})
            if resp.get("success"):
                filename = f"door_schedule_{resolved.run_id}.csv"
                filepath = Path(__file__).parent / filename

                headers = resp.get("headers", [])
                rows = resp.get("rows", [])

                with open(filepath, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for row in rows:
                        writer.writerow(row)

                with open(filepath, "rb") as f:
                    sha = hashlib.sha256(f.read()).hexdigest()

                ctx.artifacts[task.task_id] = {"type": "export", "path": str(filepath), "sha256": sha}
                print(f"    Exported: {filename} (sha256: {sha[:16]}...)")
                return True

        print(f"    FAILED: Export type '{export_type}' not supported")
        return False

    else:
        print(f"    UNKNOWN TASK TYPE: {task.task_type}")
        return False


# =============================================================================
# Step 4: Cleanup (Accounting-Perfect)
# =============================================================================

def cleanup_artifacts(ctx: ExecutionContext) -> dict:
    """
    Delete all created artifacts with proper accounting.

    Strategy:
    - Delete sheets LAST (they cascade-delete their viewports)
    - Track cascade deletions
    - "Element not found" counts as already-deleted (success)
    - Only true failures become leftovers
    """
    deleted = []
    already_deleted = []  # Cascade-deleted or already gone
    leftovers = []
    deleted_ids = set()  # Track IDs we've confirmed deleted

    # Collect all artifacts with their info for accounting
    artifacts_to_delete = []
    for task_id, artifact in ctx.artifacts.items():
        if "id" in artifact and artifact.get("type") != "export":
            artifacts_to_delete.append({
                "task_id": task_id,
                "type": artifact.get("type"),
                "id": artifact["id"],
                "name": task_id  # Use task_id as name reference
            })

    # Delete order: viewports, views, schedules, sheets (sheets last - they cascade)
    type_order = ["viewport", "view", "schedule", "sheet"]

    for artifact_type in type_order:
        for artifact in artifacts_to_delete:
            if artifact["type"] != artifact_type:
                continue

            element_id = artifact["id"]

            # Skip if already deleted by cascade
            if element_id in deleted_ids:
                already_deleted.append({
                    "type": artifact_type,
                    "id": element_id,
                    "reason": "cascade-deleted"
                })
                continue

            resp, _ = send_mcp_request("deleteElement", {"elementId": element_id})

            if resp.get("success"):
                deleted.append({
                    "type": artifact_type,
                    "id": element_id,
                    "cascade_count": resp.get("totalDeleted", 1) - 1
                })
                deleted_ids.add(element_id)

                # If cascade deleted multiple elements, note it
                cascade_count = resp.get("totalDeleted", 1) - 1
                if cascade_count > 0:
                    # Mark potential cascade victims
                    # (We can't know exact IDs, but we note the count)
                    pass

            elif "not found" in resp.get("error", "").lower():
                # Element already deleted (by cascade or prior operation)
                already_deleted.append({
                    "type": artifact_type,
                    "id": element_id,
                    "reason": "already-deleted"
                })
                deleted_ids.add(element_id)

            else:
                # True failure
                leftovers.append({
                    "type": artifact_type,
                    "id": element_id,
                    "task_id": artifact["task_id"],
                    "error": resp.get("error", "Unknown error"),
                    "prefix": "ZZ_" if "ZZ_" in artifact["task_id"] else ""
                })

    # Determine status based on leftovers
    # Rule: ZZ_ prefixed leftovers up to N=1 are WARN (allowed test artifacts)
    zz_leftovers = [l for l in leftovers if l.get("prefix") == "ZZ_"]
    real_leftovers = [l for l in leftovers if l.get("prefix") != "ZZ_"]

    if len(real_leftovers) == 0 and len(zz_leftovers) <= 1:
        status = "pass" if len(zz_leftovers) == 0 else "warn"
    elif len(real_leftovers) <= 3:
        status = "warn"
    else:
        status = "fail"

    return {
        "status": status,
        "deleted_count": len(deleted),
        "already_deleted_count": len(already_deleted),
        "leftover_count": len(leftovers),
        "leftovers": leftovers,
        "already_deleted": already_deleted,
        "accounting": {
            "created": len(artifacts_to_delete),
            "deleted": len(deleted),
            "cascade_deleted": len(already_deleted),
            "leftovers": len(leftovers),
            "accounted": len(deleted) + len(already_deleted) + len(leftovers)
        }
    }


# =============================================================================
# Main Workflow
# =============================================================================

def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def run_spine_v02(standards_path: Path, profile_path: Path = None):
    """
    Run Spine v0.2 adaptive workflow (legacy path-based interface).
    """
    standards = load_json(standards_path)
    return run_spine_v02_with_standards(standards, profile_path)


def run_spine_v02_with_standards(standards: dict, profile_path: Path = None):
    """
    Run Spine v0.2 adaptive workflow with pre-loaded standards.
    """
    print("\n" + "=" * 70)
    print("SPINE v0.2: ADAPTIVE PERMIT SKELETON")
    print("=" * 70)

    print(f"Standards: {standards.get('name', 'unknown')}")

    # Load or generate profile
    if profile_path and profile_path.exists():
        profile = load_json(profile_path)
        print(f"Profile: {profile_path.name}")
    else:
        # Run profiler inline
        print("Profile: Generating from current model...")
        from project_profiler import profile_project
        profile = profile_project(standards.get("name"))

    # Create report
    report = WorkflowReport("spine_v02_adaptive")
    report.set_budget_limits(max_steps=30, max_total_retries=5, max_elapsed_ms=300000)

    print(f"\nRun ID: {report.run_id}")
    print("-" * 70)

    # Step 1: Resolve config
    print("\n[RESOLVE] Merging profile + standards...")
    resolved = resolve(profile, standards, report.run_id)
    print(f"  Title Block: {resolved.titleblock_name} (ID: {resolved.titleblock_id})")
    print(f"  Levels: {list(resolved.level_map.keys())}")
    print(f"  Scale: 1/{resolved.scales.get('floorPlan', 48)}\" = 1'-0\"")
    print(f"  Crop Margin: {resolved.crop_margin_feet}'")

    # Step 2: Build plan
    print("\n[PLAN] Building task list...")
    tasks = build_plan(resolved)
    print(f"  Tasks: {len(tasks)}")
    for task in tasks:
        req = "REQ" if task.required else "OPT"
        print(f"    [{req}] {task.task_id}: {task.description}")

    # Step 3: Execute tasks
    print("\n[EXECUTE] Running tasks...")
    ctx = ExecutionContext(resolved, report)

    required_failures = 0
    optional_failures = 0

    for task in tasks:
        report.start_step(task.task_id)
        print(f"\n  {task.task_id}:")

        success = execute_task(task, ctx)

        if success:
            report.end_step(outputs={"success": True})
        else:
            if task.required:
                required_failures += 1
                report.add_issue(f"{task.task_id.upper()}_FAILED", Severity.BLOCKER,
                               f"Required task failed: {task.description}")
            else:
                optional_failures += 1
                report.add_issue(f"{task.task_id.upper()}_SKIPPED", Severity.WARNING,
                               f"Optional task skipped: {task.description}")
            report.end_step(status="fail" if task.required else "warn")

    # Step 4: Verify postconditions
    print("\n[VERIFY] Checking postconditions...")

    # Sheet count
    expected_sheets = len([t for t in tasks if t.task_type == "create_sheet"])
    actual_sheets = len(ctx.sheets)
    sheet_ok = actual_sheets == expected_sheets
    report.add_postcondition("SHEET_COUNT_MATCHES", "pass" if sheet_ok else "fail",
                            {"expected": expected_sheets, "actual": actual_sheets})
    print(f"  SHEET_COUNT_MATCHES: {'PASS' if sheet_ok else 'FAIL'} ({actual_sheets}/{expected_sheets})")

    # Viewport count (floor plans only)
    expected_viewports = len([t for t in tasks if t.task_type == "place_viewport" and t.required])
    actual_viewports = len([v for v in ctx.viewports])
    viewport_ok = actual_viewports >= expected_viewports
    report.add_postcondition("PLAN_VIEWPORTS_PLACED", "pass" if viewport_ok else "fail",
                            {"expected": expected_viewports, "actual": actual_viewports})
    print(f"  PLAN_VIEWPORTS_PLACED: {'PASS' if viewport_ok else 'FAIL'} ({actual_viewports}/{expected_viewports})")

    # Exports
    sheet_export = any("sheet_list" in str(a.get("path", "")) for a in ctx.artifacts.values())
    schedule_export = any("door_schedule" in str(a.get("path", "")) for a in ctx.artifacts.values())
    report.add_postcondition("EXPORT_SHEET_LIST_EXISTS", "pass" if sheet_export else "fail")
    report.add_postcondition("EXPORT_DOOR_SCHEDULE_EXISTS", "pass" if schedule_export else "fail")
    print(f"  EXPORT_SHEET_LIST_EXISTS: {'PASS' if sheet_export else 'FAIL'}")
    print(f"  EXPORT_DOOR_SCHEDULE_EXISTS: {'PASS' if schedule_export else 'FAIL'}")

    # Optional postconditions
    elevation_placed = any("elevation" in task_id.lower() and artifact.get("type") == "viewport"
                          for task_id, artifact in ctx.artifacts.items())
    schedule_placed = resolved.capabilities.get("can_place_schedule", False)
    report.add_postcondition("ELEVATION_VIEWPORT_PLACED", "warn" if not elevation_placed else "pass",
                            {"optional": True})
    report.add_postcondition("SCHEDULE_VIEWPORT_PLACED", "warn" if not schedule_placed else "pass",
                            {"optional": True})
    print(f"  ELEVATION_VIEWPORT_PLACED: WARN (optional)")
    print(f"  SCHEDULE_VIEWPORT_PLACED: WARN (optional)")

    # Step 5: Cleanup
    print("\n[CLEANUP] Deleting artifacts...")
    cleanup_result = cleanup_artifacts(ctx)
    report.record_cleanup(cleanup_result["status"],
                         f"Deleted {cleanup_result['deleted_count']}, leftovers {cleanup_result['leftover_count']}")
    report.add_postcondition("CLEANUP_STATUS", cleanup_result["status"], cleanup_result)

    # Show accounting detail
    acct = cleanup_result["accounting"]
    print(f"  Created:  {acct['created']} artifacts")
    print(f"  Deleted:  {acct['deleted']} (direct)")
    print(f"  Cascade:  {acct['cascade_deleted']} (already gone)")
    print(f"  Leftover: {acct['leftovers']}")
    print(f"  Status:   {cleanup_result['status'].upper()}")

    if cleanup_result["leftovers"]:
        print(f"  ⚠ Leftovers:")
        for lo in cleanup_result["leftovers"]:
            print(f"    - {lo['type']} #{lo['id']}: {lo.get('error', 'unknown')}")

    # Finalize
    report.finalize()
    report.save()

    # Print summary
    print("\n" + "=" * 70)
    print("SPINE v0.2 RESULTS")
    print("=" * 70)
    print(f"\nrun.status: {report.status.value}")
    print(f"severity_counts: blocker={required_failures}, warning={optional_failures}, info=0")

    if report.issues:
        print("\nissues[]:")
        for issue in report.issues:
            sev = issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity)
            msg = getattr(issue, 'message', getattr(issue, 'description', str(issue)))
            print(f"  - [{sev}] {issue.id}: {msg}")

    print("\npostconditions:")
    for pc in report.postconditions:
        print(f"  - {pc.id}: {pc.status}")

    print(f"\ncapability_matrix:")
    for cap, val in resolved.capabilities.items():
        print(f"  {cap}: {val}")

    print("-" * 70)
    passed = report.status in (RunStatus.PASS, RunStatus.WARN)
    print(f"SPINE v0.2: {'PASS' if passed else 'FAIL'}")
    print("=" * 70)

    return report


def load_standards(args, base_dir: Path) -> tuple:
    """
    Load standards from various sources.
    Returns (standards_dict, source_description)
    """
    # Priority: --pack > --sector > --standards

    if args.pack:
        # Direct pack file (v1 or v2)
        pack_path = Path(args.pack)
        if not pack_path.is_absolute():
            pack_path = base_dir / "template_packs" / args.pack

        if not pack_path.exists():
            raise FileNotFoundError(f"Pack not found: {pack_path}")

        # Import adapter and load
        import sys
        sys.path.insert(0, str(base_dir / "template_packs"))
        from pack_adapter import load_and_adapt

        standards = load_and_adapt(str(pack_path))
        return standards, f"Pack: {pack_path.name}"

    elif args.sector:
        # Auto-resolve from sector
        import sys
        sys.path.insert(0, str(base_dir / "template_packs"))
        from pack_resolver import resolve_pack

        core_path = base_dir / "template_packs" / "_core" / "standards.json"
        sector_path = base_dir / "template_packs" / args.sector / "standards.json"

        if not sector_path.exists():
            raise FileNotFoundError(f"Sector module not found: {args.sector}")

        # Load firm overrides if specified
        firm_overrides = None
        if args.firm:
            firm_path = base_dir / "template_packs" / "_firms" / f"{args.firm.lower()}.json"
            if firm_path.exists():
                with open(firm_path) as f:
                    firm_overrides = json.load(f)

        # Resolve pack
        resolved = resolve_pack(core_path, sector_path, firm_overrides)

        # Adapt to v1 format
        from pack_adapter import adapt_pack_for_spine
        standards = adapt_pack_for_spine(resolved)

        firm_str = f" + {args.firm}" if args.firm else ""
        return standards, f"Sector: {args.sector}{firm_str}"

    elif args.standards:
        # Legacy v1 standards
        standards_path = base_dir / "standards" / f"{args.standards}.json"

        if not standards_path.exists():
            raise FileNotFoundError(f"Standards pack not found: {standards_path}")

        with open(standards_path) as f:
            standards = json.load(f)

        return standards, f"Standards: {args.standards}"

    else:
        raise ValueError("Must specify --standards, --pack, or --sector")


def main():
    parser = argparse.ArgumentParser(description="Spine v0.2 Adaptive Permit Skeleton")

    # Standards source (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--standards", "-s",
                             help="Legacy standards pack name (e.g., ARKY_SFH_v1)")
    source_group.add_argument("--pack", "-k",
                             help="Template pack path (v1 or v2 format)")
    source_group.add_argument("--sector", "-t",
                             help="Sector module to auto-resolve (e.g., multifamily)")

    # Optional modifiers
    parser.add_argument("--firm", "-f",
                       help="Firm overrides (used with --sector)")
    parser.add_argument("--profile", "-p",
                       help="Profile JSON path (generates if not provided)")

    args = parser.parse_args()

    # Require at least one source
    if not args.standards and not args.pack and not args.sector:
        parser.error("Must specify --standards, --pack, or --sector")

    # Resolve paths
    base_dir = Path(__file__).parent

    try:
        standards, source_desc = load_standards(args, base_dir)
        print(f"Loaded: {source_desc}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR loading standards: {e}")
        return 1

    profile_path = Path(args.profile) if args.profile else None

    report = run_spine_v02_with_standards(standards, profile_path)

    return 0 if report.status in (RunStatus.PASS, RunStatus.WARN) else 1


if __name__ == "__main__":
    exit(main())
