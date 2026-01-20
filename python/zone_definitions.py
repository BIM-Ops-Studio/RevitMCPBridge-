"""
Zone Definitions for Smart Floor Plan Generator

Zones represent functional areas that group related spaces together.
The zone system enforces privacy gradients and logical space organization.

Privacy Gradient:
    PUBLIC (0) -> SEMI_PUBLIC (1) -> PRIVATE (2) -> SERVICE (3)

Design Principle:
    - Never skip levels (no direct public-to-private transition)
    - Circulation connects zones at boundaries
    - Daylight priority decreases with privacy level
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import IntEnum


class ZoneType(IntEnum):
    """Zone types ordered by privacy level."""
    PUBLIC = 0       # Visitors can access freely
    SEMI_PUBLIC = 1  # Visitors with escort, staff areas
    PRIVATE = 2      # Staff/residents only
    SERVICE = 3      # Back of house, utilities


@dataclass
class Zone:
    """Definition of a spatial zone."""
    zone_type: ZoneType
    name: str
    description: str
    placement_priority: str  # "near_entry", "perimeter", "core", "back"
    daylight_requirement: str  # "required", "preferred", "not_required"
    typical_rooms: List[str] = field(default_factory=list)
    can_transition_to: List[ZoneType] = field(default_factory=list)  # Adjacent zones allowed


@dataclass
class BuildingZones:
    """Complete zone configuration for a building type."""
    building_type: str
    zones: Dict[ZoneType, Zone] = field(default_factory=dict)
    room_zone_map: Dict[str, ZoneType] = field(default_factory=dict)

    def get_zone(self, room_name: str) -> Optional[ZoneType]:
        """Get the zone type for a room name."""
        # Normalize name (remove numbers, lowercase)
        import re
        normalized = re.sub(r'\s*\d+$', '', room_name.lower().strip())

        # Direct lookup
        if normalized in self.room_zone_map:
            return self.room_zone_map[normalized]

        # Partial match
        for key, zone in self.room_zone_map.items():
            if key in normalized or normalized in key:
                return zone

        return None

    def get_rooms_in_zone(self, zone_type: ZoneType) -> List[str]:
        """Get all room types that belong to a zone."""
        return [room for room, zone in self.room_zone_map.items()
                if zone == zone_type]

    def can_be_adjacent(self, zone_a: ZoneType, zone_b: ZoneType) -> bool:
        """Check if two zones can be adjacent (privacy gradient)."""
        if zone_a not in self.zones or zone_b not in self.zones:
            return True  # Unknown zones default to allowed

        return zone_b in self.zones[zone_a].can_transition_to


# =============================================================================
# OFFICE ZONES
# =============================================================================

OFFICE_ZONES = BuildingZones(
    building_type="office",
    zones={
        ZoneType.PUBLIC: Zone(
            zone_type=ZoneType.PUBLIC,
            name="Public Zone",
            description="Visitor-accessible areas near entry",
            placement_priority="near_entry",
            daylight_requirement="preferred",
            typical_rooms=["Entry", "Reception", "Waiting", "Lobby", "Conference"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC]
        ),
        ZoneType.SEMI_PUBLIC: Zone(
            zone_type=ZoneType.SEMI_PUBLIC,
            name="Semi-Public Zone",
            description="Staff work areas with occasional visitors",
            placement_priority="middle",
            daylight_requirement="preferred",
            typical_rooms=["Open Office", "Break Room", "Training Room", "Collaboration"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
        ZoneType.PRIVATE: Zone(
            zone_type=ZoneType.PRIVATE,
            name="Private Zone",
            description="Staff-only private offices",
            placement_priority="perimeter",
            daylight_requirement="required",
            typical_rooms=["Private Office", "Executive Office", "Focus Room"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
        ZoneType.SERVICE: Zone(
            zone_type=ZoneType.SERVICE,
            name="Service Zone",
            description="Support and utility spaces",
            placement_priority="core",
            daylight_requirement="not_required",
            typical_rooms=["Restroom", "Storage", "Mechanical", "IT Room", "Server Room", "Copy Room"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
    },
    room_zone_map={
        # Public
        "entry": ZoneType.PUBLIC,
        "reception": ZoneType.PUBLIC,
        "waiting": ZoneType.PUBLIC,
        "lobby": ZoneType.PUBLIC,
        "conference": ZoneType.PUBLIC,
        "conference room": ZoneType.PUBLIC,
        "conference small": ZoneType.PUBLIC,
        "boardroom": ZoneType.PUBLIC,

        # Semi-Public
        "open office": ZoneType.SEMI_PUBLIC,
        "break room": ZoneType.SEMI_PUBLIC,
        "break": ZoneType.SEMI_PUBLIC,
        "kitchen": ZoneType.SEMI_PUBLIC,
        "kitchenette": ZoneType.SEMI_PUBLIC,
        "training": ZoneType.SEMI_PUBLIC,
        "collaboration": ZoneType.SEMI_PUBLIC,
        "huddle": ZoneType.SEMI_PUBLIC,

        # Private
        "private office": ZoneType.PRIVATE,
        "executive office": ZoneType.PRIVATE,
        "focus room": ZoneType.PRIVATE,
        "phone room": ZoneType.PRIVATE,
        "office": ZoneType.PRIVATE,

        # Service
        "restroom": ZoneType.SERVICE,
        "storage": ZoneType.SERVICE,
        "mechanical": ZoneType.SERVICE,
        "it room": ZoneType.SERVICE,
        "server room": ZoneType.SERVICE,
        "copy room": ZoneType.SERVICE,
        "mail room": ZoneType.SERVICE,
        "janitor": ZoneType.SERVICE,
    }
)


# =============================================================================
# RESIDENTIAL ZONES
# =============================================================================

RESIDENTIAL_ZONES = BuildingZones(
    building_type="residential",
    zones={
        ZoneType.PUBLIC: Zone(
            zone_type=ZoneType.PUBLIC,
            name="Public Zone",
            description="Guest-accessible living areas",
            placement_priority="near_entry",
            daylight_requirement="required",
            typical_rooms=["Entry", "Foyer", "Living", "Dining", "Family Room", "Powder Room"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC]
        ),
        ZoneType.SEMI_PUBLIC: Zone(
            zone_type=ZoneType.SEMI_PUBLIC,
            name="Semi-Public Zone",
            description="Family activity areas",
            placement_priority="middle",
            daylight_requirement="preferred",
            typical_rooms=["Kitchen", "Breakfast", "Office", "Playroom"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
        ZoneType.PRIVATE: Zone(
            zone_type=ZoneType.PRIVATE,
            name="Private Zone",
            description="Bedrooms and private spaces",
            placement_priority="back",
            daylight_requirement="required",
            typical_rooms=["Master Bedroom", "Bedroom", "Master Bath", "Bathroom", "Walk-in Closet"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
        ZoneType.SERVICE: Zone(
            zone_type=ZoneType.SERVICE,
            name="Service Zone",
            description="Utility and storage spaces",
            placement_priority="core",
            daylight_requirement="not_required",
            typical_rooms=["Laundry", "Pantry", "Garage", "Storage", "Mechanical", "Mudroom"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
    },
    room_zone_map={
        # Public
        "entry": ZoneType.PUBLIC,
        "foyer": ZoneType.PUBLIC,
        "living": ZoneType.PUBLIC,
        "living room": ZoneType.PUBLIC,
        "dining": ZoneType.PUBLIC,
        "dining room": ZoneType.PUBLIC,
        "family room": ZoneType.PUBLIC,
        "great room": ZoneType.PUBLIC,
        "powder room": ZoneType.PUBLIC,
        "half bath": ZoneType.PUBLIC,

        # Semi-Public
        "kitchen": ZoneType.SEMI_PUBLIC,
        "breakfast": ZoneType.SEMI_PUBLIC,
        "breakfast nook": ZoneType.SEMI_PUBLIC,
        "office": ZoneType.SEMI_PUBLIC,
        "study": ZoneType.SEMI_PUBLIC,
        "den": ZoneType.SEMI_PUBLIC,
        "playroom": ZoneType.SEMI_PUBLIC,
        "sunroom": ZoneType.SEMI_PUBLIC,

        # Private
        "master bedroom": ZoneType.PRIVATE,
        "bedroom": ZoneType.PRIVATE,
        "master bath": ZoneType.PRIVATE,
        "master bathroom": ZoneType.PRIVATE,
        "bathroom": ZoneType.PRIVATE,
        "walk-in closet": ZoneType.PRIVATE,
        "closet": ZoneType.PRIVATE,
        "nursery": ZoneType.PRIVATE,

        # Service
        "laundry": ZoneType.SERVICE,
        "pantry": ZoneType.SERVICE,
        "garage": ZoneType.SERVICE,
        "storage": ZoneType.SERVICE,
        "mechanical": ZoneType.SERVICE,
        "mudroom": ZoneType.SERVICE,
        "utility": ZoneType.SERVICE,
    }
)


# =============================================================================
# HEALTHCARE ZONES
# =============================================================================

HEALTHCARE_ZONES = BuildingZones(
    building_type="healthcare",
    zones={
        ZoneType.PUBLIC: Zone(
            zone_type=ZoneType.PUBLIC,
            name="Public Zone",
            description="Patient and visitor waiting areas",
            placement_priority="near_entry",
            daylight_requirement="preferred",
            typical_rooms=["Entry", "Reception", "Waiting", "Restroom"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC]
        ),
        ZoneType.SEMI_PUBLIC: Zone(
            zone_type=ZoneType.SEMI_PUBLIC,
            name="Clinical Zone",
            description="Patient care areas",
            placement_priority="middle",
            daylight_requirement="preferred",
            typical_rooms=["Exam Room", "Procedure Room", "Consultation", "Nurse Station"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
        ZoneType.PRIVATE: Zone(
            zone_type=ZoneType.PRIVATE,
            name="Staff Zone",
            description="Provider offices and staff areas",
            placement_priority="perimeter",
            daylight_requirement="required",
            typical_rooms=["Doctor Office", "Staff Lounge", "Medical Records"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
        ZoneType.SERVICE: Zone(
            zone_type=ZoneType.SERVICE,
            name="Support Zone",
            description="Clinical support and utilities",
            placement_priority="core",
            daylight_requirement="not_required",
            typical_rooms=["Lab", "Clean Utility", "Soiled Utility", "Supply Room", "Mechanical"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
    },
    room_zone_map={
        # Public
        "entry": ZoneType.PUBLIC,
        "reception": ZoneType.PUBLIC,
        "waiting": ZoneType.PUBLIC,
        "waiting room": ZoneType.PUBLIC,
        "lobby": ZoneType.PUBLIC,
        "restroom": ZoneType.PUBLIC,

        # Clinical (Semi-Public)
        "exam room": ZoneType.SEMI_PUBLIC,
        "exam": ZoneType.SEMI_PUBLIC,
        "procedure room": ZoneType.SEMI_PUBLIC,
        "procedure": ZoneType.SEMI_PUBLIC,
        "consultation": ZoneType.SEMI_PUBLIC,
        "nurse station": ZoneType.SEMI_PUBLIC,
        "recovery": ZoneType.SEMI_PUBLIC,

        # Staff (Private)
        "doctor office": ZoneType.PRIVATE,
        "physician office": ZoneType.PRIVATE,
        "staff lounge": ZoneType.PRIVATE,
        "break room": ZoneType.PRIVATE,
        "medical records": ZoneType.PRIVATE,

        # Support (Service)
        "lab": ZoneType.SERVICE,
        "laboratory": ZoneType.SERVICE,
        "clean utility": ZoneType.SERVICE,
        "soiled utility": ZoneType.SERVICE,
        "supply room": ZoneType.SERVICE,
        "supply": ZoneType.SERVICE,
        "storage": ZoneType.SERVICE,
        "mechanical": ZoneType.SERVICE,
    }
)


# =============================================================================
# RETAIL ZONES
# =============================================================================

RETAIL_ZONES = BuildingZones(
    building_type="retail",
    zones={
        ZoneType.PUBLIC: Zone(
            zone_type=ZoneType.PUBLIC,
            name="Sales Zone",
            description="Customer-accessible retail floor",
            placement_priority="near_entry",
            daylight_requirement="preferred",
            typical_rooms=["Entry", "Sales Floor", "Fitting Room", "Checkout"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC]
        ),
        ZoneType.SEMI_PUBLIC: Zone(
            zone_type=ZoneType.SEMI_PUBLIC,
            name="Support Zone",
            description="Customer service areas",
            placement_priority="middle",
            daylight_requirement="preferred",
            typical_rooms=["Customer Service", "Restroom"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC, ZoneType.SERVICE]
        ),
        ZoneType.PRIVATE: Zone(
            zone_type=ZoneType.PRIVATE,
            name="Admin Zone",
            description="Staff offices",
            placement_priority="back",
            daylight_requirement="preferred",
            typical_rooms=["Office", "Manager Office"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
        ZoneType.SERVICE: Zone(
            zone_type=ZoneType.SERVICE,
            name="Back of House",
            description="Stock and receiving",
            placement_priority="back",
            daylight_requirement="not_required",
            typical_rooms=["Stockroom", "Receiving", "Loading Dock", "Break Room", "Storage"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
    },
    room_zone_map={
        # Sales
        "entry": ZoneType.PUBLIC,
        "sales floor": ZoneType.PUBLIC,
        "sales": ZoneType.PUBLIC,
        "fitting room": ZoneType.PUBLIC,
        "checkout": ZoneType.PUBLIC,
        "cashier": ZoneType.PUBLIC,

        # Support
        "customer service": ZoneType.SEMI_PUBLIC,
        "restroom": ZoneType.SEMI_PUBLIC,

        # Admin
        "office": ZoneType.PRIVATE,
        "manager office": ZoneType.PRIVATE,

        # Back of house
        "stockroom": ZoneType.SERVICE,
        "receiving": ZoneType.SERVICE,
        "loading dock": ZoneType.SERVICE,
        "break room": ZoneType.SERVICE,
        "storage": ZoneType.SERVICE,
    }
)


# =============================================================================
# EDUCATIONAL ZONES
# =============================================================================

EDUCATIONAL_ZONES = BuildingZones(
    building_type="educational",
    zones={
        ZoneType.PUBLIC: Zone(
            zone_type=ZoneType.PUBLIC,
            name="Entry Zone",
            description="Main entry and administration",
            placement_priority="near_entry",
            daylight_requirement="preferred",
            typical_rooms=["Entry", "Reception", "Waiting", "Principal Office", "Admin"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC]
        ),
        ZoneType.SEMI_PUBLIC: Zone(
            zone_type=ZoneType.SEMI_PUBLIC,
            name="Learning Zone",
            description="Classrooms and learning spaces",
            placement_priority="perimeter",
            daylight_requirement="required",
            typical_rooms=["Classroom", "Library", "Computer Lab", "Art Room", "Music Room"],
            can_transition_to=[ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC, ZoneType.SERVICE]
        ),
        ZoneType.PRIVATE: Zone(
            zone_type=ZoneType.PRIVATE,
            name="Staff Zone",
            description="Faculty offices and workrooms",
            placement_priority="perimeter",
            daylight_requirement="preferred",
            typical_rooms=["Teacher Office", "Workroom", "Conference"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
        ZoneType.SERVICE: Zone(
            zone_type=ZoneType.SERVICE,
            name="Support Zone",
            description="Common areas and support",
            placement_priority="core",
            daylight_requirement="not_required",
            typical_rooms=["Cafeteria", "Gymnasium", "Locker Room", "Kitchen", "Restroom", "Storage"],
            can_transition_to=[ZoneType.SEMI_PUBLIC, ZoneType.PRIVATE, ZoneType.SERVICE]
        ),
    },
    room_zone_map={
        # Entry
        "entry": ZoneType.PUBLIC,
        "reception": ZoneType.PUBLIC,
        "waiting": ZoneType.PUBLIC,
        "principal office": ZoneType.PUBLIC,
        "admin": ZoneType.PUBLIC,
        "office": ZoneType.PUBLIC,

        # Learning
        "classroom": ZoneType.SEMI_PUBLIC,
        "library": ZoneType.SEMI_PUBLIC,
        "media center": ZoneType.SEMI_PUBLIC,
        "computer lab": ZoneType.SEMI_PUBLIC,
        "art room": ZoneType.SEMI_PUBLIC,
        "music room": ZoneType.SEMI_PUBLIC,
        "science lab": ZoneType.SEMI_PUBLIC,

        # Staff
        "teacher office": ZoneType.PRIVATE,
        "workroom": ZoneType.PRIVATE,
        "conference": ZoneType.PRIVATE,
        "planning room": ZoneType.PRIVATE,

        # Support
        "cafeteria": ZoneType.SERVICE,
        "gymnasium": ZoneType.SERVICE,
        "gym": ZoneType.SERVICE,
        "locker room": ZoneType.SERVICE,
        "kitchen": ZoneType.SERVICE,
        "restroom": ZoneType.SERVICE,
        "storage": ZoneType.SERVICE,
        "mechanical": ZoneType.SERVICE,
    }
)


# =============================================================================
# ZONE REGISTRY
# =============================================================================

ZONE_REGISTRY: Dict[str, BuildingZones] = {
    "office": OFFICE_ZONES,
    "residential": RESIDENTIAL_ZONES,
    "healthcare": HEALTHCARE_ZONES,
    "retail": RETAIL_ZONES,
    "educational": EDUCATIONAL_ZONES,
}


def get_zones(building_type: str) -> BuildingZones:
    """Get zone configuration for a building type."""
    bt = building_type.lower()
    if bt not in ZONE_REGISTRY:
        available = list(ZONE_REGISTRY.keys())
        raise ValueError(f"Unknown building type: {building_type}. Available: {available}")
    return ZONE_REGISTRY[bt]


def get_room_zone(building_type: str, room_name: str) -> Optional[ZoneType]:
    """Get the zone for a specific room in a building type."""
    zones = get_zones(building_type)
    return zones.get_zone(room_name)


def get_placement_priority(building_type: str, room_name: str) -> str:
    """Get placement priority for a room based on its zone."""
    zones = get_zones(building_type)
    zone_type = zones.get_zone(room_name)

    if zone_type is None:
        return "middle"  # Default

    zone = zones.zones.get(zone_type)
    return zone.placement_priority if zone else "middle"


def get_daylight_requirement(building_type: str, room_name: str) -> str:
    """Get daylight requirement for a room based on its zone."""
    zones = get_zones(building_type)
    zone_type = zones.get_zone(room_name)

    if zone_type is None:
        return "preferred"  # Default

    zone = zones.zones.get(zone_type)
    return zone.daylight_requirement if zone else "preferred"


def validate_zone_transitions(
    building_type: str,
    room_placements: List[Dict],
    adjacency_threshold: float = 15.0
) -> Dict:
    """
    Validate that zone transitions in a floor plan respect privacy gradients.

    Args:
        building_type: Type of building
        room_placements: List of room dicts with 'name', 'x', 'y'
        adjacency_threshold: Distance to consider rooms adjacent

    Returns:
        Dict with validation results
    """
    zones = get_zones(building_type)
    violations = []
    valid_transitions = 0

    # Check each pair of rooms that are adjacent
    for i, room_a in enumerate(room_placements):
        for room_b in room_placements[i + 1:]:
            # Calculate distance
            dist = ((room_a['x'] - room_b['x'])**2 +
                   (room_a['y'] - room_b['y'])**2) ** 0.5

            if dist > adjacency_threshold:
                continue  # Not adjacent

            zone_a = zones.get_zone(room_a['name'])
            zone_b = zones.get_zone(room_b['name'])

            if zone_a is None or zone_b is None:
                continue  # Unknown zones

            if zones.can_be_adjacent(zone_a, zone_b):
                valid_transitions += 1
            else:
                violations.append({
                    "room_a": room_a['name'],
                    "zone_a": zone_a.name,
                    "room_b": room_b['name'],
                    "zone_b": zone_b.name,
                    "distance": round(dist, 1),
                    "issue": f"Direct {zone_a.name}-to-{zone_b.name} transition violates privacy gradient"
                })

    total = valid_transitions + len(violations)
    score = (valid_transitions / total * 100) if total > 0 else 100

    return {
        "zone_transition_score": round(score, 1),
        "valid_transitions": valid_transitions,
        "violations": len(violations),
        "violation_details": violations
    }


def group_rooms_by_zone(
    building_type: str,
    rooms: List[str]
) -> Dict[ZoneType, List[str]]:
    """
    Group a list of rooms by their zone type.

    Args:
        building_type: Type of building
        rooms: List of room names

    Returns:
        Dict mapping ZoneType to list of room names
    """
    zones = get_zones(building_type)
    grouped = {zone_type: [] for zone_type in ZoneType}

    for room in rooms:
        zone = zones.get_zone(room)
        if zone is not None:
            grouped[zone].append(room)
        else:
            # Unknown rooms go to SEMI_PUBLIC as default
            grouped[ZoneType.SEMI_PUBLIC].append(room)

    return grouped


if __name__ == "__main__":
    # Test the zone system
    print("Testing Zone Definitions System")
    print("=" * 50)

    # Test office zones
    office = get_zones("office")
    print(f"\nOffice building zones:")
    for zone_type, zone in office.zones.items():
        print(f"  {zone.name}: {len(office.get_rooms_in_zone(zone_type))} room types")

    # Test room zone lookup
    print(f"\nReception zone: {office.get_zone('Reception')}")
    print(f"Private Office zone: {office.get_zone('Private Office 1')}")
    print(f"Restroom zone: {office.get_zone('Restroom')}")

    # Test zone transitions
    print(f"\nPUBLIC can be adjacent to PRIVATE: {office.can_be_adjacent(ZoneType.PUBLIC, ZoneType.PRIVATE)}")
    print(f"PUBLIC can be adjacent to SEMI_PUBLIC: {office.can_be_adjacent(ZoneType.PUBLIC, ZoneType.SEMI_PUBLIC)}")

    # Test room grouping
    rooms = ["Reception", "Conference Room", "Private Office 1", "Open Office", "Break Room", "Restroom", "Storage"]
    grouped = group_rooms_by_zone("office", rooms)
    print(f"\nRooms grouped by zone:")
    for zone_type, room_list in grouped.items():
        if room_list:
            print(f"  {zone_type.name}: {room_list}")

    # Test placement priorities
    print(f"\nPlacement priorities:")
    for room in rooms:
        priority = get_placement_priority("office", room)
        daylight = get_daylight_requirement("office", room)
        print(f"  {room}: {priority}, daylight={daylight}")
