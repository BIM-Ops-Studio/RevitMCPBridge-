"""
FREE Floor Plan Generator for RevitMCPBridge
Generates parametric floor plans without any external API costs.

This replaces paid services like Hypar by using:
- Algorithmic space planning
- Direct integration with RevitMCPBridge
- No API keys or subscriptions needed

Usage:
    python floor_plan_generator.py --width 60 --depth 40 --program office
    python floor_plan_generator.py --rooms "Reception:200,Office:150x4,Conference:300"
"""

import json
import sys
import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class Room:
    """A room with dimensions and placement."""
    name: str
    target_area: float
    width: float = 0
    depth: float = 0
    x: float = 0
    y: float = 0
    adjacency: List[str] = field(default_factory=list)

    @property
    def area(self) -> float:
        return self.width * self.depth

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Returns (x1, y1, x2, y2)"""
        return (self.x, self.y, self.x + self.width, self.y + self.depth)


@dataclass
class Wall:
    """A wall segment."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    wall_type: str = "Interior"
    height: float = 10.0


@dataclass
class Door:
    """A door placement."""
    x: float
    y: float
    width: float = 3.0
    host_wall: Optional[Wall] = None


class FloorPlanGenerator:
    """
    Generates floor plans algorithmically.
    No external APIs - runs entirely locally.
    """

    # Standard room dimensions by type (width x depth in feet)
    ROOM_DEFAULTS = {
        "reception": (15, 12),
        "office": (12, 10),
        "private_office": (12, 12),
        "conference": (20, 15),
        "conference_small": (12, 10),
        "bathroom": (8, 6),
        "restroom": (10, 8),
        "kitchen": (12, 10),
        "break_room": (15, 12),
        "storage": (8, 8),
        "mechanical": (10, 10),
        "corridor": (5, 20),
        "open_office": (30, 25),
        "lobby": (20, 15),
    }

    # Typical programs by building type
    PROGRAMS = {
        "office": [
            ("Reception", 200),
            ("Open Office", 600),
            ("Private Office", 150, 3),  # 3 offices
            ("Conference Room", 250),
            ("Conference Small", 120),
            ("Break Room", 200),
            ("Restroom", 100, 2),  # 2 restrooms
            ("Storage", 80),
        ],
        "residential": [
            ("Living Room", 250),
            ("Kitchen", 150),
            ("Master Bedroom", 200),
            ("Bedroom", 150, 2),
            ("Bathroom", 60, 2),
            ("Laundry", 40),
        ],
        "retail": [
            ("Sales Floor", 800),
            ("Storage", 200),
            ("Office", 120),
            ("Restroom", 80, 2),
        ],
        "healthcare": [
            ("Waiting Room", 300),
            ("Reception", 150),
            ("Exam Room", 120, 4),
            ("Office", 150),
            ("Restroom", 80, 2),
            ("Storage", 100),
        ],
    }

    def __init__(self, width: float, depth: float):
        """
        Initialize generator with building envelope.

        Args:
            width: Total building width in feet
            depth: Total building depth in feet
        """
        self.width = width
        self.depth = depth
        self.rooms: List[Room] = []
        self.walls: List[Wall] = []
        self.doors: List[Door] = []

    def add_exterior_walls(self):
        """Add the building perimeter walls."""
        self.walls.extend([
            Wall(0, 0, self.width, 0, "Exterior"),  # South
            Wall(self.width, 0, self.width, self.depth, "Exterior"),  # East
            Wall(self.width, self.depth, 0, self.depth, "Exterior"),  # North
            Wall(0, self.depth, 0, 0, "Exterior"),  # West
        ])

    def generate_from_program(self, program: str) -> bool:
        """
        Generate floor plan from predefined program.

        Args:
            program: One of: office, residential, retail, healthcare

        Returns:
            True if successful
        """
        if program not in self.PROGRAMS:
            print(f"Unknown program: {program}")
            print(f"Available: {list(self.PROGRAMS.keys())}")
            return False

        # Parse program into rooms
        for item in self.PROGRAMS[program]:
            name = item[0]
            area = item[1]
            quantity = item[2] if len(item) > 2 else 1

            for i in range(quantity):
                room_name = f"{name} {i+1}" if quantity > 1 else name
                self.rooms.append(Room(name=room_name, target_area=area))

        return self._layout_rooms()

    def generate_from_rooms(self, room_specs: List[Tuple[str, float]]) -> bool:
        """
        Generate floor plan from room specifications.

        Args:
            room_specs: List of (name, area) tuples

        Returns:
            True if successful
        """
        for name, area in room_specs:
            self.rooms.append(Room(name=name, target_area=area))

        return self._layout_rooms()

    def _layout_rooms(self) -> bool:
        """
        Layout rooms using strip packing algorithm.
        Simple but effective for rectangular spaces.
        """
        # Add exterior walls first
        self.add_exterior_walls()

        # Calculate room dimensions from target areas
        for room in self.rooms:
            # Use golden ratio for pleasing proportions
            ratio = 1.2
            room.depth = math.sqrt(room.target_area / ratio)
            room.width = room.target_area / room.depth

        # Sort rooms by area (largest first)
        sorted_rooms = sorted(self.rooms, key=lambda r: r.target_area, reverse=True)

        # Simple strip packing
        current_x = 0
        current_y = 0
        row_height = 0
        corridor_width = 5

        # Leave space for corridor along south side
        current_y = corridor_width

        for room in sorted_rooms:
            # Check if room fits in current row
            if current_x + room.width > self.width:
                # Start new row
                current_x = 0
                current_y += row_height + 0.5  # 6" wall thickness
                row_height = 0

            # Check if we've exceeded depth
            if current_y + room.depth > self.depth:
                print(f"Warning: Room {room.name} may not fit")
                # Try to fit anyway with reduced size
                room.depth = self.depth - current_y
                room.width = room.target_area / room.depth

            # Place room
            room.x = current_x
            room.y = current_y

            # Update position
            current_x += room.width + 0.5  # 6" wall thickness
            row_height = max(row_height, room.depth)

        # Generate interior walls
        self._generate_interior_walls()

        # Generate doors
        self._generate_doors()

        return True

    def _generate_interior_walls(self):
        """Generate interior partition walls between rooms."""
        for room in self.rooms:
            x1, y1, x2, y2 = room.bounds

            # Add walls around room (checking for duplicates with exterior)
            walls_to_add = [
                Wall(x1, y1, x2, y1, "Interior"),  # South
                Wall(x2, y1, x2, y2, "Interior"),  # East
                Wall(x2, y2, x1, y2, "Interior"),  # North
                Wall(x1, y2, x1, y1, "Interior"),  # West
            ]

            for wall in walls_to_add:
                # Skip if this is on the perimeter (would duplicate exterior wall)
                if not self._is_perimeter_wall(wall):
                    # Check for duplicates
                    if not self._wall_exists(wall):
                        self.walls.append(wall)

    def _is_perimeter_wall(self, wall: Wall) -> bool:
        """Check if wall is on the building perimeter."""
        epsilon = 0.1

        # Check south edge
        if abs(wall.start_y) < epsilon and abs(wall.end_y) < epsilon:
            return True
        # Check north edge
        if abs(wall.start_y - self.depth) < epsilon and abs(wall.end_y - self.depth) < epsilon:
            return True
        # Check west edge
        if abs(wall.start_x) < epsilon and abs(wall.end_x) < epsilon:
            return True
        # Check east edge
        if abs(wall.start_x - self.width) < epsilon and abs(wall.end_x - self.width) < epsilon:
            return True

        return False

    def _wall_exists(self, wall: Wall) -> bool:
        """Check if a wall already exists (avoid duplicates)."""
        epsilon = 0.5
        for existing in self.walls:
            if (abs(existing.start_x - wall.start_x) < epsilon and
                abs(existing.start_y - wall.start_y) < epsilon and
                abs(existing.end_x - wall.end_x) < epsilon and
                abs(existing.end_y - wall.end_y) < epsilon):
                return True
        return False

    def _generate_doors(self):
        """Generate doors for each room."""
        for room in self.rooms:
            x1, y1, x2, y2 = room.bounds

            # Place door on south wall of room (corridor side)
            door_x = x1 + (x2 - x1) / 2  # Center of room
            door_y = y1

            self.doors.append(Door(x=door_x, y=door_y, width=3.0))

    def to_revit_format(self) -> Dict:
        """
        Export to RevitMCPBridge-compatible format.

        Returns:
            Dict with walls, rooms, doors ready for MCP calls
        """
        result = {
            "walls": [],
            "rooms": [],
            "doors": [],
            "metadata": {
                "building_width": self.width,
                "building_depth": self.depth,
                "total_area": self.width * self.depth,
                "room_count": len(self.rooms),
                "wall_count": len(self.walls),
                "door_count": len(self.doors),
            }
        }

        for wall in self.walls:
            result["walls"].append({
                "startX": wall.start_x,
                "startY": wall.start_y,
                "endX": wall.end_x,
                "endY": wall.end_y,
                "height": wall.height,
                "wallType": wall.wall_type,
            })

        for room in self.rooms:
            result["rooms"].append({
                "name": room.name,
                "x": room.x + room.width / 2,  # Center point
                "y": room.y + room.depth / 2,
                "width": room.width,
                "depth": room.depth,
                "area": room.area,
                "targetArea": room.target_area,
            })

        for door in self.doors:
            result["doors"].append({
                "x": door.x,
                "y": door.y,
                "width": door.width,
            })

        return result

    def save_json(self, filepath: str) -> str:
        """Save to JSON file."""
        data = self.to_revit_format()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return filepath

    def print_summary(self):
        """Print generation summary."""
        print(f"\n{'='*50}")
        print("FLOOR PLAN GENERATED")
        print(f"{'='*50}")
        print(f"Building: {self.width}' x {self.depth}' = {self.width * self.depth} SF")
        print(f"\nRooms ({len(self.rooms)}):")
        for room in self.rooms:
            print(f"  - {room.name}: {room.width:.1f}' x {room.depth:.1f}' = {room.area:.0f} SF")
        print(f"\nWalls: {len(self.walls)} (including {4} exterior)")
        print(f"Doors: {len(self.doors)}")
        print(f"{'='*50}")


def parse_room_string(room_str: str) -> List[Tuple[str, float]]:
    """
    Parse room string like "Reception:200,Office:150x4,Conference:300"

    Returns list of (name, area) tuples
    """
    rooms = []
    for item in room_str.split(','):
        item = item.strip()
        if ':' in item:
            name, spec = item.split(':', 1)
            if 'x' in spec:
                # "Office:150x4" means 4 offices of 150 SF each
                area, count = spec.split('x')
                for i in range(int(count)):
                    rooms.append((f"{name} {i+1}", float(area)))
            else:
                rooms.append((name, float(spec)))
    return rooms


def main():
    parser = argparse.ArgumentParser(description="FREE Floor Plan Generator")
    parser.add_argument("--width", type=float, default=60, help="Building width in feet")
    parser.add_argument("--depth", type=float, default=40, help="Building depth in feet")
    parser.add_argument("--program", type=str, default="office",
                       help="Program type: office, residential, retail, healthcare")
    parser.add_argument("--rooms", type=str, default=None,
                       help='Custom rooms: "Reception:200,Office:150x4,Conference:300"')
    parser.add_argument("--output", type=str, default="floor_plan.json",
                       help="Output JSON file")

    args = parser.parse_args()

    print("FREE Floor Plan Generator")
    print("=" * 50)
    print("No API keys. No subscriptions. No cost.")
    print("=" * 50)

    generator = FloorPlanGenerator(args.width, args.depth)

    if args.rooms:
        # Custom room list
        room_specs = parse_room_string(args.rooms)
        print(f"\nGenerating from custom rooms: {len(room_specs)} rooms")
        generator.generate_from_rooms(room_specs)
    else:
        # Predefined program
        print(f"\nGenerating {args.program} program...")
        generator.generate_from_program(args.program)

    generator.print_summary()

    # Save output
    output_path = generator.save_json(args.output)
    print(f"\nSaved to: {output_path}")
    print("\nTo import to Revit, use the JSON with RevitMCPBridge createWalls method.")

    return generator.to_revit_format()


if __name__ == "__main__":
    main()
