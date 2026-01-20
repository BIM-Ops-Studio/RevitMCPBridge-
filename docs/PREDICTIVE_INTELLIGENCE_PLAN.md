# Predictive Intelligence System - Game Plan

## Vision
Transform RevitMCPBridge from a reactive tool (waits for commands) into a proactive assistant that predicts what needs to be done next based on project state, standards, and learned patterns.

---

## Core Problem Statement
Currently:
- User must explicitly tell Claude what to do
- No automatic gap detection
- No understanding of "what's missing"
- No prediction of next logical steps

Goal:
- System analyzes project automatically
- Identifies gaps against standards
- Predicts next required actions
- Suggests or executes improvements

---

## System Architecture

### Layer 1: Project State Analyzer (C# - Revit API)
New methods to deeply scan and catalog the entire project:

```
analyzeProjectCompleteness
├── getAllSheets (with placed views, empty status)
├── getAllViews (with placement status, type, what they show)
├── getAllLevels (with associated views per level)
├── getSheetViewMatrix (which views on which sheets)
├── getNamingPatterns (detect conventions in use)
├── getScheduleStatus (which schedules exist, which placed)
└── getDetailStatus (drafting views, detail groups)
```

**Key Data Points:**
- Sheets: number, name, titleblock, placed views, empty?
- Views: name, type, level association, placed on sheet?, duplicates?
- Levels: name, elevation, floor plans exist?, RCPs exist?, elevations exist?
- Schedules: type, placed?, complete?
- Details: category, placed?, orphaned?

### Layer 2: Standards Engine (JSON/Memory)
Define what a "complete" project looks like:

```json
{
  "projectType": "residential",
  "requiredSheets": [
    {"pattern": "A0.*", "purpose": "general", "requiredViews": ["cover", "notes", "symbols"]},
    {"pattern": "A1.*", "purpose": "plans", "requiredViews": ["floor_plan_per_level"]},
    {"pattern": "A2.*", "purpose": "elevations", "requiredViews": ["4_elevations"]},
    {"pattern": "A3.*", "purpose": "sections", "requiredViews": ["min_2_sections"]},
    {"pattern": "A5.*", "purpose": "schedules", "requiredViews": ["door_schedule", "window_schedule"]}
  ],
  "requiredViewsPerLevel": [
    "Floor Plan",
    "Reflected Ceiling Plan"
  ],
  "requiredSchedules": [
    "Door Schedule",
    "Window Schedule",
    "Room Finish Schedule"
  ],
  "namingConventions": {
    "floorPlan": "{LEVEL_NAME} - Floor Plan",
    "rcp": "{LEVEL_NAME} - RCP",
    "elevation": "{DIRECTION} Elevation"
  }
}
```

### Layer 3: Gap Analyzer (Logic Engine)
Compares project state against standards and identifies:

```
Gaps Detected:
├── Missing Sheets
│   └── "No A301 section sheet found"
├── Missing Views
│   └── "Second Floor has no RCP view"
├── Unplaced Views
│   └── "Door Schedule exists but not on any sheet"
├── Empty Sheets
│   └── "Sheet A9.2 has only 2 of expected 9 details"
├── Naming Issues
│   └── "View 'Level 2' doesn't match pattern 'Second Floor - Floor Plan'"
└── Incomplete Items
    └── "Exterior elevations: 3 of 4 created (missing West)"
```

### Layer 4: Prediction Engine
Generates prioritized action list:

```
Predicted Next Steps (Priority Order):
1. [HIGH] Create "West Elevation" view - all other elevations exist
2. [HIGH] Place "Door Schedule" on sheet A501 - schedule exists, unplaced
3. [MEDIUM] Create sheet A301 for building sections
4. [MEDIUM] Create "Second Floor - RCP" view
5. [LOW] Rename "Level 2" to "Second Floor - Floor Plan" for consistency
```

### Layer 5: Action Executor
Can execute predictions automatically or create placeholders:

```
Execution Modes:
├── Suggest Only - List what needs to be done
├── Create Placeholders - Add empty views/sheets with TODO markers
├── Auto-Execute Safe - Do non-destructive actions automatically
└── Full Auto - Execute all predicted actions
```

---

## Implementation Phases

### Phase 1: Deep Project Analysis (Week 1-2)
**New C# Methods:**
```csharp
// Comprehensive project scan
analyzeProjectState() → returns full project model as JSON
getSheetViewMatrix() → sheet-to-view relationships
getViewPlacementStatus() → which views placed where
getLevelViewCoverage() → what views exist per level
detectNamingPatterns() → analyze naming conventions in use
```

**Deliverable:** Can scan any project and produce structured state report

### Phase 2: Standards Definition (Week 2-3)
**Create standards system:**
- JSON schema for project standards
- Default standards for residential/commercial
- Learning from existing projects (extract patterns)
- Memory integration for project-specific overrides

**Deliverable:** Standards files + method to compare project vs standard

### Phase 3: Gap Analysis Engine (Week 3-4)
**Build comparison logic:**
- Compare state vs standards
- Categorize gaps by type and severity
- Generate human-readable gap report
- Prioritization algorithm

**Deliverable:** `analyzeProjectGaps()` returns prioritized issue list

### Phase 4: Prediction System (Week 4-5)
**Intelligence layer:**
- Predict next actions based on gaps
- Learn from user corrections
- Context-aware suggestions (what user is currently working on)
- Integration with memory for learned patterns

**Deliverable:** `predictNextSteps()` returns actionable suggestions

### Phase 5: Execution Integration (Week 5-6)
**Action system:**
- Execute safe predictions automatically
- Create placeholders for items needing user input
- Batch execution for multiple actions
- Undo/rollback capability

**Deliverable:** `executeNextSteps()` with safety controls

---

## Example Workflow

### User Opens Project
```
Claude: "Analyzing AP Builder Residence..."

Project Analysis Complete:
├── 25 sheets (3 empty)
├── 344 views (47 unplaced)
├── 7 levels
├── 12 schedules (2 unplaced)

Gaps Detected:
1. Sheet A3.2 "Second Floor RCP" is empty
2. "Window Schedule" not placed on any sheet
3. No "West Elevation" view exists
4. Sheet A9.2 has 10 details, expected 12 based on grid

Predicted Next Steps:
1. Create West Elevation view
2. Place Window Schedule on A2.3
3. Add 2 more details to A9.2 or resize existing

Shall I execute any of these, or show more details?
```

### User Says "Fix the Window Schedule"
```
Claude: "Placing Window Schedule on sheet A2.3..."
- Found Window Schedule (ID: 1936926)
- Sheet A2.3 has space at X=0.7, Y=1.5
- Placing now...
Done. Window Schedule placed on A2.3.

Remaining gaps: 3
Next suggestion: Create West Elevation view?
```

---

## Data Structures

### ProjectState Model
```json
{
  "projectName": "AP Builder Residence",
  "analyzedAt": "2025-12-17T22:00:00Z",
  "summary": {
    "sheetCount": 25,
    "viewCount": 344,
    "levelCount": 7,
    "scheduleCount": 12
  },
  "sheets": [...],
  "views": [...],
  "levels": [...],
  "schedules": [...],
  "gaps": [...],
  "predictions": [...]
}
```

### Gap Model
```json
{
  "id": "gap_001",
  "type": "missing_view",
  "severity": "high",
  "description": "West Elevation does not exist",
  "context": "North, South, East elevations all exist",
  "suggestedAction": "createView",
  "actionParams": {
    "viewType": "elevation",
    "direction": "west",
    "suggestedName": "West Elevation"
  }
}
```

### Prediction Model
```json
{
  "id": "pred_001",
  "priority": 1,
  "action": "createView",
  "description": "Create West Elevation",
  "confidence": 0.95,
  "reasoning": "3 of 4 cardinal elevations exist",
  "canAutoExecute": true,
  "params": {...}
}
```

---

## Memory Integration

Store learned patterns:
```
memory_store:
- Project-specific sheet patterns learned
- User preferences for view placement
- Corrections when predictions were wrong
- Successful automation patterns to repeat
```

Query patterns:
```
memory_recall:
- "What sheet pattern does this project use?"
- "Where did user prefer schedules placed?"
- "What predictions were rejected?"
```

---

## Success Metrics

1. **Gap Detection Accuracy**: % of real gaps identified
2. **Prediction Acceptance Rate**: % of suggestions user accepts
3. **Time Savings**: Reduction in manual analysis time
4. **Learning Rate**: Improvement over sessions

---

## Next Steps

1. Review this plan together
2. Prioritize which phase to start
3. Begin with Phase 1 (Deep Project Analysis) as foundation
4. Build incrementally, testing each phase

---

*This is a living document - update as we refine the approach*
