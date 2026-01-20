#!/usr/bin/env python3
"""Create walls in Revit from Florida 1713 floor plan extraction"""
import json
import sys
import win32file
import pywintypes

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# Wall data from floor-plan-vision extraction (page 4)
# Scale: 1/2" = 1'-0" (24 scale factor)
# PDF points to feet: pdf_units / 72 * 24 = feet
# But we need to normalize - PDF origin is top-left, Revit is bottom-left
# Also need to center the model around origin

WALLS_DATA = [
    # Format: (start_x, start_y, end_x, end_y, thickness, wall_type)
    # Exterior walls first
    {"start": {"x": 1404.12, "y": 366.18}, "end": {"x": 1603.56, "y": 366.90}, "thickness": 17.4, "type": "exterior"},
    {"start": {"x": 1591.92, "y": 919.56}, "end": {"x": 1591.92, "y": 775.68}, "thickness": 17.04, "type": "exterior"},
    {"start": {"x": 1397.16, "y": 964.14}, "end": {"x": 1757.28, "y": 962.52}, "thickness": 14.64, "type": "exterior"},
    {"start": {"x": 1404.84, "y": 471.00}, "end": {"x": 1404.84, "y": 619.32}, "thickness": 16.08, "type": "exterior"},
    {"start": {"x": 1841.99, "y": 550.08}, "end": {"x": 1841.99, "y": 357.48}, "thickness": 0.75, "type": "exterior"},
    {"start": {"x": 1603.08, "y": 357.48}, "end": {"x": 1396.80, "y": 357.48}, "thickness": 0.75, "type": "exterior"},
    {"start": {"x": 1412.16, "y": 955.20}, "end": {"x": 1412.16, "y": 784.68}, "thickness": 0.75, "type": "exterior"},
    {"start": {"x": 1396.80, "y": 729.96}, "end": {"x": 1396.80, "y": 970.56}, "thickness": 0.75, "type": "exterior"},
    {"start": {"x": 1826.64, "y": 625.56}, "end": {"x": 1825.92, "y": 714.84}, "thickness": 0.75, "type": "exterior"},
    # Interior walls
    {"start": {"x": 1411.80, "y": 780.54}, "end": {"x": 1596.36, "y": 781.50}, "thickness": 6.36, "type": "interior"},
    {"start": {"x": 1600.74, "y": 621.96}, "end": {"x": 1600.74, "y": 955.92}, "thickness": 6.84, "type": "interior"},
    {"start": {"x": 1487.34, "y": 392.52}, "end": {"x": 1483.68, "y": 556.32}, "thickness": 7.32, "type": "interior"},
    {"start": {"x": 1412.16, "y": 559.50}, "end": {"x": 1603.44, "y": 556.32}, "thickness": 7.68, "type": "interior"},
    {"start": {"x": 1603.80, "y": 850.38}, "end": {"x": 1645.98, "y": 851.34}, "thickness": 6.36, "type": "interior"},
    {"start": {"x": 1646.94, "y": 850.38}, "end": {"x": 1645.98, "y": 955.56}, "thickness": 6.36, "type": "interior"},
    {"start": {"x": 1679.58, "y": 718.74}, "end": {"x": 1827.00, "y": 719.70}, "thickness": 8.04, "type": "interior"},
    {"start": {"x": 1610.40, "y": 469.32}, "end": {"x": 1606.50, "y": 619.20}, "thickness": 6.24, "type": "interior"},
    {"start": {"x": 1603.44, "y": 475.68}, "end": {"x": 1603.44, "y": 556.32}, "thickness": 6.96, "type": "interior"},
]

def call_mcp(method, params=None):
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None, win32file.OPEN_EXISTING, 0, None
        )
        request = {"method": method, "params": params or {}}
        message = json.dumps(request) + '\n'
        win32file.WriteFile(handle, message.encode('utf-8'))

        response_data = b''
        while True:
            result, chunk = win32file.ReadFile(handle, 64 * 1024)
            response_data += chunk
            if b'\n' in chunk or len(chunk) == 0:
                break

        win32file.CloseHandle(handle)
        return json.loads(response_data.decode('utf-8').strip())
    except Exception as e:
        return {"success": False, "error": str(e)}

def pdf_to_revit(x, y, pdf_width=2592, pdf_height=1728):
    """Convert PDF coordinates to Revit feet.

    PDF: origin top-left, units = points (72/inch)
    Scale: 1/2" = 1'-0" means 24 PDF points = 1 foot (0.5" on paper * 24 scale = 12" real)
    Actually: 72 points = 1 inch on PDF, and 1/2" = 1' means 36 points = 1 foot

    Let's simplify: at 1/2" = 1'-0" scale, the drawing is half-size
    So 1 inch on PDF = 2 feet in reality
    72 points = 2 feet
    1 point = 2/72 feet = 1/36 feet
    """
    # Center the drawing around origin
    center_x = pdf_width / 2
    center_y = pdf_height / 2

    # Convert: PDF point to feet at 1/2" = 1'-0" scale
    # 72 points = 1 inch on paper, 1/2" on paper = 1' real, so 36 points = 1 foot
    scale_factor = 1 / 36.0

    revit_x = (x - center_x) * scale_factor
    # Flip Y axis (PDF is top-down, Revit is bottom-up)
    revit_y = (center_y - y) * scale_factor

    return revit_x, revit_y

def create_walls():
    # Wall type IDs from Revit
    EXTERIOR_WALL_TYPE = 441515  # Exterior - Wood Siding on Wood Stud (0.6' = 7.25")
    INTERIOR_WALL_TYPE = 441519  # Interior - 4 1/2" Partition

    # Level ID for L1
    LEVEL_ID = 30

    # Wall height
    HEIGHT = 10.0  # 10 feet

    walls_created = []
    errors = []

    print(f"Creating {len(WALLS_DATA)} walls...")

    for i, wall in enumerate(WALLS_DATA):
        # Convert coordinates
        start_x, start_y = pdf_to_revit(wall["start"]["x"], wall["start"]["y"])
        end_x, end_y = pdf_to_revit(wall["end"]["x"], wall["end"]["y"])

        # Select wall type
        wall_type_id = EXTERIOR_WALL_TYPE if wall["type"] == "exterior" else INTERIOR_WALL_TYPE

        # Create wall - use startPoint/endPoint arrays as expected by CreateWallByPoints
        params = {
            "startPoint": [start_x, start_y, 0.0],  # [x, y, z]
            "endPoint": [end_x, end_y, 0.0],        # [x, y, z]
            "levelId": LEVEL_ID,
            "height": HEIGHT,
            "wallTypeId": wall_type_id
        }

        result = call_mcp("createWallByPoints", params)  # Correct method name

        if result.get("success"):
            walls_created.append({
                "index": i,
                "wallId": result.get("wallId"),
                "type": wall["type"],
                "start": (start_x, start_y),
                "end": (end_x, end_y)
            })
            print(f"  Wall {i+1}: Created (ID: {result.get('wallId')})")
        else:
            errors.append({
                "index": i,
                "error": result.get("error"),
                "params": params
            })
            print(f"  Wall {i+1}: ERROR - {result.get('error')}")

    return {
        "success": len(errors) == 0,
        "walls_created": len(walls_created),
        "errors": len(errors),
        "details": walls_created,
        "error_details": errors
    }

if __name__ == "__main__":
    result = create_walls()
    print("\n" + "="*50)
    print(f"Result: {result['walls_created']} walls created, {result['errors']} errors")
    print(json.dumps(result, indent=2))
