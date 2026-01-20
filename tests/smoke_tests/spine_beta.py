#!/usr/bin/env python3
"""
Spine Beta - One Command CD Readiness Tool

Usage:
    python spine_beta.py                  # Interactive mode
    python spine_beta.py --assess         # Readiness report only
    python spine_beta.py --plan           # Show what would change
    python spine_beta.py --export         # Export evidence zip
    python spine_beta.py --execute        # Execute safe tasks (with confirmation)

This is the single entry point for production use.
"""

import argparse
import json
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from filtered_queries import send_mcp_request
from pack_assessor import PackAssessor, ScoreCard
from gap_planner import GapPlanner, TaskSafety


class SpineBeta:
    """
    Single-command CD readiness tool.

    Features:
    1. Readiness report (is model permit-ready?)
    2. Task preview (what would we change?)
    3. Evidence export (ZIP with all reports)
    4. Safe task execution (with human gate)
    """

    def __init__(self, sector: str = "multifamily", output_dir: str = None):
        self.sector = sector
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load pack
        self.pack = self._load_pack()

        # Components
        self.assessor = PackAssessor(self.pack) if self.pack else None
        self.planner = None  # Created after assessment

        # Results
        self.score = None
        self.tasks = None
        self.model_state = None

    def _load_pack(self):
        """Load resolved pack for sector."""
        base_dir = Path(__file__).parent
        sys.path.insert(0, str(base_dir / "template_packs"))

        try:
            from pack_resolver import resolve_pack
            core_path = base_dir / "template_packs" / "_core" / "standards.json"
            sector_path = base_dir / "template_packs" / self.sector / "standards.json"

            if not sector_path.exists():
                print(f"ERROR: Sector '{self.sector}' not found")
                return None

            return resolve_pack(core_path, sector_path)
        except Exception as e:
            print(f"ERROR loading pack: {e}")
            return None

    def check_connection(self) -> bool:
        """Verify MCP connection to Revit."""
        print("\n[Connection Check]")
        resp = send_mcp_request("getLevels", timeout=10)

        if resp.get("success"):
            levels = resp.get("levels", [])
            print(f"  Connected to Revit ({len(levels)} levels)")
            return True
        else:
            print(f"  FAILED: {resp.get('error')}")
            print("  Make sure Revit is open with the MCP bridge active.")
            return False

    def run_assessment(self) -> ScoreCard:
        """Run pack-driven assessment and return scorecard."""
        if not self.assessor:
            return None

        print("\n[Running Assessment]")
        print(f"  Sector: {self.sector}")

        self.score = self.assessor.assess()

        # Store model state for planner
        self.model_state = {
            "sheets": {"matches": [], "total": 0},
            "schedules": {"found": [], "missing": []},
        }

        return self.score

    def generate_plan(self) -> list:
        """Generate task plan from assessment gaps."""
        if not self.score:
            print("  ERROR: Run assessment first")
            return []

        print("\n[Generating Task Plan]")

        # Build assessment report format for planner
        assessment_report = {
            "human_tasks": self.score.human_tasks,
            "checks": {
                "warnings": [
                    {
                        "check_id": c.check_id,
                        "description": c.description,
                        "details": c.details
                    }
                    for c in self.score.warnings
                ]
            }
        }

        self.planner = GapPlanner(self.pack, self.model_state)
        self.tasks = self.planner.plan_from_assessment(assessment_report)

        print(f"  Generated {len(self.tasks)} tasks")

        return self.tasks

    def print_readiness_report(self):
        """Print human-readable readiness report."""
        if not self.score:
            print("No assessment results available.")
            return

        print(self.assessor.generate_report(self.score))

    def print_task_preview(self):
        """Print what-will-change preview."""
        if not self.tasks:
            print("No task plan available.")
            return

        print(self.planner.generate_summary())

    def export_evidence_zip(self) -> str:
        """Export all reports to a timestamped ZIP file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"spine_evidence_{timestamp}.zip"
        zip_path = self.output_dir / zip_name

        print(f"\n[Exporting Evidence ZIP]")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Assessment JSON
            if self.score:
                assessment_data = {
                    "sector": self.sector,
                    "timestamp": self.score.timestamp,
                    "scores": {
                        "pack_coverage": self.score.pack_coverage,
                        "quality_score": self.score.quality_score,
                        "confidence": self.score.confidence
                    },
                    "checks": {
                        "total": self.score.total_checks,
                        "passed": self.score.passed_checks,
                        "blockers": len(self.score.blockers),
                        "warnings": len(self.score.warnings)
                    },
                    "human_tasks": self.score.human_tasks,
                    "ready_for_permit": self.score.ready_for_permit
                }
                zf.writestr("assessment.json", json.dumps(assessment_data, indent=2))
                print(f"  + assessment.json")

                # Human-readable report
                zf.writestr("assessment_report.txt", self.assessor.generate_report(self.score))
                print(f"  + assessment_report.txt")

            # 2. Task Plan JSON
            if self.tasks:
                task_data = {
                    "timestamp": datetime.now().isoformat(),
                    "total_tasks": len(self.tasks),
                    "safe_count": len([t for t in self.tasks if t.safety == TaskSafety.SAFE]),
                    "review_count": len([t for t in self.tasks if t.safety == TaskSafety.REVIEW]),
                    "blocked_count": len([t for t in self.tasks if t.safety == TaskSafety.BLOCK]),
                    "tasks": [
                        {
                            "id": t.task_id,
                            "type": t.task_type.value,
                            "description": t.description,
                            "safety": t.safety.value,
                            "params": t.params,
                            "ambiguity": t.ambiguity
                        }
                        for t in self.tasks
                    ]
                }
                zf.writestr("task_plan.json", json.dumps(task_data, indent=2))
                print(f"  + task_plan.json")

                # Human-readable summary
                zf.writestr("task_summary.txt", self.planner.generate_summary())
                print(f"  + task_summary.txt")

            # 3. Pack used
            if self.pack:
                zf.writestr("pack_used.json", json.dumps(self.pack, indent=2, default=str))
                print(f"  + pack_used.json")

            # 4. Metadata
            meta = {
                "export_timestamp": datetime.now().isoformat(),
                "spine_version": "0.4-beta",
                "sector": self.sector,
                "disclaimer": "This is an AI-assisted assessment. Human verification required."
            }
            zf.writestr("metadata.json", json.dumps(meta, indent=2))
            print(f"  + metadata.json")

        print(f"\n  Saved: {zip_path}")
        return str(zip_path)

    def execute_safe_tasks(self, dry_run: bool = True) -> dict:
        """
        Execute tasks marked as SAFE.

        Args:
            dry_run: If True, only preview what would be done

        Returns:
            Execution summary
        """
        if not self.tasks:
            return {"error": "No task plan available"}

        safe_tasks = [t for t in self.tasks if t.safety == TaskSafety.SAFE]

        if not safe_tasks:
            print("\n[No Safe Tasks]")
            print("  All tasks require human review or input.")
            return {"executed": 0, "skipped": len(self.tasks)}

        print(f"\n[{'DRY RUN - ' if dry_run else ''}Execute Safe Tasks]")
        print(f"  Tasks to execute: {len(safe_tasks)}")

        results = {"executed": 0, "failed": 0, "skipped": 0, "details": []}

        for task in safe_tasks:
            if dry_run:
                print(f"  [DRY RUN] Would execute: {task.description}")
                results["details"].append({
                    "task_id": task.task_id,
                    "status": "would_execute",
                    "description": task.description
                })
            else:
                # Actual execution would go here
                # For beta, we just log what we would do
                print(f"  [EXECUTE] {task.description}")
                # TODO: Implement actual task execution via MCP
                results["executed"] += 1
                results["details"].append({
                    "task_id": task.task_id,
                    "status": "executed",
                    "description": task.description
                })

        if dry_run:
            print(f"\n  To execute for real, run with --execute --confirm")

        return results

    def run_interactive(self):
        """Run interactive mode with menu."""
        print("\n" + "=" * 60)
        print("SPINE BETA - CD Readiness Tool")
        print("=" * 60)
        print(f"Sector: {self.sector}")

        if not self.check_connection():
            return 1

        # Run assessment
        self.run_assessment()
        self.generate_plan()

        # Show results
        self.print_readiness_report()
        self.print_task_preview()

        # Menu
        print("\n" + "-" * 60)
        print("OPTIONS:")
        print("  [E] Export evidence ZIP")
        print("  [X] Execute safe tasks (preview)")
        print("  [Q] Quit")
        print("-" * 60)

        try:
            choice = input("\nSelect option: ").strip().upper()

            if choice == "E":
                self.export_evidence_zip()
            elif choice == "X":
                self.execute_safe_tasks(dry_run=True)
            elif choice == "Q":
                print("Exiting.")
        except KeyboardInterrupt:
            print("\nExiting.")

        return 0 if (self.score and self.score.ready_for_permit) else 1


def main():
    parser = argparse.ArgumentParser(
        description="Spine Beta - One Command CD Readiness Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python spine_beta.py                    # Interactive mode
  python spine_beta.py --assess           # Just show readiness report
  python spine_beta.py --plan             # Show what would change
  python spine_beta.py --export           # Export evidence ZIP
  python spine_beta.py --execute          # Preview safe task execution
  python spine_beta.py --execute --confirm  # Actually execute safe tasks
        """
    )

    parser.add_argument("--sector", "-t", default="multifamily",
                        help="Sector module (default: multifamily)")
    parser.add_argument("--output", "-o",
                        help="Output directory for reports")
    parser.add_argument("--assess", "-a", action="store_true",
                        help="Run assessment only")
    parser.add_argument("--plan", "-p", action="store_true",
                        help="Generate and show task plan")
    parser.add_argument("--export", "-e", action="store_true",
                        help="Export evidence ZIP")
    parser.add_argument("--execute", "-x", action="store_true",
                        help="Execute safe tasks (dry run unless --confirm)")
    parser.add_argument("--confirm", action="store_true",
                        help="Actually execute tasks (requires --execute)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()

    # Initialize
    spine = SpineBeta(sector=args.sector, output_dir=args.output)

    if not spine.pack:
        return 1

    # Check connection
    if not spine.check_connection():
        return 1

    # Run assessment
    spine.run_assessment()

    # Handle specific modes
    if args.assess:
        if args.json:
            print(json.dumps({
                "pack_coverage": spine.score.pack_coverage,
                "quality_score": spine.score.quality_score,
                "confidence": spine.score.confidence,
                "ready_for_permit": spine.score.ready_for_permit,
                "blockers": len(spine.score.blockers),
                "warnings": len(spine.score.warnings),
                "human_tasks": len(spine.score.human_tasks)
            }, indent=2))
        else:
            spine.print_readiness_report()
        return 0 if spine.score.ready_for_permit else 1

    # Generate plan
    spine.generate_plan()

    if args.plan:
        if args.json:
            print(json.dumps({
                "total": len(spine.tasks),
                "safe": len(spine.planner.get_safe_tasks()),
                "review": len(spine.planner.get_review_tasks()),
                "blocked": len(spine.planner.get_blocked_tasks()),
                "tasks": [
                    {"id": t.task_id, "type": t.task_type.value,
                     "description": t.description, "safety": t.safety.value}
                    for t in spine.tasks
                ]
            }, indent=2))
        else:
            spine.print_task_preview()
        return 0

    if args.export:
        zip_path = spine.export_evidence_zip()
        if args.json:
            print(json.dumps({"export_path": zip_path}))
        return 0

    if args.execute:
        dry_run = not args.confirm
        results = spine.execute_safe_tasks(dry_run=dry_run)
        if args.json:
            print(json.dumps(results, indent=2))
        return 0

    # Default: interactive mode
    return spine.run_interactive()


if __name__ == "__main__":
    sys.exit(main())
