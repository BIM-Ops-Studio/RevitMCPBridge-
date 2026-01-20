#!/usr/bin/env python3
from mcp_call import call
import json
import time

# Switch to source project
result1 = call("setActiveDocument", {"documentName": "512_CLEMATIS-2"})
print("Switched to source:", result1.get("success"))

# Wait for pipe to release
time.sleep(0.5)

# Get levels
result2 = call("getLevels", {})
print(json.dumps(result2, indent=2))
