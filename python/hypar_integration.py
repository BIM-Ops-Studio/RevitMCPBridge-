"""
Hypar Integration for RevitMCPBridge
Connects to Hypar's computational design platform for parametric generation.

Hypar offers a free tier that includes:
- 5 design options per month
- Basic space planning functions
- JSON output for Revit import

Setup:
1. Create account at https://hypar.io
2. Get API key from dashboard
3. Set HYPAR_API_KEY environment variable

Usage:
    from hypar_integration import HyparClient
    client = HyparClient()
    result = client.generate_floor_plan(width=50, depth=40, program="office")
"""

import os
import json
import requests
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class SpaceProgram:
    """Defines a space requirement for Hypar generation."""
    name: str
    area_sf: float
    quantity: int = 1
    adjacency: Optional[List[str]] = None


@dataclass
class GenerationResult:
    """Result from Hypar generation."""
    success: bool
    walls: List[Dict]
    rooms: List[Dict]
    doors: List[Dict]
    metadata: Dict
    raw_response: Any = None


class HyparClient:
    """Client for Hypar computational design API."""

    BASE_URL = "https://api.hypar.io/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Hypar client.

        Args:
            api_key: Hypar API key. If not provided, reads from HYPAR_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("HYPAR_API_KEY")
        if not self.api_key:
            print("Warning: No HYPAR_API_KEY found. Running in offline/mock mode.")
            self._offline_mode = True
        else:
            self._offline_mode = False

    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make authenticated request to Hypar API."""
        if self._offline_mode:
            return self._mock_response(endpoint, data)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{self.BASE_URL}/{endpoint}",
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text, "status_code": response.status_code}

    def _mock_response(self, endpoint: str, data: Dict) -> Dict:
        """Generate mock response for offline mode / testing."""
        width = data.get("width", 50)
        depth = data.get("depth", 40)

        # Generate simple floor plan
        walls = [
            {"start": [0, 0], "end": [width, 0], "height": 10, "type": "Exterior"},
            {"start": [width, 0], "end": [width, depth], "height": 10, "type": "Exterior"},
            {"start": [width, depth], "end": [0, depth], "height": 10, "type": "Exterior"},
            {"start": [0, depth], "end": [0, 0], "height": 10, "type": "Exterior"},
            # Interior partition
            {"start": [width/2, 0], "end": [width/2, depth], "height": 10, "type": "Interior"}
        ]

        rooms = [
            {"name": "Office A", "bounds": [[0, 0], [width/2, depth]], "area": (width/2) * depth},
            {"name": "Office B", "bounds": [[width/2, 0], [width, depth]], "area": (width/2) * depth}
        ]

        doors = [
            {"location": [width/2, depth/2], "width": 3, "host_wall_index": 4}
        ]

        return {
            "success": True,
            "walls": walls,
            "rooms": rooms,
            "doors": doors,
            "metadata": {
                "total_area": width * depth,
                "generation_time_ms": 150,
                "mode": "mock"
            }
        }

    def generate_floor_plan(
        self,
        width: float,
        depth: float,
        program: str = "office",
        num_options: int = 1
    ) -> GenerationResult:
        """
        Generate floor plan options.

        Args:
            width: Building width in feet
            depth: Building depth in feet
            program: Building program type (office, residential, retail, healthcare)
            num_options: Number of options to generate (free tier: max 5/month)

        Returns:
            GenerationResult with walls, rooms, and doors
        """
        data = {
            "width": width,
            "depth": depth,
            "program": program,
            "options": num_options
        }

        response = self._make_request("generate/floor-plan", data)

        if "error" in response:
            return GenerationResult(
                success=False,
                walls=[],
                rooms=[],
                doors=[],
                metadata={"error": response["error"]},
                raw_response=response
            )

        return GenerationResult(
            success=True,
            walls=response.get("walls", []),
            rooms=response.get("rooms", []),
            doors=response.get("doors", []),
            metadata=response.get("metadata", {}),
            raw_response=response
        )

    def generate_from_program(
        self,
        spaces: List[SpaceProgram],
        site_width: float,
        site_depth: float,
        building_type: str = "office"
    ) -> GenerationResult:
        """
        Generate floor plan from space program.

        Args:
            spaces: List of SpaceProgram requirements
            site_width: Site boundary width
            site_depth: Site boundary depth
            building_type: Type of building

        Returns:
            GenerationResult with generated layout
        """
        space_data = [
            {
                "name": s.name,
                "area": s.area_sf,
                "quantity": s.quantity,
                "adjacency": s.adjacency or []
            }
            for s in spaces
        ]

        data = {
            "site": {"width": site_width, "depth": site_depth},
            "spaces": space_data,
            "building_type": building_type
        }

        response = self._make_request("generate/from-program", data)

        if "error" in response:
            return GenerationResult(
                success=False,
                walls=[],
                rooms=[],
                doors=[],
                metadata={"error": response["error"]},
                raw_response=response
            )

        return GenerationResult(
            success=True,
            walls=response.get("walls", []),
            rooms=response.get("rooms", []),
            doors=response.get("doors", []),
            metadata=response.get("metadata", {}),
            raw_response=response
        )

    def optimize_layout(
        self,
        existing_layout: Dict,
        objectives: List[str]
    ) -> GenerationResult:
        """
        Optimize existing layout based on objectives.

        Args:
            existing_layout: Current layout JSON (walls, rooms, doors)
            objectives: List of objectives like "maximize_daylight", "minimize_circulation"

        Returns:
            GenerationResult with optimized layout
        """
        data = {
            "layout": existing_layout,
            "objectives": objectives
        }

        response = self._make_request("optimize", data)

        if "error" in response:
            return GenerationResult(
                success=False,
                walls=[],
                rooms=[],
                doors=[],
                metadata={"error": response["error"]},
                raw_response=response
            )

        return GenerationResult(
            success=True,
            walls=response.get("walls", []),
            rooms=response.get("rooms", []),
            doors=response.get("doors", []),
            metadata=response.get("metadata", {}),
            raw_response=response
        )


def convert_to_revit_format(result: GenerationResult) -> Dict:
    """
    Convert Hypar result to RevitMCPBridge format.

    Returns dict ready for createWalls, createRooms, placeDoor methods.
    """
    revit_data = {
        "walls": [],
        "rooms": [],
        "doors": []
    }

    # Convert walls
    for wall in result.walls:
        revit_data["walls"].append({
            "startX": wall["start"][0],
            "startY": wall["start"][1],
            "endX": wall["end"][0],
            "endY": wall["end"][1],
            "height": wall.get("height", 10),
            "wallType": "Basic Wall" if wall.get("type") == "Interior" else "Exterior Wall"
        })

    # Convert rooms
    for room in result.rooms:
        bounds = room.get("bounds", [[0, 0], [10, 10]])
        center_x = (bounds[0][0] + bounds[1][0]) / 2
        center_y = (bounds[0][1] + bounds[1][1]) / 2
        revit_data["rooms"].append({
            "name": room["name"],
            "x": center_x,
            "y": center_y,
            "expectedArea": room.get("area", 0)
        })

    # Convert doors
    for door in result.doors:
        loc = door.get("location", [0, 0])
        revit_data["doors"].append({
            "x": loc[0],
            "y": loc[1],
            "width": door.get("width", 3)
        })

    return revit_data


def save_for_revit(result: GenerationResult, output_path: str) -> str:
    """
    Save Hypar result as JSON for Revit import.

    Args:
        result: GenerationResult from Hypar
        output_path: Path to save JSON file

    Returns:
        Path to saved file
    """
    revit_data = convert_to_revit_format(result)

    with open(output_path, 'w') as f:
        json.dump(revit_data, f, indent=2)

    return output_path


# CLI usage
if __name__ == "__main__":
    import sys

    print("Hypar Integration Test")
    print("=" * 40)

    client = HyparClient()

    # Test basic generation
    print("\nGenerating 50x40 office floor plan...")
    result = client.generate_floor_plan(width=50, depth=40, program="office")

    if result.success:
        print(f"Generated {len(result.walls)} walls, {len(result.rooms)} rooms, {len(result.doors)} doors")
        print(f"Total area: {result.metadata.get('total_area', 'N/A')} SF")

        # Save for Revit
        output_path = "hypar_result.json"
        save_for_revit(result, output_path)
        print(f"\nSaved Revit-compatible JSON to: {output_path}")
    else:
        print(f"Generation failed: {result.metadata.get('error', 'Unknown error')}")

    # Test program-based generation
    print("\n" + "=" * 40)
    print("Testing program-based generation...")

    spaces = [
        SpaceProgram(name="Reception", area_sf=200, quantity=1),
        SpaceProgram(name="Private Office", area_sf=150, quantity=4, adjacency=["Reception"]),
        SpaceProgram(name="Conference Room", area_sf=300, quantity=1, adjacency=["Reception"]),
        SpaceProgram(name="Open Office", area_sf=800, quantity=1)
    ]

    result = client.generate_from_program(spaces, site_width=80, site_depth=60)

    if result.success:
        print(f"Generated layout with {len(result.rooms)} rooms")
    else:
        print(f"Generation failed: {result.metadata.get('error', 'Unknown error')}")
