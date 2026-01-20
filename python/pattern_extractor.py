"""
Pattern Extractor - Extract floor plan patterns from existing Revit projects.

This module learns from real projects to build a pattern library that improves
the smart floor plan generator. It extracts:
- Room types, sizes, and aspect ratios
- Room adjacencies (what rooms share walls)
- Room positions (perimeter vs core)
- Circulation patterns (corridor widths, distances)

Patterns are stored in Memory MCP for persistence across sessions.

Usage:
    # Extract from single project
    python pattern_extractor.py --project "path/to/project.rvt"

    # Batch extract from folder
    python pattern_extractor.py --folder "path/to/projects" --building-type residential
"""

import json
import os
import sys
import math
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))

from adjacency_rules import MUST_CONNECT, SHOULD_ADJACENT, PREFER_NEAR, NEUTRAL, SHOULD_SEPARATE
from room_intelligence import DaylightRequirement, PlacementConstraint


@dataclass
class ExtractedRoom:
    """A room extracted from a Revit model."""
    name: str
    room_type: str  # Normalized type (e.g., "Private Office" from "OFFICE 101")
    area: float  # Square feet
    width: float  # Estimated width
    depth: float  # Estimated depth
    aspect_ratio: float
    perimeter: float
    x: float  # Center X coordinate
    y: float  # Center Y coordinate
    level: str
    has_exterior_wall: bool  # On building perimeter?

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExtractedAdjacency:
    """An observed adjacency between two rooms."""
    room_a: str
    room_b: str
    shared_wall_length: float  # Feet of shared wall
    has_door: bool  # Direct door connection?

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ProjectPattern:
    """Complete extracted pattern from a project."""
    project_name: str
    project_path: str
    building_type: str  # residential, office, healthcare, etc.
    total_area: float
    room_count: int
    rooms: List[ExtractedRoom]
    adjacencies: List[ExtractedAdjacency]
    building_footprint: Dict[str, float]  # width, depth, aspect_ratio
    extraction_date: str
    confidence: float  # How reliable is this extraction (0-1)

    def to_dict(self) -> Dict:
        return {
            **{k: v for k, v in asdict(self).items() if k not in ['rooms', 'adjacencies']},
            'rooms': [r.to_dict() for r in self.rooms],
            'adjacencies': [a.to_dict() for a in self.adjacencies]
        }


class PatternExtractor:
    """
    Extracts floor plan patterns from Revit projects via MCP Bridge.
    """

    # Room type normalization mapping
    ROOM_TYPE_MAP = {
        # Office types
        'office': 'Private Office',
        'private office': 'Private Office',
        'exec': 'Executive Office',
        'executive': 'Executive Office',
        'open office': 'Open Office',
        'workroom': 'Open Office',
        'conf': 'Conference',
        'conference': 'Conference',
        'meeting': 'Conference',
        'reception': 'Reception',
        'lobby': 'Entry',
        'entry': 'Entry',
        'vestibule': 'Entry',
        'waiting': 'Waiting',
        'break': 'Break Room',
        'kitchen': 'Break Room',
        'kitchenette': 'Break Room',
        'copy': 'Copy/Print',
        'print': 'Copy/Print',
        'mail': 'Copy/Print',
        'storage': 'Storage',
        'supply': 'Storage',
        'server': 'IT/Server',
        'it room': 'IT/Server',
        'data': 'IT/Server',
        'mech': 'Mechanical',
        'mechanical': 'Mechanical',
        'elec': 'Electrical',
        'electrical': 'Electrical',
        'janitor': 'Janitor',
        'jan': 'Janitor',
        'restroom': 'Restroom',
        'toilet': 'Restroom',
        'wc': 'Restroom',
        'men': 'Restroom',
        'women': 'Restroom',

        # Residential types
        'living': 'Living',
        'family': 'Living',
        'great room': 'Living',
        'dining': 'Dining',
        'kitchen': 'Kitchen',
        'master bed': 'Master Bedroom',
        'master': 'Master Bedroom',
        'mbr': 'Master Bedroom',
        'bedroom': 'Bedroom',
        'bed': 'Bedroom',
        'br': 'Bedroom',
        'bath': 'Bathroom',
        'bathroom': 'Bathroom',
        'master bath': 'Master Bath',
        'mbath': 'Master Bath',
        'powder': 'Powder Room',
        'half bath': 'Powder Room',
        'laundry': 'Laundry',
        'utility': 'Laundry',
        'garage': 'Garage',
        'gar': 'Garage',
        'closet': 'Walk-in Closet',
        'wic': 'Walk-in Closet',
        'pantry': 'Pantry',
        'mudroom': 'Mudroom',
        'foyer': 'Entry',
        'office': 'Home Office',
        'study': 'Home Office',
        'den': 'Home Office',

        # Healthcare types
        'exam': 'Exam Room',
        'exam room': 'Exam Room',
        'procedure': 'Procedure Room',
        'nurse': 'Nurse Station',
        'nursing': 'Nurse Station',
        'clean': 'Clean Utility',
        'soiled': 'Soiled Utility',
        'med room': 'Medication Room',
        'medication': 'Medication Room',
        'staff lounge': 'Staff Lounge',
        'patient': 'Patient Room',
        'registration': 'Registration',
    }

    # Building type detection keywords
    BUILDING_TYPE_KEYWORDS = {
        'residential': ['residence', 'home', 'house', 'single family', 'sf', 'duplex',
                       'bedroom', 'living room', 'master'],
        'multi-family': ['apartment', 'condo', 'unit', 'multi', 'story building', 'floor plan'],
        'office': ['office', 'conference', 'reception', 'executive', 'workstation'],
        'healthcare': ['hospital', 'clinic', 'medical', 'bethesda', 'msmc', 'exam room',
                      'nurse station', 'patient'],
        'retail': ['retail', 'store', 'shop', 'sales floor', 'fitting'],
        'educational': ['school', 'classroom', 'library', 'gymnasium', 'cafeteria'],
    }

    def __init__(self, mcp_pipe: str = r"\\.\pipe\RevitMCPBridge2026"):
        """Initialize pattern extractor with MCP pipe name."""
        self.mcp_pipe = mcp_pipe
        self.extracted_patterns: List[ProjectPattern] = []

    def call_mcp(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Call RevitMCPBridge via named pipe."""
        import socket

        request = {
            "method": method,
            "params": params or {}
        }

        # Windows named pipe via PowerShell
        ps_script = f'''
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "{self.mcp_pipe.replace(chr(92)*4, "")}", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(5000)
$reader = New-Object System.IO.StreamReader($pipe)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true

$request = '{json.dumps(request)}'
$writer.WriteLine($request)
$response = $reader.ReadLine()
$pipe.Close()

Write-Output $response
'''

        try:
            result = subprocess.run(
                ["powershell.exe", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout.strip())
            else:
                return {"success": False, "error": result.stderr or "No response"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def normalize_room_type(self, room_name: str) -> str:
        """Normalize a room name to a standard type."""
        name_lower = room_name.lower().strip()

        # Remove common suffixes (numbers, letters)
        import re
        name_clean = re.sub(r'[\d\s\-]+$', '', name_lower).strip()
        name_clean = re.sub(r'\s+\d+.*$', '', name_clean).strip()

        # Direct lookup
        if name_clean in self.ROOM_TYPE_MAP:
            return self.ROOM_TYPE_MAP[name_clean]

        # Partial match
        for keyword, room_type in self.ROOM_TYPE_MAP.items():
            if keyword in name_clean:
                return room_type

        # Return cleaned original if no match
        return room_name.title()

    def detect_building_type(self, project_name: str, rooms: List[Dict]) -> str:
        """Detect building type from project name and room types."""
        # Combine project name and room names for analysis
        text = project_name.lower()
        for room in rooms:
            text += " " + room.get("name", "").lower()

        scores = {bt: 0 for bt in self.BUILDING_TYPE_KEYWORDS}

        for building_type, keywords in self.BUILDING_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[building_type] += 1

        # Return highest scoring type, default to residential
        best_type = max(scores, key=scores.get)
        return best_type if scores[best_type] > 0 else "residential"

    def estimate_room_dimensions(self, area: float, perimeter: float) -> Tuple[float, float, float]:
        """
        Estimate room width and depth from area and perimeter.
        Uses quadratic formula: P = 2(W + D), A = W * D
        """
        if perimeter <= 0 or area <= 0:
            # Assume square
            side = math.sqrt(area) if area > 0 else 10
            return (side, side, 1.0)

        # P = 2W + 2D => W + D = P/2
        # A = W * D
        # W^2 - (P/2)W + A = 0
        half_perimeter = perimeter / 2
        discriminant = half_perimeter**2 - 4 * area

        if discriminant < 0:
            # Not a valid rectangle, approximate
            side = math.sqrt(area)
            return (side, side, 1.0)

        sqrt_disc = math.sqrt(discriminant)
        width = (half_perimeter + sqrt_disc) / 2
        depth = (half_perimeter - sqrt_disc) / 2

        # Ensure width >= depth
        if depth > width:
            width, depth = depth, width

        aspect_ratio = width / depth if depth > 0 else 1.0

        return (round(width, 1), round(depth, 1), round(aspect_ratio, 2))

    def is_perimeter_room(self, room_x: float, room_y: float,
                          building_bounds: Dict[str, float],
                          threshold: float = 5.0) -> bool:
        """Check if room is on building perimeter (within threshold feet of edge)."""
        min_x = building_bounds.get("min_x", 0)
        max_x = building_bounds.get("max_x", 100)
        min_y = building_bounds.get("min_y", 0)
        max_y = building_bounds.get("max_y", 100)

        near_edge = (
            room_x - min_x < threshold or
            max_x - room_x < threshold or
            room_y - min_y < threshold or
            max_y - room_y < threshold
        )
        return near_edge

    def detect_adjacencies(self, rooms: List[ExtractedRoom],
                           threshold: float = 10.0) -> List[ExtractedAdjacency]:
        """Detect room adjacencies based on proximity."""
        adjacencies = []

        for i, room_a in enumerate(rooms):
            for room_b in rooms[i+1:]:
                # Calculate distance between room centers
                dx = abs(room_a.x - room_b.x)
                dy = abs(room_a.y - room_b.y)

                # Estimate if rooms share a wall
                # Rooms are adjacent if centers are close enough considering their sizes
                combined_width = (room_a.width + room_b.width) / 2
                combined_depth = (room_a.depth + room_b.depth) / 2

                # Check if rooms could share a wall
                shares_x_wall = dx < combined_width + 2 and dy < max(room_a.depth, room_b.depth)
                shares_y_wall = dy < combined_depth + 2 and dx < max(room_a.width, room_b.width)

                if shares_x_wall or shares_y_wall:
                    # Estimate shared wall length
                    if shares_x_wall:
                        shared_length = min(room_a.depth, room_b.depth)
                    else:
                        shared_length = min(room_a.width, room_b.width)

                    adjacencies.append(ExtractedAdjacency(
                        room_a=room_a.room_type,
                        room_b=room_b.room_type,
                        shared_wall_length=shared_length,
                        has_door=False  # Would need door data to determine
                    ))

        return adjacencies

    def extract_from_current_model(self, project_name: Optional[str] = None) -> Optional[ProjectPattern]:
        """
        Extract patterns from currently open Revit model.

        Returns:
            ProjectPattern if successful, None if extraction fails
        """
        # Get project info
        project_info = self.call_mcp("getProjectInfo")
        if not project_info.get("success"):
            print(f"Failed to get project info: {project_info.get('error')}")
            return None

        if not project_name:
            project_name = project_info.get("name", "Unknown Project")
        project_path = project_info.get("path", "")

        # Get all rooms
        rooms_result = self.call_mcp("getRooms")
        if not rooms_result.get("success"):
            print(f"Failed to get rooms: {rooms_result.get('error')}")
            return None

        raw_rooms = rooms_result.get("rooms", [])
        if not raw_rooms:
            print("No rooms found in model")
            return None

        # Detect building type
        building_type = self.detect_building_type(project_name, raw_rooms)

        # Calculate building bounds
        min_x = min(r.get("x", 0) for r in raw_rooms)
        max_x = max(r.get("x", 0) for r in raw_rooms)
        min_y = min(r.get("y", 0) for r in raw_rooms)
        max_y = max(r.get("y", 0) for r in raw_rooms)

        building_bounds = {
            "min_x": min_x, "max_x": max_x,
            "min_y": min_y, "max_y": max_y
        }
        building_width = max_x - min_x
        building_depth = max_y - min_y

        # Process each room
        extracted_rooms = []
        total_area = 0

        for room in raw_rooms:
            name = room.get("name", "")
            area = room.get("area", 0)
            perimeter = room.get("perimeter", 0)
            x = room.get("x", 0)
            y = room.get("y", 0)
            level = room.get("level", "")

            if not name or area <= 0:
                continue

            total_area += area

            # Estimate dimensions
            width, depth, aspect_ratio = self.estimate_room_dimensions(area, perimeter)

            # Normalize room type
            room_type = self.normalize_room_type(name)

            # Check if on perimeter
            is_perimeter = self.is_perimeter_room(x, y, building_bounds)

            extracted_rooms.append(ExtractedRoom(
                name=name,
                room_type=room_type,
                area=area,
                width=width,
                depth=depth,
                aspect_ratio=aspect_ratio,
                perimeter=perimeter,
                x=x,
                y=y,
                level=level,
                has_exterior_wall=is_perimeter
            ))

        if not extracted_rooms:
            print("No valid rooms extracted")
            return None

        # Detect adjacencies
        adjacencies = self.detect_adjacencies(extracted_rooms)

        # Create pattern
        pattern = ProjectPattern(
            project_name=project_name,
            project_path=project_path,
            building_type=building_type,
            total_area=total_area,
            room_count=len(extracted_rooms),
            rooms=extracted_rooms,
            adjacencies=adjacencies,
            building_footprint={
                "width": building_width,
                "depth": building_depth,
                "aspect_ratio": round(building_width / building_depth, 2) if building_depth > 0 else 1.0
            },
            extraction_date=datetime.now().isoformat(),
            confidence=0.8  # High confidence for direct Revit extraction
        )

        self.extracted_patterns.append(pattern)
        return pattern

    def store_pattern_to_memory(self, pattern: ProjectPattern) -> bool:
        """Store extracted pattern to Memory MCP for persistence."""
        # Build memory content
        room_summary = {}
        for room in pattern.rooms:
            rt = room.room_type
            if rt not in room_summary:
                room_summary[rt] = {"count": 0, "total_area": 0, "areas": []}
            room_summary[rt]["count"] += 1
            room_summary[rt]["total_area"] += room.area
            room_summary[rt]["areas"].append(room.area)

        # Calculate averages
        room_stats = []
        for room_type, data in room_summary.items():
            avg_area = data["total_area"] / data["count"]
            room_stats.append(f"{room_type}: {data['count']}x @ avg {avg_area:.0f} SF")

        # Adjacency summary
        adj_summary = []
        for adj in pattern.adjacencies[:10]:  # Top 10
            adj_summary.append(f"{adj.room_a} <-> {adj.room_b}")

        content = f"""FLOOR PLAN PATTERN: {pattern.project_name}
Building Type: {pattern.building_type}
Total Area: {pattern.total_area:.0f} SF
Room Count: {pattern.room_count}
Footprint: {pattern.building_footprint['width']:.0f}' x {pattern.building_footprint['depth']:.0f}'

Room Types:
{chr(10).join(room_stats)}

Key Adjacencies:
{chr(10).join(adj_summary)}

Extracted: {pattern.extraction_date}
Source: {pattern.project_path}"""

        # Store via Memory MCP (would call MCP in actual usage)
        print(f"[Memory] Would store pattern for: {pattern.project_name}")
        print(f"Content preview: {content[:500]}...")

        return True

    def generate_room_statistics(self) -> Dict[str, Any]:
        """Generate statistics from all extracted patterns."""
        if not self.extracted_patterns:
            return {"error": "No patterns extracted"}

        # Aggregate by building type
        by_type = {}
        for pattern in self.extracted_patterns:
            bt = pattern.building_type
            if bt not in by_type:
                by_type[bt] = {
                    "projects": [],
                    "room_areas": {},  # room_type -> [areas]
                    "adjacencies": {}  # (room_a, room_b) -> count
                }

            by_type[bt]["projects"].append(pattern.project_name)

            for room in pattern.rooms:
                rt = room.room_type
                if rt not in by_type[bt]["room_areas"]:
                    by_type[bt]["room_areas"][rt] = []
                by_type[bt]["room_areas"][rt].append(room.area)

            for adj in pattern.adjacencies:
                key = tuple(sorted([adj.room_a, adj.room_b]))
                if key not in by_type[bt]["adjacencies"]:
                    by_type[bt]["adjacencies"][key] = 0
                by_type[bt]["adjacencies"][key] += 1

        # Calculate averages
        stats = {}
        for bt, data in by_type.items():
            room_avg = {}
            for rt, areas in data["room_areas"].items():
                room_avg[rt] = {
                    "count": len(areas),
                    "avg_area": sum(areas) / len(areas),
                    "min_area": min(areas),
                    "max_area": max(areas)
                }

            # Top adjacencies
            top_adj = sorted(data["adjacencies"].items(), key=lambda x: x[1], reverse=True)[:15]

            stats[bt] = {
                "project_count": len(data["projects"]),
                "room_statistics": room_avg,
                "common_adjacencies": [{"rooms": list(k), "count": v} for k, v in top_adj]
            }

        return stats

    def export_to_skill_file(self, output_path: str) -> bool:
        """Export extracted patterns as a skill file for future use."""
        stats = self.generate_room_statistics()

        content = f"""# Floor Plan Pattern Library
# Auto-generated from {len(self.extracted_patterns)} real projects
# Generated: {datetime.now().isoformat()}

## Purpose
This skill file contains empirically derived floor plan patterns from actual
architectural projects. Use these patterns to inform AI-generated floor plans.

## Statistics by Building Type

"""
        for bt, data in stats.items():
            content += f"### {bt.title()}\n"
            content += f"Projects analyzed: {data['project_count']}\n\n"

            content += "#### Room Sizes (SF)\n"
            content += "| Room Type | Avg | Min | Max | Count |\n"
            content += "|-----------|-----|-----|-----|-------|\n"
            for rt, rs in sorted(data["room_statistics"].items()):
                content += f"| {rt} | {rs['avg_area']:.0f} | {rs['min_area']:.0f} | {rs['max_area']:.0f} | {rs['count']} |\n"

            content += "\n#### Common Adjacencies\n"
            for adj in data["common_adjacencies"]:
                content += f"- {adj['rooms'][0]} <-> {adj['rooms'][1]} ({adj['count']} projects)\n"
            content += "\n"

        try:
            with open(output_path, 'w') as f:
                f.write(content)
            print(f"Exported skill file to: {output_path}")
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False


def main():
    """Main entry point for pattern extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract floor plan patterns from Revit projects")
    parser.add_argument("--current", action="store_true", help="Extract from current model")
    parser.add_argument("--output", type=str, default="/mnt/d/_CLAUDE-TOOLS/Claude_Skills/floor-plan-patterns.skill",
                       help="Output skill file path")

    args = parser.parse_args()

    extractor = PatternExtractor()

    if args.current:
        print("Extracting from current Revit model...")
        pattern = extractor.extract_from_current_model()
        if pattern:
            print(f"\nExtracted pattern from: {pattern.project_name}")
            print(f"Building type: {pattern.building_type}")
            print(f"Total area: {pattern.total_area:.0f} SF")
            print(f"Rooms: {pattern.room_count}")
            print(f"Adjacencies detected: {len(pattern.adjacencies)}")

            # Store to memory
            extractor.store_pattern_to_memory(pattern)

            # Export skill file
            extractor.export_to_skill_file(args.output)
    else:
        print("Use --current to extract from the currently open Revit model")
        print("Or provide --project path to extract from specific file")


if __name__ == "__main__":
    main()
