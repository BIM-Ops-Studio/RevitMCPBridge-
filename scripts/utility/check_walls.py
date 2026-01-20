from mcp_call import call
import json

r = call("getWalls", {})
walls = r.get("walls", [])
print("Wall count:", len(walls))
if walls:
    print("First wall keys:", list(walls[0].keys()))
    print(json.dumps(walls[0], indent=2))
else:
    print("No walls found")
