"""
Workflow Report Schema v1.0

Standardized report format for all RevitMCPBridge workflows.
Provides:
- Summary JSON (human-readable + machine-parseable)
- NDJSON forensic log
- Budget tracking
- Artifact tracking for rollback
- Postcondition verification
"""

import json
import time
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class RunStatus(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    STOPPED = "STOPPED"


class BudgetExceeded(Exception):
    """Raised when a budget limit is exceeded."""
    def __init__(self, budget_field: str, limit: int, usage: int, step_id: str = None):
        self.budget_field = budget_field
        self.limit = limit
        self.usage = usage
        self.step_id = step_id
        super().__init__(f"Budget exceeded: {budget_field} ({usage}/{limit}) at step {step_id}")


class Severity(Enum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class EventType(Enum):
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    MCP_CALL = "mcp_call"
    CHECK = "check"
    BUDGET = "budget"


@dataclass
class BudgetLimits:
    max_steps: int = 50
    max_total_retries: int = 5
    max_retries_per_step: int = 2
    max_elapsed_ms: int = 180000
    max_undos: int = 2


@dataclass
class BudgetUsage:
    steps: int = 0
    total_retries: int = 0
    undos: int = 0
    elapsed_ms: int = 0


@dataclass
class Issue:
    id: str
    severity: str
    message: str
    evidence: Optional[Dict[str, Any]] = None
    suggested_action: Optional[str] = None


@dataclass
class Artifact:
    type: str
    id: str
    name: Optional[str] = None
    cleanup: Optional[str] = None  # "delete" | "rollback" | None


@dataclass
class Export:
    type: str
    path: str
    sha256: Optional[str] = None


@dataclass
class Postcondition:
    id: str
    status: str  # "pass" | "fail" | "skip"
    details: Optional[Dict[str, Any]] = None


@dataclass
class Step:
    step_id: str
    status: str  # "ok" | "fail" | "skip"
    elapsed_ms: int = 0
    retries: int = 0
    mcp_calls: int = 0
    outputs: Optional[Dict[str, Any]] = None


class WorkflowReport:
    """
    Manages workflow execution reporting with standardized schema.

    Usage:
        report = WorkflowReport("door_schedule_preflight")
        report.set_environment(revit_version="2026", doc_title="TEST-4")

        # During workflow
        report.start_step("01_find_doors")
        result = report.log_mcp_call("getDoors", {}, response)
        report.add_artifact("schedule", "12345", "Door Schedule", cleanup="delete")
        report.end_step(outputs={"door_count": 26})

        # At end
        report.add_postcondition("EXPORT_EXISTS", "pass", {"path": "..."})
        report.finalize(RunStatus.PASS)
        report.save()
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, workflow: str, log_dir: Path = None):
        self.workflow = workflow
        self.run_id = str(uuid.uuid4())[:8]
        self.started_at = datetime.now(timezone.utc)
        self.ended_at: Optional[datetime] = None

        # Directories
        self.log_dir = log_dir or Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        ts = self.started_at.strftime("%Y%m%d_%H%M%S")
        self.summary_path = self.log_dir / f"{workflow}_{ts}_{self.run_id}.json"
        self.ndjson_path = self.log_dir / f"{workflow}_{ts}_{self.run_id}.ndjson"

        # Environment
        self.revit_version: Optional[str] = None
        self.bridge_version: str = "2026.1.0"
        self.doc_title: Optional[str] = None
        self.doc_path: Optional[str] = None
        self.doc_id: Optional[str] = None

        # Budgets
        self.budget_limits = BudgetLimits()
        self.budget_usage = BudgetUsage()
        self.budget_exceeded = False
        self.exceeded_fields: List[str] = []

        # Results
        self.status: RunStatus = RunStatus.PASS
        self.stopped_reason: Optional[str] = None
        self.issues: List[Issue] = []
        self.human_action_required = False

        # Artifacts
        self.artifacts_created: List[Artifact] = []
        self.artifacts_modified: List[Dict[str, Any]] = []
        self.exports: List[Export] = []
        self.cleanup_attempted = False
        self.cleanup_status = "pending"
        self.cleanup_notes: Optional[str] = None

        # Postconditions
        self.postconditions: List[Postcondition] = []

        # Steps
        self.steps: List[Step] = []
        self._current_step: Optional[Step] = None
        self._step_start_time: Optional[float] = None
        self._step_counter = 0
        self._ndjson_step_id = 0

        # Metrics (workflow-specific)
        self.metrics: Dict[str, Any] = {}

        # Budget enforcement state
        self._step_retries = 0  # Retries within current step
        self._is_stopped = False

        # Write workflow_start to NDJSON
        self._log_ndjson(EventType.WORKFLOW_START, workflow=workflow)

    @property
    def is_stopped(self) -> bool:
        """Check if workflow has been stopped due to budget or error."""
        return self._is_stopped

    def set_environment(self, revit_version: str = None, doc_title: str = None,
                       doc_path: str = None, doc_id: str = None):
        """Set environment info (call after first MCP response)."""
        if revit_version:
            self.revit_version = revit_version
        if doc_title:
            self.doc_title = doc_title
        if doc_path:
            self.doc_path = doc_path
        if doc_id:
            self.doc_id = doc_id

    def set_budget_limits(self, **kwargs):
        """Override default budget limits."""
        for key, value in kwargs.items():
            if hasattr(self.budget_limits, key):
                setattr(self.budget_limits, key, value)

    def start_step(self, step_id: str) -> bool:
        """
        Begin a new workflow step.

        BUDGET ENFORCEMENT CHOKE POINT #1:
        - Checks max_steps
        - Checks max_elapsed_ms

        Returns:
            bool: True if step can proceed, False if budget exceeded (workflow stopped)

        Raises:
            BudgetExceeded: If enforce_budgets=True and budget exceeded
        """
        # Check if already stopped
        if self._is_stopped:
            return False

        # Update elapsed time before check
        elapsed = int((datetime.now(timezone.utc) - self.started_at).total_seconds() * 1000)
        self.budget_usage.elapsed_ms = elapsed

        # ENFORCE: max_elapsed_ms
        if elapsed >= self.budget_limits.max_elapsed_ms:
            self._trigger_budget_stop("max_elapsed_ms", self.budget_limits.max_elapsed_ms,
                                      elapsed, step_id)
            return False

        # ENFORCE: max_steps (check BEFORE incrementing)
        if self.budget_usage.steps >= self.budget_limits.max_steps:
            self._trigger_budget_stop("max_steps", self.budget_limits.max_steps,
                                      self.budget_usage.steps, step_id)
            return False

        # Proceed with step
        self._step_counter += 1
        self._step_retries = 0  # Reset per-step retry counter
        self._current_step = Step(
            step_id=step_id,
            status="ok",
            elapsed_ms=0,
            retries=0,
            mcp_calls=0,
            outputs={}
        )
        self._step_start_time = time.time()
        return True

    def end_step(self, status: str = "ok", outputs: Dict[str, Any] = None):
        """Complete current step."""
        if self._current_step:
            self._current_step.status = status
            if self._step_start_time:
                self._current_step.elapsed_ms = int((time.time() - self._step_start_time) * 1000)
            if outputs:
                self._current_step.outputs = outputs
            self.steps.append(self._current_step)
            self.budget_usage.steps += 1
            self._check_budgets()
        self._current_step = None
        self._step_start_time = None

    def log_mcp_call(self, method: str, params: Dict[str, Any], response: Dict[str, Any],
                    elapsed_ms: float, retry_index: int = 0) -> tuple:
        """
        Log an MCP call and extract artifacts.

        BUDGET ENFORCEMENT CHOKE POINT #2:
        - Checks max_retries_per_step
        - Checks max_total_retries

        Returns:
            tuple: (response, should_continue) - should_continue is False if budget exceeded
        """
        # Check if already stopped
        if self._is_stopped:
            return response, False

        # Track in current step
        if self._current_step:
            self._current_step.mcp_calls += 1
            if retry_index > 0:
                self._current_step.retries += 1
                self._step_retries += 1
                self.budget_usage.total_retries += 1

        # Determine transaction state
        tx = "commit" if response.get("success") else "rollback"
        result = "ok" if response.get("success") else "fail"

        # Extract artifact references
        artifact_ref = {}
        for key in ["scheduleId", "sheetId", "wallId", "elementId", "viewId", "viewportId"]:
            if key in response:
                artifact_ref[key] = response[key]

        # Log to NDJSON BEFORE budget check (so we have record of the call)
        self._log_ndjson(
            EventType.MCP_CALL,
            method=method,
            args_summary=self._summarize_args(params),
            tx=tx,
            elapsed_ms=round(elapsed_ms, 2),
            result=result,
            retry_index=retry_index,
            artifact_ref=artifact_ref if artifact_ref else None,
            error=response.get("error") if not response.get("success") else None
        )

        # ENFORCE: max_retries_per_step
        step_id = self._current_step.step_id if self._current_step else "unknown"
        if self._step_retries >= self.budget_limits.max_retries_per_step:
            self._trigger_budget_stop("max_retries_per_step", self.budget_limits.max_retries_per_step,
                                      self._step_retries, step_id)
            return response, False

        # ENFORCE: max_total_retries
        if self.budget_usage.total_retries >= self.budget_limits.max_total_retries:
            self._trigger_budget_stop("max_total_retries", self.budget_limits.max_total_retries,
                                      self.budget_usage.total_retries, step_id)
            return response, False

        self._check_budgets()
        return response, True

    def add_artifact(self, artifact_type: str, artifact_id: str,
                    name: str = None, cleanup: str = "delete"):
        """Track a created artifact for potential rollback."""
        self.artifacts_created.append(Artifact(
            type=artifact_type,
            id=str(artifact_id),
            name=name,
            cleanup=cleanup
        ))

    def add_modified(self, artifact_type: str, artifact_id: str, **changes):
        """Track a modified artifact."""
        self.artifacts_modified.append({
            "type": artifact_type,
            "id": str(artifact_id),
            **changes
        })

    def add_export(self, export_type: str, path: str, compute_hash: bool = False):
        """Track an exported file."""
        sha256 = None
        if compute_hash:
            try:
                with open(path, "rb") as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()
            except:
                pass
        self.exports.append(Export(type=export_type, path=path, sha256=sha256))

    def add_issue(self, issue_id: str, severity: Severity, message: str,
                 evidence: Dict[str, Any] = None, suggested_action: str = None):
        """Add an issue found during workflow."""
        self.issues.append(Issue(
            id=issue_id,
            severity=severity.value,
            message=message,
            evidence=evidence,
            suggested_action=suggested_action
        ))

        # Update status based on severity
        if severity == Severity.BLOCKER:
            self.status = RunStatus.FAIL

    def add_postcondition(self, condition_id: str, status: str,
                         details: Dict[str, Any] = None):
        """Add a postcondition check result."""
        self.postconditions.append(Postcondition(
            id=condition_id,
            status=status,
            details=details
        ))

    def set_metric(self, key: str, value: Any):
        """Set a workflow-specific metric."""
        self.metrics[key] = value

    def record_cleanup(self, status: str, notes: str = None):
        """Record cleanup attempt results."""
        self.cleanup_attempted = True
        self.cleanup_status = status
        self.cleanup_notes = notes

    def check_budget(self, field: str) -> bool:
        """Check if a specific budget is exceeded. Returns True if OK."""
        limit = getattr(self.budget_limits, field, None)
        usage = getattr(self.budget_usage, field, None)
        if limit is not None and usage is not None:
            return usage < limit
        return True

    def stop(self, reason: str):
        """Stop workflow execution due to budget or error."""
        self._is_stopped = True
        self.status = RunStatus.STOPPED
        self.stopped_reason = reason
        self.human_action_required = True
        self._log_ndjson(EventType.BUDGET, exceeded=True, reason=reason)

    def _trigger_budget_stop(self, budget_field: str, limit: int, usage: int, step_id: str):
        """
        Internal method to trigger a budget stop with proper reporting.
        Called by enforcement choke points.
        """
        self._is_stopped = True
        self.budget_exceeded = True
        if budget_field not in self.exceeded_fields:
            self.exceeded_fields.append(budget_field)

        reason = f"{budget_field} exceeded ({usage}/{limit}) at step {step_id}"
        self.stopped_reason = reason
        self.status = RunStatus.STOPPED
        self.human_action_required = True

        # Add blocker issue
        self.issues.append(Issue(
            id="BUDGET_EXCEEDED",
            severity="blocker",
            message=reason,
            evidence={
                "budget_field": budget_field,
                "limit": limit,
                "usage": usage,
                "step_id": step_id
            },
            suggested_action=f"Reduce workflow complexity or increase {budget_field} limit"
        ))

        # Log budget event
        self._log_ndjson(EventType.BUDGET, exceeded=True, reason=reason,
                        budget_field=budget_field, limit=limit, usage=usage)

    def record_undo(self) -> bool:
        """
        Record an undo/rollback operation.

        BUDGET ENFORCEMENT CHOKE POINT #3:
        - Checks max_undos

        Returns:
            bool: True if undo can proceed, False if budget exceeded
        """
        if self._is_stopped:
            return False

        self.budget_usage.undos += 1

        # ENFORCE: max_undos
        if self.budget_usage.undos > self.budget_limits.max_undos:
            step_id = self._current_step.step_id if self._current_step else "cleanup"
            self._trigger_budget_stop("max_undos", self.budget_limits.max_undos,
                                      self.budget_usage.undos, step_id)
            return False

        return True

    def finalize(self, status: RunStatus = None):
        """Finalize the report before saving."""
        self.ended_at = datetime.now(timezone.utc)

        # Calculate duration
        duration = self.ended_at - self.started_at
        self.budget_usage.elapsed_ms = int(duration.total_seconds() * 1000)

        # Set final status
        if status:
            self.status = status
        elif self.budget_exceeded:
            self.status = RunStatus.STOPPED
        elif any(i.severity == "blocker" for i in self.issues):
            self.status = RunStatus.FAIL
        elif any(i.severity == "warning" for i in self.issues):
            self.status = RunStatus.WARN

        # Check postconditions
        failed_postconditions = [p for p in self.postconditions if p.status == "fail"]
        if failed_postconditions and self.status == RunStatus.PASS:
            self.status = RunStatus.FAIL

        # Determine human action required
        self.human_action_required = (
            self.status == RunStatus.STOPPED or
            self.status == RunStatus.FAIL or
            any(i.severity == "blocker" for i in self.issues)
        )

        # Log workflow end
        self._log_ndjson(
            EventType.WORKFLOW_END,
            status=self.status.value,
            duration_ms=self.budget_usage.elapsed_ms
        )

    def _check_budgets(self):
        """Check all budgets and update exceeded status."""
        checks = [
            ("steps", self.budget_usage.steps, self.budget_limits.max_steps),
            ("total_retries", self.budget_usage.total_retries, self.budget_limits.max_total_retries),
            ("elapsed_ms", self.budget_usage.elapsed_ms, self.budget_limits.max_elapsed_ms),
            ("undos", self.budget_usage.undos, self.budget_limits.max_undos),
        ]

        for field, usage, limit in checks:
            if usage >= limit and field not in self.exceeded_fields:
                self.exceeded_fields.append(field)
                self.budget_exceeded = True

    def _summarize_args(self, params: Dict[str, Any], max_len: int = 80) -> str:
        """Create a summary of arguments for logging."""
        if not params:
            return "None"
        s = str(params)
        return s[:max_len] if len(s) <= max_len else s[:max_len-3] + "..."

    def _log_ndjson(self, event_type: EventType, **kwargs):
        """Write an entry to the NDJSON log."""
        self._ndjson_step_id += 1
        entry = {
            "event_type": event_type.value,
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "step_id": self._ndjson_step_id,
        }

        # Add doc_title on workflow_start
        if event_type == EventType.WORKFLOW_START and self.doc_title:
            entry["doc_title"] = self.doc_title

        # Add other kwargs, filtering None values
        for k, v in kwargs.items():
            if v is not None:
                entry[k] = v

        with open(self.ndjson_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def to_dict(self) -> Dict[str, Any]:
        """Generate the full summary JSON structure."""
        # Count severities
        severity_counts = {"blocker": 0, "warning": 0, "info": 0}
        for issue in self.issues:
            if issue.severity in severity_counts:
                severity_counts[issue.severity] += 1

        return {
            "schema_version": self.SCHEMA_VERSION,
            "run": {
                "run_id": self.run_id,
                "workflow": self.workflow,
                "started_at": self.started_at.isoformat(),
                "ended_at": self.ended_at.isoformat() if self.ended_at else None,
                "duration_ms": self.budget_usage.elapsed_ms,
                "status": self.status.value,
                "stopped_reason": self.stopped_reason
            },
            "environment": {
                "revit_version": self.revit_version,
                "bridge_version": self.bridge_version,
                "machine": None,
                "document": {
                    "title": self.doc_title,
                    "path": self.doc_path,
                    "doc_id": self.doc_id
                }
            },
            "budgets": {
                "limits": asdict(self.budget_limits),
                "usage": asdict(self.budget_usage),
                "exceeded": self.budget_exceeded,
                "exceeded_fields": self.exceeded_fields
            },
            "results": {
                "passed": self.status in (RunStatus.PASS, RunStatus.WARN),
                "severity_counts": severity_counts,
                "issues": [asdict(i) for i in self.issues],
                "human_action_required": self.human_action_required
            },
            "artifacts": {
                "created": [asdict(a) for a in self.artifacts_created],
                "modified": self.artifacts_modified,
                "exports": [asdict(e) for e in self.exports],
                "cleanup": {
                    "attempted": self.cleanup_attempted,
                    "status": self.cleanup_status,
                    "notes": self.cleanup_notes
                }
            },
            "postconditions": [asdict(p) for p in self.postconditions],
            "steps": [asdict(s) for s in self.steps],
            "metrics": self.metrics
        }

    def save(self) -> Path:
        """Save the summary JSON and return path."""
        with open(self.summary_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        return self.summary_path

    def print_summary(self):
        """Print a human-readable summary to console."""
        print("\n" + "=" * 60)
        print(f"WORKFLOW REPORT: {self.workflow}")
        print("=" * 60)
        print(f"Run ID:   {self.run_id}")
        print(f"Status:   {self.status.value}")
        print(f"Duration: {self.budget_usage.elapsed_ms}ms")
        print("-" * 60)

        # Budgets
        print("Budgets:")
        print(f"  Steps:   {self.budget_usage.steps}/{self.budget_limits.max_steps}")
        print(f"  Retries: {self.budget_usage.total_retries}/{self.budget_limits.max_total_retries}")
        print(f"  Time:    {self.budget_usage.elapsed_ms}/{self.budget_limits.max_elapsed_ms}ms")
        if self.budget_exceeded:
            print(f"  EXCEEDED: {', '.join(self.exceeded_fields)}")
        print("-" * 60)

        # Steps
        print("Steps:")
        for step in self.steps:
            icon = "✓" if step.status == "ok" else "✗" if step.status == "fail" else "⚠"
            print(f"  {icon} {step.step_id}: {step.status} ({step.elapsed_ms}ms, {step.mcp_calls} calls)")
        print("-" * 60)

        # Artifacts
        if self.artifacts_created:
            print(f"Artifacts Created: {len(self.artifacts_created)}")
            for a in self.artifacts_created:
                print(f"  - {a.type}: {a.id} ({a.name})")

        if self.exports:
            print(f"Exports: {len(self.exports)}")
            for e in self.exports:
                print(f"  - {e.type}: {e.path}")
        print("-" * 60)

        # Issues
        if self.issues:
            print("Issues:")
            for issue in self.issues:
                print(f"  [{issue.severity.upper()}] {issue.id}: {issue.message}")

        # Postconditions
        if self.postconditions:
            print("Postconditions:")
            for pc in self.postconditions:
                icon = "✓" if pc.status == "pass" else "✗"
                print(f"  {icon} {pc.id}: {pc.status}")

        print("-" * 60)
        if self.human_action_required:
            print("⚠ HUMAN ACTION REQUIRED")
        print(f"Summary: {self.summary_path}")
        print(f"Log:     {self.ndjson_path}")
        print("=" * 60)
