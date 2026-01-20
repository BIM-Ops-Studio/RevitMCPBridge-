"""
Get all rooms from the current Revit project
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    client = RevitClient()
    result = client.send_request('getRooms', {})

    if not result.get('success'):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return

    rooms = result.get('rooms', [])
    print(f"\nFound {len(rooms)} rooms in your project:")
    print()
    print("=" * 80)

    # Group by level
    by_level = {}
    for room in rooms:
        level = room.get('Level', 'No Level')
        if level not in by_level:
            by_level[level] = []
        by_level[level].append(room)

    # Display by level
    for level in sorted(by_level.keys()):
        print(f"\nLEVEL: {level}")
        print("-" * 80)
        level_rooms = by_level[level]

        for room in level_rooms:
            num = room.get('Number', 'N/A')
            name = room.get('Name', 'Unnamed')
            area = room.get('Area', 0)

            try:
                area_sf = float(area)
                print(f"  [{num:6s}] {name:30s} - {area_sf:8.1f} SF")
            except:
                print(f"  [{num:6s}] {name:30s} - {area}")

        # Level summary
        total_area = sum(float(r.get('Area', 0)) for r in level_rooms if r.get('Area'))
        print(f"\n  Level Total: {len(level_rooms)} rooms, {total_area:,.1f} SF")

    print()
    print("=" * 80)

    # Project summary
    total_area = sum(float(r.get('Area', 0)) for r in rooms if r.get('Area'))
    print(f"PROJECT TOTAL: {len(rooms)} rooms, {total_area:,.1f} SF")
    print("=" * 80)

if __name__ == "__main__":
    main()
