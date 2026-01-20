#!/usr/bin/env python3
"""
Human Review Gates - Interactive checkpoints for workflow approval

Gates provide stopping points where humans can review progress
and decide whether to continue or stop for manual review.

Gate 1: Structure Review (after Spine A - sheets/views)
Gate 2: Content Review (after Spine B+C - tags/schedules)
Gate 3: Submit Review (before final export)

Usage:
    from human_gates import GateReviewer

    reviewer = GateReviewer(interactive=True)
    if not reviewer.gate_structure(sheets_created, views_placed):
        return  # User denied, stop execution
"""

import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class GateDecision(Enum):
    APPROVED = "approved"
    DENIED = "denied"
    SKIPPED = "skipped"  # Non-interactive mode


@dataclass
class GateResult:
    """Result of a gate review."""
    gate_name: str
    decision: GateDecision
    summary: Dict[str, Any]
    notes: str = ""


class GateReviewer:
    """Manages human review gates during workflow execution."""

    def __init__(self, interactive: bool = True, auto_approve: bool = False):
        """
        Initialize the gate reviewer.

        Args:
            interactive: If True, prompts for user input. If False, skips gates.
            auto_approve: If True (and interactive), auto-approves without prompting.
        """
        self.interactive = interactive
        self.auto_approve = auto_approve
        self.gate_history: List[GateResult] = []

    def _print_gate_box(self, title: str, content: List[str],
                        approve_prompt: str = "APPROVE to continue?"):
        """Print a formatted gate review box."""
        width = 60
        print()
        print("┌" + "─" * (width - 2) + "┐")
        print(f"│ {title:<{width-4}} │")
        print("├" + "─" * (width - 2) + "┤")

        for line in content:
            # Truncate long lines
            display_line = line[:width-4] if len(line) > width-4 else line
            print(f"│ {display_line:<{width-4}} │")

        print("│" + " " * (width - 2) + "│")
        print(f"│ {approve_prompt:<{width-4}} │")
        print(f"│ {'[Y] Yes  [N] No (stop and review in Revit)':<{width-4}} │")
        print("└" + "─" * (width - 2) + "┘")

    def _get_user_decision(self) -> GateDecision:
        """Get user decision from input."""
        if self.auto_approve:
            print("  → Auto-approved")
            return GateDecision.APPROVED

        try:
            response = input("\n  Your choice [Y/n]: ").strip().lower()
            if response in ("y", "yes", ""):
                return GateDecision.APPROVED
            else:
                return GateDecision.DENIED
        except (EOFError, KeyboardInterrupt):
            print("\n  → Interrupted")
            return GateDecision.DENIED

    def gate_structure(self,
                       sheets_created: int,
                       sheets_expected: int,
                       views_placed: int,
                       views_expected: int,
                       optional_skipped: int = 0) -> GateResult:
        """
        Gate 1: Structure Review

        Reviews sheet and view creation after Spine A.

        Returns:
            GateResult with decision and summary
        """
        summary = {
            "sheets_created": sheets_created,
            "sheets_expected": sheets_expected,
            "views_placed": views_placed,
            "views_expected": views_expected,
            "optional_skipped": optional_skipped
        }

        if not self.interactive:
            result = GateResult(
                gate_name="structure",
                decision=GateDecision.SKIPPED,
                summary=summary
            )
            self.gate_history.append(result)
            return result

        # Format content
        content = [
            f"Sheets created: {sheets_created}/{sheets_expected}" +
            (f" ({optional_skipped} optional skipped)" if optional_skipped else ""),
            f"Views placed: {views_placed}/{views_expected}",
            "",
            "Layout: ✓ All views centered on sheets" if views_placed > 0 else "",
        ]

        self._print_gate_box(
            "GATE 1: STRUCTURE REVIEW",
            [c for c in content if c],
            "APPROVE to continue to annotations?"
        )

        decision = self._get_user_decision()

        result = GateResult(
            gate_name="structure",
            decision=decision,
            summary=summary
        )
        self.gate_history.append(result)
        return result

    def gate_content(self,
                     tags_placed: Dict[str, int],
                     tag_coverage: float,
                     schedules_created: int,
                     schedules_expected: int,
                     duplicate_marks: int = 0,
                     untagged_details: str = "") -> GateResult:
        """
        Gate 2: Content Review

        Reviews annotation and schedule work after Spine B+C.

        Returns:
            GateResult with decision and summary
        """
        summary = {
            "tags_placed": tags_placed,
            "tag_coverage": tag_coverage,
            "schedules_created": schedules_created,
            "schedules_expected": schedules_expected,
            "duplicate_marks": duplicate_marks
        }

        if not self.interactive:
            result = GateResult(
                gate_name="content",
                decision=GateDecision.SKIPPED,
                summary=summary
            )
            self.gate_history.append(result)
            return result

        # Format tag summary
        tag_str = ", ".join([f"{v} {k.lower()}" for k, v in tags_placed.items()])

        content = [
            f"Tags placed: {tag_str}",
            f"Tag coverage: {tag_coverage:.0f}%",
            f"  {untagged_details}" if untagged_details else "",
            f"Schedules created: {schedules_created}/{schedules_expected}",
            f"Duplicate marks: {duplicate_marks}",
        ]

        self._print_gate_box(
            "GATE 2: CONTENT REVIEW",
            [c for c in content if c],
            "APPROVE to generate final report?"
        )

        decision = self._get_user_decision()

        result = GateResult(
            gate_name="content",
            decision=decision,
            summary=summary
        )
        self.gate_history.append(result)
        return result

    def gate_submit(self,
                    completion_percent: float,
                    blocker_count: int,
                    warning_count: int,
                    human_tasks: List[Dict],
                    warnings: List[str] = None) -> GateResult:
        """
        Gate 3: Submit Review

        Final review before export.

        Returns:
            GateResult with decision and summary
        """
        summary = {
            "completion_percent": completion_percent,
            "blocker_count": blocker_count,
            "warning_count": warning_count,
            "human_tasks_count": len(human_tasks)
        }

        if not self.interactive:
            result = GateResult(
                gate_name="submit",
                decision=GateDecision.SKIPPED,
                summary=summary
            )
            self.gate_history.append(result)
            return result

        content = [
            f"Completion: {completion_percent:.0f}%",
            f"Blockers: {blocker_count}",
            f"Warnings: {warning_count}",
        ]

        # Add warning details
        if warnings:
            for w in warnings[:3]:  # Show up to 3 warnings
                content.append(f"  - {w[:50]}")

        content.append("")
        content.append(f"Human tasks remaining: {len(human_tasks)}")

        # Add task preview
        for i, task in enumerate(human_tasks[:5], 1):
            desc = task.get("description", str(task))[:40]
            content.append(f"  {i}. {desc}")

        if len(human_tasks) > 5:
            content.append(f"  ... and {len(human_tasks) - 5} more")

        self._print_gate_box(
            "GATE 3: SUBMIT REVIEW",
            content,
            "EXPORT evidence package?"
        )

        decision = self._get_user_decision()

        result = GateResult(
            gate_name="submit",
            decision=decision,
            summary=summary
        )
        self.gate_history.append(result)
        return result

    def get_passed_gates(self) -> List[str]:
        """Get list of gate names that were approved."""
        return [r.gate_name for r in self.gate_history
                if r.decision in (GateDecision.APPROVED, GateDecision.SKIPPED)]

    def get_pending_gates(self) -> List[str]:
        """Get list of gates not yet reviewed."""
        all_gates = ["structure", "content", "submit"]
        reviewed = [r.gate_name for r in self.gate_history]
        return [g for g in all_gates if g not in reviewed]

    def was_denied(self) -> bool:
        """Check if any gate was denied."""
        return any(r.decision == GateDecision.DENIED for r in self.gate_history)


def demo():
    """Demo the gate system."""
    print("\n" + "=" * 60)
    print("HUMAN REVIEW GATES - DEMO")
    print("=" * 60)

    reviewer = GateReviewer(interactive=True)

    # Gate 1
    result1 = reviewer.gate_structure(
        sheets_created=12,
        sheets_expected=14,
        views_placed=8,
        views_expected=8,
        optional_skipped=2
    )

    if result1.decision == GateDecision.DENIED:
        print("\n⚠ Workflow stopped at Gate 1")
        return

    # Gate 2
    result2 = reviewer.gate_content(
        tags_placed={"doors": 45, "windows": 23, "rooms": 18},
        tag_coverage=98,
        schedules_created=3,
        schedules_expected=3,
        duplicate_marks=0,
        untagged_details="2 doors in closets untagged"
    )

    if result2.decision == GateDecision.DENIED:
        print("\n⚠ Workflow stopped at Gate 2")
        return

    # Gate 3
    result3 = reviewer.gate_submit(
        completion_percent=87,
        blocker_count=0,
        warning_count=3,
        human_tasks=[
            {"description": "Add exterior dimensions"},
            {"description": "Place keynote legend"},
            {"description": "Verify ADA room tags"},
            {"description": "Fill door hardware parameters"},
            {"description": "Fix room boundary for Room 104"},
        ],
        warnings=[
            "2 doors missing hardware parameter",
            "1 room has area = 0 (check boundaries)",
        ]
    )

    if result3.decision == GateDecision.DENIED:
        print("\n⚠ Workflow stopped at Gate 3")
        return

    print("\n✓ All gates passed!")
    print(f"  Passed: {reviewer.get_passed_gates()}")


if __name__ == "__main__":
    demo()
