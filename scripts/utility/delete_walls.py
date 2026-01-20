from mcp_call import call
import json

# First get current walls
result = call("getWalls", {})
if result.get("success"):
    walls = result.get("walls", [])
    wall_ids = [w.get("id") for w in walls if w.get("id")]
    print(f"Found {len(wall_ids)} walls to delete: {wall_ids}")

    if wall_ids:
        # Delete them
        result = call("deleteElements", {"elementIds": wall_ids})
        print(json.dumps(result, indent=2))
else:
    print(f"Error getting walls: {result}")
