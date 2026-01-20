#!/usr/bin/env python3
from mcp_call import call
import json

# Values from 512 Clematis
# Project Base Point: position (0, 0, 0)
# Survey Point: position (0, 0, 0.334)

# Set Project Base Point
result1 = call("setProjectBasePoint", {"position": [0.0, 0.0, 0.0]})
print("Set Project Base Point:")
print(json.dumps(result1, indent=2))

# Set Survey Point
result2 = call("setSurveyPoint", {"position": [0.0, 0.0, 0.3339907284108605]})
print("\nSet Survey Point:")
print(json.dumps(result2, indent=2))
