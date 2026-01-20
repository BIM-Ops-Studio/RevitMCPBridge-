#!/usr/bin/env python3
"""Send structural walls to Revit, forcing Revit to be idle via mouse clicks."""

import json
import struct
import time
import sys

try:
    import pyautogui
    import win32gui
    import win32file
    HAVE_GUI = True
except ImportError:
    HAVE_GUI = False
    print("Note: pyautogui not available, will not auto-click Revit")

PIPE_PATH = r"\\.\pipe\RevitMCPBridge2026"


def click_revit_window():
    """Find Revit window and click in it to trigger idle."""
    if not HAVE_GUI:
        return False

    def enum_windows_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Autodesk Revit" in title:
                results.append((hwnd, title))
        return True

    results = []
    win32gui.EnumWindows(enum_windows_callback, results)

    if not results:
        print("Revit window not found!")
        return False

    hwnd, title = results[0]
    print(f"Found Revit: {title}")

    # Get window rect and click in center
    try:
        rect = win32gui.GetWindowRect(hwnd)
        x = (rect[0] + rect[2]) // 2
        y = (rect[1] + rect[3]) // 2

        # Bring window to front
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.2)

        # Click in window
        pyautogui.click(x, y)
        print(f"Clicked at ({x}, {y})")
        time.sleep(0.3)

        # Press ESC to deselect
        pyautogui.press('escape')
        time.sleep(0.2)

        return True
    except Exception as e:
        print(f"Click failed: {e}")
        return False


def send_mcp_request(method: str, params: dict = None, timeout: float = 30.0) -> dict:
    """Send a request to Revit MCP with timeout handling."""
    import threading

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }

    request_json = json.dumps(request)
    request_bytes = request_json.encode('utf-8')

    result = {"error": "Timeout"}
    completed = threading.Event()

    def do_request():
        nonlocal result
        try:
            handle = win32file.CreateFile(
                PIPE_PATH,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )

            # Send length prefix + message
            length_bytes = struct.pack('<I', len(request_bytes))
            win32file.WriteFile(handle, length_bytes + request_bytes)

            # Read response length
            _, length_data = win32file.ReadFile(handle, 4)
            response_length = struct.unpack('<I', length_data)[0]

            # Read response
            _, response_data = win32file.ReadFile(handle, response_length)
            result = json.loads(response_data.decode('utf-8'))

            win32file.CloseHandle(handle)
        except Exception as e:
            result = {"error": str(e)}
        finally:
            completed.set()

    thread = threading.Thread(target=do_request)
    thread.daemon = True
    thread.start()

    # Wait for completion or timeout
    start = time.time()
    while not completed.is_set():
        if time.time() - start > timeout:
            # Try clicking Revit to trigger idle
            if HAVE_GUI:
                print("  Timeout - clicking Revit to trigger idle...")
                click_revit_window()
            time.sleep(1)
            if time.time() - start > timeout * 2:
                return result  # Give up after 2x timeout
        else:
            completed.wait(timeout=1)

    return result


def main():
    print("=" * 50)
    print("Floor Plan Wall Creator for Revit")
    print("=" * 50)

    # Load walls
    with open('D:/RevitMCPBridge2026/cleaned_walls.json') as f:
        data = json.load(f)

    walls = data['walls']
    print(f"\nLoaded {len(walls)} walls to create")
    print(f"Building envelope: {data['building_envelope']['width_ft']:.1f}' x {data['building_envelope']['depth_ft']:.1f}'")

    # Click Revit first to ensure it's ready
    if HAVE_GUI:
        print("\nActivating Revit...")
        click_revit_window()
        time.sleep(0.5)

    # Test connection with getLevels
    print("\nConnecting to Revit MCP...")
    response = send_mcp_request("getLevels", timeout=15)

    if "error" in response and "Timeout" in str(response.get("error", "")):
        print("Connection timeout - Revit may need manual interaction")
        print("Please click in Revit drawing area and try again")
        return

    result = response.get("result", {})
    if not result.get("success"):
        print(f"getLevels failed: {result}")
        return

    levels = result.get("levels", [])
    print(f"Connected! Found {len(levels)} levels:")
    for level in levels:
        print(f"  {level['name']}: {level['elevation']}' (ID: {level['id']})")

    # Use first level
    level_id = levels[0]['id'] if levels else 0
    print(f"\nUsing level ID: {level_id}")

    # Create walls
    print(f"\nCreating {len(walls)} walls...")
    success_count = 0
    fail_count = 0

    for i, wall in enumerate(walls):
        # Update level ID
        wall['levelId'] = level_id

        # Click Revit periodically to keep it responsive
        if HAVE_GUI and i % 10 == 0 and i > 0:
            click_revit_window()
            time.sleep(0.1)

        response = send_mcp_request("createWall", wall, timeout=10)
        result = response.get("result", {})

        if result.get("success"):
            success_count += 1
            wall_id = result.get("wallId", "unknown")
            print(f"  Wall {i+1}/{len(walls)}: Created (ID: {wall_id})")
        else:
            fail_count += 1
            error = result.get("error", response.get("error", "Unknown error"))
            print(f"  Wall {i+1}/{len(walls)}: FAILED - {error}")

    print(f"\n{'=' * 50}")
    print(f"DONE! Created {success_count} walls, {fail_count} failed")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
