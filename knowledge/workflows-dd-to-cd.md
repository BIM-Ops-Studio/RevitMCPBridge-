# DD to CD Workflow

## Overview
This workflow converts a Design Development (DD) model into Construction Documents (CD) set.

## Prerequisites
- DD model complete with walls, doors, windows, rooms
- Levels established
- Views created for each floor
- Target model for CD set (can be same document)

## Workflow Steps

### Phase 1: Model Verification (5 min)
```
1. getProjectInfo → Verify project data
2. getLevels → Confirm all levels exist
3. getWalls → Count total walls
4. getDoorSchedule → Count doors
5. getWindowSchedule → Count windows
6. getRooms → Verify room separation
```

**Success Criteria**: All elements present, no orphan elements

### Phase 2: Sheet Setup (10 min)
```
1. detectSheetPattern → Identify numbering system
2. getSheets → Check existing sheets
3. createSheetsFromPattern → Generate sheet set
   - Cover sheet (G001 or A000)
   - Floor plans (A101, A102...)
   - Elevations (A201, A202...)
   - Sections (A301, A302...)
   - Details (A401, A402...)
   - Schedules (A501, A502...)
```

**Success Criteria**: All required sheets created

### Phase 3: View Placement (15 min)
```
1. getViews → List all views
2. For each sheet:
   - placeViewOnSheet → Add view at position
   - Adjust viewport placement
```

**Success Criteria**: All views placed on sheets

### Phase 4: Annotation (30 min)
```
1. tagAllRooms → Room names and numbers
2. tagDoors → Door tags
3. tagWindows → Window tags
4. addDimensions:
   - Overall building dimensions
   - Opening dimensions
   - String dimensions
5. createTextNote → General notes
```

**Success Criteria**: All elements tagged, dimensions complete

### Phase 5: Schedule Creation (10 min)
```
1. createSchedule → Door schedule
2. createSchedule → Window schedule
3. createSchedule → Room finish schedule
4. addScheduleField (for each)
5. addScheduleFilter (if needed)
6. addScheduleSorting
7. placeScheduleOnSheet
```

**Success Criteria**: All schedules populated and placed

### Phase 6: Quality Check (5 min)
```
1. getProjectInfo → Final verification
2. getSheets → Confirm all sheets
3. Screenshot each sheet → Visual check
```

**Success Criteria**: QA ready for human review

## Error Recovery

### Common Errors

**"Element not tagged"**
- Retry with specific element ID
- Check if tag family loaded

**"View already on sheet"**
- Skip and log
- May need to remove first

**"Pipe timeout"**
- Wait 5 seconds
- Retry up to 3 times
- Exponential backoff: 2s, 4s, 8s

**"Type not found"**
- Load missing family
- Use fallback type

### Retry Strategy
- Pre-delay: 0.5s before each MCP call
- Post-delay: 0.5s after each call
- Max retries: 3 per operation
- Backoff: 2^attempt seconds

## Timing Estimates
| Phase | Tasks | Duration |
|-------|-------|----------|
| 1. Verification | 6 | 5 min |
| 2. Sheet Setup | 4 | 10 min |
| 3. View Placement | N views | 15 min |
| 4. Annotation | 20+ | 30 min |
| 5. Schedules | 10 | 10 min |
| 6. QA | 3 | 5 min |
| **Total** | | **75 min** |

## Checkpoint Strategy
Save after each phase:
- `checkpoint_phase1.json` - Element counts
- `checkpoint_phase2.json` - Sheet IDs
- `checkpoint_phase3.json` - View placements
- `checkpoint_phase4.json` - Annotation progress
- `checkpoint_phase5.json` - Schedule IDs

To resume: Read latest checkpoint, skip completed phases

## Success Metrics
- **Level 3 Target**: 70% correct without intervention
- **Time to QA**: < 30 minutes
- **Retry rate**: < 10% of operations

---
*Last Updated: 2025-11-24 (Session 59)*
