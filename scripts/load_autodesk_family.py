"""
Load Autodesk Family - UI Automation Script
Automates the "Load Autodesk Family" dialog in Revit 2026

Usage:
    python load_autodesk_family.py "family search term" [--category "Detail Items"]
"""

import sys
import time
import json
import argparse
from pathlib import Path

try:
    import pyautogui
    import pygetwindow as gw
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "Required packages not installed. Run: pip install pyautogui pygetwindow"
    }))
    sys.exit(1)

try:
    import win32gui
    import win32con
    import win32api
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "pywin32 not installed. Run: pip install pywin32"
    }))
    sys.exit(1)


def find_revit_window():
    """Find the main Revit window"""
    windows = gw.getWindowsWithTitle('Autodesk Revit')
    for w in windows:
        if 'Autodesk Revit' in w.title:
            return w
    return None


def find_dialog_window(title_contains="Load Autodesk Family", timeout=10):
    """Wait for and find a dialog window"""
    start = time.time()
    while time.time() - start < timeout:
        windows = gw.getAllWindows()
        for w in windows:
            if title_contains.lower() in w.title.lower():
                return w
        time.sleep(0.5)
    return None


def bring_window_to_front(window):
    """Bring a window to the foreground"""
    try:
        hwnd = window._hWnd
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"Warning: Could not bring window to front: {e}", file=sys.stderr)
        return False


def take_screenshot(region=None, save_path=None):
    """Take a screenshot, optionally of a specific region"""
    screenshot = pyautogui.screenshot(region=region)
    if save_path:
        screenshot.save(save_path)
    return screenshot


def click_at(x, y, clicks=1, button='left'):
    """Click at screen coordinates"""
    pyautogui.click(x, y, clicks=clicks, button=button)
    time.sleep(0.2)


def type_text(text, interval=0.05):
    """Type text with optional interval between characters"""
    pyautogui.typewrite(text, interval=interval)
    time.sleep(0.3)


def press_key(key):
    """Press a keyboard key"""
    pyautogui.press(key)
    time.sleep(0.2)


def hotkey(*keys):
    """Press a hotkey combination"""
    pyautogui.hotkey(*keys)
    time.sleep(0.2)


def locate_on_screen(image_path, confidence=0.8, region=None):
    """Find an image on screen"""
    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence, region=region)
        return location
    except Exception:
        return None


def get_dialog_region(dialog_window):
    """Get the screen region of a dialog window"""
    return (dialog_window.left, dialog_window.top, dialog_window.width, dialog_window.height)


class LoadAutodeskFamilyAutomation:
    """Automates the Load Autodesk Family dialog in Revit"""

    def __init__(self):
        self.dialog = None
        self.revit_window = None
        self.screenshots_dir = Path(__file__).parent / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)

    def wait_for_dialog(self, timeout=15):
        """Wait for the Load Autodesk Family dialog to appear"""
        print("Waiting for Load Autodesk Family dialog...", file=sys.stderr)

        # The dialog might have different titles
        possible_titles = [
            "Load Autodesk Family",
            "Autodesk Family",
            "Load Family",
            "Content Delivery"
        ]

        start = time.time()
        while time.time() - start < timeout:
            for title in possible_titles:
                self.dialog = find_dialog_window(title, timeout=1)
                if self.dialog:
                    print(f"Found dialog: {self.dialog.title}", file=sys.stderr)
                    return True
            time.sleep(0.5)

        return False

    def search_family(self, search_term, category=None):
        """Search for a family in the dialog"""
        if not self.dialog:
            return False

        # Bring dialog to front
        bring_window_to_front(self.dialog)
        time.sleep(0.5)

        # Take screenshot for debugging
        screenshot_path = self.screenshots_dir / "dialog_before_search.png"
        take_screenshot(save_path=str(screenshot_path))

        # The Load Autodesk Family dialog typically has:
        # - A search box at the top
        # - Category filters on the left
        # - Results in the center
        # - Load/Cancel buttons at the bottom

        # Get dialog dimensions
        dialog_region = get_dialog_region(self.dialog)
        dialog_x, dialog_y, dialog_w, dialog_h = dialog_region

        # Click in the search box area (typically near top center)
        # Search box is usually about 1/3 from the top, centered
        search_x = dialog_x + dialog_w // 2
        search_y = dialog_y + 80  # Near top of dialog

        print(f"Clicking search area at ({search_x}, {search_y})", file=sys.stderr)
        click_at(search_x, search_y)
        time.sleep(0.3)

        # Clear any existing text
        hotkey('ctrl', 'a')
        time.sleep(0.1)

        # Type search term
        print(f"Typing search term: {search_term}", file=sys.stderr)
        pyautogui.write(search_term, interval=0.05)
        time.sleep(0.5)

        # Press Enter to search
        press_key('enter')
        time.sleep(2)  # Wait for search results

        # Take screenshot after search
        screenshot_path = self.screenshots_dir / "dialog_after_search.png"
        take_screenshot(save_path=str(screenshot_path))

        return True

    def select_first_result(self):
        """Select the first search result"""
        if not self.dialog:
            return False

        dialog_region = get_dialog_region(self.dialog)
        dialog_x, dialog_y, dialog_w, dialog_h = dialog_region

        # Results are typically in the center/right area
        # Click on the first result (estimate position)
        result_x = dialog_x + dialog_w // 2
        result_y = dialog_y + dialog_h // 2 - 50  # Above center

        print(f"Clicking first result at ({result_x}, {result_y})", file=sys.stderr)
        click_at(result_x, result_y)
        time.sleep(0.5)

        # Double-click to select/expand
        click_at(result_x, result_y, clicks=2)
        time.sleep(0.5)

        return True

    def click_load_button(self):
        """Click the Load button to load the selected family"""
        if not self.dialog:
            return False

        dialog_region = get_dialog_region(self.dialog)
        dialog_x, dialog_y, dialog_w, dialog_h = dialog_region

        # Load button is typically at bottom right
        load_x = dialog_x + dialog_w - 150  # Near right edge
        load_y = dialog_y + dialog_h - 40   # Near bottom

        print(f"Clicking Load button at ({load_x}, {load_y})", file=sys.stderr)
        click_at(load_x, load_y)
        time.sleep(1)

        # Take final screenshot
        screenshot_path = self.screenshots_dir / "dialog_after_load.png"
        take_screenshot(save_path=str(screenshot_path))

        return True

    def click_cancel_button(self):
        """Click Cancel to close the dialog without loading"""
        if not self.dialog:
            return False

        dialog_region = get_dialog_region(self.dialog)
        dialog_x, dialog_y, dialog_w, dialog_h = dialog_region

        # Cancel button is typically at bottom, left of Load
        cancel_x = dialog_x + dialog_w - 250
        cancel_y = dialog_y + dialog_h - 40

        click_at(cancel_x, cancel_y)
        time.sleep(0.5)

        return True

    def run(self, search_term, category=None, auto_load=True):
        """Run the complete automation workflow"""
        result = {
            "success": False,
            "search_term": search_term,
            "category": category,
            "message": ""
        }

        # Step 1: Wait for dialog
        if not self.wait_for_dialog():
            result["error"] = "Timeout waiting for Load Autodesk Family dialog"
            return result

        # Step 2: Search for family
        if not self.search_family(search_term, category):
            result["error"] = "Failed to search for family"
            return result

        # Step 3: Select first result
        if not self.select_first_result():
            result["error"] = "Failed to select search result"
            return result

        # Step 4: Load or cancel
        if auto_load:
            if not self.click_load_button():
                result["error"] = "Failed to click Load button"
                return result
            result["message"] = f"Loaded family matching '{search_term}'"
        else:
            result["message"] = f"Found family matching '{search_term}' (auto_load=False)"

        result["success"] = True
        return result


def main():
    parser = argparse.ArgumentParser(description="Automate Load Autodesk Family dialog in Revit")
    parser.add_argument("search_term", help="Family name or search term")
    parser.add_argument("--category", "-c", help="Category filter (e.g., 'Detail Items')")
    parser.add_argument("--no-load", action="store_true", help="Don't auto-click Load button")
    parser.add_argument("--timeout", "-t", type=int, default=15, help="Timeout in seconds")

    args = parser.parse_args()

    automation = LoadAutodeskFamilyAutomation()
    result = automation.run(
        search_term=args.search_term,
        category=args.category,
        auto_load=not args.no_load
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
