#!/usr/bin/env python3
from mcp_call import call
import json

# Copy the single railing type found
result = call("copyElementsBetweenDocuments", {
    "sourceDocumentName": "512_CLEMATIS-2",
    "targetDocumentName": "MF-project-test-3",
    "elementIds": [8319849]  # POOL HAND RIALING type ID
})

print(json.dumps(result, indent=2))
