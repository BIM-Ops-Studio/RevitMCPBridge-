#!/usr/bin/env python3
"""
Revit Detail Library Learning Script
=====================================
Automatically catalogs and learns from the Revit Detail Library.
Creates a structured knowledge base that Claude can reference.

Usage:
  python learn_detail_library.py catalog    # Catalog all files
  python learn_detail_library.py analyze    # Analyze naming patterns
  python learn_detail_library.py extract    # Extract via MCP (needs Revit open)
  python learn_detail_library.py report     # Generate summary report
"""

import os
import sys
import json
import socket
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional

# Configuration - use /mnt/d for WSL compatibility
import platform
if platform.system() == "Linux":
    # WSL paths
    LIBRARY_ROOT = Path("/mnt/d/Revit Detail Libraries")
    OUTPUT_DIR = Path("/mnt/d/RevitMCPBridge2026/knowledge/detail_library")
else:
    # Windows paths
    LIBRARY_ROOT = Path(r"D:\Revit Detail Libraries")
    OUTPUT_DIR = Path(r"D:\RevitMCPBridge2026\knowledge\detail_library")
MCP_PIPE_NAME = r"\\.\pipe\RevitMCPBridge2026"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class DetailLibraryLearner:
    """Learns from Revit Detail Library files"""

    def __init__(self):
        self.catalog = {
            "generated_at": datetime.now().isoformat(),
            "library_root": str(LIBRARY_ROOT),
            "families": {},      # .rfa files
            "projects": {},      # .rvt files
            "patterns": {},      # Naming patterns discovered
            "categories": {},    # Category statistics
            "lessons": []        # Extracted lessons
        }

    def catalog_files(self) -> Dict[str, Any]:
        """Scan all Revit files and build catalog"""
        print("=" * 60)
        print("CATALOGING REVIT DETAIL LIBRARY")
        print("=" * 60)

        # Scan for .rfa files
        print("\n[1/4] Scanning for family files (.rfa)...")
        rfa_files = list(LIBRARY_ROOT.rglob("*.rfa"))
        print(f"      Found: {len(rfa_files)} families")

        for f in rfa_files:
            rel_path = f.relative_to(LIBRARY_ROOT)
            category = self._get_category(f)

            self.catalog["families"][str(rel_path)] = {
                "name": f.stem,
                "category": category,
                "size_kb": f.stat().st_size / 1024,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "patterns": self._extract_naming_patterns(f.stem)
            }

            # Track category stats
            if category not in self.catalog["categories"]:
                self.catalog["categories"][category] = {"families": 0, "projects": 0}
            self.catalog["categories"][category]["families"] += 1

        # Scan for .rvt files
        print("\n[2/4] Scanning for project files (.rvt)...")
        rvt_files = list(LIBRARY_ROOT.rglob("*.rvt"))
        print(f"      Found: {len(rvt_files)} projects")

        for f in rvt_files:
            rel_path = f.relative_to(LIBRARY_ROOT)
            category = self._get_category(f)

            self.catalog["projects"][str(rel_path)] = {
                "name": f.stem,
                "category": category,
                "size_mb": f.stat().st_size / (1024 * 1024),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }

            if category not in self.catalog["categories"]:
                self.catalog["categories"][category] = {"families": 0, "projects": 0}
            self.catalog["categories"][category]["projects"] += 1

        # Analyze patterns
        print("\n[3/4] Analyzing naming patterns...")
        self._analyze_patterns()

        # Save catalog
        print("\n[4/4] Saving catalog...")
        catalog_path = OUTPUT_DIR / "library_catalog.json"
        with open(catalog_path, 'w') as f:
            json.dump(self.catalog, f, indent=2)
        print(f"      Saved to: {catalog_path}")

        return self.catalog

    def _get_category(self, path: Path) -> str:
        """Extract category from file path"""
        parts = path.relative_to(LIBRARY_ROOT).parts

        if len(parts) >= 3 and parts[0] == "Master Library" and parts[1] == "Families":
            return parts[2]  # The folder under Families
        elif len(parts) >= 2 and parts[0] == "Drafting View Details":
            return parts[1]  # The detail category
        elif len(parts) >= 1:
            return parts[0]
        return "Uncategorized"

    def _extract_naming_patterns(self, name: str) -> Dict[str, Any]:
        """Extract patterns from family name"""
        patterns = {}

        # Detect dimensions (e.g., "8x8x16", "2x4", "24x36")
        dim_match = re.search(r'(\d+)x(\d+)(?:x(\d+))?', name, re.IGNORECASE)
        if dim_match:
            patterns["dimensions"] = dim_match.group(0)

        # Detect units (e.g., "12\"", "3'-6\"")
        unit_match = re.search(r"(\d+['\"-]?\s*\d*['\"-]?)", name)
        if unit_match:
            patterns["unit_spec"] = unit_match.group(0)

        # Detect material keywords
        materials = ["CMU", "CONCRETE", "WOOD", "STEEL", "METAL", "GLASS",
                    "ALUMINUM", "BRICK", "STONE", "GYPSUM", "DRYWALL"]
        for mat in materials:
            if mat in name.upper():
                patterns["material"] = mat
                break

        # Detect component type keywords
        types = ["DETAIL", "SECTION", "TAG", "HEAD", "JAMB", "SILL",
                "BEAM", "COLUMN", "REBAR", "BOND", "CAP", "BASE"]
        for t in types:
            if t in name.upper():
                patterns.setdefault("component_types", []).append(t)

        # Detect backup files (.0001, .0002)
        backup_match = re.search(r'\.(\d{4})$', name)
        if backup_match:
            patterns["is_backup"] = True
            patterns["backup_version"] = int(backup_match.group(1))

        return patterns

    def _analyze_patterns(self):
        """Analyze overall naming patterns in the library"""
        pattern_counts = defaultdict(int)
        material_counts = defaultdict(int)
        type_counts = defaultdict(int)

        for family_data in self.catalog["families"].values():
            patterns = family_data.get("patterns", {})

            if patterns.get("dimensions"):
                pattern_counts["has_dimensions"] += 1
            if patterns.get("material"):
                material_counts[patterns["material"]] += 1
            for t in patterns.get("component_types", []):
                type_counts[t] += 1

        self.catalog["patterns"] = {
            "dimension_patterns": pattern_counts["has_dimensions"],
            "materials_found": dict(material_counts),
            "component_types": dict(type_counts),
            "naming_conventions": self._identify_naming_conventions()
        }

    def _identify_naming_conventions(self) -> List[str]:
        """Identify naming conventions used in the library"""
        conventions = []

        # Sample names to analyze
        names = [f["name"] for f in list(self.catalog["families"].values())[:100]]

        uppercase_count = sum(1 for n in names if n.isupper() or n.replace("-", "").replace(" ", "").isupper())
        if uppercase_count > len(names) * 0.5:
            conventions.append("UPPERCASE naming preferred")

        hyphen_count = sum(1 for n in names if "-" in n)
        if hyphen_count > len(names) * 0.3:
            conventions.append("Hyphen-separated naming common")

        underscore_count = sum(1 for n in names if "_" in n)
        if underscore_count > len(names) * 0.3:
            conventions.append("Underscore_separated naming common")

        prefix_count = sum(1 for n in names if re.match(r'^[A-Z]+-', n))
        if prefix_count > len(names) * 0.2:
            conventions.append("PREFIX- category system used")

        return conventions

    def analyze_detail_items(self) -> Dict[str, Any]:
        """Deep analysis of Detail Items category - most relevant for drawing details"""
        print("\n" + "=" * 60)
        print("ANALYZING DETAIL ITEMS")
        print("=" * 60)

        detail_items = {}
        detail_path = LIBRARY_ROOT / "Master Library" / "Families" / "Detail Items"

        if not detail_path.exists():
            print("Detail Items folder not found!")
            return {}

        # Group by type
        groups = defaultdict(list)
        for f in detail_path.glob("*.rfa"):
            name = f.stem

            # Identify group by prefix or content
            if "CMU" in name.upper() or "MASONRY" in name.upper():
                groups["CMU/Masonry"].append(name)
            elif "WOOD" in name.upper() or "LUMBER" in name.upper():
                groups["Wood Framing"].append(name)
            elif "STEEL" in name.upper() or "METAL" in name.upper():
                groups["Steel/Metal"].append(name)
            elif "INSUL" in name.upper():
                groups["Insulation"].append(name)
            elif "FLASH" in name.upper():
                groups["Flashing"].append(name)
            elif "REBAR" in name.upper() or "REINF" in name.upper():
                groups["Reinforcement"].append(name)
            elif "BREAK" in name.upper():
                groups["Break Lines"].append(name)
            elif "SECTION" in name.upper():
                groups["Section Marks"].append(name)
            else:
                groups["Other"].append(name)

        detail_items = {
            "total_count": sum(len(v) for v in groups.values()),
            "groups": {k: {"count": len(v), "examples": v[:5]} for k, v in groups.items()}
        }

        # Save analysis
        analysis_path = OUTPUT_DIR / "detail_items_analysis.json"
        with open(analysis_path, 'w') as f:
            json.dump(detail_items, f, indent=2)
        print(f"Saved analysis to: {analysis_path}")

        return detail_items

    def generate_learning_queue(self) -> List[Dict]:
        """Generate a prioritized list of files to learn from"""
        print("\n" + "=" * 60)
        print("GENERATING LEARNING QUEUE")
        print("=" * 60)

        queue = []

        # Priority 1: Detail Items (most relevant for construction documents)
        detail_items = [p for p in self.catalog["families"].keys()
                       if "Detail Items" in p and ".0001" not in p and ".0002" not in p]
        for p in detail_items[:20]:  # Top 20
            queue.append({
                "path": str(LIBRARY_ROOT / p),
                "priority": 1,
                "reason": "Detail Items - core for CD production",
                "category": "Detail Items"
            })

        # Priority 2: Profiles (for wall/roof assemblies)
        profiles = [p for p in self.catalog["families"].keys()
                   if "Profile" in p and ".0001" not in p]
        for p in profiles[:10]:
            queue.append({
                "path": str(LIBRARY_ROOT / p),
                "priority": 2,
                "reason": "Profiles - needed for system families",
                "category": "Profiles"
            })

        # Priority 3: Annotation families
        annotations = [p for p in self.catalog["families"].keys()
                      if any(x in p for x in ["Tag", "Mark", "Head"]) and ".0001" not in p]
        for p in annotations[:10]:
            queue.append({
                "path": str(LIBRARY_ROOT / p),
                "priority": 3,
                "reason": "Annotations - documentation standards",
                "category": "Annotations"
            })

        # Save queue
        queue_path = OUTPUT_DIR / "learning_queue.json"
        with open(queue_path, 'w') as f:
            json.dump(queue, f, indent=2)
        print(f"Generated queue with {len(queue)} priority files")
        print(f"Saved to: {queue_path}")

        return queue

    def generate_report(self) -> str:
        """Generate a human-readable summary report"""
        print("\n" + "=" * 60)
        print("GENERATING SUMMARY REPORT")
        print("=" * 60)

        # Load existing catalog if available
        catalog_path = OUTPUT_DIR / "library_catalog.json"
        if catalog_path.exists():
            with open(catalog_path) as f:
                self.catalog = json.load(f)

        report = []
        report.append("# Revit Detail Library Analysis Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"Library Root: {LIBRARY_ROOT}")

        report.append("\n## Summary Statistics")
        report.append(f"- Total Families (.rfa): {len(self.catalog.get('families', {}))}")
        report.append(f"- Total Projects (.rvt): {len(self.catalog.get('projects', {}))}")
        report.append(f"- Categories: {len(self.catalog.get('categories', {}))}")

        report.append("\n## Categories Breakdown")
        report.append("| Category | Families | Projects |")
        report.append("|----------|----------|----------|")
        for cat, stats in sorted(self.catalog.get("categories", {}).items(),
                                 key=lambda x: x[1].get("families", 0), reverse=True):
            report.append(f"| {cat[:40]} | {stats.get('families', 0)} | {stats.get('projects', 0)} |")

        report.append("\n## Naming Patterns Discovered")
        patterns = self.catalog.get("patterns", {})
        report.append(f"- Files with dimension specs: {patterns.get('dimension_patterns', 0)}")
        report.append("\n### Materials Found")
        for mat, count in sorted(patterns.get("materials_found", {}).items(),
                                 key=lambda x: x[1], reverse=True):
            report.append(f"  - {mat}: {count} families")

        report.append("\n### Component Types")
        for t, count in sorted(patterns.get("component_types", {}).items(),
                               key=lambda x: x[1], reverse=True):
            report.append(f"  - {t}: {count} occurrences")

        report.append("\n### Naming Conventions")
        for conv in patterns.get("naming_conventions", []):
            report.append(f"  - {conv}")

        report.append("\n## Key Lessons for Claude")
        report.append("""
1. **Detail Item naming**: Use UPPERCASE with hyphens (e.g., "CMU-8x8x16-SECTION")
2. **Category organization**: Follow Autodesk category structure
3. **Versioning**: Avoid .0001/.0002 backup files - use primary files
4. **Materials in names**: Include material type for searchability
5. **Dimensions in names**: Include key dimensions where applicable
""")

        report_text = "\n".join(report)

        # Save report
        report_path = OUTPUT_DIR / "library_report.md"
        with open(report_path, 'w') as f:
            f.write(report_text)
        print(f"Saved report to: {report_path}")

        return report_text

    def extract_via_mcp(self, file_path: str) -> Optional[Dict]:
        """
        Extract detailed information from a file opened in Revit via MCP.
        This requires Revit to be open with the MCP server running.
        """
        print(f"\n[MCP] Attempting to connect to Revit...")

        # This would need to use the named pipe to communicate
        # For now, return a placeholder showing what we'd extract
        print("[MCP] Note: MCP extraction requires Revit with MCP server running")
        print("[MCP] Open the family in Revit and run: getElementsByCategory")

        return {
            "status": "requires_revit",
            "instructions": [
                "1. Open Revit",
                "2. Open the family file",
                "3. Use MCP to call getElementsByCategory to list elements",
                "4. Use getFamilyInstances to get placement details"
            ]
        }


def main():
    learner = DetailLibraryLearner()

    if len(sys.argv) < 2:
        print(__doc__)
        print("\nRunning full catalog and analysis...")
        learner.catalog_files()
        learner.analyze_detail_items()
        learner.generate_learning_queue()
        learner.generate_report()
        return

    command = sys.argv[1].lower()

    if command == "catalog":
        learner.catalog_files()
    elif command == "analyze":
        learner.catalog_files()
        learner.analyze_detail_items()
    elif command == "queue":
        learner.catalog_files()
        learner.generate_learning_queue()
    elif command == "report":
        learner.generate_report()
    elif command == "extract":
        if len(sys.argv) > 2:
            learner.extract_via_mcp(sys.argv[2])
        else:
            print("Usage: python learn_detail_library.py extract <file_path>")
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
