#!/usr/bin/env python3
"""Reset Revit state and send walls via MCP bridge.

This script:
1. Sends multiple ESC keypresses to cancel any active Revit commands
2. Posts keyboard input to force Revit idle state
3. Sends wall creation commands via MCP
"""

import json
import struct
import time
import sys
import ctypes
from ctypes import wintypes

try:
    import win32gui
    import win32con
    import win32api
    import win32file
    HAVE_WIN32 = True
except ImportError:
    HAVE_WIN32 = False
    print("Error: win32 modules required")
    sys.exit(1)

PIPE_PATH = r"\\.\pipe\RevitMCPBridge2026"

# Windows API constants
VK_ESCAPE = 0x1B
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102


def find_revit_window():
    """Find the Revit main window handle."""
    result = []

    def enum_callback(hwnd, param):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Autodesk Revit" in title:
                param.append((hwnd, title))
        return True

    win32gui.EnumWindows(enum_callback, result)
    return result[0] if result else (None, None)


def send_escape_to_revit(hwnd, count=5):
    """Send ESC key multiple times to cancel any active command."""
    print(f"Sending {count} ESC keypresses to Revit...")

    for i in range(count):
        # Send WM_KEYDOWN for ESC
        win32gui.PostMessage(hwnd, WM_KEYDOWN, VK_ESCAPE, 0)
        time.sleep(0.05)
        # Send WM_KEYUP for ESC
        win32gui.PostMessage(hwnd, WM_KEYUP, VK_ESCAPE, 0)
        time.sleep(0.1)

    print("ESC keys sent")
    time.sleep(0.5)


def activate_revit_window(hwnd):
    """Bring Revit to foreground and activate it."""
    try:
        # Try to bring window to foreground
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"Warning: Could not activate window: {e}")
        return False


def send_mcp_request(method: str, params: dict = None, timeout: float = 15.0) -> dict:
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

    # Wait with periodic ESC sending
    hwnd, _ = find_revit_window()
    start = time.time()
    esc_sent = 0

    while not completed.is_set():
        elapsed = time.time() - start

        # Send ESC every 3 seconds to keep Revit responsive
        if elapsed > 3 * (esc_sent + 1) and hwnd and esc_sent < 5:
            print(f"  Waiting {elapsed:.1f}s - sending ESC to trigger idle...")
            send_escape_to_revit(hwnd, count=2)
            esc_sent += 1

        if elapsed > timeout:
            return result

        completed.wait(timeout=0.5)

    return result


def main():
    print("=" * 60)
    print("Reset Revit State and Create Walls")
    print("=" * 60)

    # Find Revit window
    hwnd, title = find_revit_window()
    if not hwnd:
        print("ERROR: Revit window not found!")
        return

    print(f"\nFound Revit: {title}")

    # Step 1: Activate and reset Revit state
    print("\n--- Step 1: Resetting Revit state ---")
    activate_revit_window(hwnd)
    send_escape_to_revit(hwnd, count=10)
    time.sleep(1)

    # Step 2: Test MCP connection
    print("\n--- Step 2: Testing MCP connection ---")
    response = send_mcp_request("getLevels", timeout=20)

    if "error" in response and "Timeout" in str(response.get("error", "")):
        print("Connection timeout after reset attempts")
        print("\nThe MCP server may be stuck. Try these manual steps:")
        print("1. In Revit, go to Add-ins tab")
        print("2. Click the 'Stop MCP' button (if available)")
        print("3. Click the 'Start MCP' button")
        print("4. Then re-run this script")
        return

    result = response.get("result", {})
    if not result.get("success"):
        print(f"getLevels failed: {result}")
        return

    levels = result.get("levels", [])
    print(f"SUCCESS! Connected to Revit. Found {len(levels)} levels:")
    for level in levels:
        print(f"  {level['name']}: {level['elevation']}' (ID: {level['id']})")

    # Step 3: Load walls and create them
    print("\n--- Step 3: Creating walls ---")

    with open('D:/RevitMCPBridge2026/cleaned_walls.json') as f:
        data = json.load(f)

    walls = data['walls']
    level_id = levels[0]['id'] if levels else 0

    print(f"Creating {len(walls)} walls on level ID {level_id}...")

    success_count = 0
    fail_count = 0

    for i, wall in enumerate(walls):
        wall['levelId'] = level_id

        # Send ESC periodically to keep Revit responsive
        if i % 5 == 0 and i > 0:
            send_escape_to_revit(hwnd, count=1)

        response = send_mcp_request("createWall", wall, timeout=15)
        result = response.get("result", {})

        if result.get("success"):
            success_count += 1
            wall_id = result.get("wallId", "unknown")
            print(f"  Wall {i+1}/{len(walls)}: Created (ID: {wall_id})")
        else:
            fail_count += 1
            error = result.get("error", response.get("error", "Unknown error"))
            print(f"  Wall {i+1}/{len(walls)}: FAILED - {error}")

    print(f"\n{'=' * 60}")
    print(f"DONE! Created {success_count} walls, {fail_count} failed")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
