"""
RevitMCP - Core client library for RevitMCPBridge2026
Provides a clean Python interface to the Revit API via MCP.

Usage:
    from core.revit_mcp import RevitMCP

    revit = RevitMCP()
    levels = revit.get_levels()
    walls = revit.create_walls([...])
"""

import subprocess
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Point:
    """3D point representation"""
    x: float
    y: float
    z: float = 0.0

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass
class Wall:
    """Wall element data"""
    id: int
    start: Point
    end: Point
    height: float
    wall_type: str
    level_id: int


@dataclass
class Room:
    """Room element data"""
    id: int
    name: str
    number: str
    area: float
    level: str


class RevitMCPError(Exception):
    """Exception raised for MCP errors"""
    pass


class RevitMCP:
    """
    Main client class for interacting with Revit via MCP Bridge.

    Example:
        revit = RevitMCP()

        # Get all levels
        levels = revit.get_levels()

        # Create a wall
        wall = revit.create_wall(
            start=(0, 0),
            end=(20, 0),
            height=10,
            level_id=levels[0]['id']
        )
    """

    def __init__(self, pipe_name: str = "RevitMCPBridge2026", timeout: int = 30):
        self.pipe_name = pipe_name
        self.timeout = timeout
        self._last_error = None

    def _send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send a request to the MCP server and return the response."""
        request = {"method": method}
        if params:
            request["params"] = params

        ps_script = f'''
$pipeName = '{self.pipe_name}'
$request = @'
{json.dumps(request)}
'@
try {{
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect({self.timeout * 1000})
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.WriteLine($request)
    $writer.Flush()
    $response = $reader.ReadLine()
    $pipe.Close()
    Write-Output $response
}} catch {{
    Write-Output ('{{"success": false, "error": "' + $_.Exception.Message + '"}}')
}}
'''

        result = subprocess.run(
            ['powershell.exe', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=self.timeout + 5
        )

        output = result.stdout.strip()
        json_start = output.find('{')
        if json_start >= 0:
            output = output[json_start:]

        try:
            response = json.loads(output)
        except json.JSONDecodeError:
            raise RevitMCPError(f"Invalid JSON response: {output[:200]}")

        if not response.get("success", False):
            self._last_error = response.get("error", "Unknown error")
            raise RevitMCPError(self._last_error)

        return response

    def call(self, method: str, **params) -> Dict[str, Any]:
        """Generic method caller for any MCP method."""
        return self._send_request(method, params if params else None)

    # ==================== LEVELS ====================

    def get_levels(self) -> List[Dict]:
        """Get all levels in the project."""
        result = self._send_request("getLevels")
        # Handle both nested and flat response formats
        levels = result.get("levels", result.get("result", {}).get("levels", []))
        # Normalize field names (levelId -> id)
        for level in levels:
            if "levelId" in level and "id" not in level:
                level["id"] = level["levelId"]
        return levels

    def create_level(self, name: str, elevation: float) -> Dict:
        """Create a new level."""
        return self._send_request("createLevel", {
            "name": name,
            "elevation": elevation
        })

    # ==================== WALLS ====================

    def get_walls(self) -> List[Dict]:
        """Get all walls in the project."""
        result = self._send_request("getWalls")
        return result.get("result", {}).get("walls", [])

    def get_wall_types(self) -> List[Dict]:
        """Get all available wall types."""
        result = self._send_request("getWallTypes")
        # Handle both nested and flat response formats
        types = result.get("wallTypes", result.get("result", {}).get("wallTypes", []))
        # Normalize field names (wallTypeId -> id)
        for t in types:
            if "wallTypeId" in t and "id" not in t:
                t["id"] = t["wallTypeId"]
        return types

    def create_wall(self, start: Tuple[float, float], end: Tuple[float, float],
                    height: float, level_id: int, wall_type_id: Optional[int] = None) -> Dict:
        """Create a single wall."""
        params = {
            "startPoint": {"x": start[0], "y": start[1], "z": 0},
            "endPoint": {"x": end[0], "y": end[1], "z": 0},
            "height": height,
            "levelId": level_id
        }
        if wall_type_id:
            params["wallTypeId"] = wall_type_id
        return self._send_request("createWall", params)

    def create_walls_batch(self, walls: List[Dict]) -> Dict:
        """Create multiple walls at once.

        Each wall dict should have: startPoint, endPoint, height, levelId
        """
        return self._send_request("createWalls", {"walls": walls})

    def create_rectangular_room(self, x: float, y: float, width: float, depth: float,
                                 height: float, level_id: int, wall_type_id: Optional[int] = None) -> List[Dict]:
        """Create 4 walls forming a rectangular room."""
        walls = [
            {"start": (x, y), "end": (x + width, y)},           # Bottom
            {"start": (x + width, y), "end": (x + width, y + depth)},  # Right
            {"start": (x + width, y + depth), "end": (x, y + depth)},  # Top
            {"start": (x, y + depth), "end": (x, y)}            # Left
        ]

        results = []
        for wall in walls:
            result = self.create_wall(
                start=wall["start"],
                end=wall["end"],
                height=height,
                level_id=level_id,
                wall_type_id=wall_type_id
            )
            results.append(result)
            time.sleep(0.1)

        return results

    # ==================== ROOMS ====================

    def get_rooms(self) -> List[Dict]:
        """Get all rooms in the project."""
        result = self._send_request("getRooms")
        return result.get("result", {}).get("rooms", [])

    def create_room(self, level_id: int, location: Tuple[float, float],
                    name: Optional[str] = None, number: Optional[str] = None) -> Dict:
        """Create a room at a location."""
        params = {
            "levelId": level_id,
            "location": {"x": location[0], "y": location[1]}
        }
        if name:
            params["name"] = name
        if number:
            params["number"] = number
        return self._send_request("createRoom", params)

    # ==================== DOORS & WINDOWS ====================

    def get_door_types(self) -> List[Dict]:
        """Get all available door types."""
        result = self._send_request("getDoorTypes")
        return result.get("result", {}).get("doorTypes", [])

    def get_window_types(self) -> List[Dict]:
        """Get all available window types."""
        result = self._send_request("getWindowTypes")
        return result.get("result", {}).get("windowTypes", [])

    def place_door(self, wall_id: int, location: Tuple[float, float, float],
                   door_type_id: int) -> Dict:
        """Place a door in a wall."""
        return self._send_request("placeDoor", {
            "wallId": wall_id,
            "location": {"x": location[0], "y": location[1], "z": location[2]},
            "doorTypeId": door_type_id
        })

    def place_window(self, wall_id: int, location: Tuple[float, float, float],
                     window_type_id: int) -> Dict:
        """Place a window in a wall."""
        return self._send_request("placeWindow", {
            "wallId": wall_id,
            "location": {"x": location[0], "y": location[1], "z": location[2]},
            "windowTypeId": window_type_id
        })

    # ==================== VIEWS ====================

    def get_views(self, view_type: Optional[str] = None) -> List[Dict]:
        """Get all views, optionally filtered by type."""
        params = {}
        if view_type:
            params["viewType"] = view_type
        result = self._send_request("getViews", params if params else None)
        return result.get("result", {}).get("views", [])

    def create_floor_plan(self, level_id: int, name: Optional[str] = None) -> Dict:
        """Create a floor plan view for a level."""
        params = {"levelId": level_id}
        if name:
            params["viewName"] = name
        return self._send_request("createFloorPlan", params)

    def set_active_view(self, view_id: int) -> Dict:
        """Set the active view in Revit."""
        return self._send_request("setActiveView", {"viewId": view_id})

    def zoom_to_fit(self, view_id: Optional[int] = None) -> Dict:
        """Zoom to fit in current or specified view."""
        params = {}
        if view_id:
            params["viewId"] = view_id
        return self._send_request("zoomToFit", params if params else None)

    # ==================== SHEETS ====================

    def get_sheets(self) -> List[Dict]:
        """Get all sheets in the project."""
        result = self._send_request("getAllSheets")
        return result.get("result", {}).get("sheets", [])

    def create_sheet(self, number: str, name: str,
                     title_block_id: Optional[int] = None) -> Dict:
        """Create a new sheet."""
        params = {"sheetNumber": number, "sheetName": name}
        if title_block_id:
            params["titleBlockId"] = title_block_id
        return self._send_request("createSheet", params)

    def place_view_on_sheet(self, sheet_id: int, view_id: int,
                            location: Tuple[float, float]) -> Dict:
        """Place a view on a sheet."""
        return self._send_request("placeViewOnSheet", {
            "sheetId": sheet_id,
            "viewId": view_id,
            "location": [location[0], location[1]]
        })

    # ==================== FAMILIES ====================

    def get_family_types(self, category: Optional[str] = None) -> List[Dict]:
        """Get available family types, optionally filtered by category."""
        params = {}
        if category:
            params["category"] = category
        result = self._send_request("getFamilyTypes", params if params else None)
        return result.get("result", {}).get("familyTypes", [])

    def place_family_instance(self, family_type_id: int,
                               location: Tuple[float, float, float],
                               level_id: int,
                               rotation: float = 0.0) -> Dict:
        """Place a family instance."""
        return self._send_request("placeFamilyInstance", {
            "familyTypeId": family_type_id,
            "location": {"x": location[0], "y": location[1], "z": location[2]},
            "levelId": level_id,
            "rotation": rotation
        })

    # ==================== SCHEDULES ====================

    def get_schedules(self) -> List[Dict]:
        """Get all schedules in the project."""
        result = self._send_request("getSchedules")
        return result.get("result", {}).get("schedules", [])

    def create_schedule(self, name: str, category: str,
                        fields: Optional[List[str]] = None) -> Dict:
        """Create a new schedule."""
        params = {"scheduleName": name, "category": category}
        if fields:
            params["fields"] = fields
        return self._send_request("createSchedule", params)

    def export_schedule_to_csv(self, schedule_id: int, file_path: str) -> Dict:
        """Export a schedule to CSV."""
        return self._send_request("exportScheduleToCSV", {
            "scheduleId": schedule_id,
            "filePath": file_path
        })

    # ==================== PARAMETERS ====================

    def get_element_parameters(self, element_id: int) -> List[Dict]:
        """Get all parameters for an element."""
        result = self._send_request("getElementParameters", {"elementId": element_id})
        return result.get("result", {}).get("parameters", [])

    def set_parameter(self, element_id: int, parameter_name: str, value: Any) -> Dict:
        """Set a parameter value on an element."""
        return self._send_request("setParameter", {
            "elementId": element_id,
            "parameterName": parameter_name,
            "value": value
        })

    # ==================== UTILITY ====================

    def delete_element(self, element_id: int) -> Dict:
        """Delete an element by ID."""
        return self._send_request("deleteElement", {"elementId": element_id})

    def delete_elements(self, element_ids: List[int]) -> Dict:
        """Delete multiple elements."""
        return self._send_request("deleteElements", {"elementIds": element_ids})

    def get_project_info(self) -> Dict:
        """Get project information."""
        return self._send_request("getProjectInfo")

    def get_active_view(self) -> Dict:
        """Get the currently active view."""
        return self._send_request("getActiveView")


# Convenience function for quick scripts
def connect() -> RevitMCP:
    """Quick connection to Revit MCP."""
    return RevitMCP()
