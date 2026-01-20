"""
Scheme Generator - Multi-scheme design option generation.

This module generates multiple floor plan schemes for comparison,
each using different placement strategies and orientations.

Each scheme includes:
- Room placements
- Corridors
- Quality metrics
- Strengths and trade-offs analysis
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import math
from datetime import datetime

from placement_engine import (
    SmartPlacementEngine, PlacementStrategy, place_floor_plan,
    PlacedRoom, Corridor
)
from adjacency_rules import get_adjacencies
from zone_definitions import get_zones
from room_intelligence import get_room_rules, suggest_room_size


@dataclass
class SchemeInfo:
    """Information about a placement strategy/scheme type."""
    strategy: PlacementStrategy
    name: str
    description: str
    best_for: List[str]
    typical_efficiency: float
    min_aspect_ratio: float  # Min building width/depth
    max_aspect_ratio: float


# Strategy characteristics
SCHEME_TYPES: Dict[PlacementStrategy, SchemeInfo] = {
    PlacementStrategy.LINEAR: SchemeInfo(
        strategy=PlacementStrategy.LINEAR,
        name="Linear (Single-Loaded)",
        description="Single corridor with rooms on one side. Maximum daylight, clear wayfinding.",
        best_for=["narrow_sites", "views_priority", "daylight_critical", "small_programs"],
        typical_efficiency=0.70,
        min_aspect_ratio=2.0,
        max_aspect_ratio=5.0
    ),
    PlacementStrategy.DOUBLE_LOADED: SchemeInfo(
        strategy=PlacementStrategy.DOUBLE_LOADED,
        name="Double-Loaded Corridor",
        description="Central corridor with rooms on both sides. Maximum efficiency, clear organization.",
        best_for=["maximum_efficiency", "standard_sites", "medium_programs", "cost_sensitive"],
        typical_efficiency=0.78,
        min_aspect_ratio=1.2,
        max_aspect_ratio=3.0
    ),
    PlacementStrategy.CLUSTER: SchemeInfo(
        strategy=PlacementStrategy.CLUSTER,
        name="Clustered Pods",
        description="Grouped zones around shared spaces. Good for team-based work.",
        best_for=["collaborative_space", "team_based", "flexible_layouts", "large_programs"],
        typical_efficiency=0.72,
        min_aspect_ratio=1.0,
        max_aspect_ratio=2.0
    ),
    PlacementStrategy.L_SHAPE: SchemeInfo(
        strategy=PlacementStrategy.L_SHAPE,
        name="L-Shape Configuration",
        description="Two wings at 90 degrees. Good zone separation, corner site utilization.",
        best_for=["corner_sites", "zone_separation", "phase_construction", "view_preservation"],
        typical_efficiency=0.73,
        min_aspect_ratio=0.8,
        max_aspect_ratio=1.5
    ),
    PlacementStrategy.U_SHAPE: SchemeInfo(
        strategy=PlacementStrategy.U_SHAPE,
        name="U-Shape / Courtyard",
        description="Three wings around central open space. Maximum daylight, defined outdoor room.",
        best_for=["courtyard_desired", "institutional", "large_sites", "daylight_priority"],
        typical_efficiency=0.68,
        min_aspect_ratio=0.8,
        max_aspect_ratio=1.5
    ),
    PlacementStrategy.PERIMETER: SchemeInfo(
        strategy=PlacementStrategy.PERIMETER,
        name="Perimeter Ring",
        description="Rooms around perimeter with central core. All rooms have exterior access.",
        best_for=["all_daylight", "open_core", "exhibition", "flexible_center"],
        typical_efficiency=0.65,
        min_aspect_ratio=0.9,
        max_aspect_ratio=1.3
    ),
}


@dataclass
class GeneratedScheme:
    """A complete generated design scheme."""
    scheme_id: str
    strategy: PlacementStrategy
    scheme_info: SchemeInfo
    placed_rooms: List[Dict[str, Any]]
    corridors: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    strengths: List[str]
    trade_offs: List[str]
    building_width: float
    building_depth: float
    building_type: str
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "scheme_id": self.scheme_id,
            "strategy": self.strategy.name,
            "scheme_name": self.scheme_info.name,
            "description": self.scheme_info.description,
            "placed_rooms": self.placed_rooms,
            "corridors": self.corridors,
            "metrics": self.metrics,
            "strengths": self.strengths,
            "trade_offs": self.trade_offs,
            "building_dimensions": {
                "width": self.building_width,
                "depth": self.building_depth,
                "area": self.building_width * self.building_depth
            },
            "building_type": self.building_type,
            "generated_at": self.generated_at
        }


class SchemeGenerator:
    """
    Generates multiple design schemes for comparison.

    Given a building program and footprint, generates N different
    schemes using appropriate placement strategies, then ranks
    them by quality metrics.
    """

    def __init__(self, building_width: float, building_depth: float,
                 building_type: str, entry_side: str = "south"):
        """
        Initialize scheme generator.

        Args:
            building_width: Total width in feet
            building_depth: Total depth in feet
            building_type: Type of building
            entry_side: Side with main entry
        """
        self.building_width = building_width
        self.building_depth = building_depth
        self.building_type = building_type.lower()
        self.entry_side = entry_side.lower()
        self.aspect_ratio = building_width / building_depth if building_depth > 0 else 1.0

    def generate_schemes(self, program: List[Dict[str, Any]],
                         count: int = 3) -> List[GeneratedScheme]:
        """
        Generate multiple design schemes.

        Args:
            program: List of room dicts with 'name', 'width', 'depth'
            count: Number of schemes to generate (default 3)

        Returns:
            List of GeneratedScheme objects, sorted by quality
        """
        # Select best strategies for this building
        strategies = self._select_strategies(program, count)

        schemes = []
        for i, strategy in enumerate(strategies):
            scheme = self._generate_single_scheme(program, strategy, i + 1)
            schemes.append(scheme)

        # Sort by overall quality (efficiency * adjacency)
        schemes.sort(
            key=lambda s: s.metrics.get("efficiency", 0) * s.metrics.get("adjacency_score", 0),
            reverse=True
        )

        return schemes

    def _select_strategies(self, program: List[Dict[str, Any]],
                           count: int) -> List[PlacementStrategy]:
        """Select best strategies for this building and program."""
        scored_strategies = []

        for strategy, info in SCHEME_TYPES.items():
            score = self._score_strategy_fit(strategy, info, program)
            scored_strategies.append((strategy, score))

        # Sort by score and take top N
        scored_strategies.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored_strategies[:count]]

    def _score_strategy_fit(self, strategy: PlacementStrategy,
                           info: SchemeInfo,
                           program: List[Dict[str, Any]]) -> float:
        """Score how well a strategy fits this building and program."""
        score = 50.0  # Base score

        # Aspect ratio compatibility
        if info.min_aspect_ratio <= self.aspect_ratio <= info.max_aspect_ratio:
            score += 20
        elif self.aspect_ratio < info.min_aspect_ratio:
            score -= 10 * (info.min_aspect_ratio - self.aspect_ratio)
        else:
            score -= 10 * (self.aspect_ratio - info.max_aspect_ratio)

        # Building type bonuses
        if self.building_type == "office":
            if strategy == PlacementStrategy.DOUBLE_LOADED:
                score += 15  # Most common for office
            elif strategy == PlacementStrategy.CLUSTER:
                score += 10  # Good for collaborative offices
        elif self.building_type == "residential":
            if strategy == PlacementStrategy.LINEAR:
                score += 10  # Good daylight for homes
            elif strategy == PlacementStrategy.L_SHAPE:
                score += 10  # Common residential form
        elif self.building_type == "healthcare":
            if strategy == PlacementStrategy.DOUBLE_LOADED:
                score += 20  # Standard healthcare layout
        elif self.building_type == "educational":
            if strategy == PlacementStrategy.DOUBLE_LOADED:
                score += 15  # Efficient for classrooms
            elif strategy == PlacementStrategy.CLUSTER:
                score += 10  # Good for learning communities

        # Program size considerations
        total_area = sum(r.get("width", 10) * r.get("depth", 10) for r in program)
        building_area = self.building_width * self.building_depth

        if total_area / building_area > 0.75:
            # Tight fit - efficiency matters
            score += 10 * info.typical_efficiency
        else:
            # More flexibility
            if strategy in [PlacementStrategy.U_SHAPE, PlacementStrategy.PERIMETER]:
                score += 5  # Can afford less efficient layouts

        return score

    def _generate_single_scheme(self, program: List[Dict[str, Any]],
                                strategy: PlacementStrategy,
                                scheme_number: int) -> GeneratedScheme:
        """Generate a single scheme with given strategy."""
        # Make unique room names if duplicates
        program_copy = self._make_unique_names(program)

        # Run placement
        result = place_floor_plan(
            self.building_width,
            self.building_depth,
            self.building_type,
            program_copy,
            strategy,
            self.entry_side
        )

        # Analyze strengths and trade-offs
        info = SCHEME_TYPES[strategy]
        strengths, trade_offs = self._analyze_scheme(result, info)

        scheme_id = f"{self.building_type[:3].upper()}-{strategy.name[:4]}-{scheme_number:02d}"

        return GeneratedScheme(
            scheme_id=scheme_id,
            strategy=strategy,
            scheme_info=info,
            placed_rooms=result["placed_rooms"],
            corridors=result["corridors"],
            metrics=result["metrics"],
            strengths=strengths,
            trade_offs=trade_offs,
            building_width=self.building_width,
            building_depth=self.building_depth,
            building_type=self.building_type,
            generated_at=datetime.now().isoformat()
        )

    def _make_unique_names(self, program: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Make room names unique by adding numbers to duplicates."""
        result = []
        name_counts = {}

        for room in program:
            room_copy = dict(room)
            name = room_copy["name"]

            if name in name_counts:
                name_counts[name] += 1
                room_copy["name"] = f"{name} {name_counts[name]}"
            else:
                name_counts[name] = 1

            result.append(room_copy)

        return result

    def _analyze_scheme(self, result: Dict[str, Any],
                       info: SchemeInfo) -> Tuple[List[str], List[str]]:
        """Analyze scheme for strengths and trade-offs."""
        strengths = []
        trade_offs = []
        metrics = result["metrics"]

        # Efficiency analysis
        efficiency = metrics.get("efficiency", 0)
        if efficiency >= 0.75:
            strengths.append(f"High space efficiency ({efficiency*100:.0f}%)")
        elif efficiency < 0.65:
            trade_offs.append(f"Lower efficiency ({efficiency*100:.0f}%) - more circulation")

        # Adjacency analysis
        adjacency = metrics.get("adjacency_score", 0)
        if adjacency >= 0.8:
            strengths.append(f"Excellent adjacency satisfaction ({adjacency*100:.0f}%)")
        elif adjacency < 0.5:
            trade_offs.append(f"Some adjacency compromises ({adjacency*100:.0f}%)")

        # Daylight analysis
        daylight = metrics.get("daylight_ratio", 0)
        if daylight >= 0.7:
            strengths.append(f"Good natural light access ({daylight*100:.0f}% rooms)")
        elif daylight < 0.4:
            trade_offs.append(f"Limited daylight ({daylight*100:.0f}% rooms on perimeter)")

        # Placement success
        success = metrics.get("placement_success", 0)
        if success >= 1.0:
            strengths.append("All rooms successfully placed")
        elif success < 0.9:
            trade_offs.append(f"Some rooms could not be placed ({success*100:.0f}%)")

        # Strategy-specific notes
        strengths.extend(info.best_for[:2])  # Add top 2 "best for" items

        return strengths, trade_offs

    def compare_schemes(self, schemes: List[GeneratedScheme]) -> Dict[str, Any]:
        """
        Create a comparison summary of multiple schemes.

        Returns dict with rankings by different criteria.
        """
        comparison = {
            "schemes_compared": len(schemes),
            "by_efficiency": [],
            "by_adjacency": [],
            "by_daylight": [],
            "by_overall": [],
            "recommendation": None,
            "recommendation_reason": ""
        }

        # Sort by different criteria
        by_efficiency = sorted(schemes,
                               key=lambda s: s.metrics.get("efficiency", 0),
                               reverse=True)
        by_adjacency = sorted(schemes,
                              key=lambda s: s.metrics.get("adjacency_score", 0),
                              reverse=True)
        by_daylight = sorted(schemes,
                             key=lambda s: s.metrics.get("daylight_ratio", 0),
                             reverse=True)

        # Overall = weighted combination
        def overall_score(s):
            e = s.metrics.get("efficiency", 0)
            a = s.metrics.get("adjacency_score", 0)
            d = s.metrics.get("daylight_ratio", 0)
            p = s.metrics.get("placement_success", 0)
            return (e * 0.3) + (a * 0.35) + (d * 0.2) + (p * 0.15)

        by_overall = sorted(schemes, key=overall_score, reverse=True)

        for s in by_efficiency:
            comparison["by_efficiency"].append({
                "scheme_id": s.scheme_id,
                "value": s.metrics.get("efficiency", 0)
            })
        for s in by_adjacency:
            comparison["by_adjacency"].append({
                "scheme_id": s.scheme_id,
                "value": s.metrics.get("adjacency_score", 0)
            })
        for s in by_daylight:
            comparison["by_daylight"].append({
                "scheme_id": s.scheme_id,
                "value": s.metrics.get("daylight_ratio", 0)
            })
        for s in by_overall:
            comparison["by_overall"].append({
                "scheme_id": s.scheme_id,
                "value": round(overall_score(s), 3)
            })

        # Recommendation
        if by_overall:
            best = by_overall[0]
            comparison["recommendation"] = best.scheme_id
            comparison["recommendation_reason"] = (
                f"{best.scheme_info.name} provides best overall balance with "
                f"{best.metrics.get('efficiency', 0)*100:.0f}% efficiency and "
                f"{best.metrics.get('adjacency_score', 0)*100:.0f}% adjacency satisfaction."
            )

        return comparison


def generate_design_schemes(building_width: float, building_depth: float,
                           building_type: str, program: List[Dict[str, Any]],
                           count: int = 3, entry_side: str = "south") -> Dict[str, Any]:
    """
    Convenience function to generate multiple design schemes.

    Args:
        building_width: Building width in feet
        building_depth: Building depth in feet
        building_type: Type of building
        program: List of room dicts
        count: Number of schemes to generate
        entry_side: Side with main entry

    Returns:
        Dict with schemes, comparison, and metadata
    """
    generator = SchemeGenerator(building_width, building_depth, building_type, entry_side)
    schemes = generator.generate_schemes(program, count)
    comparison = generator.compare_schemes(schemes)

    return {
        "building_type": building_type,
        "building_dimensions": {
            "width": building_width,
            "depth": building_depth,
            "area": building_width * building_depth
        },
        "program_rooms": len(program),
        "schemes": [s.to_dict() for s in schemes],
        "comparison": comparison,
        "generated_at": datetime.now().isoformat()
    }


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("Scheme Generator - Test Output")
    print("=" * 60)

    # Test office program
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

    print(f"Building: 80' x 50' Office")
    print(f"Program: {len(test_program)} rooms")
    print("\n" + "-" * 60)

    result = generate_design_schemes(80, 50, "office", test_program, count=3)

    print("\nGENERATED SCHEMES:")
    print("-" * 60)

    for scheme in result["schemes"]:
        print(f"\n{scheme['scheme_id']}: {scheme['scheme_name']}")
        print(f"  {scheme['description']}")
        print(f"\n  Metrics:")
        for key, value in scheme["metrics"].items():
            if isinstance(value, float):
                print(f"    {key}: {value:.1%}" if value <= 1 else f"    {key}: {value}")
            else:
                print(f"    {key}: {value}")
        print(f"\n  Strengths:")
        for s in scheme["strengths"]:
            print(f"    + {s}")
        print(f"  Trade-offs:")
        for t in scheme["trade_offs"]:
            print(f"    - {t}")

    print("\n" + "-" * 60)
    print("COMPARISON:")
    comp = result["comparison"]
    print(f"\n  By Overall Score:")
    for item in comp["by_overall"]:
        print(f"    {item['scheme_id']}: {item['value']:.3f}")

    print(f"\n  RECOMMENDATION: {comp['recommendation']}")
    print(f"  {comp['recommendation_reason']}")

    print("\n" + "=" * 60)
    print("Scheme Generator loaded successfully!")
