#!/usr/bin/env python3
"""Restart MCP server by simulating clicks on the Revit ribbon button."""

import time
import sys

try:
    import win32gui
    import win32con
    import win32api
    import pyautogui
    HAVE_GUI = True
except ImportError:
    HAVE_GUI = False
    print("Error: pyautogui and win32gui required")
    sys.exit(1)


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


def activate_window(hwnd):
    """Bring window to foreground."""
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"Warning: Could not activate window: {e}")
        return False


def find_mcp_button():
    """Try to find the MCP button location by searching for Add-ins tab."""
    # Get Revit window
    hwnd, title = find_revit_window()
    if not hwnd:
        return None

    activate_window(hwnd)

    # Get window position
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    print(f"Revit window: {left},{top} - {right},{bottom} ({width}x{height})")

    # The Add-ins tab is usually in the ribbon area
    # Typical ribbon height is about 120-150 pixels from top
    # Tabs are at the very top (within first 30 pixels of ribbon)

    # Estimate Add-ins tab location (usually rightmost tabs area)
    # This is an approximation - actual position varies by Revit configuration
    ribbon_top = top + 30  # Account for title bar
    ribbon_left = left

    return {
        'window': (left, top, right, bottom),
        'ribbon_top': ribbon_top,
        'ribbon_left': ribbon_left
    }


def main():
    print("=" * 60)
    print("MCP Server Restart Helper")
    print("=" * 60)

    hwnd, title = find_revit_window()
    if not hwnd:
        print("ERROR: Revit not found!")
        return

    print(f"Found: {title}")

    # Activate Revit
    print("\nActivating Revit window...")
    activate_window(hwnd)
    time.sleep(0.5)

    # Get window position
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect

    print(f"Window position: {left},{top} to {right},{bottom}")

    # Method 1: Use keyboard shortcut to access Add-ins tab
    # Alt+N typically opens Add-ins in Revit (may vary)
    print("\n--- Method 1: Try keyboard navigation ---")
    print("Pressing Alt to activate ribbon...")
    pyautogui.press('alt')
    time.sleep(0.3)

    # Try pressing 'A' for Add-ins tab (may need adjustment)
    print("Pressing 'A' for Add-ins tab...")
    pyautogui.press('a')
    time.sleep(0.3)

    # Press ESC to cancel if it didn't work
    pyautogui.press('escape')
    time.sleep(0.5)

    # Method 2: Click in the ribbon area where Add-ins tab typically is
    print("\n--- Method 2: Click in Add-ins tab area ---")

    # Add-ins tab is usually about 800-900 pixels from left edge
    # and about 50 pixels from top of Revit window
    tab_x = left + 850  # Approximate X position for Add-ins tab
    tab_y = top + 50    # Approximate Y position for tabs

    print(f"Clicking at estimated Add-ins tab location: ({tab_x}, {tab_y})")
    pyautogui.click(tab_x, tab_y)
    time.sleep(0.5)

    # Now click where the MCP button might be (in the panel area)
    # MCP button is typically in a panel about 100-200 pixels from left
    # and about 80-100 pixels from top of Revit window
    button_x = left + 150
    button_y = top + 90

    print(f"Clicking at estimated MCP button location: ({button_x}, {button_y})")
    pyautogui.click(button_x, button_y)
    time.sleep(0.3)

    # Click again to toggle (stop then start)
    print("Clicking again to restart...")
    pyautogui.click(button_x, button_y)
    time.sleep(0.5)

    # Send ESC to close any opened panel
    pyautogui.press('escape')

    print("\n" + "=" * 60)
    print("Done! Please check Revit to see if MCP was restarted.")
    print("Look for the MCP status indicator in the Add-ins tab.")
    print("=" * 60)

    print("\nIf the button locations were wrong, you can manually:")
    print("1. Go to Add-ins tab in Revit")
    print("2. Find the MCP Bridge panel")
    print("3. Click 'Stop MCP' (if running)")
    print("4. Click 'Start MCP'")


if __name__ == "__main__":
    main()
