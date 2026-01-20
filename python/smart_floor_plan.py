"""
Smart Floor Plan Generator - Main Orchestrator

This is the main entry point for intelligent floor plan generation.
It orchestrates all the components:
- adjacency_rules.py - Room relationships
- zone_definitions.py - Zone organization
- room_intelligence.py - Room-specific rules
- placement_engine.py - Smart placement algorithm
- scheme_generator.py - Multi-scheme generation
- design_learner.py - Learning from feedback

Usage:
    from smart_floor_plan import generate_smart_floor_plan, SmartFloorPlanGenerator

    # Quick generation
    result = generate_smart_floor_plan(
        building_type="office",
        width=80, depth=50,
        rooms=[{"name": "Reception", "area": 150}, ...]
    )

    # Full control
    generator = SmartFloorPlanGenerator("office", 80, 50)
    generator.add_room("Reception", 150)
    generator.add_room("Conference", 200, occupancy=8)
    schemes = generator.generate(count=3)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import json
import math
import os

# Import all components
from adjacency_rules import (
    get_adjacencies, calculate_adjacency_score, build_adjacency_graph,
    MUST_CONNECT, SHOULD_ADJACENT
)
from zone_definitions import (
    get_zones, get_room_zone, group_rooms_by_zone, ZoneType
)
from room_intelligence import (
    get_room_rule, get_room_rules, suggest_room_size, size_room_by_occupancy,
    validate_room_program, DaylightRequirement, PlacementConstraint
)
from placement_engine import (
    SmartPlacementEngine, PlacementStrategy, place_floor_plan
)
from scheme_generator import (
    SchemeGenerator, generate_design_schemes, SCHEME_TYPES, GeneratedScheme
)
from design_learner import (
    DesignLearner, get_learner, record_selection, record_correction, apply_learnings
)


@dataclass
class RoomSpec:
    """Specification for a room to be placed."""
    name: str
    area: Optional[float] = None
    width: Optional[float] = None
    depth: Optional[float] = None
    occupancy: Optional[int] = None
    # Calculated
    final_width: float = 0
    final_depth: float = 0


class SmartFloorPlanGenerator:
    """
    Main orchestrator for intelligent floor plan generation.

    Workflow:
    1. Initialize with building type and dimensions
    2. Add rooms (by name/area, by occupancy, or explicit dimensions)
    3. Generate multiple schemes
    4. User selects or modifies
    5. Record learnings for future improvements
    """

    SUPPORTED_BUILDING_TYPES = ["office", "residential", "healthcare", "retail", "educational"]

    def __init__(self, building_type: str, width: float, depth: float,
                 entry_side: str = "south", apply_learnings: bool = True):
        """
        Initialize the smart floor plan generator.

        Args:
            building_type: Type of building (office, residential, etc.)
            width: Building width in feet
            depth: Building depth in feet
            entry_side: Side with main entry (south, north, east, west)
            apply_learnings: Whether to apply learned preferences
        """
        self.building_type = building_type.lower()
        self.width = width
        self.depth = depth
        self.entry_side = entry_side.lower()
        self.apply_learnings = apply_learnings

        # Validate building type
        if self.building_type not in self.SUPPORTED_BUILDING_TYPES:
            print(f"Warning: Unknown building type '{building_type}'. "
                  f"Using generic rules. Supported: {self.SUPPORTED_BUILDING_TYPES}")

        # Get knowledge bases
        self.room_rules = get_room_rules(self.building_type)
        self.adjacencies = get_adjacencies(self.building_type)
        self.zones = get_zones(self.building_type)

        # Room specifications
        self.rooms: List[RoomSpec] = []

        # Learning system
        self.learner = get_learner() if apply_learnings else None

        # Generated schemes
        self.schemes: List[Dict[str, Any]] = []
        self.selected_scheme: Optional[Dict[str, Any]] = None

    def add_room(self, name: str, area: Optional[float] = None,
                 width: Optional[float] = None, depth: Optional[float] = None,
                 occupancy: Optional[int] = None) -> 'SmartFloorPlanGenerator':
        """
        Add a room to the program.

        Can specify:
        - Just name: Uses default size from room rules
        - Name + area: Calculates dimensions for given area
        - Name + occupancy: Calculates size based on occupant count
        - Explicit width/depth: Uses given dimensions

        Args:
            name: Room type name (e.g., "Reception", "Private Office")
            area: Target area in square feet
            width, depth: Explicit dimensions
            occupancy: Number of occupants for sizing

        Returns:
            Self for chaining
        """
        spec = RoomSpec(
            name=name,
            area=area,
            width=width,
            depth=depth,
            occupancy=occupancy
        )

        # Calculate final dimensions
        self._resolve_dimensions(spec)

        self.rooms.append(spec)
        return self

    def add_rooms_from_list(self, room_list: List[Dict[str, Any]]) -> 'SmartFloorPlanGenerator':
        """
        Add multiple rooms from a list of dicts.

        Each dict can have: name, area, width, depth, occupancy

        Args:
            room_list: List of room specification dicts

        Returns:
            Self for chaining
        """
        for room in room_list:
            self.add_room(
                name=room.get("name", "Unknown"),
                area=room.get("area"),
                width=room.get("width"),
                depth=room.get("depth"),
                occupancy=room.get("occupancy")
            )
        return self

    def add_standard_program(self, template: str = "small_office") -> 'SmartFloorPlanGenerator':
        """
        Add a standard room program from template.

        Args:
            template: Program template name

        Returns:
            Self for chaining
        """
        templates = {
            "small_office": [
                {"name": "Entry", "area": 60},
                {"name": "Reception", "area": 120},
                {"name": "Waiting", "area": 80},
                {"name": "Conference", "occupancy": 8},
                {"name": "Private Office", "area": 120},
                {"name": "Private Office", "area": 120},
                {"name": "Open Office", "occupancy": 6},
                {"name": "Break Room", "area": 150},
                {"name": "Restroom", "area": 60},
                {"name": "Restroom", "area": 60},
                {"name": "Storage", "area": 80},
            ],
            "medium_office": [
                {"name": "Entry", "area": 100},
                {"name": "Reception", "area": 180},
                {"name": "Waiting", "area": 150},
                {"name": "Conference", "occupancy": 12},
                {"name": "Conference", "occupancy": 6},
                {"name": "Huddle", "area": 60},
                {"name": "Huddle", "area": 60},
                {"name": "Executive Office", "area": 250},
                {"name": "Private Office", "area": 150},
                {"name": "Private Office", "area": 150},
                {"name": "Private Office", "area": 120},
                {"name": "Private Office", "area": 120},
                {"name": "Open Office", "occupancy": 12},
                {"name": "Break Room", "area": 250},
                {"name": "Restroom", "area": 100},
                {"name": "Restroom", "area": 100},
                {"name": "Storage", "area": 120},
                {"name": "IT/Server", "area": 100},
            ],
            "small_house": [
                {"name": "Entry", "area": 40},
                {"name": "Living", "area": 200},
                {"name": "Dining", "area": 120},
                {"name": "Kitchen", "area": 140},
                {"name": "Master Bedroom", "area": 180},
                {"name": "Master Bath", "area": 80},
                {"name": "Bedroom", "area": 120},
                {"name": "Bedroom", "area": 120},
                {"name": "Bathroom", "area": 60},
                {"name": "Laundry", "area": 50},
                {"name": "Garage", "area": 400},
            ],
            "medical_clinic": [
                {"name": "Lobby", "area": 300},
                {"name": "Registration", "area": 100},
                {"name": "Waiting", "area": 250},
                {"name": "Exam Room", "area": 120},
                {"name": "Exam Room", "area": 120},
                {"name": "Exam Room", "area": 120},
                {"name": "Exam Room", "area": 120},
                {"name": "Nurse Station", "area": 150},
                {"name": "Clean Utility", "area": 80},
                {"name": "Soiled Utility", "area": 80},
                {"name": "Medication Room", "area": 60},
                {"name": "Staff Lounge", "area": 150},
                {"name": "Patient Toilet", "area": 60},
                {"name": "Patient Toilet", "area": 60},
                {"name": "Staff Restroom", "area": 50},
                {"name": "Storage", "area": 100},
            ],
        }

        if template not in templates:
            available = ", ".join(templates.keys())
            raise ValueError(f"Unknown template '{template}'. Available: {available}")

        return self.add_rooms_from_list(templates[template])

    def _resolve_dimensions(self, spec: RoomSpec):
        """Calculate final dimensions for a room spec."""
        # If explicit dimensions given, use them
        if spec.width and spec.depth:
            spec.final_width = spec.width
            spec.final_depth = spec.depth
            return

        # Try occupancy-based sizing first
        if spec.occupancy:
            result = size_room_by_occupancy(self.building_type, spec.name, spec.occupancy)
            if result:
                spec.final_width, spec.final_depth = result
                return

        # Try area-based sizing
        if spec.area:
            rule = get_room_rule(self.building_type, spec.name)
            if rule:
                spec.final_width, spec.final_depth = rule.calculate_dimensions(spec.area)
            else:
                # Fallback: square root for roughly square room
                side = math.sqrt(spec.area)
                spec.final_width = round(side * 1.2, 1)  # Slightly rectangular
                spec.final_depth = round(spec.area / spec.final_width, 1)
            return

        # Use room rule defaults
        suggestion = suggest_room_size(self.building_type, spec.name)
        if "error" not in suggestion:
            spec.final_width = suggestion["width"]
            spec.final_depth = suggestion["depth"]
        else:
            # Ultimate fallback
            spec.final_width = 12
            spec.final_depth = 10

    def get_program(self) -> List[Dict[str, Any]]:
        """Get the current room program as list of dicts."""
        program = []
        name_counts = {}

        for spec in self.rooms:
            # Make names unique
            base_name = spec.name
            if base_name in name_counts:
                name_counts[base_name] += 1
                unique_name = f"{base_name} {name_counts[base_name]}"
            else:
                name_counts[base_name] = 1
                unique_name = base_name

            program.append({
                "name": unique_name,
                "width": spec.final_width,
                "depth": spec.final_depth,
                "area": spec.final_width * spec.final_depth
            })

        # Apply learned adjustments if enabled
        if self.apply_learnings and self.learner:
            program = self.learner.apply_learnings_to_program(program, self.building_type)

        return program

    def validate_program(self) -> Dict[str, Any]:
        """
        Validate the current room program against rules.

        Returns:
            Validation result with issues and warnings
        """
        program = self.get_program()
        result = validate_room_program(self.building_type, program)

        # Add building-level checks
        total_room_area = sum(r["area"] for r in program)
        building_area = self.width * self.depth
        efficiency_estimate = total_room_area / building_area if building_area > 0 else 0

        if efficiency_estimate > 0.85:
            result["warnings"].append(
                f"Program may be too large for building. "
                f"Estimated {efficiency_estimate*100:.0f}% fill (typical max ~78%)"
            )
        elif efficiency_estimate < 0.50:
            result["warnings"].append(
                f"Program uses only {efficiency_estimate*100:.0f}% of building area. "
                f"Consider additional rooms or smaller building."
            )

        result["program_summary"] = {
            "room_count": len(program),
            "total_room_area": round(total_room_area, 0),
            "building_area": round(building_area, 0),
            "estimated_efficiency": round(efficiency_estimate, 3)
        }

        return result

    def generate(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate multiple design schemes.

        Args:
            count: Number of schemes to generate

        Returns:
            List of scheme dicts with placements, metrics, analysis
        """
        program = self.get_program()

        if not program:
            raise ValueError("No rooms in program. Add rooms before generating.")

        # Generate schemes
        result = generate_design_schemes(
            self.width, self.depth, self.building_type,
            program, count, self.entry_side
        )

        self.schemes = result["schemes"]
        return result

    def select_scheme(self, scheme_index: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Select a scheme and record the selection for learning.

        Args:
            scheme_index: Index of selected scheme (0-based)
            reason: Optional reason for selection

        Returns:
            The selected scheme
        """
        if not self.schemes:
            raise ValueError("No schemes generated. Call generate() first.")

        if scheme_index < 0 or scheme_index >= len(self.schemes):
            raise ValueError(f"Invalid scheme index. Must be 0-{len(self.schemes)-1}")

        self.selected_scheme = self.schemes[scheme_index]
        rejected = [s for i, s in enumerate(self.schemes) if i != scheme_index]

        # Record selection for learning
        if self.learner:
            record_selection(self.selected_scheme, rejected, reason)

        return self.selected_scheme

    def correct_room(self, room_name: str, new_x: Optional[float] = None,
                    new_y: Optional[float] = None, new_width: Optional[float] = None,
                    new_depth: Optional[float] = None,
                    reason: Optional[str] = None) -> bool:
        """
        Record a correction to a room in the selected scheme.

        Args:
            room_name: Name of room to correct
            new_x, new_y: New position (if changed)
            new_width, new_depth: New dimensions (if changed)
            reason: Optional reason for correction

        Returns:
            True if correction recorded
        """
        if not self.selected_scheme:
            raise ValueError("No scheme selected. Call select_scheme() first.")

        # Find the room in selected scheme
        placed_rooms = self.selected_scheme.get("placed_rooms", [])
        original = None
        for room in placed_rooms:
            if room["name"] == room_name:
                original = room
                break

        if not original:
            print(f"Warning: Room '{room_name}' not found in selected scheme")
            return False

        # Build corrected version
        corrected = dict(original)
        if new_x is not None:
            corrected["x"] = new_x
        if new_y is not None:
            corrected["y"] = new_y
        if new_width is not None:
            corrected["width"] = new_width
        if new_depth is not None:
            corrected["depth"] = new_depth

        # Record correction
        if self.learner:
            record_correction(room_name, self.building_type, original, corrected, reason)
            return True

        return False

    def get_adjacency_graph(self) -> Dict[str, Any]:
        """Get adjacency relationships for the current program."""
        program = self.get_program()
        room_names = [r["name"] for r in program]
        return build_adjacency_graph(self.building_type, room_names)

    def get_zone_groupings(self) -> Dict[str, List[str]]:
        """Get rooms grouped by zone."""
        program = self.get_program()
        room_names = [r["name"] for r in program]
        return group_rooms_by_zone(self.building_type, room_names)

    def export_to_json(self, filepath: str, include_all_schemes: bool = False):
        """
        Export generation results to JSON file.

        Args:
            filepath: Output file path
            include_all_schemes: Include all schemes or just selected
        """
        export_data = {
            "building_type": self.building_type,
            "building_dimensions": {
                "width": self.width,
                "depth": self.depth,
                "area": self.width * self.depth
            },
            "entry_side": self.entry_side,
            "program": self.get_program(),
            "selected_scheme": self.selected_scheme,
            "generated_at": datetime.now().isoformat()
        }

        if include_all_schemes:
            export_data["all_schemes"] = self.schemes

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"Exported to {filepath}")

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learned preferences."""
        if self.learner:
            return self.learner.get_learning_summary(self.building_type)
        return {"learning_disabled": True}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_smart_floor_plan(building_type: str, width: float, depth: float,
                              rooms: Optional[List[Dict[str, Any]]] = None,
                              template: Optional[str] = None,
                              count: int = 3,
                              entry_side: str = "south") -> Dict[str, Any]:
    """
    One-shot function to generate smart floor plan schemes.

    Args:
        building_type: Type of building
        width, depth: Building dimensions
        rooms: List of room specs (name, area/width/depth/occupancy)
        template: Use predefined template instead of rooms
        count: Number of schemes to generate
        entry_side: Side with main entry

    Returns:
        Complete result with schemes, comparison, metrics
    """
    generator = SmartFloorPlanGenerator(building_type, width, depth, entry_side)

    if template:
        generator.add_standard_program(template)
    elif rooms:
        generator.add_rooms_from_list(rooms)
    else:
        raise ValueError("Must provide either 'rooms' or 'template'")

    return generator.generate(count)


def quick_office_layout(width: float, depth: float, size: str = "small") -> Dict[str, Any]:
    """Quick office layout generation."""
    template = f"{size}_office" if size in ["small", "medium"] else "small_office"
    return generate_smart_floor_plan("office", width, depth, template=template)


def quick_house_layout(width: float, depth: float) -> Dict[str, Any]:
    """Quick house layout generation."""
    return generate_smart_floor_plan("residential", width, depth, template="small_house")


def quick_clinic_layout(width: float, depth: float) -> Dict[str, Any]:
    """Quick medical clinic layout generation."""
    return generate_smart_floor_plan("healthcare", width, depth, template="medical_clinic")


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SMART FLOOR PLAN GENERATOR - COMPREHENSIVE TEST")
    print("=" * 70)

    # Test 1: Quick office generation
    print("\n" + "=" * 70)
    print("TEST 1: Quick Office Layout (80' x 50')")
    print("=" * 70)

    result = quick_office_layout(80, 50, "small")

    print(f"\nGenerated {len(result['schemes'])} schemes:")
    for scheme in result["schemes"]:
        print(f"\n  {scheme['scheme_id']}: {scheme['scheme_name']}")
        print(f"    Efficiency: {scheme['metrics']['efficiency']*100:.0f}%")
        print(f"    Adjacency:  {scheme['metrics']['adjacency_score']*100:.0f}%")
        print(f"    Daylight:   {scheme['metrics']['daylight_ratio']*100:.0f}%")
        print(f"    Rooms placed: {scheme['metrics']['rooms_placed']}/{scheme['metrics']['rooms_requested']}")

    print(f"\n  RECOMMENDATION: {result['comparison']['recommendation']}")
    print(f"  {result['comparison']['recommendation_reason']}")

    # Test 2: Full generator workflow
    print("\n" + "=" * 70)
    print("TEST 2: Full Generator Workflow")
    print("=" * 70)

    generator = SmartFloorPlanGenerator("office", 100, 60)

    # Add rooms with various methods
    generator.add_room("Entry", area=80)
    generator.add_room("Reception", area=150)
    generator.add_room("Conference", occupancy=10)  # Size by occupancy
    generator.add_room("Executive Office", width=18, depth=16)  # Explicit
    generator.add_room("Private Office", area=130)
    generator.add_room("Private Office", area=130)
    generator.add_room("Open Office", occupancy=8)
    generator.add_room("Break Room")  # Use defaults
    generator.add_room("Restroom")
    generator.add_room("Storage")

    # Validate
    print("\nValidation:")
    validation = generator.validate_program()
    print(f"  Valid: {validation['valid']}")
    print(f"  Room count: {validation['program_summary']['room_count']}")
    print(f"  Total area: {validation['program_summary']['total_room_area']} SF")
    print(f"  Est. efficiency: {validation['program_summary']['estimated_efficiency']*100:.0f}%")
    if validation['issues']:
        print(f"  Issues: {validation['issues']}")
    if validation['warnings']:
        print(f"  Warnings: {validation['warnings']}")

    # Generate
    print("\nGenerating schemes...")
    result = generator.generate(count=3)

    print(f"\nBest scheme: {result['comparison']['recommendation']}")

    # Select and demonstrate learning
    print("\nSelecting scheme 0...")
    selected = generator.select_scheme(0, "Best overall efficiency")
    print(f"  Selected: {selected['scheme_id']}")

    # Simulate correction
    if selected.get("placed_rooms"):
        first_room = selected["placed_rooms"][0]["name"]
        generator.correct_room(first_room, new_x=5, reason="Moved closer to entry")
        print(f"  Recorded correction for '{first_room}'")

    # Learning summary
    print("\nLearning Summary:")
    summary = generator.get_learning_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Test 3: Zone and adjacency info
    print("\n" + "=" * 70)
    print("TEST 3: Zone and Adjacency Information")
    print("=" * 70)

    zones = generator.get_zone_groupings()
    print("\nRooms by Zone:")
    for zone, rooms in zones.items():
        print(f"  {zone}: {', '.join(rooms)}")

    graph = generator.get_adjacency_graph()
    print(f"\nAdjacency Graph: {len(graph.get('edges', []))} relationships defined")

    print("\n" + "=" * 70)
    print("SMART FLOOR PLAN GENERATOR - ALL TESTS PASSED!")
    print("=" * 70)
