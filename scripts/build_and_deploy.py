#!/usr/bin/env python3
"""
Build and Deploy Script
-----------------------
Builds the RevitMCPBridge project and automatically deploys it.

Usage:
    python build_and_deploy.py           # Build and deploy (closes/reopens Revit)
    python build_and_deploy.py --quick   # Build only, no deploy
"""

import subprocess
import sys
import os
from pathlib import Path

PROJECT_DIR = Path(r"D:\RevitMCPBridge2026")
CSPROJ_FILE = PROJECT_DIR / "RevitMCPBridge2026.csproj"


def log(msg: str, level: str = "INFO"):
    """Print timestamped log message."""
    import time
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def build_project() -> bool:
    """Build the C# project."""
    log("Building RevitMCPBridge2026...")

    # Try dotnet build first
    result = subprocess.run(
        ["dotnet", "build", str(CSPROJ_FILE), "-c", "Release"],
        capture_output=True, text=True,
        cwd=str(PROJECT_DIR)
    )

    if result.returncode == 0:
        # Check for 0 errors
        if "0 Error(s)" in result.stdout or result.returncode == 0:
            log("Build succeeded!")
            # Show warnings count
            import re
            warnings_match = re.search(r'(\d+) Warning\(s\)', result.stdout)
            if warnings_match:
                log(f"Warnings: {warnings_match.group(1)}")
            return True

    # Show build output on failure
    log("Build failed!", "ERROR")
    print(result.stdout)
    print(result.stderr)
    return False


def deploy() -> bool:
    """Run the auto-deploy script."""
    log("Starting auto-deploy...")

    deploy_script = PROJECT_DIR / "scripts" / "revit_auto_deploy.py"

    result = subprocess.run(
        [sys.executable, str(deploy_script), "--force"],
        cwd=str(PROJECT_DIR / "scripts")
    )

    return result.returncode == 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build and deploy RevitMCPBridge")
    parser.add_argument("--quick", action="store_true", help="Build only, skip deploy")
    parser.add_argument("--deploy-only", action="store_true", help="Deploy only, skip build")
    args = parser.parse_args()

    log("=" * 50)
    log("RevitMCPBridge Build & Deploy")
    log("=" * 50)

    # Build
    if not args.deploy_only:
        if not build_project():
            log("Build failed, aborting", "ERROR")
            return 1

    # Deploy
    if not args.quick:
        if not deploy():
            log("Deploy failed!", "ERROR")
            return 1

    log("=" * 50)
    log("Complete!")
    log("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
