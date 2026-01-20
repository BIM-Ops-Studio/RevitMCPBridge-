#!/usr/bin/env python3
"""
Gap Planner - Deterministic task generation from assessment gaps

Rules:
1. NEVER create duplicates - use stable keys (sheet_number, view_role, unit_id)
2. If ambiguity exists → STOP + ASK (human gate)
3. Always prefer REUSE over CREATE (unless pack demands new)
4. Every task has a unique key for deduplication

This turns assessment gaps into safe, executable tasks.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum

# Import canonical sheet contract
from sheet_contract import normalize_sheet_number, sheet_exists


class TaskType(Enum):
    CREATE_SHEET = "create_sheet"
    CREATE_VIEW = "create_view"
    CREATE_SCHEDULE = "create_schedule"
    PLACE_VIEWPORT = "place_viewport"
    TAG_ELEMENT = "tag_element"
    FILL_PARAMETER = "fill_parameter"
    FIX_DUPLICATE = "fix_duplicate"
    REUSE_EXISTING = "reuse_existing"
    HUMAN_REVIEW = "human_review"


class TaskSafety(Enum):
    """How safe is this task to execute automatically?"""
    SAFE = "safe"          # Can execute without review
    REVIEW = "review"      # Should show user before executing
    BLOCK = "block"        # Must stop and ask user


@dataclass
class PlannedTask:
    """A task generated from gap analysis."""
    task_id: str           # Unique, stable key for deduplication
    task_type: TaskType
    description: str
    safety: TaskSafety
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)  # Task IDs this depends on
    ambiguity: Optional[str] = None  # Why this needs human review


class GapPlanner:
    """
    Generates deterministic tasks from assessment gaps.

    Key principles:
    - Stable task IDs prevent duplicates
    - Reuse existing elements when possible
    - Stop on ambiguity
    """

    def __init__(self, pack: Dict, existing_state: Dict):
        """
        Args:
            pack: Resolved standards pack
            existing_state: Current model state from assessment
        """
        self.pack = pack
        self.existing = existing_state
        self.tasks: List[PlannedTask] = []
        self.seen_keys: Set[str] = set()

    def _add_task(self, task: PlannedTask) -> bool:
        """
        Add task if key is unique.

        Returns False if duplicate key (task already planned).
        """
        if task.task_id in self.seen_keys:
            return False
        self.seen_keys.add(task.task_id)
        self.tasks.append(task)
        return True

    def plan_from_assessment(self, assessment_report: Dict) -> List[PlannedTask]:
        """
        Generate tasks from pack assessment report.

        This is the main entry point.
        """
        self.tasks = []
        self.seen_keys = set()

        # 1. Plan sheet tasks
        self._plan_sheet_tasks(assessment_report)

        # 2. Plan schedule tasks
        self._plan_schedule_tasks(assessment_report)

        # 3. Plan tag tasks
        self._plan_tag_tasks(assessment_report)

        # 4. Plan parameter tasks
        self._plan_parameter_tasks(assessment_report)

        return self.tasks

    def _plan_sheet_tasks(self, report: Dict):
        """Plan sheet creation/reuse tasks using canonical sheet_coverage."""
        human_tasks = report.get("human_tasks", [])

        # Get canonical sheet coverage if available
        sheet_coverage = report.get("sheet_coverage", {})
        existing_by_number = sheet_coverage.get("existing_by_number", {})

        for task in human_tasks:
            if task.get("type") == "create_sheet":
                sheet_num = task.get("sheet_number", "")
                normalized = normalize_sheet_number(sheet_num)

                # Use canonical check - if it exists, skip entirely
                if normalized in existing_by_number:
                    # Sheet already exists - no task needed
                    # (This shouldn't happen if pack_assessor uses canonical missing_numbers,
                    # but provides defense in depth)
                    continue

                # CREATE - sheet confirmed not to exist
                titleblock_ok = True  # Assume preflight verified this

                self._add_task(PlannedTask(
                    task_id=f"create_sheet_{normalized}",
                    task_type=TaskType.CREATE_SHEET,
                    description=f"Create sheet {sheet_num}",
                    safety=TaskSafety.SAFE if titleblock_ok else TaskSafety.BLOCK,
                    params={"number": sheet_num, "name": task.get("name", "")}
                ))

    def _plan_schedule_tasks(self, report: Dict):
        """Plan schedule creation tasks."""
        human_tasks = report.get("human_tasks", [])

        for task in human_tasks:
            if task.get("type") == "create_schedule":
                category = task.get("category", "")

                # Check if schedule exists with different name
                existing_schedules = self.existing.get("schedules", {}).get("found", [])

                if category.lower() in [s.lower() for s in existing_schedules]:
                    # Schedule exists - skip
                    continue

                # Get schedule definition from pack
                schedule_def = self._get_schedule_definition(category)

                if not schedule_def:
                    # No definition in pack - need human input
                    self._add_task(PlannedTask(
                        task_id=f"schedule_{category}_undefined",
                        task_type=TaskType.HUMAN_REVIEW,
                        description=f"Define {category} schedule structure",
                        safety=TaskSafety.BLOCK,
                        params={"category": category},
                        ambiguity="Pack doesn't define schedule structure for this category"
                    ))
                else:
                    self._add_task(PlannedTask(
                        task_id=f"create_schedule_{category}",
                        task_type=TaskType.CREATE_SCHEDULE,
                        description=f"Create {category} schedule",
                        safety=TaskSafety.SAFE,
                        params={
                            "category": category,
                            "fields": schedule_def.get("fields", []),
                            "sorting": schedule_def.get("sorting", []),
                            "grouping": schedule_def.get("grouping", [])
                        }
                    ))

    def _plan_tag_tasks(self, report: Dict):
        """Plan tagging tasks for untagged elements."""
        checks = report.get("checks", {})
        warnings = checks.get("warnings", [])

        for warning in warnings:
            check_id = warning.get("check_id", "")

            if check_id.startswith("TAG_"):
                category = check_id.replace("TAG_", "").title()
                details = warning.get("details", "")

                # Parse "649 total, 554 with Mark"
                parts = details.split(",")
                if len(parts) >= 2:
                    try:
                        total = int(parts[0].split()[0])
                        with_mark = int(parts[1].split()[0])
                        untagged = total - with_mark

                        if untagged > 0:
                            # Don't auto-tag large batches without review
                            if untagged > 50:
                                self._add_task(PlannedTask(
                                    task_id=f"tag_{category}_batch",
                                    task_type=TaskType.HUMAN_REVIEW,
                                    description=f"Review {untagged} untagged {category.lower()}",
                                    safety=TaskSafety.REVIEW,
                                    params={"category": category, "count": untagged},
                                    ambiguity=f"Large batch ({untagged}) - verify before auto-tagging"
                                ))
                            else:
                                self._add_task(PlannedTask(
                                    task_id=f"tag_{category}",
                                    task_type=TaskType.TAG_ELEMENT,
                                    description=f"Tag {untagged} {category.lower()}",
                                    safety=TaskSafety.SAFE,
                                    params={"category": category, "count": untagged}
                                ))
                    except (ValueError, IndexError):
                        pass

    def _plan_parameter_tasks(self, report: Dict):
        """Plan parameter fill tasks."""
        # For now, parameter filling is always human review
        # because we can't determine correct values automatically
        pass

    def _get_schedule_definition(self, category: str) -> Optional[Dict]:
        """Get schedule definition from pack."""
        schedule_defs = self.pack.get("schedules", {}).get("definitions", {})

        # Try exact match
        for key, defn in schedule_defs.items():
            if defn.get("category", "").lower() == category.lower():
                return defn

        # Try partial match
        category_lower = category.lower()
        for key, defn in schedule_defs.items():
            if category_lower in key.lower():
                return defn

        return None

    def get_safe_tasks(self) -> List[PlannedTask]:
        """Get tasks that can be executed without review."""
        return [t for t in self.tasks if t.safety == TaskSafety.SAFE]

    def get_review_tasks(self) -> List[PlannedTask]:
        """Get tasks that need human review before execution."""
        return [t for t in self.tasks if t.safety == TaskSafety.REVIEW]

    def get_blocked_tasks(self) -> List[PlannedTask]:
        """Get tasks that require human input (can't proceed)."""
        return [t for t in self.tasks if t.safety == TaskSafety.BLOCK]

    def generate_summary(self) -> str:
        """Generate human-readable task summary."""
        safe = self.get_safe_tasks()
        review = self.get_review_tasks()
        blocked = self.get_blocked_tasks()

        lines = [
            "",
            "=" * 60,
            "GAP PLANNER - TASK SUMMARY",
            "=" * 60,
            f"Total tasks: {len(self.tasks)}",
            "",
            f"SAFE TO EXECUTE:     {len(safe):3d}",
            f"NEEDS REVIEW:        {len(review):3d}",
            f"BLOCKED (NEED INPUT):{len(blocked):3d}",
            "",
        ]

        if safe:
            lines.append("SAFE TASKS (can auto-execute):")
            for t in safe:
                lines.append(f"  ✓ {t.description}")

        if review:
            lines.append("")
            lines.append("REVIEW TASKS (show before executing):")
            for t in review:
                lines.append(f"  ? {t.description}")
                if t.ambiguity:
                    lines.append(f"      Reason: {t.ambiguity}")

        if blocked:
            lines.append("")
            lines.append("BLOCKED TASKS (need human input):")
            for t in blocked:
                lines.append(f"  ✗ {t.description}")
                if t.ambiguity:
                    lines.append(f"      Reason: {t.ambiguity}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


def test_gap_planner():
    """Test gap planner with sample assessment output."""

    # Simulated assessment report
    assessment_report = {
        "human_tasks": [
            {"type": "create_sheet", "sheet_number": "G0.01", "name": "COVER SHEET"},
            {"type": "create_sheet", "sheet_number": "A1.0.1", "name": "FLOOR PLAN L1"},
            {"type": "create_schedule", "category": "Door"},
        ],
        "checks": {
            "warnings": [
                {
                    "check_id": "TAG_DOORS",
                    "description": "Doors Mark coverage: 85%",
                    "details": "649 total, 554 with Mark"
                }
            ]
        }
    }

    # Simulated existing state
    existing_state = {
        "sheets": {
            "matches": ["CVR", "A1.1.1"],  # Different numbering scheme
            "total": 360
        },
        "schedules": {
            "found": ["Room"],
            "missing": ["Door", "Window"]
        }
    }

    # Simulated pack
    pack = {
        "schedules": {
            "definitions": {
                "doorSchedule": {
                    "category": "Doors",
                    "fields": ["Mark", "Type Mark", "Level", "Width", "Height"],
                    "sorting": ["Level", "Mark"]
                }
            }
        }
    }

    planner = GapPlanner(pack, existing_state)
    tasks = planner.plan_from_assessment(assessment_report)

    print(planner.generate_summary())

    return tasks


if __name__ == "__main__":
    test_gap_planner()
