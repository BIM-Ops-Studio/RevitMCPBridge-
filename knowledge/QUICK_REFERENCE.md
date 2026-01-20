# RevitMCPBridge Quick Reference

## Most Common Operations

### Create Walls
```json
{"method": "createWallsFromPolyline", "params": {
  "points": [[0,0,0], [45,0,0], [45,30,0], [0,30,0], [0,0,0]],
  "levelId": 30, "height": 10, "isClosed": true
}}
```

### Place Family Instance
```json
{"method": "placeFamilyInstance", "params": {
  "familyTypeId": 123456, "location": [10.5, 20.0, 0], "levelId": 30
}}
```

### Place View on Sheet
```json
{"method": "placeViewOnSheet", "params": {"viewId": 100, "sheetId": 200}}
{"method": "moveViewport", "params": {"viewportId": 300, "newLocation": [1.1, 0.58]}}
```

### Copy View Content Between Documents
```json
{"method": "copyViewContentBetweenDocuments", "params": {
  "sourceDocumentName": "Source", "targetDocumentName": "Target",
  "sourceViewId": 12345, "targetViewId": 67890
}}
```

---

## Critical Rules

| Rule | Details |
|------|---------|
| **params not parameters** | `{"params": {...}}` NOT `{"parameters": {...}}` |
| **Points as arrays** | `[x, y, z]` NOT `{"x": x, "y": y, "z": z}` |
| **Level ID required** | Query `getLevels` first, use integer ID |
| **Walls past doors** | Walls must extend past door openings |
| **WarningSwallower** | Element placement uses this pattern |

---

## Sheet Layout (ARCH D 36x24)

```
Boundaries: X=0.13-2.70, Y=0.10-1.93 ft
Title offset: 0.08 ft below viewport
Safe minY: 0.18 ft

Floor Plan Positions (stacked):
  L1: X=1.1, Y=0.58
  L2: X=1.1, Y=1.54
```

---

## Common Queries

| Query | Method |
|-------|--------|
| Get levels | `getLevels` |
| Get wall types | `getWallTypes` |
| Get views | `getViews(viewType="FloorPlan")` |
| Get sheets | `getSheets` |
| Get viewports | `getViewportsOnSheet(sheetId)` |
| Project standards | `analyzeProjectStandards` |

---

## Text Sizes

- Regular: **3/32"** (default)
- Headers: 3/16" or 1/8"
- Large: 1/4" (rare)

---

## Error Recovery

| Error | Fix |
|-------|-----|
| Timeout | Click in Revit, close dialogs, retry |
| Null reference | Check `params` not `parameters` |
| Element wrong location | Verify level, check family origin |
| Method not found | Rebuild DLL, restart Revit |

---

## Pipe Names

```
Revit 2026: \\.\pipe\RevitMCPBridge2026
Revit 2025: \\.\pipe\RevitMCPBridge2025
```

---

## File Paths

```
DLL:      D:\RevitMCPBridge2026\bin\Release\RevitMCPBridge2026.dll
Addins:   C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\
Knowledge: D:\RevitMCPBridge2026\knowledge\
```
