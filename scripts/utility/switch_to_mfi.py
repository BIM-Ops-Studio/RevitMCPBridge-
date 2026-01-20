#!/usr/bin/env python3
from mcp_call import call
import json

# Switch to MFI project
result = call("setActiveDocument", {"documentName": "MF-project-test-3"})
print(json.dumps(result, indent=2))
