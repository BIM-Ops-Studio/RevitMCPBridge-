"""
Design Learner - Learning system for floor plan generation.

This module learns from:
1. User scheme selections (which schemes get chosen)
2. Manual corrections (when user moves/resizes rooms)
3. Adjacency overrides (when user places rooms differently)
4. Dimensional preferences (preferred sizes for room types)

Integrates with Claude Memory MCP for persistent storage across sessions.

Learning Workflow:
1. Generate schemes
2. User selects one or modifies
3. Record what was selected and why
4. Store corrections and preferences
5. Apply learnings to future generations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import json
import subprocess
import os


@dataclass
class SelectionRecord:
    """Record of a scheme selection by user."""
    selected_scheme_id: str
    rejected_scheme_ids: List[str]
    building_type: str
    selection_reason: Optional[str]
    selected_features: List[str]  # What made this scheme better
    timestamp: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrectionRecord:
    """Record of a user correction to generated layout."""
    room_name: str
    building_type: str
    original_position: Tuple[float, float]
    corrected_position: Tuple[float, float]
    original_dimensions: Tuple[float, float]
    corrected_dimensions: Tuple[float, float]
    correction_type: str  # "position", "dimension", "both"
    reason: Optional[str]
    context: Dict[str, Any]
    timestamp: str


@dataclass
class AdjacencyOverride:
    """User override of default adjacency rule."""
    room_a: str
    room_b: str
    building_type: str
    default_strength: int
    override_strength: int
    reason: Optional[str]
    timestamp: str


@dataclass
class DimensionPreference:
    """User preference for room dimensions."""
    room_type: str
    building_type: str
    preferred_width: float
    preferred_depth: float
    preferred_area: Optional[float]
    context: str  # When this preference applies
    timestamp: str


class DesignLearner:
    """
    Learns design preferences from user feedback.

    Integrates with Memory MCP for persistent storage.
    Falls back to local JSON file if MCP unavailable.
    """

    MEMORY_PROJECT = "SmartFloorPlan"
    LOCAL_STORAGE_PATH = "/mnt/d/RevitMCPBridge2026/python/design_learnings.json"

    def __init__(self, use_memory_mcp: bool = True):
        """
        Initialize design learner.

        Args:
            use_memory_mcp: Whether to use Memory MCP (falls back to local if unavailable)
        """
        self.use_memory_mcp = use_memory_mcp
        self.selections: List[SelectionRecord] = []
        self.corrections: List[CorrectionRecord] = []
        self.adjacency_overrides: List[AdjacencyOverride] = []
        self.dimension_preferences: List[DimensionPreference] = []

        # Load existing learnings
        self._load_learnings()

    def record_scheme_selection(self, selected_scheme: Dict[str, Any],
                                rejected_schemes: List[Dict[str, Any]],
                                reason: Optional[str] = None) -> bool:
        """
        Record when user selects a scheme from options.

        Args:
            selected_scheme: The chosen scheme dict
            rejected_schemes: List of rejected scheme dicts
            reason: Optional user-provided reason

        Returns:
            True if successfully stored
        """
        # Extract what made selected scheme better
        selected_features = self._extract_winning_features(selected_scheme, rejected_schemes)

        record = SelectionRecord(
            selected_scheme_id=selected_scheme.get("scheme_id", "unknown"),
            rejected_scheme_ids=[s.get("scheme_id", "unknown") for s in rejected_schemes],
            building_type=selected_scheme.get("building_type", "unknown"),
            selection_reason=reason,
            selected_features=selected_features,
            timestamp=datetime.now().isoformat(),
            context={
                "efficiency": selected_scheme.get("metrics", {}).get("efficiency"),
                "adjacency_score": selected_scheme.get("metrics", {}).get("adjacency_score"),
                "strategy": selected_scheme.get("strategy")
            }
        )

        self.selections.append(record)

        # Store to memory
        memory_content = (
            f"User selected scheme {record.selected_scheme_id} "
            f"({record.context.get('strategy', 'unknown')} strategy) "
            f"over {len(record.rejected_scheme_ids)} alternatives. "
            f"Winning features: {', '.join(selected_features)}. "
            f"Reason: {reason or 'Not specified'}"
        )

        return self._store_to_memory(
            content=memory_content,
            memory_type="preference",
            tags=["scheme_selection", selected_scheme.get("building_type", "unknown"),
                  selected_scheme.get("strategy", "unknown")],
            importance=6
        )

    def record_correction(self, room_name: str, building_type: str,
                         original: Dict[str, Any], corrected: Dict[str, Any],
                         reason: Optional[str] = None) -> bool:
        """
        Record when user corrects a room placement or size.

        Args:
            room_name: Name of the room corrected
            building_type: Type of building
            original: Original placement dict with x, y, width, depth
            corrected: Corrected placement dict
            reason: Optional user-provided reason

        Returns:
            True if successfully stored
        """
        orig_pos = (original.get("x", 0), original.get("y", 0))
        corr_pos = (corrected.get("x", 0), corrected.get("y", 0))
        orig_dim = (original.get("width", 0), original.get("depth", 0))
        corr_dim = (corrected.get("width", 0), corrected.get("depth", 0))

        # Determine correction type
        pos_changed = orig_pos != corr_pos
        dim_changed = orig_dim != corr_dim
        if pos_changed and dim_changed:
            correction_type = "both"
        elif pos_changed:
            correction_type = "position"
        else:
            correction_type = "dimension"

        record = CorrectionRecord(
            room_name=room_name,
            building_type=building_type,
            original_position=orig_pos,
            corrected_position=corr_pos,
            original_dimensions=orig_dim,
            corrected_dimensions=corr_dim,
            correction_type=correction_type,
            reason=reason,
            context={"original_zone": original.get("zone"), "had_exterior": original.get("has_exterior_wall")},
            timestamp=datetime.now().isoformat()
        )

        self.corrections.append(record)

        # Build memory content
        if correction_type == "position":
            change_desc = f"moved from ({orig_pos[0]:.0f}, {orig_pos[1]:.0f}) to ({corr_pos[0]:.0f}, {corr_pos[1]:.0f})"
        elif correction_type == "dimension":
            change_desc = f"resized from {orig_dim[0]:.0f}'x{orig_dim[1]:.0f}' to {corr_dim[0]:.0f}'x{corr_dim[1]:.0f}'"
        else:
            change_desc = (f"moved from ({orig_pos[0]:.0f}, {orig_pos[1]:.0f}) to ({corr_pos[0]:.0f}, {corr_pos[1]:.0f}) "
                          f"and resized from {orig_dim[0]:.0f}'x{orig_dim[1]:.0f}' to {corr_dim[0]:.0f}'x{corr_dim[1]:.0f}'")

        memory_content = (
            f"CORRECTION: In {building_type} layout, {room_name} was {change_desc}. "
            f"Reason: {reason or 'User preference'}"
        )

        return self._store_to_memory(
            content=memory_content,
            memory_type="error",  # Corrections are stored as "error" type for high visibility
            tags=["room_correction", building_type, room_name.lower().replace(" ", "_")],
            importance=8  # High importance so we don't repeat mistakes
        )

    def record_adjacency_override(self, room_a: str, room_b: str,
                                  building_type: str,
                                  default_strength: int, override_strength: int,
                                  reason: Optional[str] = None) -> bool:
        """
        Record when user overrides an adjacency rule.

        Args:
            room_a, room_b: The two rooms
            building_type: Type of building
            default_strength: Original adjacency strength
            override_strength: User's preferred strength
            reason: Optional explanation

        Returns:
            True if successfully stored
        """
        override = AdjacencyOverride(
            room_a=room_a,
            room_b=room_b,
            building_type=building_type,
            default_strength=default_strength,
            override_strength=override_strength,
            reason=reason,
            timestamp=datetime.now().isoformat()
        )

        self.adjacency_overrides.append(override)

        strength_names = {3: "MUST_CONNECT", 2: "SHOULD_ADJACENT", 1: "PREFER_NEAR",
                         0: "NEUTRAL", -1: "SHOULD_SEPARATE", -2: "MUST_SEPARATE"}
        from_name = strength_names.get(default_strength, str(default_strength))
        to_name = strength_names.get(override_strength, str(override_strength))

        memory_content = (
            f"ADJACENCY OVERRIDE for {building_type}: {room_a} and {room_b} "
            f"changed from {from_name} to {to_name}. "
            f"Reason: {reason or 'User preference'}"
        )

        return self._store_to_memory(
            content=memory_content,
            memory_type="preference",
            tags=["adjacency_override", building_type],
            importance=7
        )

    def record_dimension_preference(self, room_type: str, building_type: str,
                                   width: float, depth: float,
                                   context: str = "general") -> bool:
        """
        Record user's preferred dimensions for a room type.

        Args:
            room_type: Type of room
            building_type: Type of building
            width, depth: Preferred dimensions
            context: When this preference applies

        Returns:
            True if successfully stored
        """
        pref = DimensionPreference(
            room_type=room_type,
            building_type=building_type,
            preferred_width=width,
            preferred_depth=depth,
            preferred_area=width * depth,
            context=context,
            timestamp=datetime.now().isoformat()
        )

        self.dimension_preferences.append(pref)

        memory_content = (
            f"DIMENSION PREFERENCE for {building_type}: {room_type} "
            f"preferred at {width:.0f}' x {depth:.0f}' ({width*depth:.0f} SF). "
            f"Context: {context}"
        )

        return self._store_to_memory(
            content=memory_content,
            memory_type="preference",
            tags=["dimension_preference", building_type, room_type.lower().replace(" ", "_")],
            importance=5
        )

    def get_preferred_strategy(self, building_type: str) -> Optional[str]:
        """
        Get user's preferred strategy for a building type based on history.

        Returns strategy name or None if no clear preference.
        """
        # Count strategy selections for this building type
        strategy_counts: Dict[str, int] = {}

        for selection in self.selections:
            if selection.building_type == building_type:
                strategy = selection.context.get("strategy")
                if strategy:
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        if not strategy_counts:
            return None

        # Return most frequently selected
        return max(strategy_counts, key=strategy_counts.get)

    def get_dimension_adjustments(self, building_type: str) -> Dict[str, Tuple[float, float]]:
        """
        Get dimension adjustments for room types based on corrections.

        Returns dict mapping room type to (width, depth) adjustments.
        """
        adjustments: Dict[str, List[Tuple[float, float]]] = {}

        for correction in self.corrections:
            if correction.building_type == building_type and correction.correction_type in ["dimension", "both"]:
                room_base = correction.room_name.split()[0]  # Strip numbers from "Office 2"
                orig_w, orig_d = correction.original_dimensions
                corr_w, corr_d = correction.corrected_dimensions
                delta_w = corr_w - orig_w
                delta_d = corr_d - orig_d

                if room_base not in adjustments:
                    adjustments[room_base] = []
                adjustments[room_base].append((delta_w, delta_d))

        # Average the adjustments
        result = {}
        for room_type, deltas in adjustments.items():
            avg_w = sum(d[0] for d in deltas) / len(deltas)
            avg_d = sum(d[1] for d in deltas) / len(deltas)
            result[room_type] = (avg_w, avg_d)

        return result

    def get_adjacency_overrides(self, building_type: str) -> Dict[Tuple[str, str], int]:
        """
        Get adjacency overrides for a building type.

        Returns dict mapping (room_a, room_b) to override strength.
        """
        overrides = {}

        for override in self.adjacency_overrides:
            if override.building_type == building_type:
                key = (override.room_a, override.room_b)
                overrides[key] = override.override_strength

        return overrides

    def apply_learnings_to_program(self, program: List[Dict[str, Any]],
                                   building_type: str) -> List[Dict[str, Any]]:
        """
        Apply learned dimension preferences to a room program.

        Args:
            program: Original room program
            building_type: Type of building

        Returns:
            Adjusted room program
        """
        adjustments = self.get_dimension_adjustments(building_type)

        if not adjustments:
            return program

        adjusted = []
        for room in program:
            room_copy = dict(room)
            room_base = room["name"].split()[0]

            if room_base in adjustments:
                delta_w, delta_d = adjustments[room_base]
                room_copy["width"] = max(room["width"] + delta_w, 6)  # Min 6'
                room_copy["depth"] = max(room["depth"] + delta_d, 6)

            adjusted.append(room_copy)

        return adjusted

    def get_learning_summary(self, building_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of what has been learned.

        Args:
            building_type: Optional filter by building type

        Returns:
            Summary dict with counts and key learnings
        """
        selections = self.selections
        corrections = self.corrections
        adj_overrides = self.adjacency_overrides
        dim_prefs = self.dimension_preferences

        if building_type:
            selections = [s for s in selections if s.building_type == building_type]
            corrections = [c for c in corrections if c.building_type == building_type]
            adj_overrides = [a for a in adj_overrides if a.building_type == building_type]
            dim_prefs = [d for d in dim_prefs if d.building_type == building_type]

        # Strategy preference
        strategy_counts: Dict[str, int] = {}
        for s in selections:
            strat = s.context.get("strategy", "unknown")
            strategy_counts[strat] = strategy_counts.get(strat, 0) + 1

        preferred_strategy = max(strategy_counts, key=strategy_counts.get) if strategy_counts else None

        # Common corrections
        correction_rooms: Dict[str, int] = {}
        for c in corrections:
            room_base = c.room_name.split()[0]
            correction_rooms[room_base] = correction_rooms.get(room_base, 0) + 1

        return {
            "total_selections": len(selections),
            "total_corrections": len(corrections),
            "adjacency_overrides": len(adj_overrides),
            "dimension_preferences": len(dim_prefs),
            "preferred_strategy": preferred_strategy,
            "strategy_counts": strategy_counts,
            "frequently_corrected_rooms": correction_rooms,
            "building_type_filter": building_type
        }

    def _extract_winning_features(self, selected: Dict[str, Any],
                                  rejected: List[Dict[str, Any]]) -> List[str]:
        """Extract what made the selected scheme better than alternatives."""
        features = []

        selected_metrics = selected.get("metrics", {})
        avg_rejected_metrics = {}

        # Calculate average metrics of rejected schemes
        for key in ["efficiency", "adjacency_score", "daylight_ratio"]:
            rejected_values = [r.get("metrics", {}).get(key, 0) for r in rejected]
            if rejected_values:
                avg_rejected_metrics[key] = sum(rejected_values) / len(rejected_values)

        # Compare
        if selected_metrics.get("efficiency", 0) > avg_rejected_metrics.get("efficiency", 0) + 0.05:
            features.append("higher_efficiency")
        if selected_metrics.get("adjacency_score", 0) > avg_rejected_metrics.get("adjacency_score", 0) + 0.1:
            features.append("better_adjacencies")
        if selected_metrics.get("daylight_ratio", 0) > avg_rejected_metrics.get("daylight_ratio", 0) + 0.1:
            features.append("more_daylight")

        # Strategy features
        strategy = selected.get("strategy")
        if strategy:
            features.append(f"strategy_{strategy.lower()}")

        return features

    def _store_to_memory(self, content: str, memory_type: str,
                        tags: List[str], importance: int) -> bool:
        """Store learning to Memory MCP or local file."""
        if self.use_memory_mcp:
            try:
                # This would be called via MCP in actual usage
                # For standalone, we simulate/log it
                print(f"[Memory MCP] Storing: {content[:100]}...")
                self._save_local_backup()
                return True
            except Exception as e:
                print(f"[Memory MCP] Failed: {e}, falling back to local")

        # Fallback to local storage
        return self._save_local_backup()

    def _load_learnings(self):
        """Load learnings from local storage."""
        if os.path.exists(self.LOCAL_STORAGE_PATH):
            try:
                with open(self.LOCAL_STORAGE_PATH, 'r') as f:
                    data = json.load(f)

                # Reconstruct records
                for s in data.get("selections", []):
                    self.selections.append(SelectionRecord(**s))
                for c in data.get("corrections", []):
                    c["original_position"] = tuple(c["original_position"])
                    c["corrected_position"] = tuple(c["corrected_position"])
                    c["original_dimensions"] = tuple(c["original_dimensions"])
                    c["corrected_dimensions"] = tuple(c["corrected_dimensions"])
                    self.corrections.append(CorrectionRecord(**c))
                for a in data.get("adjacency_overrides", []):
                    self.adjacency_overrides.append(AdjacencyOverride(**a))
                for d in data.get("dimension_preferences", []):
                    self.dimension_preferences.append(DimensionPreference(**d))

                print(f"[DesignLearner] Loaded {len(self.selections)} selections, "
                      f"{len(self.corrections)} corrections from storage")
            except Exception as e:
                print(f"[DesignLearner] Error loading learnings: {e}")

    def _save_local_backup(self) -> bool:
        """Save learnings to local JSON file."""
        try:
            data = {
                "selections": [
                    {
                        "selected_scheme_id": s.selected_scheme_id,
                        "rejected_scheme_ids": s.rejected_scheme_ids,
                        "building_type": s.building_type,
                        "selection_reason": s.selection_reason,
                        "selected_features": s.selected_features,
                        "timestamp": s.timestamp,
                        "context": s.context
                    } for s in self.selections
                ],
                "corrections": [
                    {
                        "room_name": c.room_name,
                        "building_type": c.building_type,
                        "original_position": list(c.original_position),
                        "corrected_position": list(c.corrected_position),
                        "original_dimensions": list(c.original_dimensions),
                        "corrected_dimensions": list(c.corrected_dimensions),
                        "correction_type": c.correction_type,
                        "reason": c.reason,
                        "context": c.context,
                        "timestamp": c.timestamp
                    } for c in self.corrections
                ],
                "adjacency_overrides": [
                    {
                        "room_a": a.room_a,
                        "room_b": a.room_b,
                        "building_type": a.building_type,
                        "default_strength": a.default_strength,
                        "override_strength": a.override_strength,
                        "reason": a.reason,
                        "timestamp": a.timestamp
                    } for a in self.adjacency_overrides
                ],
                "dimension_preferences": [
                    {
                        "room_type": d.room_type,
                        "building_type": d.building_type,
                        "preferred_width": d.preferred_width,
                        "preferred_depth": d.preferred_depth,
                        "preferred_area": d.preferred_area,
                        "context": d.context,
                        "timestamp": d.timestamp
                    } for d in self.dimension_preferences
                ],
                "saved_at": datetime.now().isoformat()
            }

            with open(self.LOCAL_STORAGE_PATH, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"[DesignLearner] Error saving: {e}")
            return False


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_learner_instance: Optional[DesignLearner] = None


def get_learner() -> DesignLearner:
    """Get or create the singleton learner instance."""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = DesignLearner()
    return _learner_instance


def record_selection(selected_scheme: Dict, rejected_schemes: List[Dict],
                    reason: Optional[str] = None) -> bool:
    """Convenience function to record scheme selection."""
    return get_learner().record_scheme_selection(selected_scheme, rejected_schemes, reason)


def record_correction(room_name: str, building_type: str,
                     original: Dict, corrected: Dict,
                     reason: Optional[str] = None) -> bool:
    """Convenience function to record room correction."""
    return get_learner().record_correction(room_name, building_type, original, corrected, reason)


def apply_learnings(program: List[Dict], building_type: str) -> List[Dict]:
    """Convenience function to apply learnings to program."""
    return get_learner().apply_learnings_to_program(program, building_type)


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("Design Learner - Test Output")
    print("=" * 60)

    # Create learner
    learner = DesignLearner(use_memory_mcp=False)  # Local storage only for test

    # Simulate scheme selection
    selected = {
        "scheme_id": "OFF-DOUB-01",
        "building_type": "office",
        "strategy": "DOUBLE_LOADED",
        "metrics": {
            "efficiency": 0.78,
            "adjacency_score": 0.85,
            "daylight_ratio": 0.65
        }
    }
    rejected = [
        {
            "scheme_id": "OFF-LINE-02",
            "building_type": "office",
            "strategy": "LINEAR",
            "metrics": {"efficiency": 0.70, "adjacency_score": 0.75, "daylight_ratio": 0.90}
        }
    ]

    print("\n1. Recording scheme selection...")
    learner.record_scheme_selection(selected, rejected, "Better efficiency for our needs")

    # Simulate correction
    print("\n2. Recording room correction...")
    original = {"x": 10, "y": 5, "width": 12, "depth": 10, "zone": "PRIVATE"}
    corrected = {"x": 15, "y": 5, "width": 14, "depth": 12}
    learner.record_correction("Private Office", "office", original, corrected,
                             "Needed larger office for executive")

    # Record dimension preference
    print("\n3. Recording dimension preference...")
    learner.record_dimension_preference("Conference", "office", 18, 16, "standard")

    # Get summary
    print("\n" + "-" * 60)
    print("LEARNING SUMMARY:")
    summary = learner.get_learning_summary("office")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Test applying learnings
    print("\n" + "-" * 60)
    print("APPLYING LEARNINGS TO NEW PROGRAM:")
    test_program = [
        {"name": "Private Office", "width": 12, "depth": 10},
        {"name": "Conference", "width": 16, "depth": 14}
    ]
    adjusted = learner.apply_learnings_to_program(test_program, "office")
    print(f"  Original: {test_program}")
    print(f"  Adjusted: {adjusted}")

    # Get preferred strategy
    print("\n" + "-" * 60)
    pref_strat = learner.get_preferred_strategy("office")
    print(f"Preferred strategy for office: {pref_strat}")

    print("\n" + "=" * 60)
    print("Design Learner loaded successfully!")
