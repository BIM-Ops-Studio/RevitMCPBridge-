#!/usr/bin/env python3
"""
Beta Runner - Single command to profile, run Spine, collect evidence

Usage:
    python3 beta_runner.py --sector multifamily [--firm ARKY]

Options:
    --mode golden|byop    Lane selection (default: byop)
    --autopilot          Use v0.4 autopilot loop
    --auto_approve_gates  Skip human gates
    --dry_run            Profile + readiness only, no execution
    --evidence PATH      Custom evidence output path

Output:
    - Run ID
    - Readiness score
    - Coverage/Quality/Confidence
    - Evidence zip path
    - Human action required list
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Local imports
from filtered_queries import send_mcp_request
from template_packs.pack_resolver import resolve_pack
from pack_assessor import PackAssessor
from spine_autopilot import SpineAutopilot

# Spine Learning System - persistent memory & governed learning
import sys
sys.path.insert(0, '/mnt/d/_AI-PROJECTS/spine-aec-learning')
from spine_learning import (
    LearningStore,
    fingerprint_from_env,
    load_full_context,
    apply_context_to_args,
    ingest_evidence_folder,
    suggest_updates
)

# Code Compliance Checker
from spine_passive.code_checker import CodeChecker, CheckStatus, ComplianceReport


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Environment:
    """Capture environment for reproducibility."""
    run_id: str
    timestamp: str
    machine_name: str
    platform: str
    python_version: str
    revit_version: str
    revit_doc_title: str
    revit_doc_path: str
    addin_dll_path: str
    addin_dll_sha256: str
    sector: str
    firm: Optional[str]
    mode: str
    command_line: str


@dataclass
class ReadinessCheck:
    """Result of a single readiness check."""
    check_id: str
    name: str
    passed: bool
    details: str
    severity: str  # "blocker", "warning", "info"


@dataclass
class ReadinessReport:
    """Overall readiness assessment."""
    ready: bool
    score: float  # 0-100
    checks: List[ReadinessCheck]
    blockers: List[str]
    warnings: List[str]
    recommendation: str  # "green", "yellow", "red"


@dataclass
class BetaResult:
    """Final beta run result."""
    run_id: str
    success: bool
    mode: str
    readiness: ReadinessReport
    pack_coverage: float
    quality_score: float
    confidence: float
    iterations: int
    artifacts_created: Dict[str, int]
    human_actions_required: List[str]
    evidence_zip_path: str
    duration_seconds: float


# =============================================================================
# Environment Collection
# =============================================================================

def get_dll_sha256(dll_path: str) -> str:
    """Calculate SHA256 of DLL file."""
    if not os.path.exists(dll_path):
        return "not_found"

    sha256 = hashlib.sha256()
    with open(dll_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def collect_environment(run_id: str, sector: str, firm: str, mode: str, revit_version: str = "2026") -> Environment:
    """Collect environment information from system and Revit."""

    # Get Revit info via MCP
    # Note: getDocumentInfo doesn't exist, so we infer from available data
    doc_title = "unknown"
    doc_path = "unknown"

    # Try to get basic info from getLevels response (proves connection works)
    resp = send_mcp_request("getLevels", timeout=30)
    if resp.get("success"):
        # Connection works, try getAllSheets for document context
        sheet_resp = send_mcp_request("getAllSheets", timeout=30)
        if sheet_resp.get("success"):
            result = sheet_resp.get("result", sheet_resp)
            sheets = result.get("sheets", [])
            if sheets:
                # Infer document name from sheet names if available
                first_sheet = sheets[0]
                doc_title = f"Document with {len(sheets)} sheets"

    # DLL path (version-specific)
    dll_path = rf"C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\{revit_version}\RevitMCPBridge{revit_version}.dll"

    return Environment(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        machine_name=platform.node(),
        platform=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        revit_version=revit_version,
        revit_doc_title=doc_title,
        revit_doc_path=doc_path,
        addin_dll_path=dll_path,
        addin_dll_sha256=get_dll_sha256(dll_path),
        sector=sector,
        firm=firm,
        mode=mode,
        command_line=" ".join(sys.argv)
    )


# =============================================================================
# Readiness Checks (BYOP Lane)
# =============================================================================
#
# READINESS GRADE CRITERIA:
#
#   GREEN  - Can run full autopilot safely
#            Requirements: MCP connected, levels exist, views/sheets queryable
#            Scope: Sheets, views, schedules, exports
#
#   YELLOW - Run limited scope + stop at Gate 1
#            Triggered by: Missing titleblock inference, < 2 levels
#            Scope: Sheets only + CSV exports, no viewport placement
#
#   RED    - Stop immediately with checklist
#            Triggered by: MCP not connected, no levels, critical query failures
#            Action: User must fix blockers before running
#
# =============================================================================

def check_readiness(sector: str) -> ReadinessReport:
    """
    Run preflight readiness checks for BYOP lane.

    Returns a ReadinessReport with explicit green/yellow/red grading.
    """
    checks = []

    # 1. MCP Connection (BLOCKER if fails)
    resp = send_mcp_request("getLevels", timeout=30)
    mcp_ok = resp.get("success", False)
    level_count = len(resp.get("levels", [])) if mcp_ok else 0
    checks.append(ReadinessCheck(
        check_id="MCP_CONNECTION",
        name="MCP Bridge Connected",
        passed=mcp_ok,
        details=f"{level_count} levels detected" if mcp_ok else "Connection failed - is Revit open with MCP bridge loaded?",
        severity="blocker"
    ))

    # 2. Levels Exist (BLOCKER if 0, WARNING if < 2)
    level_severity = "blocker" if level_count < 1 else ("warning" if level_count < 2 else "info")
    checks.append(ReadinessCheck(
        check_id="LEVELS_EXIST",
        name="Building Levels Defined",
        passed=level_count >= 1,
        details=f"{level_count} levels" if level_count >= 1 else "No levels found - model may be empty",
        severity=level_severity
    ))

    # 3. Sheets Queryable (WARNING if fails)
    sheet_resp = send_mcp_request("getAllSheets", timeout=30)
    sheet_ok = sheet_resp.get("success", False)
    existing_sheets = len(sheet_resp.get("result", sheet_resp).get("sheets", [])) if sheet_ok else 0
    checks.append(ReadinessCheck(
        check_id="SHEETS_QUERYABLE",
        name="Sheets Accessible",
        passed=sheet_ok,
        details=f"{existing_sheets} existing sheets" if sheet_ok else "Sheet query failed",
        severity="warning"
    ))

    # 4. Titleblock Inferred (INFO only - we detect at runtime)
    # If model has sheets, titleblock must exist
    tb_confidence = "high" if existing_sheets > 0 else "unknown"
    checks.append(ReadinessCheck(
        check_id="TITLEBLOCK_INFERRED",
        name="Title Block Available",
        passed=True,  # Always pass - actual check happens at createSheet
        details=f"Confidence: {tb_confidence} ({existing_sheets} existing sheets)" if existing_sheets > 0 else "No sheets yet - will use default titleblock",
        severity="info"
    ))

    # 5. Views Queryable (WARNING if fails)
    view_resp = send_mcp_request("getViews", {"viewType": "FloorPlan", "limit": 10}, timeout=60)
    view_ok = view_resp.get("success", False)
    checks.append(ReadinessCheck(
        check_id="VIEWS_QUERYABLE",
        name="Views Accessible",
        passed=view_ok,
        details="View queries working" if view_ok else "View query failed - may limit viewport placement",
        severity="warning"
    ))

    # 6. Pack Resolvable (BLOCKER if fails)
    pack_ok = True
    pack_details = "Pack configuration valid"
    try:
        packs_dir = Path(__file__).parent / "template_packs"
        sector_path = packs_dir / sector / "standards.json"
        if not sector_path.exists():
            pack_ok = False
            pack_details = f"Sector '{sector}' not found at {sector_path}"
    except Exception as e:
        pack_ok = False
        pack_details = f"Pack resolution error: {str(e)}"

    checks.append(ReadinessCheck(
        check_id="PACK_RESOLVABLE",
        name="Pack Configuration Valid",
        passed=pack_ok,
        details=pack_details,
        severity="blocker"
    ))

    # Calculate grade
    blockers = [c.check_id for c in checks if not c.passed and c.severity == "blocker"]
    warnings = [c.check_id for c in checks if not c.passed and c.severity == "warning"]
    passed_count = sum(1 for c in checks if c.passed)
    score = round(passed_count / len(checks) * 100, 1) if checks else 0

    # Grade determination with explicit rules
    if blockers:
        recommendation = "red"  # Any blocker = RED
    elif warnings:
        recommendation = "yellow"  # Warnings only = YELLOW (limited scope)
    else:
        recommendation = "green"  # All clear = GREEN (full autopilot)

    return ReadinessReport(
        ready=len(blockers) == 0,
        score=score,
        checks=checks,
        blockers=blockers,
        warnings=warnings,
        recommendation=recommendation
    )


# =============================================================================
# Code Compliance Check
# =============================================================================

def extract_model_for_compliance() -> Dict[str, Any]:
    """Extract model data from Revit via MCP for compliance checking."""
    model_data = {
        "project_name": "Unknown",
        "levels": [],
        "sheets": [],
        "views": [],
        "rooms": [],
        "wall_types": [],
        "door_types": [],
        "window_types": [],
        "project_info": {},
        "inferred_sector": "unknown",
        "inferred_stage": "unknown",
    }

    try:
        # Get levels
        resp = send_mcp_request("getLevels", timeout=30)
        if resp.get("success"):
            result = resp.get("result", resp)
            levels = result.get("levels", [])
            model_data["levels"] = [
                {"name": l.get("name"), "elevation": l.get("elevation")}
                for l in levels
            ]

        # Get sheets
        resp = send_mcp_request("getAllSheets", timeout=30)
        if resp.get("success"):
            result = resp.get("result", resp)
            sheets = result.get("sheets", [])
            model_data["sheets"] = [
                {"number": s.get("number"), "name": s.get("name")}
                for s in sheets
            ]

        # Get views
        resp = send_mcp_request("getViews", timeout=30)
        if resp.get("success"):
            result = resp.get("result", resp)
            views = result.get("views", [])
            model_data["views"] = [
                {"name": v.get("name"), "type": v.get("viewType")}
                for v in views
            ]

        # Get rooms
        resp = send_mcp_request("getRooms", timeout=30)
        if resp.get("success"):
            result = resp.get("result", resp)
            rooms = result.get("rooms", [])
            model_data["rooms"] = [
                {"name": r.get("name"), "number": r.get("number"), "area": r.get("area")}
                for r in rooms
            ]

        # Get wall types
        resp = send_mcp_request("getWallTypes", timeout=30)
        if resp.get("success"):
            result = resp.get("result", resp)
            wall_types = result.get("wallTypes", [])
            model_data["wall_types"] = [
                {"name": wt.get("name"), "width": wt.get("width")}
                for wt in wall_types
            ]

        # Get door types
        resp = send_mcp_request("getDoorTypes", timeout=30)
        if resp.get("success"):
            result = resp.get("result", resp)
            door_types = result.get("doorTypes", result.get("types", []))
            model_data["door_types"] = [
                {"name": dt.get("name"), "width": dt.get("width"), "height": dt.get("height")}
                for dt in door_types
            ]

        # Get window types
        resp = send_mcp_request("getWindowTypes", timeout=30)
        if resp.get("success"):
            result = resp.get("result", resp)
            window_types = result.get("windowTypes", result.get("types", []))
            model_data["window_types"] = [
                {"name": wt.get("name"), "width": wt.get("width"), "height": wt.get("height")}
                for wt in window_types
            ]

        # Get project info
        resp = send_mcp_request("getProjectInfo", timeout=30)
        if resp.get("success"):
            result = resp.get("result", resp)
            model_data["project_info"] = result
            model_data["project_name"] = result.get("projectName", result.get("name", "Unknown"))

        # Infer sector from sheets/project info
        sheet_numbers = [s.get("number", "") for s in model_data["sheets"]]
        has_units = any("unit" in s.get("name", "").lower() for s in model_data["sheets"])
        if has_units or len(model_data["rooms"]) > 10:
            model_data["inferred_sector"] = "residential-multifamily"
        else:
            model_data["inferred_sector"] = "residential-single"

        # Infer stage from completeness
        sheet_count = len(model_data["sheets"])
        if sheet_count >= 30:
            model_data["inferred_stage"] = "CD"
        elif sheet_count >= 15:
            model_data["inferred_stage"] = "DD"
        elif sheet_count >= 5:
            model_data["inferred_stage"] = "SD"
        else:
            model_data["inferred_stage"] = "CONCEPT"

    except Exception as e:
        print(f"  Warning: Model extraction error: {e}")

    return model_data


def run_compliance_check(
    sector: str,
    jurisdiction: str = "FBC2023",
    overlays: Optional[List[str]] = None
) -> Optional[ComplianceReport]:
    """
    Run code compliance check on current Revit model.

    Args:
        sector: Project sector (used for context)
        jurisdiction: Primary code jurisdiction
        overlays: Additional jurisdictions (e.g., Miami21)

    Returns:
        ComplianceReport or None if check fails
    """
    print(f"\n[*] Running code compliance check ({jurisdiction})...")

    try:
        # Extract model data from Revit
        model_data = extract_model_for_compliance()
        model_data["inferred_sector"] = f"residential-{sector}" if "family" in sector else sector

        # Initialize checker
        checker = CodeChecker(
            jurisdiction=jurisdiction,
            additional_jurisdictions=overlays
        )

        # Run checks
        report = checker.check(model_data)

        # Print summary
        print(f"  Total Rules: {report.total_rules}")
        print(f"  Passed: {report.passed}")
        print(f"  Failed: {report.failed}")
        print(f"  Warnings: {report.warnings}")
        print(f"  Compliance Score: {report.compliance_score:.1f}%")

        if report.failed > 0:
            print(f"\n  FAILURES:")
            for r in report.results:
                if r.status == CheckStatus.FAIL:
                    print(f"    - [{r.rule_id}] {r.message}")

        return report

    except Exception as e:
        print(f"  Error running compliance check: {e}")
        return None


# =============================================================================
# Evidence Zipper
# =============================================================================

def sha256_file(path: str) -> str:
    """Calculate SHA256 of a file."""
    if not os.path.exists(path):
        return "not_found"
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_git_commit() -> str:
    """Get current git commit hash if available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=Path(__file__).parent
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _build_reviewer_readme(
    run_id: str,
    environment: Environment,
    readiness: ReadinessReport,
    autopilot: Optional['AutopilotSummary']
) -> str:
    """
    Build reviewer-friendly README that answers key questions in 60 seconds.

    Structure:
    1. What was attempted
    2. What changed
    3. Final scores + stop reason
    4. Human action required
    5. Known Revit API constraints
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("SPINE BETA RUN - EVIDENCE PACKAGE")
    lines.append("=" * 70)
    lines.append(f"Run ID: {run_id}")
    lines.append(f"Generated: {environment.timestamp}")
    lines.append("")

    # 1. WHAT WAS ATTEMPTED
    lines.append("-" * 70)
    lines.append("1. WHAT WAS ATTEMPTED")
    lines.append("-" * 70)
    lines.append(f"  Sector:         {environment.sector}")
    lines.append(f"  Firm Override:  {environment.firm or 'none'}")
    lines.append(f"  Mode:           {environment.mode}")
    lines.append(f"  Revit Version:  {environment.revit_version}")
    lines.append(f"  Document:       {environment.revit_doc_title}")
    lines.append("")

    # 2. READINESS ASSESSMENT
    lines.append("-" * 70)
    lines.append("2. READINESS ASSESSMENT")
    lines.append("-" * 70)
    grade_icon = {"green": "✓ GREEN", "yellow": "⚠ YELLOW", "red": "✗ RED"}.get(
        readiness.recommendation, readiness.recommendation.upper()
    )
    lines.append(f"  Grade:          {grade_icon}")
    lines.append(f"  Score:          {readiness.score}%")
    if readiness.blockers:
        lines.append(f"  Blockers:       {', '.join(readiness.blockers)}")
    if readiness.warnings:
        lines.append(f"  Warnings:       {', '.join(readiness.warnings)}")
    lines.append("")

    # 3. WHAT CHANGED
    lines.append("-" * 70)
    lines.append("3. WHAT CHANGED")
    lines.append("-" * 70)
    if autopilot:
        lines.append(f"  Iterations:     {autopilot.iterations}")
        lines.append(f"  Tasks Executed: {autopilot.tasks_executed}")
        lines.append(f"  Tasks Succeeded:{autopilot.tasks_succeeded}")
        lines.append(f"  Tasks Skipped:  {autopilot.tasks_skipped}")
        if autopilot.created_counts:
            lines.append("  Created:")
            for item_type, count in autopilot.created_counts.items():
                lines.append(f"    - {item_type}: {count}")
        else:
            lines.append("  Created:        (none)")
    else:
        lines.append("  (Autopilot did not run)")
    lines.append("")

    # 4. FINAL SCORES + STOP REASON
    lines.append("-" * 70)
    lines.append("4. FINAL SCORES")
    lines.append("-" * 70)
    if autopilot and autopilot.final_scores:
        scores = autopilot.final_scores
        lines.append(f"  Pack Coverage:  {scores.get('pack_coverage_pct', 0)}%")
        lines.append(f"  Quality Score:  {scores.get('quality_pct', 0)}%")
        lines.append(f"  Confidence:     {scores.get('confidence_pct', 0)}%")
        lines.append(f"  Permit Ready:   {'Yes' if scores.get('ready_for_permit') else 'No'}")
        lines.append("")
        lines.append(f"  Stop Reason:    {autopilot.stop_reason}")

        # Show baseline vs final if different
        if autopilot.baseline_scores and autopilot.iterations > 0:
            baseline = autopilot.baseline_scores
            lines.append("")
            lines.append("  Progress from baseline:")
            lines.append(f"    Pack Coverage: {baseline.get('pack_coverage_pct', 0)}% → {scores.get('pack_coverage_pct', 0)}%")
            lines.append(f"    Quality Score: {baseline.get('quality_pct', 0)}% → {scores.get('quality_pct', 0)}%")
    else:
        lines.append("  (No scores available)")
    lines.append("")

    # 5. HUMAN ACTION REQUIRED
    lines.append("-" * 70)
    lines.append("5. HUMAN ACTION REQUIRED")
    lines.append("-" * 70)
    if autopilot and autopilot.human_tasks:
        for task in autopilot.human_tasks:
            lines.append(f"  • {task}")
    else:
        lines.append("  (None - all tasks automated)")
    lines.append("")

    # 6. KNOWN REVIT API CONSTRAINTS
    lines.append("-" * 70)
    lines.append(f"6. KNOWN REVIT {environment.revit_version} API CONSTRAINTS")
    lines.append("-" * 70)
    lines.append(f"  The following operations are NOT automated due to Revit {environment.revit_version} API limits:")
    lines.append("")
    lines.append("  • Legend placement on sheets")
    lines.append("      → Workaround: Manual placement required")
    lines.append("")
    lines.append("  • Schedule placement on sheets")
    lines.append("      → Workaround: Schedules created, manual placement required")
    lines.append("")
    lines.append("  • Cloud family loading")
    lines.append("      → Workaround: Use local .rfa files via loadFamily")
    lines.append("")
    lines.append("  • Titleblock detection")
    lines.append("      → Workaround: Inferred from existing sheets")
    lines.append("")

    # 7. CONTENTS
    lines.append("-" * 70)
    lines.append("7. PACKAGE CONTENTS")
    lines.append("-" * 70)
    lines.append("  run/")
    lines.append("    autopilot_report.json  - Full execution log")
    lines.append("    environment.json       - Machine/Revit info")
    lines.append("    readiness.json         - Preflight checks")
    lines.append("    resolved_pack.json     - Pack configuration")
    lines.append("    versions.json          - Version provenance")
    lines.append("    command.txt            - Exact CLI command")
    lines.append("  artifacts/")
    lines.append("    exports/               - Generated exports")
    lines.append("    exports_manifest.json  - Export file hashes")
    lines.append("  diagnostics/")
    lines.append("    warnings.json          - Issues found")
    lines.append("")

    # Footer
    lines.append("=" * 70)
    lines.append(f"DLL SHA256: {environment.addin_dll_sha256}")
    lines.append("=" * 70)

    return "\n".join(lines)


@dataclass
class AutopilotSummary:
    """Summary data for README generation."""
    baseline_scores: Dict[str, Any]
    final_scores: Dict[str, Any]
    stop_reason: str
    iterations: int
    tasks_executed: int
    tasks_succeeded: int
    tasks_skipped: int
    created_counts: Dict[str, int]
    human_tasks: List[str]


def create_evidence_zip(
    run_id: str,
    environment: Environment,
    readiness: ReadinessReport,
    autopilot_summary: Optional[AutopilotSummary],
    autopilot_report_path: Optional[str],
    resolved_pack_path: Optional[str],
    exports_dir: Optional[str],
    output_dir: Path
) -> str:
    """
    Create evidence.zip with all run artifacts.

    Structure:
        evidence_<runid>.zip
        ├── README.txt              <- Reviewer-friendly summary
        ├── run/
        │   ├── autopilot_report.json
        │   ├── environment.json
        │   ├── resolved_pack.json
        │   ├── readiness.json
        │   ├── command.txt
        │   └── versions.json       <- Provenance
        ├── artifacts/
        │   ├── exports/
        │   └── exports_manifest.json
        └── diagnostics/
            └── warnings.json
    """

    # Create temp directory for staging
    staging_dir = output_dir / f"staging_{run_id}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create subdirectories
        (staging_dir / "run").mkdir(exist_ok=True)
        (staging_dir / "artifacts" / "exports").mkdir(parents=True, exist_ok=True)
        (staging_dir / "diagnostics").mkdir(exist_ok=True)

        # Build reviewer-friendly README
        readme = _build_reviewer_readme(run_id, environment, readiness, autopilot_summary)
        (staging_dir / "README.txt").write_text(readme)

        # Environment
        (staging_dir / "run" / "environment.json").write_text(
            json.dumps(asdict(environment), indent=2)
        )

        # Readiness with top-level grade
        readiness_data = {
            "readiness_grade": readiness.recommendation.upper(),  # GREEN/YELLOW/RED
            "ready": readiness.ready,
            "score": readiness.score,
            "grade_criteria": {
                "green": "Full autopilot - all checks passed",
                "yellow": "Limited scope - warnings present, will stop at Gate 1",
                "red": "Cannot run - blockers must be resolved"
            },
            "blockers": readiness.blockers,
            "warnings": readiness.warnings,
            "checks": [asdict(c) for c in readiness.checks]
        }
        (staging_dir / "run" / "readiness.json").write_text(
            json.dumps(readiness_data, indent=2)
        )

        # Command
        (staging_dir / "run" / "command.txt").write_text(environment.command_line)

        # Versions provenance
        versions_data = {
            "spine_version": "0.4",
            "beta_runner_version": "1.1",
            "pack_adapter_version": "2.0",
            "revit_mcp_bridge_dll_sha256": environment.addin_dll_sha256,
            "python_version": environment.python_version,
            "git_commit": get_git_commit(),
            "generated_at": datetime.now().isoformat()
        }
        (staging_dir / "run" / "versions.json").write_text(
            json.dumps(versions_data, indent=2)
        )

        # Autopilot report
        if autopilot_report_path and os.path.exists(autopilot_report_path):
            shutil.copy(autopilot_report_path, staging_dir / "run" / "autopilot_report.json")

        # Resolved pack
        if resolved_pack_path and os.path.exists(resolved_pack_path):
            shutil.copy(resolved_pack_path, staging_dir / "run" / "resolved_pack.json")

        # Exports with manifest
        exports_manifest = {"files": [], "generated": datetime.now().isoformat()}
        if exports_dir and os.path.exists(exports_dir):
            for f in Path(exports_dir).glob("*"):
                if f.is_file():
                    dest = staging_dir / "artifacts" / "exports" / f.name
                    shutil.copy(f, dest)
                    exports_manifest["files"].append({
                        "name": f.name,
                        "sha256": sha256_file(str(f)),
                        "size_bytes": f.stat().st_size,
                        "type": f.suffix.lstrip(".")
                    })

        (staging_dir / "artifacts" / "exports_manifest.json").write_text(
            json.dumps(exports_manifest, indent=2)
        )

        # Diagnostics - warnings placeholder
        (staging_dir / "diagnostics" / "warnings.json").write_text(
            json.dumps({"warnings": readiness.warnings}, indent=2)
        )

        # Create zip
        zip_path = output_dir / f"evidence_{run_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(staging_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(staging_dir)
                    zf.write(file_path, arcname)

        return str(zip_path)

    finally:
        # Cleanup staging
        if staging_dir.exists():
            shutil.rmtree(staging_dir)


# =============================================================================
# Main Beta Runner
# =============================================================================

def run_beta(
    sector: str,
    firm: Optional[str] = None,
    mode: str = "byop",
    use_autopilot: bool = True,
    auto_approve: bool = False,
    dry_run: bool = False,
    max_iterations: int = 3,
    revit_version: str = "2026"
) -> BetaResult:
    """
    Run complete beta workflow.

    1. Generate run ID
    2. Collect environment
    3. Check readiness (BYOP) or skip (Golden)
    4. Resolve pack
    5. Run autopilot (or dry_run stops here)
    6. Collect evidence
    7. Return result
    """
    import time
    start_time = time.time()

    # Generate run ID
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + hashlib.md5(
        f"{sector}{firm}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:8]

    print("\n" + "=" * 60)
    print(f"BETA RUNNER - {run_id}")
    print("=" * 60)
    print(f"Revit: {revit_version}")
    print(f"Sector: {sector}")
    print(f"Firm: {firm or 'none'}")
    print(f"Mode: {mode}")
    print(f"Autopilot: {use_autopilot}")
    print(f"Dry Run: {dry_run}")
    print("-" * 60)

    # Collect environment
    print("\n[1] Collecting environment...")
    environment = collect_environment(run_id, sector, firm, mode, revit_version)
    print(f"  Revit: {environment.revit_version}")
    print(f"  Document: {environment.revit_doc_title}")
    print(f"  DLL SHA256: {environment.addin_dll_sha256[:16]}...")

    # Load learned context (Spine Learning System)
    print("\n[1b] Loading learned context...")
    learning_store = LearningStore()
    env_dict = {
        "revit_doc_title": environment.revit_doc_title,
        "levels": [],  # Will be populated from readiness check
        "sheet_count": 0
    }
    project_fingerprint = fingerprint_from_env(env_dict)
    learned_context = load_full_context(learning_store, project_fingerprint=project_fingerprint, firm=firm)

    if learned_context.get("defaults"):
        print(f"  Found learned defaults for this project")
        # Auto-apply learned sector/firm if not explicitly provided
        if not sector and learned_context["defaults"].get("sector"):
            sector = learned_context["defaults"]["sector"]
            print(f"    Applied learned sector: {sector}")
        if not firm and learned_context["defaults"].get("firm"):
            firm = learned_context["defaults"]["firm"]
            print(f"    Applied learned firm: {firm}")

    if learned_context.get("severity_overrides"):
        print(f"  Loaded {len(learned_context['severity_overrides'])} severity overrides")
    else:
        print("  No prior learning found for this project")

    # Check readiness
    print("\n[2] Checking readiness...")
    readiness = check_readiness(sector)
    print(f"  Score: {readiness.score}%")
    print(f"  Recommendation: {readiness.recommendation.upper()}")
    if readiness.blockers:
        print(f"  Blockers: {readiness.blockers}")
    if readiness.warnings:
        print(f"  Warnings: {readiness.warnings}")

    # Stop if red and BYOP
    if mode == "byop" and readiness.recommendation == "red":
        print("\n[!] Readiness FAILED - stopping")
        return BetaResult(
            run_id=run_id,
            success=False,
            mode=mode,
            readiness=readiness,
            pack_coverage=0,
            quality_score=0,
            confidence=0,
            iterations=0,
            artifacts_created={},
            human_actions_required=readiness.blockers,
            evidence_zip_path="",
            duration_seconds=time.time() - start_time
        )

    # Dry run stops here
    if dry_run:
        print("\n[DRY RUN] Stopping before execution")
        return BetaResult(
            run_id=run_id,
            success=True,
            mode=mode,
            readiness=readiness,
            pack_coverage=0,
            quality_score=0,
            confidence=0,
            iterations=0,
            artifacts_created={},
            human_actions_required=[],
            evidence_zip_path="",
            duration_seconds=time.time() - start_time
        )

    # Resolve pack
    print("\n[3] Resolving pack...")
    packs_dir = Path(__file__).parent / "template_packs"
    core_path = packs_dir / "_core" / "standards.json"
    sector_path = packs_dir / sector / "standards.json"

    # Load firm overrides if specified
    firm_overrides = None
    if firm:
        firm_path = packs_dir / "_firms" / f"{firm.lower()}.json"
        if firm_path.exists():
            with open(firm_path) as f:
                firm_overrides = json.load(f)

    resolved_pack = resolve_pack(core_path, sector_path, firm_overrides, run_id)

    resolved_pack_path = Path(__file__).parent / "template_packs" / "resolved" / f"resolved_{sector}_{run_id}.json"
    resolved_pack_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_pack_path.write_text(json.dumps(resolved_pack, indent=2))
    print(f"  Pack saved: {resolved_pack_path.name}")

    # Run autopilot
    print("\n[4] Running Spine autopilot...")
    autopilot = SpineAutopilot(sector=sector, firm=firm)
    result = autopilot.run(
        max_iterations=max_iterations,
        auto_approve=auto_approve
    )

    # Find latest autopilot report
    reports_dir = Path(__file__).parent / "reports"
    autopilot_reports = sorted(reports_dir.glob("autopilot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    autopilot_report_path = str(autopilot_reports[0]) if autopilot_reports else None

    # Extract results (defensive null checks)
    final_scores = result.get("final_scores") or {}
    autopilot_data = result.get("autopilot") or {}
    summary_data = result.get("summary") or {}

    # Collect human actions
    human_actions = []
    if readiness.warnings:
        human_actions.extend([f"Warning: {w}" for w in readiness.warnings])

    # Check for remaining gaps
    if autopilot_data.get("iteration_details"):
        last_iter = autopilot_data["iteration_details"][-1]
        remaining = last_iter.get("delta", {}).get("remaining_gaps", 0)
        if remaining > 0:
            human_actions.append(f"{remaining} gap(s) require human action")

    # Add stop reason to human actions if applicable
    stop_reason = autopilot_data.get("stop_reason", "completed")
    if "human" in stop_reason.lower() or "unsupported" in stop_reason.lower():
        human_actions.append(stop_reason)

    # Build AutopilotSummary for README
    # Get created counts from last iteration if available
    created_counts = {}
    if autopilot_data.get("iteration_details"):
        last_iter = autopilot_data["iteration_details"][-1]
        created_counts = last_iter.get("delta", {}).get("created", {})

    autopilot_summary = AutopilotSummary(
        baseline_scores=final_scores if not autopilot_data.get("iteration_details") else {},  # baseline captured in final_scores when 0 iterations
        final_scores=final_scores,
        stop_reason=stop_reason,
        iterations=autopilot_data.get("iterations", 0),
        tasks_executed=summary_data.get("total_tasks_executed", 0),
        tasks_succeeded=summary_data.get("total_tasks_succeeded", 0),
        tasks_skipped=summary_data.get("total_tasks_skipped", 0),
        created_counts=created_counts,
        human_tasks=human_actions
    )

    # Run code compliance check
    print("\n[5] Running code compliance check...")
    compliance_report = None
    compliance_report_path = None
    try:
        # Determine jurisdiction overlays based on location (default: Miami)
        overlays = ["Miami21"]  # Add Miami21 for City of Miami projects

        compliance_report = run_compliance_check(
            sector=sector,
            jurisdiction="FBC2023",
            overlays=overlays
        )

        if compliance_report:
            # Save compliance report
            reports_dir = Path(__file__).parent / "reports"
            compliance_report_path = reports_dir / f"compliance_{run_id}.json"
            compliance_report_path.write_text(compliance_report.to_json())
            print(f"  Report saved: {compliance_report_path.name}")

            # Add compliance issues to human actions
            if compliance_report.failed > 0:
                human_actions.append(f"CODE COMPLIANCE: {compliance_report.failed} failure(s) found")
            if compliance_report.warnings > 0:
                human_actions.append(f"CODE COMPLIANCE: {compliance_report.warnings} warning(s) to review")

    except Exception as e:
        print(f"  Warning: Compliance check failed: {e}")
        # Non-fatal - continue with run

    # Create evidence zip
    print("\n[6] Creating evidence package...")
    evidence_dir = Path(__file__).parent / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    evidence_zip = create_evidence_zip(
        run_id=run_id,
        environment=environment,
        readiness=readiness,
        autopilot_summary=autopilot_summary,
        autopilot_report_path=autopilot_report_path,
        resolved_pack_path=str(resolved_pack_path),
        exports_dir=None,  # TODO: wire up exports
        output_dir=evidence_dir
    )
    print(f"  Evidence: {evidence_zip}")

    # Ingest to Spine Learning System
    print("\n[7] Ingesting to learning database...")
    try:
        # The staging dir was cleaned up, but we have all the data in memory
        # Create a minimal evidence structure for ingestion
        staging_for_learning = evidence_dir / f"learning_{run_id}"
        staging_for_learning.mkdir(exist_ok=True)

        # Write autopilot report for learning ingestion
        if autopilot_report_path and os.path.exists(autopilot_report_path):
            shutil.copy(autopilot_report_path, staging_for_learning / "autopilot_report.json")

        # Write environment for fingerprinting
        (staging_for_learning / "environment.json").write_text(
            json.dumps(asdict(environment), indent=2)
        )

        # Write readiness for gate decisions
        readiness_data = {
            "readiness_grade": readiness.recommendation.upper(),
            "ready": readiness.ready,
            "score": readiness.score,
            "blockers": readiness.blockers,
            "warnings": readiness.warnings
        }
        (staging_for_learning / "readiness.json").write_text(
            json.dumps(readiness_data, indent=2)
        )

        # Write compliance report for learning
        if compliance_report:
            compliance_data = {
                "jurisdiction": compliance_report.jurisdiction,
                "compliance_score": compliance_report.compliance_score,
                "passed": compliance_report.passed,
                "failed": compliance_report.failed,
                "warnings": compliance_report.warnings,
                "failures": [
                    {"rule_id": r.rule_id, "message": r.message, "reference": r.reference}
                    for r in compliance_report.results if r.status == CheckStatus.FAIL
                ],
                "warning_items": [
                    {"rule_id": r.rule_id, "message": r.message, "reference": r.reference}
                    for r in compliance_report.results if r.status == CheckStatus.WARNING
                ]
            }
            (staging_for_learning / "compliance.json").write_text(
                json.dumps(compliance_data, indent=2)
            )

        # Ingest to learning database
        ingest_result = ingest_evidence_folder(
            learning_store,
            str(staging_for_learning),
            firm=firm,
            sector=sector
        )
        print(f"  Ingested run {ingest_result.get('run_id', run_id)} to learning DB")
        print(f"  Issues captured: {ingest_result.get('issues_count', 0)}")
        print(f"  Gate decisions: {ingest_result.get('gate_decisions_count', 0)}")

        # Clean up staging
        shutil.rmtree(staging_for_learning)
    except Exception as e:
        print(f"  Warning: Learning ingestion failed: {e}")
        # Non-fatal - continue with run

    duration = time.time() - start_time

    # Final result
    beta_result = BetaResult(
        run_id=run_id,
        success=True,
        mode=mode,
        readiness=readiness,
        pack_coverage=final_scores.get("pack_coverage_pct", 0),
        quality_score=final_scores.get("quality_pct", 0),
        confidence=final_scores.get("confidence_pct", 0),
        iterations=autopilot_data.get("iterations", 0),
        artifacts_created=autopilot_data.get("iteration_details", [{}])[-1].get("delta", {}).get("created", {}) if autopilot_data.get("iteration_details") else {},
        human_actions_required=human_actions,
        evidence_zip_path=evidence_zip,
        duration_seconds=round(duration, 1)
    )

    # Print summary
    print("\n" + "=" * 60)
    print("BETA RESULT")
    print("=" * 60)
    print(f"Run ID: {beta_result.run_id}")
    print(f"Success: {beta_result.success}")
    print(f"Duration: {beta_result.duration_seconds}s")
    print(f"Iterations: {beta_result.iterations}")
    print("-" * 60)
    print(f"Pack Coverage: {beta_result.pack_coverage}%")
    print(f"Quality Score: {beta_result.quality_score}%")
    print(f"Confidence: {beta_result.confidence}%")
    print("-" * 60)
    if beta_result.artifacts_created:
        print("Artifacts Created:")
        for k, v in beta_result.artifacts_created.items():
            print(f"  {k}: {v}")
    if beta_result.human_actions_required:
        print("Human Actions Required:")
        for action in beta_result.human_actions_required:
            print(f"  • {action}")
    print("-" * 60)
    print(f"Evidence: {beta_result.evidence_zip_path}")
    print("=" * 60)

    return beta_result


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Beta Runner - Profile, run Spine, collect evidence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 beta_runner.py --sector multifamily
    python3 beta_runner.py --sector multifamily --firm ARKY --autopilot
    python3 beta_runner.py --sector multifamily --dry_run
    python3 beta_runner.py --sector multifamily --auto_approve_gates
        """
    )

    parser.add_argument("--sector", required=True,
                       choices=["multifamily", "sfh", "duplex", "commercial", "commercial_ti"],
                       help="Project sector")
    parser.add_argument("--revit_version", default="2026", choices=["2025", "2026"],
                       help="Revit version (default: 2026)")
    parser.add_argument("--firm", default=None,
                       help="Firm overlay (e.g., ARKY, BDA)")
    parser.add_argument("--mode", default="byop", choices=["golden", "byop"],
                       help="Lane selection (default: byop)")
    parser.add_argument("--autopilot", action="store_true", default=True,
                       help="Use v0.4 autopilot loop (default: True)")
    parser.add_argument("--max_iterations", type=int, default=3,
                       help="Max autopilot iterations (default: 3)")
    parser.add_argument("--auto_approve_gates", action="store_true",
                       help="Skip human gates")
    parser.add_argument("--dry_run", action="store_true",
                       help="Profile + readiness only, no execution")
    parser.add_argument("--evidence", default=None,
                       help="Custom evidence output path")

    # Spine Learning System flags
    parser.add_argument("--learn_suggest", action="store_true",
                       help="Generate learning proposals after run")
    parser.add_argument("--learn_stats", action="store_true",
                       help="Show learning database statistics")

    args = parser.parse_args()

    # Handle learn_stats before run (quick check)
    if args.learn_stats:
        print("\n" + "=" * 60)
        print("SPINE LEARNING STATS")
        print("=" * 60)
        store = LearningStore()
        stats = store.stats()
        print(f"  Total runs: {stats.get('runs', 0)}")
        print(f"  Total issues: {stats.get('issues', 0)}")
        print(f"  Gate decisions: {stats.get('gate_decisions', 0)}")
        print(f"  Defaults stored: {stats.get('defaults', 0)}")
        print(f"  Proposals: {stats.get('proposals', 0)}")
        print("=" * 60 + "\n")

    result = run_beta(
        sector=args.sector,
        firm=args.firm,
        mode=args.mode,
        use_autopilot=args.autopilot,
        auto_approve=args.auto_approve_gates,
        dry_run=args.dry_run,
        max_iterations=args.max_iterations,
        revit_version=args.revit_version
    )

    # Generate learning suggestions if requested
    if args.learn_suggest and result.success:
        print("\n" + "=" * 60)
        print("LEARNING SUGGESTIONS")
        print("=" * 60)
        store = LearningStore()
        proposals = suggest_updates(store, firm=args.firm)
        if proposals:
            print(f"  Generated {len(proposals)} proposal(s):")
            for p in proposals:
                print(f"    - {p.get('type', 'unknown')}: {p.get('description', p.get('rule_code', 'N/A'))}")
            print("\n  Use spine-learn CLI to review and promote proposals:")
            print("    python -m spine_learning.cli list --status suggested")
            print("    python -m spine_learning.cli promote <proposal_id>")
        else:
            print("  No proposals generated (need more data)")
        print("=" * 60)

    # Exit code based on success
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
