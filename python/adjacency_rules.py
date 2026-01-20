"""
Adjacency Rules for Smart Floor Plan Generator

Defines spatial relationships between rooms for intelligent placement.
These rules encode architectural best practices for different building types.

Relationship Types:
    MUST_CONNECT (3):    Direct door connection required
    SHOULD_ADJACENT (2): Should share a wall
    PREFER_NEAR (1):     Same zone, short walking distance
    NEUTRAL (0):         No strong preference
    SHOULD_SEPARATE (-1): Different zones, some distance preferred
    MUST_SEPARATE (-2):  Noise/privacy isolation required
"""

from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, field


# Relationship strength constants
MUST_CONNECT = 3
SHOULD_ADJACENT = 2
PREFER_NEAR = 1
NEUTRAL = 0
SHOULD_SEPARATE = -1
MUST_SEPARATE = -2


@dataclass
class AdjacencyRule:
    """A single adjacency rule between two room types."""
    room_a: str
    room_b: str
    strength: int
    reason: str = ""
    bidirectional: bool = True


@dataclass
class BuildingTypeAdjacencies:
    """Complete adjacency rules for a building type."""
    building_type: str
    rules: List[AdjacencyRule] = field(default_factory=list)

    def get_relationship(self, room_a: str, room_b: str) -> int:
        """Get the relationship strength between two room types."""
        # Normalize room names for matching
        a_norm = self._normalize_name(room_a)
        b_norm = self._normalize_name(room_b)

        for rule in self.rules:
            rule_a = self._normalize_name(rule.room_a)
            rule_b = self._normalize_name(rule.room_b)

            if (a_norm == rule_a and b_norm == rule_b):
                return rule.strength
            if rule.bidirectional and (a_norm == rule_b and b_norm == rule_a):
                return rule.strength

        return NEUTRAL

    def get_must_connect(self, room_type: str) -> List[str]:
        """Get all room types that MUST connect to given room."""
        results = []
        norm = self._normalize_name(room_type)

        for rule in self.rules:
            if rule.strength == MUST_CONNECT:
                if self._normalize_name(rule.room_a) == norm:
                    results.append(rule.room_b)
                elif rule.bidirectional and self._normalize_name(rule.room_b) == norm:
                    results.append(rule.room_a)

        return results

    def get_must_separate(self, room_type: str) -> List[str]:
        """Get all room types that MUST be separated from given room."""
        results = []
        norm = self._normalize_name(room_type)

        for rule in self.rules:
            if rule.strength == MUST_SEPARATE:
                if self._normalize_name(rule.room_a) == norm:
                    results.append(rule.room_b)
                elif rule.bidirectional and self._normalize_name(rule.room_b) == norm:
                    results.append(rule.room_a)

        return results

    def _normalize_name(self, name: str) -> str:
        """Normalize room name for matching (lowercase, no numbers)."""
        import re
        # Remove trailing numbers and spaces, lowercase
        normalized = re.sub(r'\s*\d+$', '', name.lower().strip())
        return normalized


# =============================================================================
# OFFICE BUILDING ADJACENCIES
# =============================================================================

OFFICE_ADJACENCIES = BuildingTypeAdjacencies(
    building_type="office",
    rules=[
        # Entry sequence
        AdjacencyRule("Entry", "Reception", MUST_CONNECT,
                     "Visitors must encounter reception immediately upon entry"),
        AdjacencyRule("Reception", "Waiting", MUST_CONNECT,
                     "Waiting area directly visible and accessible from reception"),
        AdjacencyRule("Reception", "Conference", SHOULD_ADJACENT,
                     "Visitors taken directly to conference without traversing office"),

        # Public zone relationships
        AdjacencyRule("Waiting", "Conference", PREFER_NEAR,
                     "Visitors move from waiting to meeting easily"),
        AdjacencyRule("Conference", "Conference", PREFER_NEAR,
                     "Conference rooms clustered for shared AV/catering support"),

        # Work area relationships
        AdjacencyRule("Private Office", "Conference", SHOULD_ADJACENT,
                     "Executives need quick access to meeting rooms"),
        AdjacencyRule("Private Office", "Open Office", PREFER_NEAR,
                     "Managers accessible to team"),
        AdjacencyRule("Private Office", "Private Office", PREFER_NEAR,
                     "Executive suite grouping"),
        AdjacencyRule("Open Office", "Break Room", PREFER_NEAR,
                     "Staff convenience for breaks"),

        # Support clustering
        AdjacencyRule("Break Room", "Restroom", SHOULD_ADJACENT,
                     "Convenience and plumbing efficiency"),
        AdjacencyRule("Restroom", "Restroom", SHOULD_ADJACENT,
                     "Back-to-back plumbing walls"),
        AdjacencyRule("Storage", "Copy Room", SHOULD_ADJACENT,
                     "Supply storage near equipment"),
        AdjacencyRule("IT Room", "Server Room", MUST_CONNECT,
                     "IT infrastructure clustering"),

        # Separation requirements
        AdjacencyRule("Break Room", "Private Office", SHOULD_SEPARATE,
                     "Noise from break activities"),
        AdjacencyRule("Break Room", "Conference", SHOULD_SEPARATE,
                     "Meeting disruption from casual conversations"),
        AdjacencyRule("Restroom", "Conference", SHOULD_SEPARATE,
                     "Privacy and odor concerns"),
        AdjacencyRule("Restroom", "Reception", SHOULD_SEPARATE,
                     "Not visible from entry/waiting"),
        AdjacencyRule("Storage", "Reception", SHOULD_SEPARATE,
                     "Back-of-house not visible to visitors"),
        AdjacencyRule("Mechanical", "Reception", MUST_SEPARATE,
                     "Noise and aesthetics"),
        AdjacencyRule("Mechanical", "Conference", MUST_SEPARATE,
                     "Noise during meetings"),
        AdjacencyRule("Server Room", "Break Room", MUST_SEPARATE,
                     "Temperature and humidity control"),
    ]
)


# =============================================================================
# RESIDENTIAL ADJACENCIES
# =============================================================================

RESIDENTIAL_ADJACENCIES = BuildingTypeAdjacencies(
    building_type="residential",
    rules=[
        # Entry sequence
        AdjacencyRule("Entry", "Living", MUST_CONNECT,
                     "Entry opens to main living space"),
        AdjacencyRule("Entry", "Coat Closet", SHOULD_ADJACENT,
                     "Immediate storage for outerwear"),
        AdjacencyRule("Entry", "Powder Room", PREFER_NEAR,
                     "Guest bathroom accessible without entering private areas"),

        # Living area relationships
        AdjacencyRule("Living", "Dining", SHOULD_ADJACENT,
                     "Open plan entertaining flow"),
        AdjacencyRule("Dining", "Kitchen", MUST_CONNECT,
                     "Serving efficiency"),
        AdjacencyRule("Kitchen", "Living", SHOULD_ADJACENT,
                     "Open plan, cook can interact with family"),
        AdjacencyRule("Kitchen", "Pantry", MUST_CONNECT,
                     "Storage adjacent to cooking"),
        AdjacencyRule("Kitchen", "Garage", PREFER_NEAR,
                     "Grocery unloading convenience"),

        # Wet room clustering (plumbing efficiency)
        AdjacencyRule("Kitchen", "Laundry", SHOULD_ADJACENT,
                     "Shared plumbing wall"),
        AdjacencyRule("Bathroom", "Bathroom", SHOULD_ADJACENT,
                     "Back-to-back plumbing walls"),
        AdjacencyRule("Bathroom", "Laundry", SHOULD_ADJACENT,
                     "Shared drain lines"),
        AdjacencyRule("Kitchen", "Bathroom", PREFER_NEAR,
                     "Plumbing efficiency if stacked"),

        # Bedroom relationships
        AdjacencyRule("Master Bedroom", "Master Bath", MUST_CONNECT,
                     "Private bathroom access"),
        AdjacencyRule("Master Bedroom", "Walk-in Closet", MUST_CONNECT,
                     "Dressing area"),
        AdjacencyRule("Bedroom", "Bathroom", SHOULD_ADJACENT,
                     "Bathroom accessible from bedrooms"),
        AdjacencyRule("Bedroom", "Bedroom", PREFER_NEAR,
                     "Kids' rooms near each other"),

        # Home office (modern requirement)
        AdjacencyRule("Office", "Entry", PREFER_NEAR,
                     "Work-from-home accessible without disturbing house"),

        # Privacy separations
        AdjacencyRule("Master Bedroom", "Living", SHOULD_SEPARATE,
                     "Noise from entertainment"),
        AdjacencyRule("Bedroom", "Kitchen", SHOULD_SEPARATE,
                     "Cooking noise and smells"),
        AdjacencyRule("Bedroom", "Living", SHOULD_SEPARATE,
                     "Entertainment noise"),
        AdjacencyRule("Master Bedroom", "Bedroom", PREFER_NEAR,
                     "Parents near children, but some separation"),

        # Garage relationships
        AdjacencyRule("Garage", "Entry", SHOULD_SEPARATE,
                     "Service entry separate from main entry"),
        AdjacencyRule("Garage", "Kitchen", SHOULD_ADJACENT,
                     "Grocery loading"),
        AdjacencyRule("Garage", "Laundry", PREFER_NEAR,
                     "Mudroom function"),
    ]
)


# =============================================================================
# HEALTHCARE ADJACENCIES
# =============================================================================

HEALTHCARE_ADJACENCIES = BuildingTypeAdjacencies(
    building_type="healthcare",
    rules=[
        # Entry and public areas
        AdjacencyRule("Entry", "Reception", MUST_CONNECT,
                     "Check-in immediately upon arrival"),
        AdjacencyRule("Reception", "Waiting", MUST_CONNECT,
                     "Patients wait after check-in"),
        AdjacencyRule("Waiting", "Restroom", SHOULD_ADJACENT,
                     "Patient convenience during wait"),

        # Clinical workflow
        AdjacencyRule("Waiting", "Exam Room", PREFER_NEAR,
                     "Short walk to be called back"),
        AdjacencyRule("Exam Room", "Nurse Station", SHOULD_ADJACENT,
                     "Staff efficiency and patient monitoring"),
        AdjacencyRule("Exam Room", "Exam Room", SHOULD_ADJACENT,
                     "Clustered for efficiency"),
        AdjacencyRule("Nurse Station", "Supply Room", MUST_CONNECT,
                     "Immediate access to medical supplies"),
        AdjacencyRule("Nurse Station", "Clean Utility", SHOULD_ADJACENT,
                     "Clean supply access"),
        AdjacencyRule("Nurse Station", "Soiled Utility", SHOULD_ADJACENT,
                     "Waste processing"),

        # Procedure areas
        AdjacencyRule("Procedure Room", "Nurse Station", SHOULD_ADJACENT,
                     "Staff support during procedures"),
        AdjacencyRule("Procedure Room", "Recovery", SHOULD_ADJACENT,
                     "Patient flow after procedure"),
        AdjacencyRule("Lab", "Exam Room", PREFER_NEAR,
                     "Specimen processing"),

        # Support areas
        AdjacencyRule("Clean Utility", "Soiled Utility", MUST_SEPARATE,
                     "Infection control"),
        AdjacencyRule("Staff Lounge", "Nurse Station", PREFER_NEAR,
                     "Staff breaks"),
        AdjacencyRule("Staff Lounge", "Waiting", MUST_SEPARATE,
                     "Staff privacy"),

        # Provider areas
        AdjacencyRule("Doctor Office", "Exam Room", SHOULD_ADJACENT,
                     "Provider efficiency"),
        AdjacencyRule("Doctor Office", "Doctor Office", PREFER_NEAR,
                     "Physician suite"),

        # Separations
        AdjacencyRule("Lab", "Waiting", SHOULD_SEPARATE,
                     "Clinical areas separate from public"),
        AdjacencyRule("Soiled Utility", "Waiting", MUST_SEPARATE,
                     "Out of patient view"),
        AdjacencyRule("Mechanical", "Exam Room", MUST_SEPARATE,
                     "Noise during exams"),
    ]
)


# =============================================================================
# RETAIL ADJACENCIES
# =============================================================================

RETAIL_ADJACENCIES = BuildingTypeAdjacencies(
    building_type="retail",
    rules=[
        # Customer flow
        AdjacencyRule("Entry", "Sales Floor", MUST_CONNECT,
                     "Immediate product exposure"),
        AdjacencyRule("Sales Floor", "Checkout", SHOULD_ADJACENT,
                     "Natural flow to purchase"),
        AdjacencyRule("Checkout", "Exit", SHOULD_ADJACENT,
                     "Clear departure path"),

        # Customer amenities
        AdjacencyRule("Sales Floor", "Fitting Room", SHOULD_ADJACENT,
                     "Try before buy"),
        AdjacencyRule("Sales Floor", "Restroom", PREFER_NEAR,
                     "Customer convenience"),

        # Back of house
        AdjacencyRule("Sales Floor", "Stockroom", MUST_CONNECT,
                     "Restocking efficiency"),
        AdjacencyRule("Stockroom", "Receiving", MUST_CONNECT,
                     "Delivery processing"),
        AdjacencyRule("Receiving", "Loading Dock", MUST_CONNECT,
                     "Truck access"),
        AdjacencyRule("Office", "Stockroom", SHOULD_ADJACENT,
                     "Manager oversight"),

        # Separations
        AdjacencyRule("Stockroom", "Entry", MUST_SEPARATE,
                     "Back of house hidden"),
        AdjacencyRule("Office", "Sales Floor", SHOULD_SEPARATE,
                     "Admin separate from retail"),
        AdjacencyRule("Break Room", "Sales Floor", SHOULD_SEPARATE,
                     "Staff areas private"),
    ]
)


# =============================================================================
# EDUCATIONAL ADJACENCIES
# =============================================================================

EDUCATIONAL_ADJACENCIES = BuildingTypeAdjacencies(
    building_type="educational",
    rules=[
        # Entry and administration
        AdjacencyRule("Entry", "Reception", MUST_CONNECT,
                     "Visitor control"),
        AdjacencyRule("Reception", "Principal Office", SHOULD_ADJACENT,
                     "Administration access"),
        AdjacencyRule("Reception", "Waiting", SHOULD_ADJACENT,
                     "Visitor seating"),

        # Classroom relationships
        AdjacencyRule("Classroom", "Classroom", SHOULD_ADJACENT,
                     "Grade-level clustering"),
        AdjacencyRule("Classroom", "Restroom", PREFER_NEAR,
                     "Student convenience, especially for younger"),
        AdjacencyRule("Classroom", "Storage", PREFER_NEAR,
                     "Teaching supplies"),

        # Specialized spaces
        AdjacencyRule("Science Lab", "Prep Room", MUST_CONNECT,
                     "Chemical storage and preparation"),
        AdjacencyRule("Science Lab", "Science Lab", SHOULD_ADJACENT,
                     "Shared prep resources"),
        AdjacencyRule("Art Room", "Kiln Room", SHOULD_ADJACENT,
                     "Ceramics workflow"),
        AdjacencyRule("Art Room", "Storage", MUST_CONNECT,
                     "Supply storage"),

        # Library/media center
        AdjacencyRule("Library", "Classroom", PREFER_NEAR,
                     "Research access"),
        AdjacencyRule("Library", "Computer Lab", SHOULD_ADJACENT,
                     "Technology integration"),

        # Common areas
        AdjacencyRule("Cafeteria", "Kitchen", MUST_CONNECT,
                     "Food service"),
        AdjacencyRule("Cafeteria", "Gymnasium", PREFER_NEAR,
                     "Assembly flexibility"),
        AdjacencyRule("Gymnasium", "Locker Room", MUST_CONNECT,
                     "Changing facilities"),

        # Separations
        AdjacencyRule("Music Room", "Classroom", SHOULD_SEPARATE,
                     "Acoustic isolation"),
        AdjacencyRule("Music Room", "Library", MUST_SEPARATE,
                     "Quiet study space"),
        AdjacencyRule("Gymnasium", "Classroom", SHOULD_SEPARATE,
                     "Noise from PE"),
        AdjacencyRule("Cafeteria", "Classroom", SHOULD_SEPARATE,
                     "Food odors and noise"),
        AdjacencyRule("Mechanical", "Classroom", MUST_SEPARATE,
                     "Equipment noise"),
    ]
)


# =============================================================================
# ADJACENCY REGISTRY
# =============================================================================

ADJACENCY_REGISTRY: Dict[str, BuildingTypeAdjacencies] = {
    "office": OFFICE_ADJACENCIES,
    "residential": RESIDENTIAL_ADJACENCIES,
    "healthcare": HEALTHCARE_ADJACENCIES,
    "retail": RETAIL_ADJACENCIES,
    "educational": EDUCATIONAL_ADJACENCIES,
}


def get_adjacencies(building_type: str) -> BuildingTypeAdjacencies:
    """Get adjacency rules for a building type."""
    bt = building_type.lower()
    if bt not in ADJACENCY_REGISTRY:
        available = list(ADJACENCY_REGISTRY.keys())
        raise ValueError(f"Unknown building type: {building_type}. Available: {available}")
    return ADJACENCY_REGISTRY[bt]


def calculate_adjacency_score(
    building_type: str,
    room_placements: List[Dict],
    adjacency_threshold: float = 10.0  # feet
) -> Dict:
    """
    Calculate how well a floor plan satisfies adjacency requirements.

    Args:
        building_type: Type of building
        room_placements: List of room dicts with 'name', 'x', 'y', 'width', 'depth'
        adjacency_threshold: Distance in feet to consider rooms "adjacent"

    Returns:
        Dict with scores and violations
    """
    adjacencies = get_adjacencies(building_type)

    satisfied = 0
    violated = 0
    violations = []

    for rule in adjacencies.rules:
        # Find rooms matching this rule
        rooms_a = [r for r in room_placements
                   if adjacencies._normalize_name(r['name']) == adjacencies._normalize_name(rule.room_a)]
        rooms_b = [r for r in room_placements
                   if adjacencies._normalize_name(r['name']) == adjacencies._normalize_name(rule.room_b)]

        if not rooms_a or not rooms_b:
            continue  # Rule doesn't apply if rooms don't exist

        # Check each pair
        for ra in rooms_a:
            for rb in rooms_b:
                if ra == rb:
                    continue

                # Calculate center-to-center distance
                dist = _room_distance(ra, rb)

                if rule.strength >= SHOULD_ADJACENT:
                    # Positive relationship - rooms should be close
                    if dist <= adjacency_threshold:
                        satisfied += 1
                    else:
                        violated += 1
                        violations.append({
                            "rule": f"{rule.room_a} <-> {rule.room_b}",
                            "expected": "adjacent",
                            "actual_distance": round(dist, 1),
                            "reason": rule.reason
                        })
                elif rule.strength <= SHOULD_SEPARATE:
                    # Negative relationship - rooms should be apart
                    min_distance = adjacency_threshold * 2 if rule.strength == MUST_SEPARATE else adjacency_threshold
                    if dist >= min_distance:
                        satisfied += 1
                    else:
                        violated += 1
                        violations.append({
                            "rule": f"{rule.room_a} <-> {rule.room_b}",
                            "expected": "separated",
                            "actual_distance": round(dist, 1),
                            "reason": rule.reason
                        })

    total = satisfied + violated
    score = (satisfied / total * 100) if total > 0 else 100

    return {
        "adjacency_score": round(score, 1),
        "rules_satisfied": satisfied,
        "rules_violated": violated,
        "violations": violations
    }


def _room_distance(room_a: Dict, room_b: Dict) -> float:
    """Calculate distance between room centers."""
    import math
    ax = room_a['x']
    ay = room_a['y']
    bx = room_b['x']
    by = room_b['y']
    return math.sqrt((ax - bx)**2 + (ay - by)**2)


# =============================================================================
# ADJACENCY GRAPH BUILDER
# =============================================================================

def build_adjacency_graph(building_type: str, rooms: List[str]) -> Dict[str, List[Tuple[str, int]]]:
    """
    Build a graph of room relationships for placement optimization.

    Args:
        building_type: Type of building
        rooms: List of room names to include

    Returns:
        Dict mapping room name to list of (connected_room, strength) tuples
    """
    adjacencies = get_adjacencies(building_type)
    graph = {room: [] for room in rooms}

    for room in rooms:
        for rule in adjacencies.rules:
            norm_room = adjacencies._normalize_name(room)
            norm_a = adjacencies._normalize_name(rule.room_a)
            norm_b = adjacencies._normalize_name(rule.room_b)

            if norm_room == norm_a:
                # Find matching rooms in our list
                for other in rooms:
                    if adjacencies._normalize_name(other) == norm_b:
                        graph[room].append((other, rule.strength))
            elif rule.bidirectional and norm_room == norm_b:
                for other in rooms:
                    if adjacencies._normalize_name(other) == norm_a:
                        graph[room].append((other, rule.strength))

    # Sort by relationship strength (strongest first)
    for room in graph:
        graph[room].sort(key=lambda x: x[1], reverse=True)

    return graph


if __name__ == "__main__":
    # Test the adjacency system
    print("Testing Adjacency Rules System")
    print("=" * 50)

    # Test office adjacencies
    office = get_adjacencies("office")
    print(f"\nOffice building has {len(office.rules)} adjacency rules")

    # Test relationship lookup
    print(f"\nReception <-> Conference: {office.get_relationship('Reception', 'Conference')}")
    print(f"Mechanical <-> Reception: {office.get_relationship('Mechanical', 'Reception')}")

    # Test must-connect lookup
    print(f"\nRooms that MUST connect to Reception: {office.get_must_connect('Reception')}")
    print(f"Rooms that MUST separate from Reception: {office.get_must_separate('Reception')}")

    # Test adjacency graph
    rooms = ["Reception", "Conference Room", "Private Office 1", "Break Room", "Restroom"]
    graph = build_adjacency_graph("office", rooms)
    print(f"\nAdjacency graph for {len(rooms)} rooms:")
    for room, connections in graph.items():
        if connections:
            print(f"  {room}: {connections}")

    # Test adjacency scoring
    placements = [
        {"name": "Reception", "x": 10, "y": 5, "width": 15, "depth": 12},
        {"name": "Conference Room", "x": 25, "y": 5, "width": 20, "depth": 15},
        {"name": "Break Room", "x": 10, "y": 20, "width": 15, "depth": 12},
        {"name": "Restroom", "x": 25, "y": 25, "width": 10, "depth": 8},
    ]
    score = calculate_adjacency_score("office", placements)
    print(f"\nAdjacency Score: {score['adjacency_score']}%")
    print(f"Satisfied: {score['rules_satisfied']}, Violated: {score['rules_violated']}")
    if score['violations']:
        print("Violations:")
        for v in score['violations'][:3]:  # Show first 3
            print(f"  - {v['rule']}: {v['expected']}, actual {v['actual_distance']}ft")
