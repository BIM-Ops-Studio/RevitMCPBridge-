#!/usr/bin/env python3
"""
Spine v0.4: Gap-Closure Autopilot

Assess → generate gap tasks → execute safe deterministic tasks → gate → re-assess → report delta → repeat

Core Loop:
    1. resolve(sector, firm) -> ResolvedConfig
    2. baseline = assess(resolved) -> ScoreCard
    3. while iteration < max_iterations:
        a. gaps = find_gaps(baseline, resolved)
        b. tasks = normalize_and_filter_safe(gaps)
        c. if no safe tasks: break
        d. exec_result = execute(tasks, budgets)
        e. gate_result = gate(stage, mode)
        f. new_state = assess(resolved)
        g. delta = compute_delta(baseline, new_state)
        h. scores = score(new_state, exec_result)
        i. report_iteration(...)
        j. if stop_condition: break
        k. baseline = new_state
    4. finalize_report()

Usage:
    python spine_autopilot.py --sector multifamily [--firm ARKY]
                              [--max_iterations 5]
                              [--auto_approve_gates]
                              [--stop_on_severity error]

    # Or from Python:
    from spine_autopilot import SpineAutopilot
    pilot = SpineAutopilot(sector="multifamily", firm="ARKY")
    pilot.run(max_iterations=5, auto_approve=True)
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Add template_packs to path for imports
sys.path.insert(0, str(Path(__file__).parent / "template_packs"))

from workflow_report import WorkflowReport, RunStatus, BudgetLimits, BudgetUsage, Severity
from state_assessment import StateAssessor
from pack_assessor import PackAssessor, ScoreCard
from gap_planner import GapPlanner, PlannedTask, TaskSafety, TaskType
from human_gates import GateReviewer, GateDecision
from filtered_queries import send_mcp_request


# =============================================================================
# Constants - Safe vs Unsupported Tasks
# =============================================================================

# Tasks that can be auto-executed in v0.4 (low-risk, repeatable)
SAFE_TASK_TYPES = {
    TaskType.CREATE_SHEET,
    TaskType.CREATE_VIEW,
    TaskType.CREATE_SCHEDULE,
    TaskType.PLACE_VIEWPORT,
    TaskType.REUSE_EXISTING,
}

# Tasks that require human action (known Revit 2026 constraints)
UNSUPPORTED_TASK_TYPES = {
    # Legend placement unreliable in 2026
    "place_legend",
    # Schedule placement on sheets fails
    "place_schedule",
}


# =============================================================================
# Data Classes
# =============================================================================

class AutopilotDecision(Enum):
    CONTINUE = "continue"
    COMPLETE = "complete"
    STOPPED = "stopped"


@dataclass
class AutopilotScores:
    """The 3 meaningful scores for v0.4."""
    pack_coverage: float      # % of required pack items that exist
    quality_score: float      # % of quality thresholds met
    confidence: float         # How safe to keep auto-running (0-100)

    def to_dict(self) -> Dict:
        return {
            "pack_coverage_pct": round(self.pack_coverage, 1),
            "quality_pct": round(self.quality_score, 1),
            "confidence_pct": round(self.confidence, 1)
        }


@dataclass
class IterationDelta:
    """What changed between iterations."""
    created: Dict[str, int] = field(default_factory=dict)   # type -> count
    modified: Dict[str, int] = field(default_factory=dict)
    resolved_gaps: int = 0
    remaining_gaps: int = 0
    severity_change: Dict[str, int] = field(default_factory=dict)  # blocker/warn/info delta

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IterationResult:
    """Result of a single autopilot iteration."""
    iteration: int
    tasks_planned: int
    tasks_executed: int
    tasks_succeeded: int
    tasks_skipped: int
    gate_decision: str
    scores: AutopilotScores
    delta: IterationDelta
    decision: AutopilotDecision
    stop_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "iteration": self.iteration,
            "tasks": {
                "planned": self.tasks_planned,
                "executed": self.tasks_executed,
                "succeeded": self.tasks_succeeded,
                "skipped": self.tasks_skipped
            },
            "gate_decision": self.gate_decision,
            "scores": self.scores.to_dict(),
            "delta": self.delta.to_dict(),
            "decision": self.decision.value,
            "stop_reason": self.stop_reason
        }


# =============================================================================
# Scoring Functions
# =============================================================================

def compute_scores(score_card: ScoreCard, exec_result: Dict, unsupported_count: int) -> AutopilotScores:
    """
    Compute the 3 scores from assessment + execution results.

    Pack Coverage: From ScoreCard (required items that exist)
    Quality: From ScoreCard (thresholds met)
    Confidence: How safe to keep auto-running
    """
    # Pack coverage and quality come directly from ScoreCard
    pack_coverage = score_card.pack_coverage
    quality_score = score_card.quality_score

    # Confidence score: start at 100, subtract for issues
    confidence = 100.0

    # Subtract for unsupported gaps (can't auto-resolve)
    confidence -= min(unsupported_count * 10, 40)  # Max 40 point penalty

    # Subtract for blockers
    confidence -= len(score_card.blockers) * 15

    # Subtract for execution failures
    failed = exec_result.get("failed", 0)
    confidence -= failed * 10

    # Subtract if budgets are getting tight
    budget_usage = exec_result.get("budget_usage", {})
    if budget_usage.get("steps", 0) > 35:  # Over 70% of typical 50 limit
        confidence -= 10

    confidence = max(0, min(100, confidence))  # Clamp 0-100

    return AutopilotScores(
        pack_coverage=pack_coverage,
        quality_score=quality_score,
        confidence=confidence
    )


def compute_delta(baseline: ScoreCard, new_state: ScoreCard,
                  exec_result: Dict) -> IterationDelta:
    """Compute what changed between baseline and new state."""

    # Count created artifacts from execution
    created = {}
    for artifact_type, count in exec_result.get("artifacts_created", {}).items():
        if count > 0:
            created[artifact_type] = count

    # Gaps resolved/remaining
    baseline_gaps = baseline.total_checks - baseline.passed_checks
    new_gaps = new_state.total_checks - new_state.passed_checks
    resolved = max(0, baseline_gaps - new_gaps)

    # Severity changes
    severity_change = {
        "blockers": len(new_state.blockers) - len(baseline.blockers),
        "warnings": len(new_state.warnings) - len(baseline.warnings)
    }

    return IterationDelta(
        created=created,
        modified={},
        resolved_gaps=resolved,
        remaining_gaps=new_gaps,
        severity_change=severity_change
    )


# =============================================================================
# Task Execution
# =============================================================================

def filter_safe_tasks(tasks: List[PlannedTask]) -> Tuple[List[PlannedTask], List[PlannedTask]]:
    """
    Filter tasks into safe (auto-executable) and unsupported.

    Returns (safe_tasks, unsupported_tasks)
    """
    safe = []
    unsupported = []

    for task in tasks:
        # Check safety level
        if task.safety == TaskSafety.BLOCK:
            unsupported.append(task)
            continue

        # Check task type against known unsupported
        if task.task_type.value in UNSUPPORTED_TASK_TYPES:
            unsupported.append(task)
            continue

        # Check if task type is in safe list
        if task.task_type in SAFE_TASK_TYPES:
            safe.append(task)
        elif task.safety == TaskSafety.SAFE:
            safe.append(task)
        else:
            # REVIEW tasks - for now, treat as unsupported in autopilot
            unsupported.append(task)

    return safe, unsupported


def execute_safe_tasks(tasks: List[PlannedTask], report: WorkflowReport,
                       budgets: BudgetLimits) -> Dict[str, Any]:
    """
    Execute safe tasks with budget tracking.

    Returns execution summary dict.
    """
    result = {
        "executed": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped": 0,
        "artifacts_created": {},
        "budget_usage": {"steps": 0, "retries": 0}
    }

    for task in tasks:
        # Check step budget
        if result["budget_usage"]["steps"] >= budgets.max_steps:
            result["skipped"] += 1
            continue

        result["executed"] += 1
        result["budget_usage"]["steps"] += 1

        outcome = _execute_single_task(task, report)

        if outcome == "success":
            result["succeeded"] += 1
            # Track artifact type
            artifact_type = _get_artifact_type(task)
            result["artifacts_created"][artifact_type] = \
                result["artifacts_created"].get(artifact_type, 0) + 1
        elif outcome == "skipped":
            result["skipped"] += 1
            # Don't count as failed - already exists or not applicable
        else:  # "failed"
            result["failed"] += 1

    return result


def _execute_single_task(task: PlannedTask, report: WorkflowReport) -> str:
    """
    Execute a single PlannedTask.

    Returns:
        "success" - Task completed successfully
        "skipped" - Task not needed (e.g., sheet already exists)
        "failed" - Task failed for real reason
    """
    import time

    print(f"    [{task.task_type.value}] {task.description}")

    if task.task_type == TaskType.CREATE_SHEET:
        start = time.time()
        resp = send_mcp_request("createSheet", {
            "sheetNumber": task.params.get("number", ""),
            "sheetName": task.params.get("name", "")
        })
        elapsed = (time.time() - start) * 1000
        report.log_mcp_call("createSheet", task.params, resp, elapsed)

        if resp.get("success"):
            print(f"      ✓ Created sheet {task.params.get('number')}")
            return "success"
        else:
            error = resp.get("error", "").lower()
            # "already exists" / "already in use" = SKIPPED, not FAILED
            if "already" in error or "exists" in error or "in use" in error:
                print(f"      ○ Skipped (already exists)")
                return "skipped"
            else:
                print(f"      ✗ Failed: {resp.get('error', 'unknown')[:50]}")
                return "failed"

    elif task.task_type == TaskType.CREATE_SCHEDULE:
        start = time.time()
        resp = send_mcp_request("createSchedule", {
            "category": task.params.get("category", ""),
            "scheduleName": f"{task.params.get('category', 'Item')} Schedule"
        })
        elapsed = (time.time() - start) * 1000
        report.log_mcp_call("createSchedule", task.params, resp, elapsed)

        if resp.get("success"):
            print(f"      ✓ Created {task.params.get('category')} schedule")
            return "success"
        else:
            error = resp.get("error", "").lower()
            if "already" in error or "exists" in error:
                print(f"      ○ Skipped (already exists)")
                return "skipped"
            else:
                print(f"      ✗ Failed: {resp.get('error', 'unknown')[:50]}")
                return "failed"

    elif task.task_type == TaskType.TAG_ELEMENT:
        # For now, skip tagging in autopilot (needs view context)
        print(f"      → Skipped (requires view context)")
        return "skipped"

    else:
        print(f"      → Skipped (unhandled task type)")
        return "skipped"


def _get_artifact_type(task: PlannedTask) -> str:
    """Get artifact type string from task."""
    type_map = {
        TaskType.CREATE_SHEET: "sheet",
        TaskType.CREATE_VIEW: "view",
        TaskType.CREATE_SCHEDULE: "schedule",
        TaskType.PLACE_VIEWPORT: "viewport",
    }
    return type_map.get(task.task_type, "other")


# =============================================================================
# Main Autopilot Class
# =============================================================================

class SpineAutopilot:
    """
    Gap-Closure Autopilot for Spine workflows.

    Runs the assess→gaps→execute→gate→re-assess loop until complete or stopped.
    """

    def __init__(self, sector: str = "multifamily", firm: str = None,
                 pack_path: str = None, standards_name: str = None):
        """
        Initialize autopilot with pack resolution.

        Args:
            sector: Sector module (sfh, duplex, multifamily)
            firm: Optional firm overlay (ARKY, etc.)
            pack_path: Direct path to resolved pack JSON
            standards_name: Legacy v1 standards name
        """
        self.sector = sector
        self.firm = firm
        self.resolved_pack = self._load_pack(sector, firm, pack_path, standards_name)
        self.iterations: List[IterationResult] = []
        self.baseline_scores: Optional[ScoreCard] = None  # Stored for reporting

    def _load_pack(self, sector: str, firm: str, pack_path: str,
                   standards_name: str) -> Dict:
        """Load and resolve pack configuration."""
        base_dir = Path(__file__).parent

        # Option 1: Direct pack path
        if pack_path:
            with open(pack_path) as f:
                return json.load(f)

        # Option 2: Legacy standards
        if standards_name:
            standards_path = base_dir / "standards" / f"{standards_name}.json"
            if standards_path.exists():
                with open(standards_path) as f:
                    return json.load(f)

        # Option 3: Resolve from sector + firm
        try:
            from pack_resolver import resolve_pack

            core_path = base_dir / "template_packs" / "_core" / "standards.json"
            sector_path = base_dir / "template_packs" / sector / "standards.json"

            if not sector_path.exists():
                raise FileNotFoundError(f"Sector '{sector}' not found")

            resolved = resolve_pack(core_path, sector_path)

            # Apply firm overlay if specified
            if firm:
                firm_path = base_dir / "template_packs" / "_firms" / f"{firm.lower()}.json"
                if firm_path.exists():
                    with open(firm_path) as f:
                        firm_overlay = json.load(f)
                    resolved = self._merge_firm(resolved, firm_overlay)

            return resolved

        except ImportError:
            # Fallback: load sector directly
            sector_path = base_dir / "template_packs" / sector / "standards.json"
            if sector_path.exists():
                with open(sector_path) as f:
                    return json.load(f)
            raise FileNotFoundError(f"Cannot load pack for sector '{sector}'")

    def _merge_firm(self, pack: Dict, firm: Dict) -> Dict:
        """Merge firm overlay into pack (firm wins on conflicts)."""
        # Simple shallow merge for now
        result = pack.copy()
        for key, value in firm.items():
            if isinstance(value, dict) and key in result:
                result[key] = {**result[key], **value}
            else:
                result[key] = value
        return result

    def run(self, max_iterations: int = 5, auto_approve: bool = False,
            stop_on_severity: str = "error", budgets: BudgetLimits = None) -> Dict:
        """
        Run the autopilot loop.

        Args:
            max_iterations: Maximum iterations before stopping
            auto_approve: If True, auto-approve gates (non-interactive)
            stop_on_severity: Stop if this severity found ("error", "warn", "info")
            budgets: Budget limits (uses defaults if None)

        Returns:
            Final report dict
        """
        if budgets is None:
            budgets = BudgetLimits()

        # Initialize report
        report = WorkflowReport("spine_autopilot",
                               log_dir=Path(__file__).parent / "reports")
        report.set_environment(
            revit_version="2026",
            doc_title="autopilot"
        )

        # Initialize gate reviewer
        gate_reviewer = GateReviewer(
            interactive=not auto_approve,
            auto_approve=auto_approve
        )

        print("\n" + "=" * 60)
        print("SPINE v0.4 - GAP-CLOSURE AUTOPILOT")
        print("=" * 60)
        print(f"Sector: {self.sector}")
        print(f"Firm: {self.firm or 'none'}")
        print(f"Max iterations: {max_iterations}")
        print(f"Auto-approve: {auto_approve}")
        print("-" * 60)

        # Get baseline assessment
        print("\n[BASELINE] Running initial assessment...")
        assessor = PackAssessor(self.resolved_pack)
        baseline = assessor.assess()
        self.baseline_scores = baseline  # Store for reporting

        print(f"  Pack Coverage: {baseline.pack_coverage}%")
        print(f"  Quality Score: {baseline.quality_score}%")
        print(f"  Blockers: {len(baseline.blockers)}")
        print(f"  Ready for permit: {baseline.ready_for_permit}")

        # Main loop
        iteration = 0
        final_decision = AutopilotDecision.CONTINUE
        stop_reason = None

        while iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"ITERATION {iteration}/{max_iterations}")
            print("=" * 60)

            # Step 1: Find gaps and generate tasks
            print("\n[1] Finding gaps...")
            gap_planner = GapPlanner(self.resolved_pack, self._state_to_dict(baseline))

            # Use pack_assessor's report format for gap planning
            assessment_report = {
                "human_tasks": baseline.human_tasks,
                "checks": {
                    "warnings": [asdict(w) for w in baseline.warnings],
                    "blockers": [asdict(b) for b in baseline.blockers]
                },
                "sheet_coverage": baseline.sheet_coverage  # Canonical contract for gap_planner
            }
            all_tasks = gap_planner.plan_from_assessment(assessment_report)

            # Step 2: Filter to safe tasks only
            safe_tasks, unsupported_tasks = filter_safe_tasks(all_tasks)

            print(f"  Total gap tasks: {len(all_tasks)}")
            print(f"  Safe (auto-executable): {len(safe_tasks)}")
            print(f"  Unsupported (human): {len(unsupported_tasks)}")

            if not safe_tasks:
                print("\n  → No safe tasks to execute")
                if unsupported_tasks:
                    final_decision = AutopilotDecision.STOPPED
                    stop_reason = f"{len(unsupported_tasks)} tasks require human action"
                else:
                    final_decision = AutopilotDecision.COMPLETE
                    stop_reason = "All gaps resolved"
                break

            # Step 3: Execute safe tasks
            print(f"\n[2] Executing {len(safe_tasks)} safe tasks...")
            exec_result = execute_safe_tasks(safe_tasks, report, budgets)

            print(f"  Executed: {exec_result['executed']}")
            print(f"  Succeeded: {exec_result['succeeded']}")
            print(f"  Skipped: {exec_result['skipped']}")
            print(f"  Failed: {exec_result['failed']}")

            # Step 4: Gate check
            print("\n[3] Gate check...")
            gate_result = gate_reviewer.gate_structure(
                sheets_created=exec_result["artifacts_created"].get("sheet", 0),
                sheets_expected=len([t for t in safe_tasks if t.task_type == TaskType.CREATE_SHEET]),
                views_placed=exec_result["artifacts_created"].get("view", 0),
                views_expected=len([t for t in safe_tasks if t.task_type == TaskType.CREATE_VIEW]),
            )

            if gate_result.decision == GateDecision.DENIED:
                final_decision = AutopilotDecision.STOPPED
                stop_reason = "Gate denied by user"
                break

            # Step 5: Re-assess
            print("\n[4] Re-assessing...")
            new_state = assessor.assess()

            # Step 6: Compute delta and scores
            delta = compute_delta(baseline, new_state, exec_result)
            scores = compute_scores(new_state, exec_result, len(unsupported_tasks))

            print(f"  Pack Coverage: {scores.pack_coverage}% (was {baseline.pack_coverage}%)")
            print(f"  Quality Score: {scores.quality_score}%")
            print(f"  Confidence: {scores.confidence}%")
            print(f"  Gaps resolved: {delta.resolved_gaps}")
            print(f"  Gaps remaining: {delta.remaining_gaps}")

            # Record iteration
            iter_result = IterationResult(
                iteration=iteration,
                tasks_planned=len(safe_tasks),
                tasks_executed=exec_result["executed"],
                tasks_succeeded=exec_result["succeeded"],
                tasks_skipped=exec_result.get("skipped", 0),
                gate_decision=gate_result.decision.value,
                scores=scores,
                delta=delta,
                decision=AutopilotDecision.CONTINUE
            )
            self.iterations.append(iter_result)

            # Step 7: Check stop conditions
            if scores.confidence < 30:
                final_decision = AutopilotDecision.STOPPED
                stop_reason = f"Confidence too low ({scores.confidence}%)"
                break

            if new_state.ready_for_permit and delta.remaining_gaps == 0:
                final_decision = AutopilotDecision.COMPLETE
                stop_reason = "All targets achieved"
                break

            if exec_result["succeeded"] == 0 and exec_result["executed"] > 0:
                if exec_result["failed"] == 0:
                    # All tasks skipped (already exist) - work already done
                    final_decision = AutopilotDecision.STOPPED
                    stop_reason = "All tasks skipped (already exist)"
                else:
                    # Actually failed
                    final_decision = AutopilotDecision.STOPPED
                    stop_reason = "All executed tasks failed"
                break

            # Prepare for next iteration
            baseline = new_state

        else:
            # Loop completed without break
            if iteration >= max_iterations:
                final_decision = AutopilotDecision.STOPPED
                stop_reason = f"Max iterations ({max_iterations}) reached"

        # Update last iteration with final decision
        if self.iterations:
            self.iterations[-1].decision = final_decision
            self.iterations[-1].stop_reason = stop_reason

        # Finalize
        print("\n" + "=" * 60)
        print("AUTOPILOT COMPLETE")
        print("=" * 60)
        print(f"Decision: {final_decision.value.upper()}")
        print(f"Reason: {stop_reason}")
        print(f"Iterations: {len(self.iterations)}")

        # Build final report
        final_report = self._build_report(final_decision, stop_reason, report)

        # Save report
        report_path = Path(__file__).parent / "reports" / f"autopilot_{report.run_id}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        print(f"\nReport saved: {report_path}")

        return final_report

    def _state_to_dict(self, score_card: ScoreCard) -> Dict:
        """Convert ScoreCard to dict format expected by GapPlanner."""
        return {
            "sheets": {
                "matches": [],  # Would need to track actual sheet numbers
                "total": 0
            },
            "schedules": {
                "found": [],
                "missing": []
            }
        }

    def _build_report(self, decision: AutopilotDecision, reason: str,
                      workflow_report: WorkflowReport) -> Dict:
        """Build final autopilot report."""
        return {
            "schema_version": "1.0",
            "workflow": "spine_autopilot",
            "version": "0.4",
            "run_id": workflow_report.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "sector": self.sector,
                "firm": self.firm,
                "max_iterations": len(self.iterations)
            },
            "autopilot": {
                "iterations": len(self.iterations),
                "decision": decision.value,
                "stop_reason": reason,
                "iteration_details": [i.to_dict() for i in self.iterations]
            },
            # Scores - always present for downstream dashboards
            "baseline_scores": {
                "pack_coverage_pct": self.baseline_scores.pack_coverage,
                "quality_pct": self.baseline_scores.quality_score,
                "confidence_pct": self.baseline_scores.confidence,
                "ready_for_permit": self.baseline_scores.ready_for_permit,
            } if self.baseline_scores else None,
            "iteration_scores": [i.scores.to_dict() for i in self.iterations],  # Array, may be empty
            "final_scores": self.iterations[-1].scores.to_dict() if self.iterations else (
                # Use baseline scores if no iterations executed
                {
                    "pack_coverage_pct": self.baseline_scores.pack_coverage,
                    "quality_pct": self.baseline_scores.quality_score,
                    "confidence_pct": self.baseline_scores.confidence,
                    "ready_for_permit": self.baseline_scores.ready_for_permit,
                } if self.baseline_scores else None
            ),
            "summary": {
                "total_tasks_executed": sum(i.tasks_executed for i in self.iterations),
                "total_tasks_succeeded": sum(i.tasks_succeeded for i in self.iterations),
                "gaps_resolved": sum(i.delta.resolved_gaps for i in self.iterations),
            }
        }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Spine v0.4: Gap-Closure Autopilot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python spine_autopilot.py --sector multifamily
  python spine_autopilot.py --sector sfh --firm ARKY --auto_approve_gates
  python spine_autopilot.py --sector duplex --max_iterations 3
        """
    )

    # Pack resolution options (mutually exclusive)
    pack_group = parser.add_argument_group("Pack Configuration")
    pack_group.add_argument("--sector", "-t", default="multifamily",
                           help="Sector module: sfh, duplex, multifamily")
    pack_group.add_argument("--firm", "-f", help="Firm overlay (e.g., ARKY)")
    pack_group.add_argument("--pack", help="Direct path to resolved pack JSON")
    pack_group.add_argument("--standards", help="Legacy v1 standards name")

    # Autopilot options
    auto_group = parser.add_argument_group("Autopilot Options")
    auto_group.add_argument("--max_iterations", "-n", type=int, default=5,
                           help="Maximum iterations (default: 5)")
    auto_group.add_argument("--auto_approve_gates", "-y", action="store_true",
                           help="Auto-approve all gates (non-interactive)")
    auto_group.add_argument("--stop_on_severity", choices=["error", "warn", "info"],
                           default="error", help="Stop on this severity level")

    args = parser.parse_args()

    # Test MCP connection first
    print("\n[PREFLIGHT] Testing MCP connection...")
    resp = send_mcp_request("getLevels", timeout=30)
    if not resp.get("success"):
        print(f"ERROR: MCP not connected - {resp.get('error')}")
        print("Make sure Revit is open with a project loaded.")
        return 1
    print(f"  ✓ Connected ({len(resp.get('levels', []))} levels)")

    # Run autopilot
    try:
        pilot = SpineAutopilot(
            sector=args.sector,
            firm=args.firm,
            pack_path=args.pack,
            standards_name=args.standards
        )

        result = pilot.run(
            max_iterations=args.max_iterations,
            auto_approve=args.auto_approve_gates
        )

        # Return exit code based on decision
        if result["autopilot"]["decision"] == "complete":
            return 0
        elif result["autopilot"]["decision"] == "stopped":
            return 1
        else:
            return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
