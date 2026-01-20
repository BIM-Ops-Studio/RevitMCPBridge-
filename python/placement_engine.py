"""
Smart Placement Engine - Constraint-based room placement algorithm.

This module places rooms intelligently based on:
1. Zone assignments (PUBLIC → SEMI_PUBLIC → PRIVATE → SERVICE)
2. Adjacency requirements (MUST_CONNECT, SHOULD_ADJACENT, etc.)
3. Daylight needs (perimeter vs core placement)
4. Circulation efficiency (corridor generation)
5. Room-specific constraints (plumbing clusters, entry facing, etc.)

The engine uses a priority-based constraint satisfaction approach:
- Place anchor rooms first (entry, reception)
- Propagate connected rooms from anchors
- Fill remaining spaces respecting constraints
- Generate circulation paths
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum, auto
import math
import json

from adjacency_rules import (
    get_adjacencies, calculate_adjacency_score, build_adjacency_graph,
    MUST_CONNECT, SHOULD_ADJACENT, PREFER_NEAR, NEUTRAL, SHOULD_SEPARATE, MUST_SEPARATE
)
from zone_definitions import (
    get_zones, get_room_zone, get_placement_priority, group_rooms_by_zone,
    ZoneType
)
from room_intelligence import (
    get_room_rule, get_room_rules, get_daylight_rooms, get_placement_constraints,
    DaylightRequirement, PlacementConstraint, suggest_room_size
)


class PlacementStrategy(Enum):
    """Different placement strategies for scheme generation."""
    LINEAR = auto()          # Single-loaded corridor
    DOUBLE_LOADED = auto()   # Central corridor, rooms both sides
    CLUSTER = auto()         # Grouped pods around common areas
    L_SHAPE = auto()         # Two wings at 90 degrees
    U_SHAPE = auto()         # Three wings around courtyard
    PERIMETER = auto()       # Rooms around perimeter, core in center


@dataclass
class PlacedRoom:
    """A room that has been placed in the floor plan."""
    name: str
    x: float           # Left edge X coordinate
    y: float           # Bottom edge Y coordinate
    width: float       # X dimension
    depth: float       # Y dimension
    zone: ZoneType
    rotation: float = 0.0  # Degrees, 0 = normal
    has_exterior_wall: bool = False
    connected_to: List[str] = field(default_factory=list)  # Room names with doors

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.depth / 2

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y + self.depth

    @property
    def area(self) -> float:
        return self.width * self.depth

    def overlaps(self, other: 'PlacedRoom', buffer: float = 0.0) -> bool:
        """Check if this room overlaps another (with optional buffer)."""
        return not (
            self.right + buffer <= other.x or
            other.right + buffer <= self.x or
            self.top + buffer <= other.y or
            other.top + buffer <= self.y
        )

    def distance_to(self, other: 'PlacedRoom') -> float:
        """Calculate center-to-center distance."""
        dx = self.center_x - other.center_x
        dy = self.center_y - other.center_y
        return math.sqrt(dx * dx + dy * dy)

    def shares_wall(self, other: 'PlacedRoom', tolerance: float = 0.5) -> Optional[str]:
        """
        Check if rooms share a wall. Returns wall direction or None.
        'north', 'south', 'east', 'west' from perspective of self.
        """
        # Check vertical alignment (east/west walls)
        if abs(self.y - other.y) < tolerance or abs(self.top - other.top) < tolerance or \
           (self.y < other.top and self.top > other.y):
            if abs(self.right - other.x) < tolerance:
                return "east"
            if abs(other.right - self.x) < tolerance:
                return "west"

        # Check horizontal alignment (north/south walls)
        if abs(self.x - other.x) < tolerance or abs(self.right - other.right) < tolerance or \
           (self.x < other.right and self.right > other.x):
            if abs(self.top - other.y) < tolerance:
                return "north"
            if abs(other.top - self.y) < tolerance:
                return "south"

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "depth": self.depth,
            "zone": self.zone.name,
            "rotation": self.rotation,
            "has_exterior_wall": self.has_exterior_wall,
            "connected_to": self.connected_to
        }


@dataclass
class Corridor:
    """A circulation corridor in the floor plan."""
    x: float
    y: float
    width: float
    depth: float
    is_primary: bool = True  # Primary vs secondary corridor

    @property
    def area(self) -> float:
        return self.width * self.depth

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "depth": self.depth,
            "is_primary": self.is_primary
        }


@dataclass
class PlacementGrid:
    """Grid-based placement tracking for collision detection."""
    width: float
    depth: float
    cell_size: float = 1.0  # 1 foot grid
    cells: Set[Tuple[int, int]] = field(default_factory=set)

    def mark_occupied(self, x: float, y: float, w: float, d: float):
        """Mark grid cells as occupied."""
        x1 = int(x / self.cell_size)
        y1 = int(y / self.cell_size)
        x2 = int((x + w) / self.cell_size) + 1
        y2 = int((y + d) / self.cell_size) + 1
        for gx in range(x1, x2):
            for gy in range(y1, y2):
                self.cells.add((gx, gy))

    def is_available(self, x: float, y: float, w: float, d: float) -> bool:
        """Check if area is available."""
        x1 = int(x / self.cell_size)
        y1 = int(y / self.cell_size)
        x2 = int((x + w) / self.cell_size) + 1
        y2 = int((y + d) / self.cell_size) + 1
        for gx in range(x1, x2):
            for gy in range(y1, y2):
                if (gx, gy) in self.cells:
                    return False
        return True


class SmartPlacementEngine:
    """
    Intelligent room placement engine using constraint satisfaction.

    Placement Algorithm:
    1. Analyze program and build adjacency graph
    2. Determine entry point and orientation
    3. Place anchor rooms (entry, reception) first
    4. Propagate placement using adjacency weights
    5. Place perimeter rooms on exterior walls
    6. Fill core rooms in remaining space
    7. Generate circulation corridors
    8. Optimize for adjacency satisfaction
    """

    # Corridor widths by type
    CORRIDOR_WIDTH_PRIMARY = 6.0   # Main corridor
    CORRIDOR_WIDTH_SECONDARY = 5.0  # Secondary corridor

    def __init__(self, building_width: float, building_depth: float,
                 building_type: str, entry_side: str = "south"):
        """
        Initialize placement engine.

        Args:
            building_width: Total width in feet (X dimension)
            building_depth: Total depth in feet (Y dimension)
            building_type: Type of building (office, residential, etc.)
            entry_side: Which side has main entry (south, north, east, west)
        """
        self.building_width = building_width
        self.building_depth = building_depth
        self.building_type = building_type.lower()
        self.entry_side = entry_side.lower()

        # Get rules and adjacencies
        self.adjacencies = get_adjacencies(building_type)
        self.zones = get_zones(building_type)
        self.room_rules = get_room_rules(building_type)

        # Placement state
        self.placed_rooms: List[PlacedRoom] = []
        self.corridors: List[Corridor] = []
        self.grid = PlacementGrid(building_width, building_depth)

        # Strategy configuration
        self.strategy = PlacementStrategy.DOUBLE_LOADED
        self.main_corridor_y = None  # Y position of main corridor

    def place_rooms(self, program: List[Dict[str, Any]],
                    strategy: PlacementStrategy = PlacementStrategy.DOUBLE_LOADED) -> Dict[str, Any]:
        """
        Place all rooms from program using specified strategy.

        Args:
            program: List of room dicts with 'name', 'width', 'depth'
            strategy: Placement strategy to use

        Returns:
            Dict with placed_rooms, corridors, metrics
        """
        self.strategy = strategy
        self.placed_rooms = []
        self.corridors = []
        self.grid = PlacementGrid(self.building_width, self.building_depth)

        # Step 1: Augment program with zone and adjacency info
        rooms_with_info = self._augment_program(program)

        # Step 2: Sort rooms by placement priority
        sorted_rooms = self._sort_by_priority(rooms_with_info)

        # Step 3: Establish circulation spine based on strategy
        self._establish_circulation(strategy)

        # Step 4: Place rooms in priority order
        for room_info in sorted_rooms:
            self._place_single_room(room_info)

        # Step 5: Establish door connections
        self._establish_connections()

        # Step 6: Calculate metrics
        metrics = self._calculate_metrics(program)

        return {
            "placed_rooms": [r.to_dict() for r in self.placed_rooms],
            "corridors": [c.to_dict() for c in self.corridors],
            "metrics": metrics,
            "strategy": strategy.name
        }

    def _augment_program(self, program: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add zone, priority, and constraint info to each room."""
        augmented = []
        for room in program:
            name = room.get("name", "Unknown")
            width = room.get("width", 10)
            depth = room.get("depth", 10)

            zone = get_room_zone(self.building_type, name)
            priority = get_placement_priority(self.building_type, name)
            rule = get_room_rule(self.building_type, name)
            constraints = rule.constraints if rule else []
            daylight = rule.daylight if rule else DaylightRequirement.PREFERRED

            augmented.append({
                "name": name,
                "width": width,
                "depth": depth,
                "zone": zone,
                "priority": priority,
                "constraints": constraints,
                "daylight": daylight,
                "adjacency_weight": self._calculate_adjacency_importance(name)
            })

        return augmented

    def _calculate_adjacency_importance(self, room_name: str) -> float:
        """Calculate how important this room is for adjacency satisfaction."""
        if not self.adjacencies:
            return 0.0

        total_weight = 0.0
        for rule in self.adjacencies.rules:
            if room_name.lower() in [rule.room_a.lower(), rule.room_b.lower()]:
                total_weight += abs(rule.strength)

        return total_weight

    def _sort_by_priority(self, rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort rooms by placement priority."""
        def sort_key(room):
            # Priority order: zone (PUBLIC first), then specific priority, then adjacency weight
            zone_order = {ZoneType.PUBLIC: 0, ZoneType.SEMI_PUBLIC: 1,
                          ZoneType.PRIVATE: 2, ZoneType.SERVICE: 3}
            priority_map = {"near_entry": 0, "perimeter": 1, "middle": 2, "core": 3, "back": 4}

            zone_val = zone_order.get(room["zone"], 2)
            priority_val = priority_map.get(room["priority"], 2)
            adj_weight = -room["adjacency_weight"]  # Negative so high weight comes first

            return (zone_val, priority_val, adj_weight, room["name"])

        return sorted(rooms, key=sort_key)

    def _establish_circulation(self, strategy: PlacementStrategy):
        """Set up main circulation corridor based on strategy."""
        if strategy == PlacementStrategy.LINEAR:
            # Single-loaded: corridor on one side
            corridor_y = 0 if self.entry_side == "south" else self.building_depth - self.CORRIDOR_WIDTH_PRIMARY
            self.main_corridor_y = corridor_y
            self.corridors.append(Corridor(
                x=0, y=corridor_y,
                width=self.building_width,
                depth=self.CORRIDOR_WIDTH_PRIMARY,
                is_primary=True
            ))
            self.grid.mark_occupied(0, corridor_y, self.building_width, self.CORRIDOR_WIDTH_PRIMARY)

        elif strategy == PlacementStrategy.DOUBLE_LOADED:
            # Central corridor
            corridor_y = (self.building_depth - self.CORRIDOR_WIDTH_PRIMARY) / 2
            self.main_corridor_y = corridor_y
            self.corridors.append(Corridor(
                x=0, y=corridor_y,
                width=self.building_width,
                depth=self.CORRIDOR_WIDTH_PRIMARY,
                is_primary=True
            ))
            self.grid.mark_occupied(0, corridor_y, self.building_width, self.CORRIDOR_WIDTH_PRIMARY)

        elif strategy == PlacementStrategy.PERIMETER:
            # No central corridor - rooms connect around perimeter
            self.main_corridor_y = None

        elif strategy == PlacementStrategy.L_SHAPE:
            # Horizontal corridor + vertical corridor
            horiz_y = self.building_depth / 3
            self.main_corridor_y = horiz_y
            self.corridors.append(Corridor(
                x=0, y=horiz_y,
                width=self.building_width * 0.6,
                depth=self.CORRIDOR_WIDTH_PRIMARY,
                is_primary=True
            ))
            self.corridors.append(Corridor(
                x=self.building_width * 0.4,
                y=horiz_y,
                width=self.CORRIDOR_WIDTH_PRIMARY,
                depth=self.building_depth - horiz_y,
                is_primary=True
            ))
            for c in self.corridors:
                self.grid.mark_occupied(c.x, c.y, c.width, c.depth)

        elif strategy == PlacementStrategy.CLUSTER:
            # Multiple smaller corridors connecting clusters
            self.main_corridor_y = (self.building_depth - self.CORRIDOR_WIDTH_PRIMARY) / 2

    def _place_single_room(self, room_info: Dict[str, Any]) -> bool:
        """
        Place a single room in the best available position.
        Returns True if successfully placed.
        """
        name = room_info["name"]
        width = room_info["width"]
        depth = room_info["depth"]
        zone = room_info["zone"]
        priority = room_info["priority"]
        daylight = room_info["daylight"]
        constraints = room_info["constraints"]

        # Determine candidate positions based on zone and constraints
        candidates = self._generate_candidate_positions(
            width, depth, zone, priority, daylight, constraints, name
        )

        if not candidates:
            # Fallback: find any available space
            candidates = self._find_any_available_space(width, depth)

        if not candidates:
            print(f"Warning: Could not place {name}")
            return False

        # Score each candidate and pick best
        best_pos = None
        best_score = float('-inf')

        for x, y in candidates:
            score = self._score_position(x, y, width, depth, room_info)
            if score > best_score:
                best_score = score
                best_pos = (x, y)

        if best_pos:
            x, y = best_pos
            has_exterior = self._is_on_perimeter(x, y, width, depth)

            placed = PlacedRoom(
                name=name,
                x=x,
                y=y,
                width=width,
                depth=depth,
                zone=zone,
                has_exterior_wall=has_exterior
            )
            self.placed_rooms.append(placed)
            self.grid.mark_occupied(x, y, width, depth)
            return True

        return False

    def _generate_candidate_positions(self, width: float, depth: float,
                                       zone: ZoneType, priority: str,
                                       daylight: DaylightRequirement,
                                       constraints: List[PlacementConstraint],
                                       room_name: str) -> List[Tuple[float, float]]:
        """Generate candidate placement positions based on constraints."""
        candidates = []
        step = 2.0  # 2-foot grid for candidates

        # Determine Y region based on zone and strategy
        if self.strategy == PlacementStrategy.DOUBLE_LOADED:
            if zone == ZoneType.PUBLIC or priority == "near_entry":
                # Near entry (south side if entry_side == "south")
                if self.entry_side == "south":
                    y_range = (0, self.main_corridor_y - depth if self.main_corridor_y else self.building_depth / 3)
                else:
                    y_range = (self.main_corridor_y + self.CORRIDOR_WIDTH_PRIMARY if self.main_corridor_y
                              else self.building_depth * 2/3, self.building_depth - depth)
            elif zone == ZoneType.SERVICE or priority == "core":
                # Core placement - interior (less desirable perimeter)
                y_range = (self.main_corridor_y + self.CORRIDOR_WIDTH_PRIMARY if self.main_corridor_y
                          else self.building_depth / 3,
                          self.building_depth - depth)
            else:
                # Private/semi-public: perimeter zones
                y_range = (0, self.building_depth - depth)
        else:
            y_range = (0, self.building_depth - depth)

        # Determine X region
        if priority == "near_entry":
            # Entry typically in center or specific location
            x_range = (self.building_width / 4, self.building_width * 3/4 - width)
        else:
            x_range = (0, self.building_width - width)

        # Handle perimeter constraint
        if PlacementConstraint.PERIMETER in constraints or daylight == DaylightRequirement.REQUIRED:
            # Must be on edge - generate only edge positions
            # South edge
            for x in self._frange(x_range[0], x_range[1], step):
                candidates.append((x, 0))
            # North edge
            for x in self._frange(x_range[0], x_range[1], step):
                candidates.append((x, self.building_depth - depth))
            # West edge
            for y in self._frange(y_range[0], y_range[1], step):
                candidates.append((0, y))
            # East edge
            for y in self._frange(y_range[0], y_range[1], step):
                candidates.append((self.building_width - width, y))
        elif PlacementConstraint.CORE in constraints:
            # Core rooms - avoid perimeter
            margin = max(width, depth)
            x_core = (margin, self.building_width - width - margin)
            y_core = (margin, self.building_depth - depth - margin)
            for x in self._frange(x_core[0], x_core[1], step):
                for y in self._frange(y_core[0], y_core[1], step):
                    candidates.append((x, y))
        else:
            # General placement within zone constraints
            for x in self._frange(x_range[0], x_range[1], step):
                for y in self._frange(y_range[0], y_range[1], step):
                    candidates.append((x, y))

        # Filter for corridor adjacency if needed
        if self.main_corridor_y is not None and zone != ZoneType.SERVICE:
            corridor_adjacent = []
            for x, y in candidates:
                # Check if adjacent to corridor
                if (abs(y + depth - self.main_corridor_y) < 1.0 or
                    abs(y - (self.main_corridor_y + self.CORRIDOR_WIDTH_PRIMARY)) < 1.0):
                    corridor_adjacent.append((x, y))
            if corridor_adjacent:
                candidates = corridor_adjacent

        # Filter out positions that overlap existing rooms
        valid = []
        for x, y in candidates:
            if self.grid.is_available(x, y, width, depth):
                # Also check actual room overlaps with small buffer
                overlaps = False
                for placed in self.placed_rooms:
                    test_room = PlacedRoom("test", x, y, width, depth, zone)
                    if test_room.overlaps(placed, buffer=0.5):
                        overlaps = True
                        break
                if not overlaps:
                    valid.append((x, y))

        return valid

    def _find_any_available_space(self, width: float, depth: float) -> List[Tuple[float, float]]:
        """Find any available space in the building."""
        candidates = []
        step = 2.0

        for x in self._frange(0, self.building_width - width, step):
            for y in self._frange(0, self.building_depth - depth, step):
                if self.grid.is_available(x, y, width, depth):
                    candidates.append((x, y))

        return candidates

    def _score_position(self, x: float, y: float, width: float, depth: float,
                        room_info: Dict[str, Any]) -> float:
        """
        Score a candidate position. Higher is better.

        Factors:
        - Adjacency satisfaction with already-placed rooms
        - Zone appropriateness
        - Daylight access (perimeter bonus)
        - Entry proximity for public rooms
        - Corridor access
        """
        score = 0.0
        name = room_info["name"]
        zone = room_info["zone"]
        daylight = room_info["daylight"]
        priority = room_info["priority"]

        # Create temporary room for testing
        test_room = PlacedRoom(name, x, y, width, depth, zone)

        # 1. Adjacency scoring (most important)
        if self.adjacencies:
            for placed in self.placed_rooms:
                adj_strength = self._get_adjacency_strength(name, placed.name)
                if adj_strength != 0:
                    distance = test_room.distance_to(placed)
                    shares_wall = test_room.shares_wall(placed) is not None

                    if adj_strength > 0:  # Should be close
                        if shares_wall and adj_strength >= SHOULD_ADJACENT:
                            score += 100  # Big bonus for required adjacency
                        elif distance < 20:
                            score += 50 * (1 - distance / 20)  # Closer is better
                    else:  # Should be separated
                        if distance > 30:
                            score += 20  # Bonus for separation
                        elif shares_wall and adj_strength <= SHOULD_SEPARATE:
                            score -= 100  # Penalty for unwanted adjacency

        # 2. Daylight bonus
        is_perimeter = self._is_on_perimeter(x, y, width, depth)
        if daylight == DaylightRequirement.REQUIRED:
            if is_perimeter:
                score += 50
            else:
                score -= 100  # Big penalty for interior placement
        elif daylight == DaylightRequirement.PREFERRED:
            if is_perimeter:
                score += 25

        # 3. Entry proximity for PUBLIC zone
        if zone == ZoneType.PUBLIC or priority == "near_entry":
            entry_y = 0 if self.entry_side == "south" else self.building_depth
            entry_x = self.building_width / 2
            dist_to_entry = math.sqrt((test_room.center_x - entry_x)**2 +
                                       (test_room.center_y - entry_y)**2)
            score += 30 * (1 - dist_to_entry / max(self.building_width, self.building_depth))

        # 4. Corridor access bonus
        if self.main_corridor_y is not None:
            dist_to_corridor = min(
                abs(y + depth - self.main_corridor_y),
                abs(y - (self.main_corridor_y + self.CORRIDOR_WIDTH_PRIMARY))
            )
            if dist_to_corridor < 1.0:
                score += 20  # Adjacent to corridor

        # 5. Plumbing cluster bonus
        if PlacementConstraint.PLUMBING_CLUSTER in room_info["constraints"]:
            for placed in self.placed_rooms:
                placed_rule = get_room_rule(self.building_type, placed.name)
                if placed_rule and PlacementConstraint.PLUMBING_CLUSTER in placed_rule.constraints:
                    if test_room.shares_wall(placed):
                        score += 30  # Bonus for back-to-back plumbing

        # 6. Corner bonus for corner-preferred rooms
        if PlacementConstraint.CORNER in room_info["constraints"]:
            corners = [(0, 0), (self.building_width - width, 0),
                       (0, self.building_depth - depth),
                       (self.building_width - width, self.building_depth - depth)]
            for cx, cy in corners:
                if abs(x - cx) < 2 and abs(y - cy) < 2:
                    score += 40

        return score

    def _get_adjacency_strength(self, room_a: str, room_b: str) -> int:
        """Get adjacency strength between two rooms."""
        if not self.adjacencies:
            return NEUTRAL

        for rule in self.adjacencies.rules:
            if (room_a.lower() in [rule.room_a.lower(), rule.room_b.lower()] and
                room_b.lower() in [rule.room_a.lower(), rule.room_b.lower()]):
                return rule.strength

        return NEUTRAL

    def _is_on_perimeter(self, x: float, y: float, width: float, depth: float) -> bool:
        """Check if room is on building perimeter (has exterior wall)."""
        tolerance = 1.0
        return (x < tolerance or  # West edge
                x + width > self.building_width - tolerance or  # East edge
                y < tolerance or  # South edge
                y + depth > self.building_depth - tolerance)  # North edge

    def _establish_connections(self):
        """Establish door connections between rooms based on adjacency requirements."""
        for i, room_a in enumerate(self.placed_rooms):
            for j, room_b in enumerate(self.placed_rooms):
                if i >= j:
                    continue

                adj_strength = self._get_adjacency_strength(room_a.name, room_b.name)
                shares_wall = room_a.shares_wall(room_b)

                # Connect if required adjacency and sharing wall
                if adj_strength >= SHOULD_ADJACENT and shares_wall:
                    if room_b.name not in room_a.connected_to:
                        room_a.connected_to.append(room_b.name)
                    if room_a.name not in room_b.connected_to:
                        room_b.connected_to.append(room_a.name)

    def _calculate_metrics(self, original_program: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for the placement."""
        # Calculate areas
        total_room_area = sum(r.area for r in self.placed_rooms)
        corridor_area = sum(c.area for c in self.corridors)
        building_area = self.building_width * self.building_depth
        circulation_ratio = corridor_area / building_area if building_area > 0 else 0

        # Efficiency
        net_area = total_room_area
        gross_area = building_area
        efficiency = net_area / gross_area if gross_area > 0 else 0

        # Adjacency satisfaction
        adjacency_score = self._calculate_adjacency_satisfaction()

        # Daylight ratio
        daylight_rooms = sum(1 for r in self.placed_rooms if r.has_exterior_wall)
        daylight_required = len([r for r in self.placed_rooms
                                 if get_room_rule(self.building_type, r.name) and
                                 get_room_rule(self.building_type, r.name).daylight == DaylightRequirement.REQUIRED])
        daylight_score = daylight_rooms / len(self.placed_rooms) if self.placed_rooms else 0

        # Rooms placed
        rooms_placed = len(self.placed_rooms)
        rooms_requested = len(original_program)
        placement_success = rooms_placed / rooms_requested if rooms_requested > 0 else 0

        return {
            "efficiency": round(efficiency, 3),
            "net_area_sf": round(net_area, 0),
            "gross_area_sf": round(gross_area, 0),
            "circulation_ratio": round(circulation_ratio, 3),
            "adjacency_score": round(adjacency_score, 3),
            "daylight_ratio": round(daylight_score, 3),
            "rooms_placed": rooms_placed,
            "rooms_requested": rooms_requested,
            "placement_success": round(placement_success, 3)
        }

    def _calculate_adjacency_satisfaction(self) -> float:
        """Calculate what percentage of adjacency requirements are satisfied."""
        if not self.adjacencies:
            return 1.0

        satisfied = 0
        total = 0

        for rule in self.adjacencies.rules:
            if rule.strength == NEUTRAL:
                continue

            room_a = self._find_placed_room(rule.room_a)
            room_b = self._find_placed_room(rule.room_b)

            if not room_a or not room_b:
                continue

            total += 1
            shares_wall = room_a.shares_wall(room_b) is not None
            distance = room_a.distance_to(room_b)

            if rule.strength >= MUST_CONNECT:
                if shares_wall and room_b.name in room_a.connected_to:
                    satisfied += 1
            elif rule.strength >= SHOULD_ADJACENT:
                if shares_wall:
                    satisfied += 1
            elif rule.strength >= PREFER_NEAR:
                if distance < 30:
                    satisfied += 1
            elif rule.strength <= MUST_SEPARATE:
                if distance > 40:
                    satisfied += 1
            elif rule.strength <= SHOULD_SEPARATE:
                if not shares_wall and distance > 20:
                    satisfied += 1

        return satisfied / total if total > 0 else 1.0

    def _find_placed_room(self, name: str) -> Optional[PlacedRoom]:
        """Find a placed room by name."""
        for room in self.placed_rooms:
            if room.name.lower() == name.lower():
                return room
        return None

    def _frange(self, start: float, stop: float, step: float):
        """Float range generator."""
        current = start
        while current <= stop:
            yield current
            current += step


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_placement_engine(width: float, depth: float, building_type: str,
                           entry_side: str = "south") -> SmartPlacementEngine:
    """Factory function to create a placement engine."""
    return SmartPlacementEngine(width, depth, building_type, entry_side)


def place_floor_plan(width: float, depth: float, building_type: str,
                     program: List[Dict[str, Any]],
                     strategy: PlacementStrategy = PlacementStrategy.DOUBLE_LOADED,
                     entry_side: str = "south") -> Dict[str, Any]:
    """
    Convenience function to place a complete floor plan.

    Args:
        width: Building width in feet
        depth: Building depth in feet
        building_type: Type of building
        program: List of room dicts
        strategy: Placement strategy
        entry_side: Side with main entry

    Returns:
        Complete placement result with rooms, corridors, metrics
    """
    engine = SmartPlacementEngine(width, depth, building_type, entry_side)
    return engine.place_rooms(program, strategy)


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("Smart Placement Engine - Test Output")
    print("=" * 60)

    # Test with office program
    test_program = [
        {"name": "Entry", "width": 10, "depth": 8},
        {"name": "Reception", "width": 15, "depth": 12},
        {"name": "Waiting", "width": 12, "depth": 10},
        {"name": "Conference", "width": 16, "depth": 14},
        {"name": "Private Office", "width": 12, "depth": 10},
        {"name": "Private Office", "width": 12, "depth": 10},
        {"name": "Open Office", "width": 25, "depth": 20},
        {"name": "Break Room", "width": 15, "depth": 12},
        {"name": "Restroom", "width": 8, "depth": 10},
        {"name": "Restroom", "width": 8, "depth": 10},
        {"name": "Storage", "width": 10, "depth": 8},
    ]

    # Make unique names for duplicate rooms
    name_counts = {}
    for room in test_program:
        name = room["name"]
        if name in name_counts:
            name_counts[name] += 1
            room["name"] = f"{name} {name_counts[name]}"
        else:
            name_counts[name] = 1

    print("\nTest Program:")
    for room in test_program:
        print(f"  {room['name']}: {room['width']}' x {room['depth']}'")

    print("\n" + "-" * 60)
    print("DOUBLE-LOADED CORRIDOR STRATEGY:")
    result = place_floor_plan(80, 50, "office", test_program,
                              PlacementStrategy.DOUBLE_LOADED)

    print(f"\nMetrics:")
    for key, value in result["metrics"].items():
        print(f"  {key}: {value}")

    print(f"\nPlaced Rooms ({len(result['placed_rooms'])}):")
    for room in result["placed_rooms"]:
        print(f"  {room['name']}: ({room['x']:.1f}, {room['y']:.1f}) "
              f"{room['width']}'x{room['depth']}' "
              f"[{room['zone']}] {'*perimeter*' if room['has_exterior_wall'] else ''}")
        if room["connected_to"]:
            print(f"    Connected to: {', '.join(room['connected_to'])}")

    print(f"\nCorridors ({len(result['corridors'])}):")
    for corr in result["corridors"]:
        print(f"  ({corr['x']:.1f}, {corr['y']:.1f}) "
              f"{corr['width']}'x{corr['depth']}' "
              f"{'[PRIMARY]' if corr['is_primary'] else '[SECONDARY]'}")

    print("\n" + "=" * 60)
    print("Placement Engine loaded successfully!")
