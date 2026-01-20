#!/usr/bin/env python3
from mcp_call import call
import json

result = call("setSurveyPoint", {"position": [0.0, 0.0, 0.3339907284108605]})
print(json.dumps(result, indent=2))
