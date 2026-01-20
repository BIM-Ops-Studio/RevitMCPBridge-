"""
Room Intelligence Module - Room-specific design rules and constraints.

This module defines detailed design rules for each room type including:
- Minimum and preferred areas
- Aspect ratio ranges (for natural proportions)
- Daylight requirements
- Special placement constraints
- Furniture/equipment clearances
- Code-driven requirements

Works with adjacency_rules.py and zone_definitions.py to create
intelligent floor plan layouts.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto


class DaylightRequirement(Enum):
    """Daylight access requirement for rooms."""
    REQUIRED = auto()      # Must have exterior wall/window
    PREFERRED = auto()     # Should have if possible
    NOT_REQUIRED = auto()  # Can be interior (core) space


class PlacementConstraint(Enum):
    """Special placement constraints for rooms."""
    PERIMETER = auto()         # Must be on exterior wall
    CORE = auto()              # Should be in building core
    NEAR_ENTRY = auto()        # Place near main entry
    BACK_OF_HOUSE = auto()     # Place away from public areas
    CORNER = auto()            # Benefits from corner location
    PLUMBING_CLUSTER = auto()  # Group with other wet rooms
    LOADING_ACCESS = auto()    # Needs exterior access for deliveries
    ENTRY_FACING = auto()      # Should face/see the entry


@dataclass
class RoomRule:
    """
    Complete design rules for a room type.

    Attributes:
        room_type: Name of the room type
        min_area: Absolute minimum area in square feet
        preferred_area: Ideal area in square feet
        max_area: Maximum useful area (larger is waste)
        aspect_ratio_range: (min, max) ratio of long/short side
        daylight: Daylight requirement level
        constraints: List of placement constraints
        clearances: Dict of required clearances in feet
        per_person_sf: Square feet per occupant for sizing
        description: Human-readable description of room purpose
        code_reference: Building code reference if applicable
    """
    room_type: str
    min_area: float
    preferred_area: float
    max_area: Optional[float] = None
    aspect_ratio_range: Tuple[float, float] = (1.0, 1.5)
    daylight: DaylightRequirement = DaylightRequirement.PREFERRED
    constraints: List[PlacementConstraint] = field(default_factory=list)
    clearances: Dict[str, float] = field(default_factory=dict)
    per_person_sf: Optional[float] = None
    description: str = ""
    code_reference: Optional[str] = None

    def calculate_dimensions(self, target_area: Optional[float] = None) -> Tuple[float, float]:
        """
        Calculate ideal dimensions for given area using golden ratio bias.
        Returns (width, depth) tuple in feet.
        """
        area = target_area or self.preferred_area

        # Use middle of aspect ratio range, biased toward golden ratio (1.618)
        min_ratio, max_ratio = self.aspect_ratio_range
        ideal_ratio = min(max(1.5, min_ratio), max_ratio)  # Prefer ~1.5

        # Calculate dimensions
        import math
        depth = math.sqrt(area / ideal_ratio)
        width = area / depth

        return (round(width, 1), round(depth, 1))

    def validate_dimensions(self, width: float, depth: float) -> Tuple[bool, List[str]]:
        """
        Validate proposed dimensions against rules.
        Returns (is_valid, list_of_issues).
        """
        issues = []
        area = width * depth

        if area < self.min_area:
            issues.append(f"Area {area:.0f} SF below minimum {self.min_area:.0f} SF")

        if self.max_area and area > self.max_area:
            issues.append(f"Area {area:.0f} SF exceeds maximum {self.max_area:.0f} SF")

        # Check aspect ratio
        ratio = max(width, depth) / min(width, depth) if min(width, depth) > 0 else 999
        min_ratio, max_ratio = self.aspect_ratio_range
        if ratio < min_ratio or ratio > max_ratio:
            issues.append(f"Aspect ratio {ratio:.2f} outside range ({min_ratio:.1f}-{max_ratio:.1f})")

        # Check specific clearances
        for clearance_type, required in self.clearances.items():
            if "width" in clearance_type.lower() and width < required:
                issues.append(f"Width {width:.1f}' below {clearance_type} of {required:.1f}'")
            if "depth" in clearance_type.lower() and depth < required:
                issues.append(f"Depth {depth:.1f}' below {clearance_type} of {required:.1f}'")

        return (len(issues) == 0, issues)


@dataclass
class BuildingRoomRules:
    """Collection of room rules for a building type."""
    building_type: str
    rules: Dict[str, RoomRule]

    def get_rule(self, room_type: str) -> Optional[RoomRule]:
        """Get rule for room type (case-insensitive)."""
        normalized = room_type.lower().replace("_", " ").replace("-", " ")
        for key, rule in self.rules.items():
            if key.lower() == normalized:
                return rule
        # Try partial match
        for key, rule in self.rules.items():
            if normalized in key.lower() or key.lower() in normalized:
                return rule
        return None

    def get_perimeter_rooms(self) -> List[str]:
        """Get list of rooms that must be on perimeter."""
        return [
            name for name, rule in self.rules.items()
            if PlacementConstraint.PERIMETER in rule.constraints
        ]

    def get_core_rooms(self) -> List[str]:
        """Get list of rooms that should be in core."""
        return [
            name for name, rule in self.rules.items()
            if PlacementConstraint.CORE in rule.constraints
        ]

    def get_plumbing_cluster_rooms(self) -> List[str]:
        """Get list of rooms that should be clustered for plumbing."""
        return [
            name for name, rule in self.rules.items()
            if PlacementConstraint.PLUMBING_CLUSTER in rule.constraints
        ]


# =============================================================================
# OFFICE BUILDING ROOM RULES
# =============================================================================

OFFICE_ROOM_RULES = BuildingRoomRules(
    building_type="office",
    rules={
        "Entry": RoomRule(
            room_type="Entry",
            min_area=60,
            preferred_area=100,
            max_area=200,
            aspect_ratio_range=(1.0, 2.0),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"min_width": 6.0, "door_clearance": 5.0},
            description="Main entrance vestibule/lobby"
        ),
        "Reception": RoomRule(
            room_type="Reception",
            min_area=100,
            preferred_area=150,
            max_area=300,
            aspect_ratio_range=(1.2, 1.8),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.NEAR_ENTRY, PlacementConstraint.ENTRY_FACING],
            clearances={"desk_front": 4.0, "waiting_area": 6.0},
            description="Reception desk with waiting area visibility"
        ),
        "Waiting": RoomRule(
            room_type="Waiting",
            min_area=80,
            preferred_area=120,
            max_area=250,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"seating_depth": 3.0, "aisle": 4.0},
            per_person_sf=15,
            description="Visitor waiting area near reception"
        ),
        "Conference": RoomRule(
            room_type="Conference",
            min_area=120,
            preferred_area=200,
            max_area=500,
            aspect_ratio_range=(1.3, 1.8),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"table_perimeter": 3.0, "presenter_area": 4.0},
            per_person_sf=25,
            description="Meeting room with table seating",
            code_reference="IBC Table 1004.5 - 15 net SF/person assembly"
        ),
        "Private Office": RoomRule(
            room_type="Private Office",
            min_area=100,
            preferred_area=150,
            max_area=250,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER],
            clearances={"desk_clearance": 3.0, "guest_seating": 4.0},
            description="Individual private workspace with window"
        ),
        "Executive Office": RoomRule(
            room_type="Executive Office",
            min_area=200,
            preferred_area=300,
            max_area=500,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER, PlacementConstraint.CORNER],
            clearances={"desk_clearance": 4.0, "seating_area": 6.0},
            description="Large executive office with meeting area"
        ),
        "Open Office": RoomRule(
            room_type="Open Office",
            min_area=400,
            preferred_area=1000,
            max_area=None,  # Can be very large
            aspect_ratio_range=(1.0, 2.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"aisle_main": 5.0, "aisle_secondary": 4.0},
            per_person_sf=75,  # With workstations
            description="Open plan workspace area"
        ),
        "Break Room": RoomRule(
            room_type="Break Room",
            min_area=150,
            preferred_area=250,
            max_area=500,
            aspect_ratio_range=(1.0, 1.6),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"counter_clearance": 4.0, "table_clearance": 3.0},
            per_person_sf=25,
            description="Staff kitchen and break area"
        ),
        "Restroom": RoomRule(
            room_type="Restroom",
            min_area=60,
            preferred_area=100,
            max_area=200,
            aspect_ratio_range=(0.5, 0.9),  # Typically narrow
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"fixture_clearance": 2.5, "accessible_stall": 5.0},
            description="Toilet room",
            code_reference="IBC 2902.1 - Minimum fixtures by occupancy"
        ),
        "Storage": RoomRule(
            room_type="Storage",
            min_area=50,
            preferred_area=100,
            max_area=300,
            aspect_ratio_range=(0.6, 2.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE],
            clearances={"aisle": 3.0},
            description="General storage and supplies"
        ),
        "IT/Server": RoomRule(
            room_type="IT/Server",
            min_area=80,
            preferred_area=150,
            max_area=400,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE],
            clearances={"rack_front": 4.0, "rack_back": 3.0},
            description="IT equipment and server room"
        ),
        "Mechanical": RoomRule(
            room_type="Mechanical",
            min_area=80,
            preferred_area=150,
            max_area=None,
            aspect_ratio_range=(1.0, 2.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE, PlacementConstraint.BACK_OF_HOUSE],
            clearances={"equipment_clearance": 3.0, "service_access": 4.0},
            description="HVAC and mechanical equipment"
        ),
        "Copy/Print": RoomRule(
            room_type="Copy/Print",
            min_area=60,
            preferred_area=100,
            max_area=200,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[],
            clearances={"equipment_clearance": 3.0},
            description="Copy and print center"
        ),
        "Huddle": RoomRule(
            room_type="Huddle",
            min_area=60,
            preferred_area=80,
            max_area=120,
            aspect_ratio_range=(1.0, 1.3),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"table_clearance": 2.5},
            per_person_sf=20,
            description="Small informal meeting space (2-4 people)"
        ),
        "Phone Room": RoomRule(
            room_type="Phone Room",
            min_area=30,
            preferred_area=40,
            max_area=60,
            aspect_ratio_range=(0.8, 1.2),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[],
            clearances={"min_width": 4.5},
            description="Private phone/video call booth"
        ),
    }
)


# =============================================================================
# RESIDENTIAL ROOM RULES
# =============================================================================

RESIDENTIAL_ROOM_RULES = BuildingRoomRules(
    building_type="residential",
    rules={
        "Entry": RoomRule(
            room_type="Entry",
            min_area=25,
            preferred_area=40,
            max_area=100,
            aspect_ratio_range=(0.8, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"door_swing": 3.0, "coat_closet": 2.0},
            description="Entry foyer with coat storage"
        ),
        "Living": RoomRule(
            room_type="Living",
            min_area=150,
            preferred_area=250,
            max_area=500,
            aspect_ratio_range=(1.0, 1.6),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER],
            clearances={"seating_circle": 10.0, "tv_distance": 8.0},
            description="Main living/family room"
        ),
        "Dining": RoomRule(
            room_type="Dining",
            min_area=100,
            preferred_area=150,
            max_area=300,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"table_perimeter": 3.0, "serving_side": 4.0},
            per_person_sf=20,
            description="Formal dining room"
        ),
        "Kitchen": RoomRule(
            room_type="Kitchen",
            min_area=80,
            preferred_area=150,
            max_area=350,
            aspect_ratio_range=(1.0, 1.8),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={
                "work_triangle_min": 13.0,
                "work_triangle_max": 26.0,
                "counter_depth": 2.0,
                "aisle_min": 3.5,
                "aisle_two_cook": 4.0
            },
            description="Kitchen with work triangle layout"
        ),
        "Master Bedroom": RoomRule(
            room_type="Master Bedroom",
            min_area=150,
            preferred_area=200,
            max_area=400,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER],
            clearances={"bed_sides": 2.5, "dresser_clearance": 3.0, "closet_access": 3.0},
            description="Primary bedroom suite"
        ),
        "Master Bath": RoomRule(
            room_type="Master Bath",
            min_area=60,
            preferred_area=100,
            max_area=200,
            aspect_ratio_range=(0.8, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={
                "toilet_clearance": 2.5,
                "vanity_clearance": 3.0,
                "shower_entry": 2.5,
                "tub_access": 2.0
            },
            description="Primary bathroom with shower/tub"
        ),
        "Bedroom": RoomRule(
            room_type="Bedroom",
            min_area=100,
            preferred_area=130,
            max_area=200,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER],
            clearances={"bed_access": 2.5, "closet_access": 3.0},
            description="Secondary bedroom",
            code_reference="IRC R304 - Min 70 SF, 7' min dimension"
        ),
        "Bathroom": RoomRule(
            room_type="Bathroom",
            min_area=40,
            preferred_area=60,
            max_area=120,
            aspect_ratio_range=(0.6, 1.2),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"fixture_clearance": 2.5, "door_swing": 2.5},
            description="Full or 3/4 bathroom"
        ),
        "Powder Room": RoomRule(
            room_type="Powder Room",
            min_area=20,
            preferred_area=30,
            max_area=50,
            aspect_ratio_range=(0.5, 1.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"toilet_clearance": 2.0, "vanity_clearance": 2.0},
            description="Half bath (toilet + sink only)"
        ),
        "Laundry": RoomRule(
            room_type="Laundry",
            min_area=35,
            preferred_area=60,
            max_area=120,
            aspect_ratio_range=(0.6, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"appliance_front": 3.5, "folding_area": 3.0},
            description="Laundry room with washer/dryer"
        ),
        "Garage": RoomRule(
            room_type="Garage",
            min_area=200,  # 1-car
            preferred_area=400,  # 2-car
            max_area=800,  # 3-car+
            aspect_ratio_range=(1.0, 2.5),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.LOADING_ACCESS],
            clearances={"car_width": 9.0, "car_length": 20.0, "door_aisle": 3.0},
            description="Vehicle garage"
        ),
        "Home Office": RoomRule(
            room_type="Home Office",
            min_area=80,
            preferred_area=120,
            max_area=200,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER],
            clearances={"desk_clearance": 3.0},
            description="Dedicated home office/study"
        ),
        "Pantry": RoomRule(
            room_type="Pantry",
            min_area=20,
            preferred_area=40,
            max_area=80,
            aspect_ratio_range=(0.4, 1.0),  # Often narrow walk-in
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[],
            clearances={"aisle": 3.0},
            description="Kitchen pantry storage"
        ),
        "Mudroom": RoomRule(
            room_type="Mudroom",
            min_area=40,
            preferred_area=70,
            max_area=150,
            aspect_ratio_range=(0.8, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"bench_depth": 2.0, "aisle": 4.0},
            description="Entry utility room with storage"
        ),
        "Walk-in Closet": RoomRule(
            room_type="Walk-in Closet",
            min_area=25,
            preferred_area=50,
            max_area=150,
            aspect_ratio_range=(0.5, 2.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[],
            clearances={"aisle": 3.0, "hanging_depth": 2.0},
            description="Walk-in wardrobe closet"
        ),
    }
)


# =============================================================================
# HEALTHCARE ROOM RULES
# =============================================================================

HEALTHCARE_ROOM_RULES = BuildingRoomRules(
    building_type="healthcare",
    rules={
        "Lobby": RoomRule(
            room_type="Lobby",
            min_area=200,
            preferred_area=400,
            max_area=1000,
            aspect_ratio_range=(1.0, 2.0),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"wheelchair_turning": 5.0, "seating_rows": 6.0},
            per_person_sf=15,
            description="Main lobby with accessible seating"
        ),
        "Registration": RoomRule(
            room_type="Registration",
            min_area=80,
            preferred_area=120,
            max_area=200,
            aspect_ratio_range=(1.2, 1.8),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.NEAR_ENTRY, PlacementConstraint.ENTRY_FACING],
            clearances={"counter_depth": 3.0, "queue_space": 6.0},
            description="Patient registration and check-in"
        ),
        "Waiting": RoomRule(
            room_type="Waiting",
            min_area=150,
            preferred_area=300,
            max_area=600,
            aspect_ratio_range=(1.0, 1.6),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"wheelchair_space": 4.0, "aisle": 4.0},
            per_person_sf=20,
            description="Patient and family waiting area",
            code_reference="FGI 2.1-2.4 - Waiting room requirements"
        ),
        "Exam Room": RoomRule(
            room_type="Exam Room",
            min_area=100,
            preferred_area=120,
            max_area=160,
            aspect_ratio_range=(1.0, 1.3),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={
                "exam_table_sides": 3.0,
                "exam_table_foot": 4.0,
                "wheelchair_clearance": 5.0
            },
            description="Standard medical exam room",
            code_reference="FGI 2.1-3.2.2.1 - Min 100 SF"
        ),
        "Procedure Room": RoomRule(
            room_type="Procedure Room",
            min_area=200,
            preferred_area=280,
            max_area=400,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"table_perimeter": 4.0, "equipment_space": 3.0},
            description="Minor procedure room",
            code_reference="FGI 2.1-3.2.2.4 - Min 200 SF"
        ),
        "Nurse Station": RoomRule(
            room_type="Nurse Station",
            min_area=100,
            preferred_area=200,
            max_area=400,
            aspect_ratio_range=(1.5, 3.0),  # Often linear
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"work_surface": 3.0, "charting_space": 4.0},
            description="Nursing workstation with visibility to patients"
        ),
        "Clean Utility": RoomRule(
            room_type="Clean Utility",
            min_area=60,
            preferred_area=100,
            max_area=150,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE],
            clearances={"counter_clearance": 3.0},
            description="Clean supply storage and preparation"
        ),
        "Soiled Utility": RoomRule(
            room_type="Soiled Utility",
            min_area=60,
            preferred_area=100,
            max_area=150,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"sink_clearance": 3.0, "disposal_access": 3.0},
            description="Soiled material holding and processing"
        ),
        "Medication Room": RoomRule(
            room_type="Medication Room",
            min_area=50,
            preferred_area=80,
            max_area=120,
            aspect_ratio_range=(1.0, 1.3),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE],
            clearances={"counter_clearance": 3.0, "refrigerator_access": 3.0},
            description="Secure medication storage and prep"
        ),
        "Patient Toilet": RoomRule(
            room_type="Patient Toilet",
            min_area=50,
            preferred_area=60,
            max_area=80,
            aspect_ratio_range=(0.8, 1.2),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"wheelchair_turning": 5.0, "grab_bar_space": 1.5},
            description="Accessible patient toilet room",
            code_reference="FGI 2.1-2.5.2.1 - ADA compliant"
        ),
        "Staff Restroom": RoomRule(
            room_type="Staff Restroom",
            min_area=40,
            preferred_area=50,
            max_area=70,
            aspect_ratio_range=(0.6, 1.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"fixture_clearance": 2.5},
            description="Staff toilet facility"
        ),
        "Staff Lounge": RoomRule(
            room_type="Staff Lounge",
            min_area=100,
            preferred_area=200,
            max_area=400,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.BACK_OF_HOUSE],
            clearances={"seating_area": 4.0, "kitchenette": 6.0},
            per_person_sf=25,
            description="Staff break and lounge area"
        ),
        "Storage": RoomRule(
            room_type="Storage",
            min_area=60,
            preferred_area=120,
            max_area=300,
            aspect_ratio_range=(0.6, 2.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE],
            clearances={"aisle": 3.0},
            description="General and medical supply storage"
        ),
    }
)


# =============================================================================
# RETAIL ROOM RULES
# =============================================================================

RETAIL_ROOM_RULES = BuildingRoomRules(
    building_type="retail",
    rules={
        "Sales Floor": RoomRule(
            room_type="Sales Floor",
            min_area=500,
            preferred_area=2000,
            max_area=None,  # Can be very large
            aspect_ratio_range=(1.0, 3.0),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"aisle_main": 8.0, "aisle_secondary": 5.0, "fixture_perimeter": 3.0},
            per_person_sf=30,  # Retail merchandise
            description="Main retail sales area",
            code_reference="IBC Table 1004.5 - 30-60 SF/person retail"
        ),
        "Entry Vestibule": RoomRule(
            room_type="Entry Vestibule",
            min_area=40,
            preferred_area=80,
            max_area=150,
            aspect_ratio_range=(1.0, 2.0),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"door_clearance": 5.0},
            description="Entry airlock/security vestibule"
        ),
        "Checkout": RoomRule(
            room_type="Checkout",
            min_area=100,
            preferred_area=200,
            max_area=500,
            aspect_ratio_range=(2.0, 4.0),  # Linear checkout lanes
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"lane_width": 4.0, "queue_depth": 8.0},
            description="Point of sale and checkout area"
        ),
        "Fitting Room": RoomRule(
            room_type="Fitting Room",
            min_area=30,
            preferred_area=40,
            max_area=60,
            aspect_ratio_range=(0.8, 1.2),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[],
            clearances={"mirror_distance": 3.0, "bench_clearance": 2.0},
            description="Individual fitting/dressing room"
        ),
        "Stockroom": RoomRule(
            room_type="Stockroom",
            min_area=200,
            preferred_area=500,
            max_area=None,
            aspect_ratio_range=(1.0, 2.5),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.BACK_OF_HOUSE, PlacementConstraint.LOADING_ACCESS],
            clearances={"aisle": 4.0, "receiving_area": 10.0},
            description="Back of house inventory storage"
        ),
        "Receiving": RoomRule(
            room_type="Receiving",
            min_area=150,
            preferred_area=300,
            max_area=600,
            aspect_ratio_range=(1.0, 2.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.BACK_OF_HOUSE, PlacementConstraint.LOADING_ACCESS],
            clearances={"dock_area": 12.0, "staging": 8.0},
            description="Loading dock and receiving area"
        ),
        "Office": RoomRule(
            room_type="Office",
            min_area=80,
            preferred_area=120,
            max_area=200,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.BACK_OF_HOUSE],
            clearances={"desk_clearance": 3.0},
            description="Store manager office"
        ),
        "Break Room": RoomRule(
            room_type="Break Room",
            min_area=80,
            preferred_area=150,
            max_area=300,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.BACK_OF_HOUSE, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"table_clearance": 3.0, "counter_clearance": 3.5},
            per_person_sf=25,
            description="Employee break and lunch area"
        ),
        "Restroom Public": RoomRule(
            room_type="Restroom Public",
            min_area=100,
            preferred_area=150,
            max_area=300,
            aspect_ratio_range=(0.6, 1.2),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"fixture_clearance": 2.5, "accessible_stall": 5.0},
            description="Customer restroom facility",
            code_reference="IBC 2902.1"
        ),
        "Restroom Staff": RoomRule(
            room_type="Restroom Staff",
            min_area=40,
            preferred_area=60,
            max_area=100,
            aspect_ratio_range=(0.6, 1.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.BACK_OF_HOUSE, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"fixture_clearance": 2.5},
            description="Employee restroom"
        ),
    }
)


# =============================================================================
# EDUCATIONAL ROOM RULES
# =============================================================================

EDUCATIONAL_ROOM_RULES = BuildingRoomRules(
    building_type="educational",
    rules={
        "Classroom": RoomRule(
            room_type="Classroom",
            min_area=700,
            preferred_area=900,
            max_area=1200,
            aspect_ratio_range=(1.2, 1.5),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER],
            clearances={"desk_rows": 3.0, "teaching_wall": 4.0, "aisle": 3.0},
            per_person_sf=28,  # Elementary
            description="Standard classroom for 25-30 students",
            code_reference="IBC Table 1004.5 - 20 SF/person educational"
        ),
        "Computer Lab": RoomRule(
            room_type="Computer Lab",
            min_area=800,
            preferred_area=1000,
            max_area=1500,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"workstation_depth": 4.0, "aisle": 4.0},
            per_person_sf=35,
            description="Computer workstation classroom"
        ),
        "Science Lab": RoomRule(
            room_type="Science Lab",
            min_area=1000,
            preferred_area=1400,
            max_area=1800,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"lab_bench_aisle": 4.0, "demo_area": 6.0, "emergency_shower": 3.0},
            per_person_sf=50,
            description="Science laboratory with demo area",
            code_reference="NFPA 45 - Laboratory safety"
        ),
        "Art Room": RoomRule(
            room_type="Art Room",
            min_area=1000,
            preferred_area=1200,
            max_area=1600,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"work_table_aisle": 4.0, "supply_storage": 6.0, "kiln_clearance": 4.0},
            per_person_sf=45,
            description="Art studio with natural lighting"
        ),
        "Music Room": RoomRule(
            room_type="Music Room",
            min_area=1200,
            preferred_area=1600,
            max_area=2500,
            aspect_ratio_range=(1.0, 1.4),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"instrument_storage": 8.0, "performance_area": 10.0},
            per_person_sf=35,
            description="Music classroom/rehearsal space"
        ),
        "Library/Media": RoomRule(
            room_type="Library/Media",
            min_area=2000,
            preferred_area=4000,
            max_area=8000,
            aspect_ratio_range=(1.0, 1.8),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER],
            clearances={"stack_aisle": 3.0, "reading_area": 6.0, "computer_area": 5.0},
            per_person_sf=25,
            description="Library and media center"
        ),
        "Gymnasium": RoomRule(
            room_type="Gymnasium",
            min_area=6000,
            preferred_area=8400,  # High school size
            max_area=15000,
            aspect_ratio_range=(1.3, 1.7),  # Basketball court ratio
            daylight=DaylightRequirement.PREFERRED,
            constraints=[],
            clearances={"court_perimeter": 10.0, "bleacher_depth": 8.0},
            per_person_sf=15,  # Assembly use
            description="Multi-purpose gymnasium",
            code_reference="IBC - Assembly occupancy A-4"
        ),
        "Cafeteria": RoomRule(
            room_type="Cafeteria",
            min_area=2000,
            preferred_area=4000,
            max_area=8000,
            aspect_ratio_range=(1.0, 1.8),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"serving_line": 6.0, "table_aisle": 5.0, "tray_return": 4.0},
            per_person_sf=15,
            description="Dining hall with kitchen access"
        ),
        "Kitchen": RoomRule(
            room_type="Kitchen",
            min_area=500,
            preferred_area=1000,
            max_area=2000,
            aspect_ratio_range=(1.0, 1.8),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.PLUMBING_CLUSTER, PlacementConstraint.LOADING_ACCESS],
            clearances={"cooking_aisle": 4.0, "prep_aisle": 4.0, "dishwash_area": 6.0},
            description="Commercial kitchen facility"
        ),
        "Main Office": RoomRule(
            room_type="Main Office",
            min_area=400,
            preferred_area=800,
            max_area=1500,
            aspect_ratio_range=(1.0, 2.0),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.NEAR_ENTRY],
            clearances={"counter_depth": 4.0, "waiting_area": 6.0},
            description="School administration office"
        ),
        "Principal Office": RoomRule(
            room_type="Principal Office",
            min_area=150,
            preferred_area=200,
            max_area=300,
            aspect_ratio_range=(1.0, 1.3),
            daylight=DaylightRequirement.REQUIRED,
            constraints=[PlacementConstraint.PERIMETER],
            clearances={"desk_clearance": 3.0, "meeting_area": 5.0},
            description="Principal private office"
        ),
        "Health Room": RoomRule(
            room_type="Health Room",
            min_area=200,
            preferred_area=300,
            max_area=500,
            aspect_ratio_range=(1.0, 1.5),
            daylight=DaylightRequirement.PREFERRED,
            constraints=[PlacementConstraint.NEAR_ENTRY, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"cot_space": 6.0, "exam_area": 4.0},
            description="Nurse/health office with cots"
        ),
        "Restroom Student": RoomRule(
            room_type="Restroom Student",
            min_area=150,
            preferred_area=250,
            max_area=400,
            aspect_ratio_range=(0.6, 1.2),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"fixture_clearance": 2.5, "accessible_stall": 5.0},
            description="Student restroom facilities",
            code_reference="IBC 2902.1"
        ),
        "Restroom Staff": RoomRule(
            room_type="Restroom Staff",
            min_area=50,
            preferred_area=70,
            max_area=100,
            aspect_ratio_range=(0.6, 1.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE, PlacementConstraint.PLUMBING_CLUSTER],
            clearances={"fixture_clearance": 2.5},
            description="Staff restroom"
        ),
        "Storage": RoomRule(
            room_type="Storage",
            min_area=80,
            preferred_area=150,
            max_area=400,
            aspect_ratio_range=(0.6, 2.0),
            daylight=DaylightRequirement.NOT_REQUIRED,
            constraints=[PlacementConstraint.CORE],
            clearances={"aisle": 3.0},
            description="General storage and custodial"
        ),
    }
)


# =============================================================================
# MASTER REGISTRY
# =============================================================================

ROOM_RULES_REGISTRY: Dict[str, BuildingRoomRules] = {
    "office": OFFICE_ROOM_RULES,
    "residential": RESIDENTIAL_ROOM_RULES,
    "healthcare": HEALTHCARE_ROOM_RULES,
    "retail": RETAIL_ROOM_RULES,
    "educational": EDUCATIONAL_ROOM_RULES,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_room_rules(building_type: str) -> Optional[BuildingRoomRules]:
    """Get room rules for a building type."""
    return ROOM_RULES_REGISTRY.get(building_type.lower())


def get_room_rule(building_type: str, room_type: str) -> Optional[RoomRule]:
    """Get specific room rule for building type and room."""
    rules = get_room_rules(building_type)
    if rules:
        return rules.get_rule(room_type)
    return None


def size_room_by_occupancy(building_type: str, room_type: str, occupant_count: int) -> Optional[Tuple[float, float]]:
    """
    Calculate room dimensions based on target occupancy.
    Returns (width, depth) tuple or None if no per_person_sf defined.
    """
    rule = get_room_rule(building_type, room_type)
    if not rule or not rule.per_person_sf:
        return None

    target_area = occupant_count * rule.per_person_sf
    # Clamp to min/max
    target_area = max(target_area, rule.min_area)
    if rule.max_area:
        target_area = min(target_area, rule.max_area)

    return rule.calculate_dimensions(target_area)


def get_daylight_rooms(building_type: str) -> Dict[str, List[str]]:
    """
    Get rooms grouped by daylight requirement for a building type.
    Returns dict with keys: "required", "preferred", "not_required"
    """
    rules = get_room_rules(building_type)
    if not rules:
        return {"required": [], "preferred": [], "not_required": []}

    result = {
        "required": [],
        "preferred": [],
        "not_required": []
    }

    for name, rule in rules.rules.items():
        if rule.daylight == DaylightRequirement.REQUIRED:
            result["required"].append(name)
        elif rule.daylight == DaylightRequirement.PREFERRED:
            result["preferred"].append(name)
        else:
            result["not_required"].append(name)

    return result


def get_placement_constraints(building_type: str, room_type: str) -> List[PlacementConstraint]:
    """Get placement constraints for a specific room."""
    rule = get_room_rule(building_type, room_type)
    return rule.constraints if rule else []


def validate_room_program(building_type: str, rooms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a room program against rules.

    Args:
        building_type: Type of building
        rooms: List of dicts with 'name', 'width', 'depth' keys

    Returns:
        Dict with 'valid' bool, 'issues' list, 'warnings' list
    """
    rules = get_room_rules(building_type)
    if not rules:
        return {"valid": False, "issues": [f"Unknown building type: {building_type}"], "warnings": []}

    issues = []
    warnings = []

    for room in rooms:
        name = room.get("name", "Unknown")
        width = room.get("width", 0)
        depth = room.get("depth", 0)

        rule = rules.get_rule(name)
        if not rule:
            warnings.append(f"No rules defined for room type: {name}")
            continue

        is_valid, room_issues = rule.validate_dimensions(width, depth)
        for issue in room_issues:
            issues.append(f"{name}: {issue}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }


def suggest_room_size(building_type: str, room_type: str,
                      target_occupancy: Optional[int] = None) -> Dict[str, Any]:
    """
    Suggest optimal room dimensions.

    Returns dict with:
        - width, depth: Suggested dimensions
        - area: Calculated area
        - aspect_ratio: Actual ratio
        - notes: Any relevant notes about the sizing
    """
    rule = get_room_rule(building_type, room_type)
    if not rule:
        return {"error": f"No rule found for {room_type} in {building_type}"}

    # Calculate based on occupancy if provided, otherwise use preferred
    if target_occupancy and rule.per_person_sf:
        width, depth = size_room_by_occupancy(building_type, room_type, target_occupancy)
        sizing_method = f"Sized for {target_occupancy} occupants @ {rule.per_person_sf} SF/person"
    else:
        width, depth = rule.calculate_dimensions()
        sizing_method = "Using preferred area"

    area = width * depth
    ratio = max(width, depth) / min(width, depth) if min(width, depth) > 0 else 1.0

    notes = [sizing_method]
    if rule.daylight == DaylightRequirement.REQUIRED:
        notes.append("Requires exterior wall with window")
    if PlacementConstraint.PERIMETER in rule.constraints:
        notes.append("Must be on building perimeter")
    if PlacementConstraint.PLUMBING_CLUSTER in rule.constraints:
        notes.append("Cluster with other wet rooms")
    if rule.code_reference:
        notes.append(f"Code: {rule.code_reference}")

    return {
        "width": width,
        "depth": depth,
        "area": round(area, 0),
        "aspect_ratio": round(ratio, 2),
        "min_area": rule.min_area,
        "max_area": rule.max_area,
        "daylight": rule.daylight.name.lower(),
        "notes": notes
    }


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("Room Intelligence Module - Test Output")
    print("=" * 60)

    # Test office building
    print("\nOFFICE BUILDING ROOM RULES:")
    print("-" * 40)

    for room_name in ["Reception", "Private Office", "Conference", "Restroom"]:
        suggestion = suggest_room_size("office", room_name)
        print(f"\n{room_name}:")
        print(f"  Suggested: {suggestion['width']}'W x {suggestion['depth']}'D")
        print(f"  Area: {suggestion['area']} SF (min: {suggestion['min_area']}, max: {suggestion['max_area']})")
        print(f"  Daylight: {suggestion['daylight']}")
        for note in suggestion['notes']:
            print(f"  - {note}")

    # Test conference room by occupancy
    print("\n" + "-" * 40)
    print("CONFERENCE ROOM SIZED BY OCCUPANCY:")
    for people in [6, 12, 20]:
        suggestion = suggest_room_size("office", "Conference", target_occupancy=people)
        print(f"  {people} people: {suggestion['width']}'W x {suggestion['depth']}'D = {suggestion['area']} SF")

    # Test residential
    print("\n" + "-" * 40)
    print("RESIDENTIAL KITCHEN RULES:")
    kitchen_rule = get_room_rule("residential", "Kitchen")
    if kitchen_rule:
        print(f"  Work triangle: {kitchen_rule.clearances.get('work_triangle_min', 'N/A')}' - {kitchen_rule.clearances.get('work_triangle_max', 'N/A')}'")
        print(f"  Min aisle: {kitchen_rule.clearances.get('aisle_min', 'N/A')}'")
        print(f"  Two-cook aisle: {kitchen_rule.clearances.get('aisle_two_cook', 'N/A')}'")

    # Test validation
    print("\n" + "-" * 40)
    print("VALIDATION TEST:")
    test_rooms = [
        {"name": "Private Office", "width": 8, "depth": 10},  # Valid
        {"name": "Restroom", "width": 4, "depth": 6},  # Too small
        {"name": "Conference", "width": 20, "depth": 10},  # Likely valid
    ]
    result = validate_room_program("office", test_rooms)
    print(f"  Valid: {result['valid']}")
    for issue in result['issues']:
        print(f"  Issue: {issue}")

    print("\n" + "=" * 60)
    print("Room Intelligence Module loaded successfully!")
