# What Actually Works - Consolidated Knowledge

> **Last Updated:** January 2026
> **Source:** 549 memories analyzed, 90 days of pattern analysis
> **Purpose:** Production-ready reference for AI-assisted Revit automation

---

## Quick Reference: Proven Methods

### Wall Creation

**Use `createWallsFromPolyline` (NOT `createWall`)**
```json
{
  "method": "createWallsFromPolyline",
  "params": {
    "points": [[0,0,0], [45.33,0,0], [45.33,28.67,0], [0,28.67,0], [0,0,0]],
    "levelId": 30,
    "height": 10,
    "wallTypeId": 441451,
    "isClosed": true
  }
}
```

**Why:** Individual `createWall` calls at origin (0,0) often fail with "referenced object not valid" error. Polyline method is more reliable.

**Parameter Format:**
- `startPoint` / `endPoint`: Array `[x, y, z]` in feet
- `levelId`: Integer (get from `getLevels`)
- `height`: Number in feet
- Always query `getLevels` first to get actual level IDs

**Critical Rule:** Walls must extend PAST door openings to the next wall intersection. Doors are inserted INTO walls.

---

### Sheet & Viewport Layout

**Proven Workflow:**
1. `getViewportBoundingBoxes(sheetId)` - Get actual dimensions
2. `placeViewOnSheet(viewId, sheetId)` - Places at sheet center
3. `moveViewport(viewportId, newLocation=[x, y])` - Position precisely
4. `exportViewToImage(sheetId)` - Verify result

**Sheet Boundaries (ARCH D with titleblock):**
```
minX: 0.13 ft    maxX: 2.70 ft
minY: 0.10 ft    maxY: 1.93 ft
Title offset: 0.08 ft below viewport
Safe minY: 0.18 ft (ensures title visible)
```

**Grid Pattern for Detail Sheets (5x4 = 20 cells):**
- No margin - grid fills entire usable area
- Row-based layout: tall views in top rows, short in bottom
- Column spacing: ~0.867 ft consistent

**Floor Plan Alignment (Critical):**
1. Both views MUST have identical crop boxes (same min/max XY)
2. Both viewports MUST have identical X position
3. Use `setViewCropBox` + verify with `getViewCropBox`

**Two Floor Plans on 36x24 Sheet:**
```
L1 (Ground): X=1.1 ft, Y=0.58 ft
L2 (Upper):  X=1.1 ft, Y=1.54 ft
Vertical spacing: ~0.96 ft (11.5")
```

---

### Element Placement

**Family Instance Placement:**
```json
{
  "method": "placeFamilyInstance",
  "params": {
    "familyTypeId": 123456,
    "location": [10.5, 20.0, 0],
    "levelId": 30
  }
}
```

**Critical Fix Applied:** WarningSwallower pattern prevents transaction rollback from Revit warnings. All element placement methods now use this.

**Door/Window Placement:**
- Host wall MUST exist at that level
- Wall must NOT be curtain wall (unless special door)
- Wall height must encompass the opening

---

### Text & Annotations

**Text Size Standards:**
- Regular text: 3/32" (ALWAYS use unless specified)
- Titles/Headers: 3/16" or 1/8"
- Big text: 1/4" (only when explicitly requested)

**Detail Lines:**
- Specify `lineStyleId` explicitly
- Query `getLineStyles` first
- Standard weights: "Thin Lines", "Medium Lines", "Wide Lines"
- View must be detail/drafting view (not model view)

**Text Notes:**
- `createTextNote` and `createTextNoteWithLeader` both work
- Multi-line: use `\\r` for line breaks
- Leaders render correctly

---

### Schedules (All Working)

**Tested Methods:**
- `getSchedules` - Lists all schedules
- `getScheduleData` - Returns full table data
- `getScheduleFields` - Field definitions with metadata
- `getScheduleInfo` - Complete properties
- `getDoorSchedule` - Convenience method
- `createSchedule` - Creates new schedule
- `addScheduleField` - Adds fields to schedule

---

### Batch Operations (All Working)

**Batch Methods (src/BatchMethods.cs):**
- `executeBatch` - Multiple operations in single transaction with rollback
- `createWallBatch` - Multiple walls with shared defaults
- `placeElementsBatch` - Multiple family instances with symbol caching
- `deleteElementsBatch` - Multiple deletions in single transaction
- `setParametersBatch` - Parameters on multiple elements

**Critical Rule:** Add delay between rapid API calls - Revit can't keep up with rapid regeneration.

---

### View Content Transfer Between Documents

**The Problem:** Standard `copyElementsBetweenDocuments` FAILS for view-specific elements (TextNotes, DetailLines) with error "Some of the elements cannot be copied"

**Working Solution:**
1. In DESTINATION project, create NEW DraftingView with:
   - SAME NAME as source view
   - SAME SCALE as source view (critical!)
2. Use `copyViewContentBetweenDocuments`:
```json
{
  "method": "copyViewContentBetweenDocuments",
  "params": {
    "sourceDocumentName": "Source Project",
    "targetDocumentName": "Target Project",
    "sourceViewId": 12345,
    "targetViewId": 67890
  }
}
```
3. Now view CAN be placed on sheets

**Key Insight:** Empty views cannot be placed on sheets. Views with content can.

---

### View Exports

**Settings for Quality:**
- DPI: 300 minimum for print quality
- "Print to Scale" set correctly
- Check "Hidden Line" vs "Shaded" mode
- Include annotation crop if needed
- TEST one view before batch export

---

## Critical Gotchas

### Parameter Key Name
```
WRONG: {"method": "renameView", "parameters": {...}}
RIGHT: {"method": "renameView", "params": {...}}
```
Use `"params"` NOT `"parameters"` - this causes null reference errors.

### Pipe Names
```
RIGHT: RevitMCPBridge2026, RevitMCPBridge2025
WRONG: RevitMCP2026, RevitMCP2025
```

### Level IDs
- Many methods require `levelId` (integer) not `levelName` (string)
- Always query `getLevels` first to get actual IDs

### Titleblock Selection
- NEVER use default titleblock
- Use `getTitleblockTypes` to list available
- Or use `createSheetAuto` which auto-detects project's primary titleblock

### Transaction Handling
- All modifications MUST be in Transaction blocks
- Use WarningSwallower for element placement
- Check `trans.GetStatus()` after commit

### Family Loading
- Check if family already loaded before attempting load
- Cloud families (Revit 2026+) require user interaction
- `loadFamily` works with local .rfa files only

---

## Floor Plan Tracing Pipeline

### What Works (CAD Pipeline)
- CAD extraction with layer filtering
- Center-to-center alignment for calibration
- Per-project calibration stored in memory
- Accuracy: ~21 ft (acceptable for project setup)

### What Doesn't Work Yet
- **YOLO Detection:** 10.5% precision - over-detects furniture/text as walls
- **PDF Direct Extraction:** Scale factor bugs in multiple places
- **Y-Axis Flip:** Inconsistent implementation across 3 different files

### Root Causes of Failures
1. YOLO needs retraining with better wall annotations
2. Scale formula bug: `72.0 / scale_factor` should be `72.0 * 12.0 / scale_factor`
3. Y-axis flip implemented differently in auto_tracer.py, index.html, and others

### Recommended Approach
Use CAD pipeline (serves actual projects) over YOLO/PDF pipeline until retraining complete.

---

## Proven Workflows

### Sheet Creation
```
1. getTitleblockTypes → find project's primary titleblock
2. createSheetAuto OR createSheet with correct titleblockId
3. placeViewOnSheet → places at center
4. moveViewport → precise positioning
5. exportViewToImage → verify
```

### Detail Sheet Organization
```
1. getViewportBoundingBoxes → get actual sizes
2. generateViewportLayout(sheetId, columns, rows) → auto-arrange
3. Optimal grids:
   - 6 details: 2 rows × 3 columns
   - 5 details: 2 rows × 3 columns (one empty)
   - 4 details: 2 rows × 2 columns
4. 4-6 details per sheet maximum
```

### Wall Placement from Coordinates
```
1. getLevels → get level ID
2. getWallTypes → find appropriate type
3. createWallsFromPolyline → create walls
4. getWalls → verify creation
5. Walls must extend past door openings!
```

### Standards Detection (Start of Every Session)
```
1. Read live system state
2. Get project info (name, number, client)
3. Match against firm profiles in knowledge/standards/
4. analyzeProjectStandards → scan text styles, line styles, etc.
5. Apply matching standards profile
```

---

## Orchestration Methods (22 Total)

### ValidationMethods.cs (7)
- `verifyElement` - Check single element
- `verifyTextContent` - Verify text note content
- `getValidationSnapshot` - Capture view state
- `compareViewState` - Compare before/after
- `verifyBatch` - Batch verification
- `verifyOperation` - Operation result check
- `verifyElementCount` - Element count validation

### OrchestrationMethods.cs (6)
- `createLifeSafetyLegend` - Auto-create legend
- `createAreaCalculationLegend` - Area calcs
- `executeOrchestrationWorkflow` - Run workflows
- `reviewViewForIssues` - QC review
- `batchModifyTextNotes` - Bulk text changes
- `smartPlaceElement` - Intelligent placement

### SelfHealingMethods.cs (9)
- `recordOperation` - Log operation
- `getOperationHistory` - Retrieve history
- Correction learning from failures
- Auto-recovery patterns

---

## Error Recovery Patterns

### MCP Connection Timeout
1. Check for modal dialogs in Revit
2. Click in Revit drawing area to activate
3. Close any open dialogs
4. Retry with simple command (`getLevels`)

### "Method not found"
1. Rebuild project (msbuild)
2. Copy DLL to Revit addins folder
3. Restart Revit

### Element at Wrong Location
1. Verify input coordinates
2. Check element's actual location with `GetElementLocation`
3. Adjust for family origin offset
4. Check level association

### Revit Unresponsive to MCP
1. Close dialogs manually
2. Click in drawing area
3. Try simple command
4. If still stuck, restart Revit

---

## Success Metrics

### What Determines Autonomy
For each workflow track:
1. **Pass rate** - Completes without human intervention?
2. **Time-to-complete** - Predictable execution time?
3. **Recovery rate** - Can self-heal from failures?
4. **Human cleanup minutes** - How much manual work needed?

### Current State
- Platform: 705 methods, 100% implemented
- Golden workflows: Permit set skeleton (Spine v0.1/v0.2)
- Memory system: 549 memories, continuous learning
- Standards awareness: Multi-firm detection working

---

## File Locations

| Component | Path |
|-----------|------|
| MCP Server DLL | `D:\RevitMCPBridge2026\bin\Release\RevitMCPBridge2026.dll` |
| Knowledge Base | `D:\RevitMCPBridge2026\knowledge\` (121 files) |
| Source Code | `D:\RevitMCPBridge2026\src\` (135 C# files) |
| Claude Tools | `D:\_CLAUDE-TOOLS\` (47 tools) |
| Memory Database | `D:\_CLAUDE-TOOLS\claude-memory-server\memory.db` |
| System Bridge | `D:\_CLAUDE-TOOLS\system-bridge\live_state.json` |

---

*This document consolidates 90 days of learning from 549 memories. Update as new patterns are discovered.*
