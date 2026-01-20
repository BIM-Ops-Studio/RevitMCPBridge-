#!/usr/bin/env python3
"""
Regression Harness - Test workflows across multiple real projects

Runs state assessment and (optionally) workflows against a portfolio of
real projects to ensure consistency and catch regressions.

Usage:
    python regression_harness.py --list           # List registered projects
    python regression_harness.py --run-all        # Run assessment on all projects
    python regression_harness.py --project 512    # Run on specific project
    python regression_harness.py --compare        # Compare to baseline

Projects are registered in projects.json with expected characteristics.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any


@dataclass
class ProjectConfig:
    """Configuration for a registered test project."""
    id: str
    name: str
    sector: str
    expected_levels: int
    expected_sheets_min: int
    expected_schedules_min: int
    description: str = ""
    requires_revit_open: bool = True
    baseline_file: Optional[str] = None


@dataclass
class ProjectResult:
    """Result of running assessment on a project."""
    project_id: str
    timestamp: str
    success: bool
    error: Optional[str] = None
    state_summary: Optional[Dict] = None
    gap_summary: Optional[Dict] = None
    duration_seconds: float = 0.0


# Default project registry - can be overridden by projects.json
DEFAULT_PROJECTS = [
    ProjectConfig(
        id="512_clematis",
        name="512 Clematis",
        sector="multifamily",
        expected_levels=15,
        expected_sheets_min=300,
        expected_schedules_min=200,
        description="5-story multi-family residential (production model)"
    ),
    ProjectConfig(
        id="avon_park_sfh",
        name="Avon Park Single Family",
        sector="sfh",
        expected_levels=5,
        expected_sheets_min=15,
        expected_schedules_min=5,
        description="Single-family residential with Florida hurricane code"
    ),
    ProjectConfig(
        id="hilaire_duplex",
        name="Hilaire Residential Duplex",
        sector="duplex",
        expected_levels=5,
        expected_sheets_min=25,
        expected_schedules_min=10,
        description="Duplex with per-unit schedules"
    ),
    ProjectConfig(
        id="south_golf_cove",
        name="South Golf Cove Residence",
        sector="sfh",
        expected_levels=6,
        expected_sheets_min=15,
        expected_schedules_min=5,
        description="Two-story with parapet, extensive detail library"
    ),
    ProjectConfig(
        id="test_model",
        name="Test Model (Small)",
        sector="sfh",
        expected_levels=3,
        expected_sheets_min=0,
        expected_schedules_min=0,
        description="Minimal test model for quick validation",
        requires_revit_open=True
    )
]


class RegressionHarness:
    """Runs regression tests across multiple projects."""

    def __init__(self, projects_file: Optional[Path] = None):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir / "regression_results"
        self.results_dir.mkdir(exist_ok=True)

        # Load projects
        if projects_file and projects_file.exists():
            self.projects = self._load_projects(projects_file)
        else:
            self.projects = {p.id: p for p in DEFAULT_PROJECTS}

        self.results: List[ProjectResult] = []

    def _load_projects(self, filepath: Path) -> Dict[str, ProjectConfig]:
        """Load project configurations from JSON file."""
        with open(filepath) as f:
            data = json.load(f)

        projects = {}
        for proj_data in data.get("projects", []):
            config = ProjectConfig(**proj_data)
            projects[config.id] = config

        return projects

    def list_projects(self):
        """Print list of registered projects."""
        print("\n" + "=" * 70)
        print("REGISTERED TEST PROJECTS")
        print("=" * 70)
        print(f"{'ID':<20} {'Name':<25} {'Sector':<15} {'Levels':<8}")
        print("-" * 70)

        for proj_id, proj in self.projects.items():
            print(f"{proj.id:<20} {proj.name:<25} {proj.sector:<15} {proj.expected_levels:<8}")

        print("-" * 70)
        print(f"Total: {len(self.projects)} projects")
        print()

    def run_assessment(self, project_id: str, verbose: bool = False) -> ProjectResult:
        """
        Run state assessment on a specific project.

        Note: The actual Revit file must be open in Revit for this to work.
        This method assumes the MCP server is connected to the active project.
        """
        import time

        if project_id not in self.projects:
            return ProjectResult(
                project_id=project_id,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Unknown project ID: {project_id}"
            )

        project = self.projects[project_id]
        print(f"\n[{project_id}] Running assessment...")
        print(f"  Sector: {project.sector}")

        start_time = time.time()

        try:
            # Import state assessment
            from state_assessment import StateAssessor, send_mcp_request

            # Verify MCP connection
            test_resp = send_mcp_request("getLevels")
            if not test_resp.get("success"):
                return ProjectResult(
                    project_id=project_id,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error="MCP not connected",
                    duration_seconds=time.time() - start_time
                )

            levels = test_resp.get("levels", [])
            print(f"  Connected: {len(levels)} levels found")

            # Load sector standards
            sys.path.insert(0, str(self.base_dir / "template_packs"))
            from pack_resolver import resolve_pack

            core_path = self.base_dir / "template_packs" / "_core" / "standards.json"
            sector_path = self.base_dir / "template_packs" / project.sector / "standards.json"

            if not sector_path.exists():
                return ProjectResult(
                    project_id=project_id,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error=f"Sector not found: {project.sector}",
                    duration_seconds=time.time() - start_time
                )

            resolved = resolve_pack(core_path, sector_path)

            # Run assessment
            assessor = StateAssessor(resolved)
            state = assessor.assess_all()
            gaps = assessor.find_gaps(state)
            report = assessor.generate_report(state, gaps)

            duration = time.time() - start_time

            # Extract summary
            state_summary = {
                "levels": len(levels),
                "sheets": report["sheets"]["existing"],
                "schedules": report["schedules"]["existing"],
                "completion": report["summary"]["completion_percent"],
                "tag_coverage": report["tags"]["overall_coverage"]
            }

            gap_summary = {
                "blockers": report["summary"]["blocker_count"],
                "required_tasks": report["summary"]["required_count"],
                "recommended": report["summary"]["recommended_count"]
            }

            # Verify against expectations
            issues = []
            if len(levels) < project.expected_levels * 0.5:
                issues.append(f"Levels below threshold: {len(levels)} < {project.expected_levels}")

            if report["sheets"]["existing"] < project.expected_sheets_min:
                issues.append(f"Sheets below threshold: {report['sheets']['existing']} < {project.expected_sheets_min}")

            success = len(issues) == 0

            result = ProjectResult(
                project_id=project_id,
                timestamp=datetime.now().isoformat(),
                success=success,
                error="; ".join(issues) if issues else None,
                state_summary=state_summary,
                gap_summary=gap_summary,
                duration_seconds=duration
            )

            print(f"  Sheets: {state_summary['sheets']}")
            print(f"  Schedules: {state_summary['schedules']}")
            print(f"  Completion: {state_summary['completion']}%")
            print(f"  Duration: {duration:.1f}s")

            if not success:
                print(f"  ⚠ Issues: {result.error}")

            return result

        except Exception as e:
            return ProjectResult(
                project_id=project_id,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )

    def run_all(self, skip_inactive: bool = True) -> List[ProjectResult]:
        """
        Run assessment on all registered projects.

        Note: This requires switching Revit files manually or having
        a way to open different projects programmatically.

        For now, this runs assessment on the currently open model only,
        which should match one of the registered projects.
        """
        print("\n" + "=" * 70)
        print("REGRESSION HARNESS - RUN ALL")
        print("=" * 70)

        # For now, we can only test the currently open model
        # The user must open each model in Revit and run assessment

        # Detect current model by checking MCP
        from state_assessment import send_mcp_request

        resp = send_mcp_request("getLevels")
        if not resp.get("success"):
            print("ERROR: Cannot connect to MCP. Is Revit open?")
            return []

        levels = resp.get("levels", [])
        level_count = len(levels)

        print(f"Current model has {level_count} levels")
        print("Attempting to match to registered projects...")

        # Try to match based on level count (rough heuristic)
        best_match = None
        for proj_id, proj in self.projects.items():
            if abs(proj.expected_levels - level_count) <= 2:
                if best_match is None or \
                   abs(proj.expected_levels - level_count) < abs(best_match.expected_levels - level_count):
                    best_match = proj

        if best_match:
            print(f"Best match: {best_match.name} ({best_match.sector})")
            result = self.run_assessment(best_match.id)
            self.results.append(result)
        else:
            print("No matching project found. Running as 'unknown' with multifamily sector.")
            result = self.run_assessment("test_model")
            self.results.append(result)

        return self.results

    def save_results(self, filename: Optional[str] = None):
        """Save results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"regression_{timestamp}.json"

        filepath = self.results_dir / filename

        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results],
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success)
            }
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nResults saved: {filepath}")
        return filepath

    def compare_to_baseline(self, baseline_file: Path):
        """Compare current results to a baseline."""
        if not baseline_file.exists():
            print(f"Baseline file not found: {baseline_file}")
            return

        with open(baseline_file) as f:
            baseline = json.load(f)

        print("\n" + "=" * 70)
        print("BASELINE COMPARISON")
        print("=" * 70)

        baseline_results = {r["project_id"]: r for r in baseline.get("results", [])}

        for result in self.results:
            proj_id = result.project_id
            if proj_id in baseline_results:
                baseline_r = baseline_results[proj_id]

                # Compare key metrics
                changes = []
                if result.state_summary and baseline_r.get("state_summary"):
                    curr = result.state_summary
                    prev = baseline_r["state_summary"]

                    for key in ["sheets", "schedules", "completion"]:
                        if key in curr and key in prev:
                            diff = curr[key] - prev[key]
                            if abs(diff) > 0.1:
                                changes.append(f"{key}: {prev[key]} → {curr[key]} ({'+' if diff > 0 else ''}{diff:.1f})")

                print(f"\n[{proj_id}]")
                if changes:
                    for c in changes:
                        print(f"  {c}")
                else:
                    print("  No significant changes")
            else:
                print(f"\n[{proj_id}] NEW - no baseline to compare")

    def generate_report(self) -> str:
        """Generate human-readable regression report."""
        lines = [
            "",
            "=" * 70,
            "REGRESSION TEST REPORT",
            "=" * 70,
            f"Timestamp: {datetime.now().isoformat()}",
            f"Projects tested: {len(self.results)}",
            ""
        ]

        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed

        lines.append(f"PASSED: {passed}  |  FAILED: {failed}")
        lines.append("-" * 70)

        for result in self.results:
            status = "✓" if result.success else "✗"
            lines.append(f"\n{status} {result.project_id}")

            if result.state_summary:
                s = result.state_summary
                lines.append(f"  Levels: {s.get('levels', '?')}")
                lines.append(f"  Sheets: {s.get('sheets', '?')}")
                lines.append(f"  Completion: {s.get('completion', '?')}%")

            if result.error:
                lines.append(f"  ERROR: {result.error}")

            lines.append(f"  Duration: {result.duration_seconds:.1f}s")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Regression harness for AEC automation")
    parser.add_argument("--list", action="store_true", help="List registered projects")
    parser.add_argument("--run-all", action="store_true", help="Run assessment on all (currently: active model)")
    parser.add_argument("--project", "-p", help="Run on specific project ID")
    parser.add_argument("--compare", "-c", help="Compare to baseline file")
    parser.add_argument("--save", "-s", action="store_true", help="Save results to file")
    args = parser.parse_args()

    harness = RegressionHarness()

    if args.list:
        harness.list_projects()
        return 0

    if args.project:
        result = harness.run_assessment(args.project)
        harness.results.append(result)
        print(harness.generate_report())

    elif args.run_all:
        harness.run_all()
        print(harness.generate_report())

    else:
        # Default: run on current model
        harness.run_all()
        print(harness.generate_report())

    if args.save:
        harness.save_results()

    if args.compare:
        harness.compare_to_baseline(Path(args.compare))

    return 0


if __name__ == "__main__":
    sys.exit(main())
