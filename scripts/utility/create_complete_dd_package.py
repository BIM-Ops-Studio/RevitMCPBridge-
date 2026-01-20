"""
COMPLETE DD PACKAGE CREATION - WITH VIEWS PLACED ON SHEETS!
Design Development Package with all views properly placed
Uses FIXED ElementID lookup chain
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

class DDPackageCreator:
    def __init__(self, client):
        self.client = client
        self.created_sheets = []
        self.created_views = []
        self.placement_success = []
        self.placement_failures = []

    def get_or_create_view(self, view_type, params, view_name):
        """Get existing view or create new one, return view ID"""
        # Try to find existing view first
        result = self.client.send_request("getViews", {})
        if result.get("success"):
            views_data = result.get("result", {})
            views = views_data.get("views", [])

            for view in views:
                if view.get("name") == view_name:
                    print(f"      [OK] Using existing: {view_name} (ID: {view.get('id')})")
                    return view.get("id")

        # Create new view
        result = self.client.send_request(view_type, params)
        if result.get("success"):
            # Try to get the view ID from the creation response
            view_id = result.get("viewId") or result.get("id")
            if view_id:
                print(f"      [OK] Created: {view_name} (ID: {view_id})")
                self.created_views.append(view_name)
                return view_id

            # If not in response, query for it
            result = self.client.send_request("getViews", {})
            if result.get("success"):
                views_data = result.get("result", {})
                views = views_data.get("views", [])
                for view in views:
                    if view.get("name") == view_name:
                        view_id = view.get("id")
                        print(f"      [OK] Created: {view_name} (ID: {view_id})")
                        self.created_views.append(view_name)
                        return view_id

        print(f"      [WARN] Could not get ID for: {view_name}")
        return None

    def create_sheet_with_view(self, sheet_number, sheet_name, view_id, view_name, location=[1.5, 1.0]):
        """Create sheet and place view on it"""
        print(f"\n   Creating sheet {sheet_number}: {sheet_name}")

        # Create sheet
        sheet_result = self.client.send_request("createSheet", {
            "sheetNumber": sheet_number,
            "sheetName": sheet_name
        })

        # Get sheet ID from response (FIXED approach)
        sheet_id = None
        if sheet_result.get("success"):
            sheet_id = sheet_result.get("sheetId")
            print(f"      [OK] Sheet created (ID: {sheet_id})")
        else:
            error = sheet_result.get("error", "")
            if "duplicate" in error.lower() or "exists" in error.lower():
                # Sheet exists, get its ID
                sheets_result = self.client.send_request("getAllSheets", {})
                if sheets_result.get("success"):
                    sheets = sheets_result.get("sheets", [])
                    for sheet in sheets:
                        if sheet.get("sheetNumber") == sheet_number:
                            sheet_id = sheet.get("sheetId")
                            print(f"      [INFO] Using existing sheet (ID: {sheet_id})")
                            break

        if not sheet_id:
            print(f"      [ERROR] Could not get sheet ID")
            self.placement_failures.append(f"{sheet_number}: No sheet ID")
            return False

        # Place view on sheet if we have a view ID
        if view_id:
            print(f"      [>>] Placing view on sheet...")
            place_result = self.client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": location
            })

            if place_result.get("success"):
                print(f"      [OK] View placed on sheet!")
                self.created_sheets.append(f"{sheet_number}: {sheet_name} (with {view_name})")
                self.placement_success.append(sheet_number)
                return True
            else:
                error = place_result.get("error", "Unknown")
                print(f"      [WARN] Placement failed: {error}")
                self.created_sheets.append(f"{sheet_number}: {sheet_name} (empty)")
                self.placement_failures.append(f"{sheet_number}: {error}")
        else:
            print(f"      [WARN] No view ID to place")
            self.created_sheets.append(f"{sheet_number}: {sheet_name} (empty)")
            self.placement_failures.append(f"{sheet_number}: No view ID")

        return False

    def create_complete_dd_package(self):
        """Create complete DD package with all views placed on sheets"""
        print("\n" + "=" * 80)
        print("CREATING COMPLETE DD PACKAGE - ALL VIEWS PLACED ON SHEETS")
        print("=" * 80)

        # PHASE 1: ARCHITECTURAL PLANS
        print("\n" + "=" * 80)
        print("PHASE 1: ARCHITECTURAL FLOOR PLANS")
        print("=" * 80)

        levels = ["Level 1", "Level 2", "Level 3", "Roof"]
        for i, level in enumerate(levels, 1):
            view_name = f"{level} - DD Floor Plan"
            view_id = self.get_or_create_view(
                "createFloorPlan",
                {"levelName": level, "viewName": view_name},
                view_name
            )
            self.create_sheet_with_view(
                f"A1.{i}",
                f"{level} Floor Plan - DD",
                view_id,
                view_name
            )

        # PHASE 2: BUILDING ELEVATIONS
        print("\n" + "=" * 80)
        print("PHASE 2: BUILDING ELEVATIONS")
        print("=" * 80)

        elevations = ["North", "South", "East", "West"]
        for i, direction in enumerate(elevations, 1):
            view_name = f"{direction} Elevation - DD"
            view_id = self.get_or_create_view(
                "createElevation",
                {"elevationName": view_name, "direction": direction},
                view_name
            )
            self.create_sheet_with_view(
                f"A2.{i}",
                f"{direction} Elevation - DD",
                view_id,
                view_name
            )

        # PHASE 3: BUILDING SECTIONS
        print("\n" + "=" * 80)
        print("PHASE 3: BUILDING SECTIONS")
        print("=" * 80)

        sections = [
            ("Longitudinal Section", "A3.1"),
            ("Transverse Section", "A3.2"),
            ("Wall Section - Typical", "A3.3")
        ]
        for section_name, sheet_num in sections:
            view_name = f"{section_name} - DD"
            view_id = self.get_or_create_view(
                "createSection",
                {"sectionName": view_name},
                view_name
            )
            self.create_sheet_with_view(
                sheet_num,
                section_name,
                view_id,
                view_name
            )

        # PHASE 4: SCHEDULES
        print("\n" + "=" * 80)
        print("PHASE 4: ROOM AND DOOR SCHEDULES")
        print("=" * 80)

        # Room Schedule
        print("\n   Creating Room Schedule with Finishes...")
        result = self.client.send_request("createSchedule", {
            "category": "Rooms",
            "scheduleName": "Room Schedule - DD"
        })
        if result.get("success"):
            # Add finish fields
            for field in ["Base Finish", "Wall Finish", "Floor Finish", "Ceiling Finish"]:
                self.client.send_request("addScheduleField", {
                    "scheduleName": "Room Schedule - DD",
                    "fieldName": field
                })
            print(f"      [OK] Room schedule created with finishes")

            # Get schedule view ID
            schedule_id = self.get_or_create_view(
                "createSchedule",
                {"category": "Rooms", "scheduleName": "Room Schedule - DD"},
                "Room Schedule - DD"
            )
            self.create_sheet_with_view(
                "A9.1",
                "Room Schedule - Design Development",
                schedule_id,
                "Room Schedule - DD",
                location=[0.5, 0.5]
            )

        # Door Schedule
        print("\n   Creating Door Schedule...")
        result = self.client.send_request("createSchedule", {
            "category": "Doors",
            "scheduleName": "Door Schedule - DD"
        })
        if result.get("success"):
            print(f"      [OK] Door schedule created")

            door_schedule_id = self.get_or_create_view(
                "createSchedule",
                {"category": "Doors", "scheduleName": "Door Schedule - DD"},
                "Door Schedule - DD"
            )
            self.create_sheet_with_view(
                "A9.2",
                "Door Schedule - Design Development",
                door_schedule_id,
                "Door Schedule - DD",
                location=[0.5, 0.5]
            )

        # Window Schedule
        print("\n   Creating Window Schedule...")
        result = self.client.send_request("createSchedule", {
            "category": "Windows",
            "scheduleName": "Window Schedule - DD"
        })
        if result.get("success"):
            print(f"      [OK] Window schedule created")

            window_schedule_id = self.get_or_create_view(
                "createSchedule",
                {"category": "Windows", "scheduleName": "Window Schedule - DD"},
                "Window Schedule - DD"
            )
            self.create_sheet_with_view(
                "A9.3",
                "Window Schedule - Design Development",
                window_schedule_id,
                "Window Schedule - DD",
                location=[0.5, 0.5]
            )

        # PHASE 5: 3D VIEWS
        print("\n" + "=" * 80)
        print("PHASE 5: 3D VIEWS AND RENDERINGS")
        print("=" * 80)

        views_3d = [
            ("3D - Overall Building - DD", "A5.1", "Overall Building View"),
            ("3D - Exterior Perspective - DD", "A5.2", "Exterior Perspective"),
            ("3D - Interior Lobby - DD", "A5.3", "Interior Lobby View")
        ]

        for view_name, sheet_num, sheet_name in views_3d:
            view_id = self.get_or_create_view(
                "create3DView",
                {"viewName": view_name},
                view_name
            )
            self.create_sheet_with_view(
                sheet_num,
                sheet_name,
                view_id,
                view_name
            )

        # PHASE 6: COVER SHEET
        print("\n" + "=" * 80)
        print("PHASE 6: COVER SHEET")
        print("=" * 80)

        cover_view_name = "3D - Cover Sheet - DD"
        cover_view_id = self.get_or_create_view(
            "create3DView",
            {"viewName": cover_view_name},
            cover_view_name
        )
        self.create_sheet_with_view(
            "A0.1",
            "COVER SHEET - DESIGN DEVELOPMENT",
            cover_view_id,
            cover_view_name,
            location=[1.0, 1.5]
        )

        return True

def main():
    print("\n" + "=" * 80)
    print("DD PACKAGE CREATION - COMPLETE AUTONOMOUS WORKFLOW")
    print("=" * 80)
    print("\nThis will create:")
    print("  - Floor plans for all levels (with views placed)")
    print("  - Building elevations (with views placed)")
    print("  - Building sections (with views placed)")
    print("  - Room, Door, and Window schedules (with schedules placed)")
    print("  - 3D views and renderings (with views placed)")
    print("  - Cover sheet (with view placed)")
    print()

    client = RevitClient()
    creator = DDPackageCreator(client)

    creator.create_complete_dd_package()

    # Summary
    print("\n" + "=" * 80)
    print("DD PACKAGE CREATION COMPLETE!")
    print("=" * 80)
    print(f"\nTotal Sheets Created: {len(creator.created_sheets)}")
    print(f"Views Successfully Placed: {len(creator.placement_success)}")
    print(f"Placement Failures: {len(creator.placement_failures)}")

    print("\n--- DELIVERABLES ---")
    for sheet in creator.created_sheets:
        print(f"  {sheet}")

    if creator.placement_success:
        print("\n--- SUCCESSFUL VIEW PLACEMENTS ---")
        for sheet in creator.placement_success:
            print(f"  [OK] {sheet}")

    if creator.placement_failures:
        print("\n--- PLACEMENT ISSUES ---")
        for issue in creator.placement_failures:
            print(f"  [WARN] {issue}")

    print("\n" + "=" * 80)
    print("CHECK YOUR REVIT PROJECT NOW!")
    print("All sheets should have views placed on them!")
    print("=" * 80)

if __name__ == "__main__":
    main()
