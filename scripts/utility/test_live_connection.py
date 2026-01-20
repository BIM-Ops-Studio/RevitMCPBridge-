"""
Test live connection to Revit from current Claude Code session
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("=" * 60)
    print("TESTING LIVE CONNECTION TO REVIT")
    print("=" * 60)
    print()

    print("Connecting to Revit MCP Bridge...")
    client = RevitClient()

    try:
        # Test connection
        if not client.ping():
            print("[ERROR] Cannot connect to Revit")
            print()
            print("Possible reasons:")
            print("  1. Revit is not running")
            print("  2. RevitMCPBridge2026 add-in not loaded")
            print("  3. Named pipe not available")
            return False

        print("[SUCCESS] Connected successfully!")
        print()

        # Get project info
        print("Getting current project information...")
        result = client.send_request("getProjectInfo", {})

        if not result.get("success"):
            print(f"⚠️  No active document or error: {result.get('error')}")
            print()
            print("Open a Revit project to continue.")
            return False

        # Display project info
        info = result.get("projectInfo", {})
        print()
        print("PROJECT INFORMATION:")
        print(f"  Name: {info.get('ProjectName', 'Unnamed Project')}")
        print(f"  Number: {info.get('ProjectNumber', 'N/A')}")
        print(f"  Address: {info.get('ProjectAddress', 'N/A')}")
        print(f"  Organization: {info.get('OrganizationName', 'N/A')}")
        print()

        # Try to get rooms count
        print("Checking model contents...")
        rooms_result = client.send_request("getRooms", {})
        if rooms_result.get("success"):
            rooms = rooms_result.get("rooms", [])
            print(f"  Rooms found: {len(rooms)}")

        print()
        print("=" * 60)
        print("[SUCCESS] LIVE CONNECTION WORKING!")
        print("=" * 60)
        print()
        print("You can now ask Claude to:")
        print("  - 'Show me all rooms in my project'")
        print("  - 'Create a room schedule'")
        print("  - 'Tag all doors in the current view'")
        print("  - 'Check building code compliance'")
        print()

        return True

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print()
        print("Make sure:")
        print("  1. Revit 2026 is running")
        print("  2. A project is open")
        print("  3. RevitMCPBridge2026 add-in is loaded")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
