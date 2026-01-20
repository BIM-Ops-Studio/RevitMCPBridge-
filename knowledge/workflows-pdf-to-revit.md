# PDF/Sketch to Revit Workflow

## Overview
Convert hand sketches, scanned drawings, or PDF floor plans into Revit BIM models.

**Current Readiness**: 25% (knowledge files created, testing needed)

---

## Prerequisites

- Source image/PDF accessible
- Target Revit document open
- Levels created in target
- Wall types loaded

---

## Workflow Steps

### Phase 1: Image Analysis (5 min)

```
1. READ image file
   - Tool: Read (supports PNG, JPG, PDF)

2. IDENTIFY drawing type
   - Floor plan
   - Section
   - Elevation
   - Detail

3. FIND scale reference
   - Dimension if shown
   - Door width (assume 3'-0")
   - Room size (bedroom ~12x12)

4. ESTABLISH coordinate system
   - Origin point (corner or grid)
   - Orientation (north direction)
```

**Output**: Scale factor, origin point, orientation

### Phase 2: Element Extraction (10 min)

```
1. TRACE perimeter
   - Identify exterior walls
   - Note corners and lengths
   - Mark openings

2. IDENTIFY interior walls
   - Room separations
   - Closets
   - Wet walls

3. LOCATE doors
   - Position in wall
   - Swing direction
   - Width (from scale)

4. LOCATE windows
   - Position in wall
   - Width and height
   - Sill height if shown

5. NOTE fixtures
   - Plumbing fixtures
   - Casework
   - Stairs
```

**Output**: Element list with coordinates

### Phase 3: Type Mapping (5 min)

```
1. MAP wall types
   - Exterior → CMU or Frame
   - Interior → 2x4 or 2x6
   - Demising → Fire rated

2. MAP door types
   - Width determines type
   - Swing determines hand

3. MAP window types
   - Size determines type
   - Style if indicated

4. VERIFY types exist
   - Query target model
   - Note missing types
```

**Output**: Type assignments for all elements

### Phase 4: Revit Creation (15 min)

```
1. CREATE walls (exterior first)
   Method: batchCreateWalls
   - startPoint, endPoint
   - levelId
   - wallTypeId
   - height

2. CREATE interior walls
   Method: batchCreateWalls
   - Same parameters
   - Join to exterior

3. PLACE doors
   Method: placeDoor or placeFamilyInstance
   - hostWallId
   - location
   - doorTypeId

4. PLACE windows
   Method: placeWindow or placeFamilyInstance
   - hostWallId
   - location
   - windowTypeId
   - sillHeight

5. PLACE fixtures
   Method: placeFamilyInstance
   - location
   - typeId
   - rotation
```

**Output**: Elements created in Revit

### Phase 5: Verification (5 min)

```
1. SCREENSHOT result
   Method: captureActiveView

2. COMPARE to source
   - Element count
   - General layout
   - Proportions

3. NOTE discrepancies
   - Missing elements
   - Wrong positions
   - Type mismatches

4. REPORT to user
   - What was created
   - What needs correction
```

**Output**: Screenshot and summary

---

## MCP Methods Used

| Phase | Methods |
|-------|---------|
| Analysis | (Read tool - not MCP) |
| Creation | `batchCreateWalls`, `placeDoor`, `placeWindow`, `placeFamilyInstance` |
| Verification | `captureActiveView`, `getWalls`, `getDoorSchedule` |
| Adjustment | `moveElement`, `deleteElements` |

---

## Coordinate Calculation

### From Sketch to Revit Coordinates

```python
# Given:
# - scale_factor (e.g., 1" = 4'-0" means 48)
# - origin_x, origin_y (in sketch units)
# - sketch_x, sketch_y (point in sketch)

# Calculate Revit coordinates (in feet):
revit_x = (sketch_x - origin_x) * scale_factor
revit_y = (sketch_y - origin_y) * scale_factor

# For createWall:
wall = {
    "startPoint": [start_x, start_y, 0],
    "endPoint": [end_x, end_y, 0],
    "levelId": level_id,
    "wallTypeId": type_id,
    "height": 10.0
}
```

### Wall Thickness Adjustment

```python
# Walls are drawn to centerline or face
# Adjust based on convention:

# If drawn to exterior face:
interior_offset = wall_thickness / 2

# If drawn to centerline:
# No adjustment needed

# If drawn to interior face:
exterior_offset = wall_thickness / 2
```

---

## Error Handling

### Common Issues

**"Wall creation failed"**
- Check start/end points are different
- Verify levelId exists
- Confirm wallTypeId exists
- Retry with delay

**"Door not placed"**
- Wall must exist first
- Location must be on wall
- Check host wall ID

**"Scale seems wrong"**
- Verify reference element
- Check for mixed units
- Ask user to confirm

### Retry Strategy

```python
# Standard delays
PRE_DELAY = 1.0   # Before each operation
POST_DELAY = 0.5  # After each operation
BATCH_DELAY = 3.0 # Between batches

# Retry on failure
MAX_RETRIES = 3
BACKOFF = [2, 4, 8]  # Seconds
```

---

## Quality Metrics

### Target Accuracy

| Element | Target |
|---------|--------|
| Wall count | 95% |
| Wall positions | ±6" |
| Door count | 90% |
| Door positions | ±3" |
| Window count | 90% |

### Level 3 Goal
- 70% correct without intervention
- Time: < 30 minutes for single floor
- Retries: < 10%

---

## Test Cases

### Level 1: Single Room
- 4 walls, 1 door, 1 window
- Dimensions provided
- Clear symbols

### Level 2: Simple Unit
- Bedroom, bathroom, closet
- Door swings shown
- Some dimensions

### Level 3: Full Floor
- Multiple units
- Corridors
- Stairs
- No dimensions (scale from doors)

### Level 4: Multi-Story
- Multiple floor plans
- Stair continuity
- Shaft alignment

---

## Feedback Loop

After each attempt:
1. User reviews result
2. Notes corrections needed
3. Claude stores in memory:
   - Interpretation errors
   - Type mapping improvements
   - Coordinate adjustments
4. Knowledge files updated if pattern emerges

---

## Integration with Other Workflows

### After PDF → Model
- Run DD → CD workflow
- Add annotations
- Create sheets
- Generate schedules

### Combining Sources
- PDF for floor plans
- Photos for elevations
- Specifications for types

---

*Last Updated: 2025-11-24 (Session 59)*
*Readiness: 25% (knowledge created, testing needed)*
