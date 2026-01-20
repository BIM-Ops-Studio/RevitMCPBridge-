#!/usr/bin/env python3
"""
Log Collector - Gathers diagnostic information for support

Usage:
    python collect_logs.py [--output support_package.zip]

Collects:
    - All evidence packages
    - Recent workflow reports
    - System information
    - Configuration files
"""

import sys
import json
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile


def get_system_info():
    """Collect system information."""
    info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "timestamp": datetime.now().isoformat()
    }

    # Try to get Revit version from running process
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command",
             "Get-Process Revit -ErrorAction SilentlyContinue | Select-Object -First 1 | "
             "ForEach-Object { $_.MainWindowTitle }"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            info["revit_window"] = result.stdout.strip()
    except:
        pass

    return info


def collect_logs(output_path: Path):
    """Collect all logs and create support package."""
    base_dir = Path(__file__).parent.parent.parent  # smoke_tests/

    files_to_collect = []

    # Collect evidence packages
    evidence_dir = base_dir / "evidence"
    if evidence_dir.exists():
        for f in evidence_dir.glob("*.zip"):
            files_to_collect.append(("evidence", f))

    # Collect recent workflow reports
    reports_dir = base_dir / "reports"
    if reports_dir.exists():
        # Get 5 most recent reports
        reports = sorted(reports_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        for f in reports:
            files_to_collect.append(("reports", f))

    # Collect template pack spec
    spec_file = base_dir / "template_packs" / "SPEC.md"
    if spec_file.exists():
        files_to_collect.append(("config", spec_file))

    # Collect contract
    contract_file = base_dir / "CONTRACT.md"
    if contract_file.exists():
        files_to_collect.append(("docs", contract_file))

    # Create system info file
    system_info = get_system_info()

    # Create the zip
    with ZipFile(output_path, 'w') as zf:
        # Add collected files
        for folder, filepath in files_to_collect:
            arcname = f"{folder}/{filepath.name}"
            zf.write(filepath, arcname)
            print(f"  Added: {arcname}")

        # Add system info
        zf.writestr("system_info.json", json.dumps(system_info, indent=2))
        print("  Added: system_info.json")

    return len(files_to_collect) + 1  # +1 for system_info


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Collect logs for support")
    parser.add_argument("--output", "-o", default=None,
                       help="Output zip path (default: support_TIMESTAMP.zip)")
    args = parser.parse_args()

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(__file__).parent.parent / "logs" / f"support_{timestamp}.zip"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 50)
    print("LOG COLLECTOR")
    print("=" * 50)

    file_count = collect_logs(output_path)

    print(f"\n{'=' * 50}")
    print(f"Collected {file_count} files")
    print(f"Output: {output_path}")
    print("=" * 50)

    print("\n📦 Send this file to support with your issue description.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
