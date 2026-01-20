#!/usr/bin/env python3
"""
Pack Resolver - Merges Core + Sector Modules into Resolved Standards Pack

Usage:
    python pack_resolver.py --sector multifamily [--firm ARKY] [--output resolved.json]
    python pack_resolver.py --list  # List available modules

Architecture:
    Core Pack (universal baseline)
        + Sector Module (multifamily, residential_sfh, commercial_ti, etc.)
        + Firm Overrides (optional, e.g., ARKY preferences)
        = Resolved Standards Pack
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from copy import deepcopy
from datetime import datetime


def deep_merge(base: Dict, overlay: Dict) -> Dict:
    """
    Deep merge overlay into base.
    - Dicts are merged recursively
    - Lists are replaced (not appended)
    - Scalars are replaced
    - Keys starting with _ are metadata, not merged
    """
    result = deepcopy(base)

    for key, value in overlay.items():
        # Skip metadata keys
        if key.startswith('_'):
            continue

        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        else:
            result[key] = deepcopy(value)

    return result


def load_pack(pack_path: Path) -> Dict:
    """Load a standards pack JSON file."""
    if not pack_path.exists():
        raise FileNotFoundError(f"Pack not found: {pack_path}")

    with open(pack_path) as f:
        return json.load(f)


def list_available_modules(packs_dir: Path) -> List[Dict]:
    """List all available modules with their metadata."""
    modules = []

    for subdir in packs_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('_'):
            standards_file = subdir / 'standards.json'
            if standards_file.exists():
                try:
                    pack = load_pack(standards_file)
                    modules.append({
                        'name': subdir.name,
                        'display_name': pack.get('identity', {}).get('name', subdir.name),
                        'description': pack.get('identity', {}).get('description', ''),
                        'project_type': pack.get('identity', {}).get('projectType', 'Unknown'),
                        'version': pack.get('identity', {}).get('version', '0.0.0'),
                        'path': str(standards_file)
                    })
                except Exception as e:
                    print(f"Warning: Could not load {subdir.name}: {e}")

    return sorted(modules, key=lambda x: x['name'])


def resolve_pack(
    core_path: Path,
    sector_path: Path,
    firm_overrides: Dict = None,
    run_id: str = None
) -> Dict:
    """
    Resolve a complete standards pack from core + sector + firm overrides.

    Args:
        core_path: Path to core standards.json
        sector_path: Path to sector module standards.json
        firm_overrides: Optional dict of firm-specific overrides
        run_id: Optional run ID for naming

    Returns:
        Fully resolved standards pack dict
    """
    # Load base packs
    core = load_pack(core_path)
    sector = load_pack(sector_path)

    # Merge: Core + Sector
    resolved = deep_merge(core, sector)

    # Apply firm overrides if provided
    if firm_overrides:
        resolved = deep_merge(resolved, firm_overrides)

    # Update identity for resolved pack
    resolved['identity']['name'] = f"Resolved_{sector.get('identity', {}).get('projectType', 'Unknown')}_{datetime.now().strftime('%Y%m%d')}"
    resolved['identity']['resolvedFrom'] = {
        'core': str(core_path),
        'sector': str(sector_path),
        'firmOverrides': firm_overrides is not None
    }
    resolved['identity']['resolvedAt'] = datetime.now().isoformat()

    # Validate required fields
    validate_resolved_pack(resolved)

    return resolved


def validate_resolved_pack(pack: Dict) -> None:
    """Validate that resolved pack has all required sections."""
    required_sections = ['identity', 'sheets', 'views', 'schedules']

    for section in required_sections:
        if section not in pack:
            raise ValueError(f"Resolved pack missing required section: {section}")

    # Validate identity
    identity = pack.get('identity', {})
    if not identity.get('name'):
        raise ValueError("Resolved pack must have identity.name")

    # Validate sheets has at least permit skeleton
    sheets = pack.get('sheets', {})
    if not sheets.get('sets', {}).get('permitSkeleton'):
        raise ValueError("Resolved pack must have sheets.sets.permitSkeleton")


def generate_readiness_report(pack: Dict) -> Dict:
    """Generate a readiness report for the resolved pack."""
    report = {
        'pack_name': pack.get('identity', {}).get('name'),
        'project_type': pack.get('identity', {}).get('projectType'),
        'version': pack.get('identity', {}).get('version'),
        'resolved_at': pack.get('identity', {}).get('resolvedAt'),
        'sheet_count': 0,
        'required_views': [],
        'required_schedules': [],
        'preflight_checks': []
    }

    # Count sheets
    permit_skeleton = pack.get('sheets', {}).get('sets', {}).get('permitSkeleton', [])
    report['sheet_count'] = len(permit_skeleton)

    # List required views
    for sheet in permit_skeleton:
        view_type = sheet.get('viewType')
        if view_type and not sheet.get('optional'):
            report['required_views'].append({
                'sheet': sheet.get('number'),
                'type': view_type,
                'name': sheet.get('name')
            })

    # List required schedules
    schedules = pack.get('schedules', {}).get('definitions', {})
    for sched_name, sched_def in schedules.items():
        report['required_schedules'].append({
            'name': sched_name,
            'category': sched_def.get('category'),
            'fields': sched_def.get('fields', [])
        })

    # List preflight checks
    preflight = pack.get('filters', {}).get('preflight', [])
    for check in preflight:
        report['preflight_checks'].append({
            'id': check.get('id'),
            'name': check.get('name'),
            'severity': check.get('severity')
        })

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Resolve Core + Sector modules into complete standards pack"
    )
    parser.add_argument('--sector', '-s', help='Sector module name (e.g., multifamily)')
    parser.add_argument('--firm', '-f', help='Firm name for overrides')
    parser.add_argument('--output', '-o', help='Output path for resolved pack')
    parser.add_argument('--list', '-l', action='store_true', help='List available modules')
    parser.add_argument('--report', '-r', action='store_true', help='Generate readiness report')

    args = parser.parse_args()

    # Determine base directory
    packs_dir = Path(__file__).parent
    core_path = packs_dir / '_core' / 'standards.json'

    # List modules
    if args.list:
        print("\n" + "=" * 60)
        print("AVAILABLE TEMPLATE PACK MODULES")
        print("=" * 60)

        modules = list_available_modules(packs_dir)

        print(f"\n{'Module':<20} {'Type':<20} {'Version':<10}")
        print("-" * 50)
        for mod in modules:
            print(f"{mod['name']:<20} {mod['project_type']:<20} {mod['version']:<10}")
            if mod.get('description'):
                print(f"  {mod['description'][:60]}")

        print(f"\n{'=' * 60}")
        print(f"Total: {len(modules)} modules")
        return 0

    # Require sector for resolution
    if not args.sector:
        parser.error("--sector is required (or use --list to see available modules)")

    # Find sector module
    sector_path = packs_dir / args.sector / 'standards.json'
    if not sector_path.exists():
        print(f"ERROR: Sector module not found: {args.sector}")
        print("Use --list to see available modules")
        return 1

    # Load firm overrides if specified
    firm_overrides = None
    if args.firm:
        firm_path = packs_dir / '_firms' / f'{args.firm.lower()}.json'
        if firm_path.exists():
            firm_overrides = load_pack(firm_path)
            print(f"Loaded firm overrides: {args.firm}")
        else:
            print(f"Warning: No firm overrides found for {args.firm}")

    # Resolve pack
    print("\n" + "=" * 60)
    print("RESOLVING TEMPLATE PACK")
    print("=" * 60)
    print(f"\nCore:   {core_path}")
    print(f"Sector: {sector_path}")
    if firm_overrides:
        print(f"Firm:   {args.firm}")

    try:
        resolved = resolve_pack(core_path, sector_path, firm_overrides)
        print(f"\n✓ Resolved: {resolved['identity']['name']}")
    except Exception as e:
        print(f"\n✗ Resolution failed: {e}")
        return 1

    # Generate report if requested
    if args.report:
        report = generate_readiness_report(resolved)
        print(f"\n{'─' * 40}")
        print("READINESS REPORT")
        print(f"{'─' * 40}")
        print(f"Sheets: {report['sheet_count']}")
        print(f"Required Views: {len(report['required_views'])}")
        print(f"Schedules: {len(report['required_schedules'])}")
        print(f"Preflight Checks: {len(report['preflight_checks'])}")

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = packs_dir / 'resolved' / f"resolved_{args.sector}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(resolved, f, indent=2)

    print(f"\n✓ Saved: {output_path}")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    exit(main())
