# Spine v0.3: Permit Set Backbone + Preflight QA

## Output Goal

> "A permit set that's 80% assembled + a report that lists exactly what a human must finish."

---

## Architecture Change: Gap-Based Planning

### v0.2 (Current)
```
Profile → Standards → Build Plan → Execute All → Cleanup
```

### v0.3 (New)
```
Profile → Standards → State Assessment → Gap Analysis → Build Plan (gaps only) → Execute → Gate → Report
```

**Key difference**: Only do what's missing. Stop at gates. Produce actionable report.

---

## Four Spines

### Spine A: Sheet + View Backbone
Creates the physical document structure.

| Task | Required | Trigger |
|------|----------|---------|
| Cover sheet | Yes | Always |
| Code analysis sheet | Yes | Always |
| Floor plans (per level) | Yes | Level exists |
| Enlarged plans | Conditional | Multifamily OR accessibility |
| Exterior elevations | Conditional | Views exist OR create markers |
| Building sections (1-2) | Conditional | Model depth > threshold |
| Wall section placeholders | Optional | CD set only |
| RCP (ceiling plans) | Conditional | Commercial/Multifamily |

**Postconditions:**
- `SHEETS_CREATED >= permitSkeleton.required`
- `FLOOR_PLANS_PLACED >= 1`
- `SHEET_NAMING_CONSISTENT`

### Spine B: Annotation Pass
Adds tags and basic documentation.

| Task | Required | Trigger |
|------|----------|---------|
| Door tags | Yes | Doors exist |
| Window tags | Yes | Windows exist |
| Room tags | Yes | Rooms placed |
| Basic dimensions (overall) | Optional | Walls exist |
| Room names validation | Yes | Rooms tagged |
| Keynote placement | Optional | CD set only |

**Postconditions:**
- `DOOR_TAG_COVERAGE >= 95%`
- `WINDOW_TAG_COVERAGE >= 95%`
- `ROOM_TAG_COVERAGE >= 100%`
- `ROOM_NAMES_VALID` (no "Room" or blank)

### Spine C: Schedule Suite
Creates and validates schedules.

| Task | Required | Trigger |
|------|----------|---------|
| Door schedule | Yes | Always |
| Window schedule | Yes | Windows exist |
| Room schedule | Yes | Rooms exist |
| Finish schedule | Conditional | Commercial/Multifamily |
| Parameter completeness | Yes | Check required fields |
| Duplicate mark check | Yes | Validate uniqueness |

**Postconditions:**
- `DOOR_SCHEDULE_EXISTS`
- `WINDOW_SCHEDULE_EXISTS` (if windows)
- `ROOM_SCHEDULE_EXISTS` (if rooms)
- `NO_DUPLICATE_MARKS`
- `REQUIRED_PARAMETERS_FILLED >= 80%`

### Spine D: Preflight QA Report
Analyzes what's missing and generates actionable report.

| Check | Category | Severity |
|-------|----------|----------|
| Untagged doors | Tag Coverage | Warning |
| Untagged windows | Tag Coverage | Warning |
| Untagged rooms | Tag Coverage | Blocker |
| Missing parameters | Data Quality | Warning |
| Duplicate marks | Data Quality | Blocker |
| Sheet/view mismatch | Coordination | Warning |
| Wrong view scales | Coordination | Warning |
| Missing elevation views | Completeness | Info |
| Missing section views | Completeness | Info |

**Output:**
```json
{
  "qa_summary": {
    "ready_for_permit": true|false,
    "completion_percent": 85,
    "blockers": [...],
    "warnings": [...],
    "human_tasks": [...]
  }
}
```

---

## State Assessment Analyzers

### 1. `analyze_sheet_set()`
```python
def analyze_sheet_set(profile, standards) -> SheetSetAnalysis:
    """
    Compare current sheets to expected pack.

    Returns:
        - existing_sheets: list of current sheet numbers
        - expected_sheets: list from standards pack
        - missing_sheets: expected but not present
        - extra_sheets: present but not in pack (ok, just note)
        - naming_issues: sheets with non-standard names
    """
```

### 2. `analyze_views()`
```python
def analyze_views(profile, standards) -> ViewAnalysis:
    """
    Check view coverage and configuration.

    Returns:
        - floor_plans: per-level existence
        - missing_plans: levels without floor plans
        - wrong_scale_views: views not matching template scale
        - wrong_template_views: views with non-standard templates
        - orphan_views: views not on any sheet
    """
```

### 3. `analyze_tag_coverage()`
```python
def analyze_tag_coverage(profile) -> TagAnalysis:
    """
    Check annotation coverage.

    Returns:
        - doors: {total, tagged, untagged, coverage_pct}
        - windows: {total, tagged, untagged, coverage_pct}
        - rooms: {total, tagged, untagged, coverage_pct}
        - untagged_elements: list of element IDs
    """
```

### 4. `analyze_schedule_completeness()`
```python
def analyze_schedule_completeness(profile, standards) -> ScheduleAnalysis:
    """
    Check schedule existence and data quality.

    Returns:
        - existing_schedules: list of schedule names
        - required_schedules: list from standards
        - missing_schedules: required but not present
        - field_coverage: per-schedule required field status
        - duplicate_marks: elements with duplicate Mark values
    """
```

### 5. `analyze_dimension_coverage()` (basic heuristic)
```python
def analyze_dimension_coverage(profile) -> DimensionAnalysis:
    """
    Basic dimension presence check (not layout quality).

    Returns:
        - has_overall_dims: bool (exterior wall-to-wall exists)
        - plans_with_dims: count of floor plans with any dimensions
        - plans_without_dims: count of floor plans with no dimensions
    """
```

---

## Gap-Based Planner

```python
def build_gap_plan(state_assessment, standards) -> list[Task]:
    """
    Generate tasks only for gaps between current state and standards.

    Logic:
        1. For each expected sheet not in existing → add create_sheet task
        2. For each level without floor plan → add create_view task
        3. For each untagged door/window/room → add tag task
        4. For each missing schedule → add create_schedule task
        5. For each unfilled required parameter → add fill_parameter task (or warn)

    Returns: Minimal task list to close gaps
    """
```

---

## Human Review Gates

### Gate 1: Structure Review (after Spine A)
```
┌─────────────────────────────────────────────────────┐
│ GATE 1: STRUCTURE REVIEW                            │
├─────────────────────────────────────────────────────┤
│ Sheets created: 12/14 (2 optional skipped)          │
│ Views placed: 8/8                                   │
│ Layout: ✓ All views centered on sheets              │
│                                                     │
│ APPROVE to continue to annotations?                 │
│ [Y] Yes  [N] No (stop and review in Revit)          │
└─────────────────────────────────────────────────────┘
```

**If denied**: Stop execution, preserve created elements, generate partial report.

### Gate 2: Content Review (after Spine B + C)
```
┌─────────────────────────────────────────────────────┐
│ GATE 2: CONTENT REVIEW                              │
├─────────────────────────────────────────────────────┤
│ Tags placed: 45 doors, 23 windows, 18 rooms         │
│ Tag coverage: 98% (2 doors in closets untagged)     │
│ Schedules created: 3/3                              │
│ Duplicate marks: 0                                  │
│                                                     │
│ APPROVE to generate final report?                   │
│ [Y] Yes  [N] No (stop and review in Revit)          │
└─────────────────────────────────────────────────────┘
```

### Gate 3: Submit Review (before final export)
```
┌─────────────────────────────────────────────────────┐
│ GATE 3: SUBMIT REVIEW                               │
├─────────────────────────────────────────────────────┤
│ Completion: 87%                                     │
│ Blockers: 0                                         │
│ Warnings: 3                                         │
│   - 2 doors missing hardware parameter              │
│   - 1 room has area = 0 (check boundaries)          │
│                                                     │
│ Human tasks remaining: 5                            │
│   1. Add exterior dimensions                        │
│   2. Place keynote legend                           │
│   3. Verify ADA room tags                           │
│   4. Fill door hardware parameters                  │
│   5. Fix room boundary for Room 104                 │
│                                                     │
│ EXPORT evidence package?                            │
│ [Y] Yes  [N] No                                     │
└─────────────────────────────────────────────────────┘
```

---

## QA Report Schema

```json
{
  "$schema": "qa-report-v1",
  "run_id": "abc123",
  "timestamp": "2025-12-15T01:00:00Z",
  "pack": "multifamily",

  "summary": {
    "completion_percent": 87,
    "ready_for_permit": true,
    "ready_for_cd": false,
    "blocker_count": 0,
    "warning_count": 3,
    "info_count": 5
  },

  "state_before": {
    "sheets": 5,
    "views": 12,
    "tagged_doors": 10,
    "tagged_windows": 5
  },

  "state_after": {
    "sheets": 14,
    "views": 20,
    "tagged_doors": 45,
    "tagged_windows": 23
  },

  "changes": {
    "sheets_created": 9,
    "views_created": 8,
    "tags_placed": 53,
    "schedules_created": 3
  },

  "issues": [
    {
      "id": "MISSING_HARDWARE_PARAM",
      "severity": "warning",
      "category": "data_quality",
      "message": "2 doors missing hardware parameter",
      "elements": [12345, 12346],
      "remediation": "Open door schedule, fill Hardware column"
    }
  ],

  "human_tasks": [
    {
      "id": "ADD_EXTERIOR_DIMS",
      "priority": 1,
      "description": "Add exterior wall-to-wall dimensions",
      "estimated_time": "10 min",
      "location": "A1.01 - First Floor Plan"
    }
  ],

  "gates_passed": ["structure", "content"],
  "gates_pending": ["submit"]
}
```

---

## Template Pack Additions

Each sector pack needs these additions:

```json
{
  "completeness": {
    "permit": {
      "required_sheets": ["cover", "code", "floor_plans", "elevations"],
      "required_schedules": ["door"],
      "min_tag_coverage": 0.90,
      "allow_missing_dims": true
    },
    "cd": {
      "required_sheets": ["cover", "code", "floor_plans", "enlarged_plans", "elevations", "sections", "details"],
      "required_schedules": ["door", "window", "room", "finish"],
      "min_tag_coverage": 0.98,
      "allow_missing_dims": false
    },
    "bid": {
      "required_sheets": ["ALL"],
      "required_schedules": ["ALL"],
      "min_tag_coverage": 1.00,
      "allow_missing_dims": false
    }
  },

  "annotation_rules": {
    "doors": {
      "tag_family": "Door Tag",
      "required_params": ["Mark", "Type Mark", "Width", "Height"],
      "optional_params": ["Hardware", "Fire Rating"]
    },
    "windows": {
      "tag_family": "Window Tag",
      "required_params": ["Mark", "Type Mark"],
      "optional_params": ["Sill Height", "Head Height"]
    },
    "rooms": {
      "tag_family": "Room Tag",
      "required_params": ["Number", "Name"],
      "disallowed_names": ["Room", "ROOM", "Unnamed", ""]
    }
  }
}
```

---

## Execution Modes

### Mode 1: Full Run (default)
```bash
aec run --sector multifamily --mode full
```
Runs all spines A→B→C→D with gates.

### Mode 2: Structure Only
```bash
aec run --sector multifamily --mode structure
```
Runs Spine A only (sheets + views), stops at Gate 1.

### Mode 3: Audit Only
```bash
aec audit --sector multifamily
```
No changes. Runs state assessment + generates QA report.

### Mode 4: Fix Gaps
```bash
aec fix --sector multifamily
```
Runs gap analysis, then only executes tasks to close gaps.

---

## Implementation Order

1. **State Assessment** (required first)
   - `analyze_sheet_set()`
   - `analyze_views()`
   - `analyze_tag_coverage()`
   - `analyze_schedule_completeness()`

2. **Gap-Based Planner**
   - `build_gap_plan()`
   - Integration with existing task executor

3. **Spine A Expansion**
   - Enlarged plan triggers
   - Elevation/section placeholders

4. **Spine B: Annotation Pass** (new)
   - Tag placement tasks
   - Tag coverage verification

5. **Spine C: Schedule Suite** (expand existing)
   - Additional schedule types
   - Parameter validation

6. **Spine D: QA Report** (new)
   - Report generation
   - Human task list

7. **Gates**
   - Gate UI (CLI prompts)
   - Gate state persistence

---

## Success Criteria

### Permit Set Backbone
- [ ] 80%+ of permit sheets created automatically
- [ ] All required views placed
- [ ] Tag coverage > 90%
- [ ] Schedules populated with required fields
- [ ] Zero duplicate marks

### QA Report
- [ ] Actionable human task list generated
- [ ] Blockers vs warnings clearly distinguished
- [ ] Completion percentage accurate
- [ ] Export package includes report

### User Experience
- [ ] Can run audit without changes
- [ ] Can approve/deny at each gate
- [ ] Clear "what's left" after run
- [ ] Evidence package supports troubleshooting

---

*Spec Version: 0.3.0*
*Date: 2025-12-15*
