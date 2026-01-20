# Model Transfer Workflow

## Overview
Transfer complete model data from source to target Revit document via MCP.

## Prerequisites
- Both source and target documents open in Revit
- Target document has template/levels set up
- MCP server running

## Workflow Steps

### Phase 1: Foundation Setup (5 min)
```
1. getProjectBasePoint (source)
2. setProjectBasePoint (target) → Match source
3. getSurveyPoint (source)
4. setSurveyPoint (target) → Match source
5. getLevels (source)
6. createLevel (target) → Create missing levels
```

**Delay**: 3-5 seconds between calls
**Success Criteria**: Coordinate systems aligned

### Phase 2: Type Transfer (15 min)
Transfer family types using `getFamilyInstanceTypes` + `copyElementsBetweenDocuments`

**Order matters** (dependencies):
```
1. Wall types (foundation for all)
2. Door types
3. Window types
4. Plumbing fixtures
5. Lighting fixtures
6. Electrical fixtures
7. Furniture
8. Specialty equipment
9. Railings
```

**For each category**:
```python
# 1. Get types from source
result = call("getFamilyInstanceTypes", {"category": category})
type_ids = [t["typeId"] for t in result.get("familyTypes", [])]

# 2. Copy in batches
batch_size = 20
for i in range(0, len(type_ids), batch_size):
    batch = type_ids[i:i+batch_size]
    time.sleep(3)  # Pre-delay
    result = call("copyElementsBetweenDocuments", {
        "sourceDocumentName": source,
        "targetDocumentName": target,
        "elementIds": batch
    })
```

**Important**: Do NOT use `getElements` for fixtures - use `getFamilyInstanceTypes`

### Phase 3: Wall Instance Transfer (20 min)
```
1. getWalls (source) → Get all wall instances
2. getWallTypes (target) → Get available types
3. getLevels (target) → Get level IDs
4. Build type name → ID mapping
5. Build level name → ID mapping
6. Transform wall data:
   - Map wall type name to target type ID
   - Map level name to target level ID
   - Extract start/end points
7. batchCreateWalls (target) → Create in batches of 50
```

**Mapping code**:
```python
target_walls.append({
    "startPoint": [start["x"], start["y"], 0],
    "endPoint": [end["x"], end["y"], 0],
    "levelId": level_map[level_name],
    "wallTypeId": type_map[type_name],
    "height": wall.get("height", 10.0)
})
```

### Phase 4: Door/Window Transfer (10 min)
```
1. getDoorSchedule (source) → Get door element IDs
2. getWindowSchedule (source) → Get window element IDs
3. copyElementsBetweenDocuments → Direct copy in batches
```

**Notes**:
- `getDoors`/`getWindows` methods don't exist - use schedule methods
- Curtain wall panels will fail (skip these)
- Batch size: 50 elements
- Delay: 5 seconds between batches

### Phase 5: Hosted Elements (optional)
For fixtures, furniture, etc. that require hosts:
```
1. Get hosted elements from source
2. Verify hosts exist in target
3. Copy elements
4. Adjust placement if needed
```

## Error Handling

### "All pipe instances are busy"
- **Cause**: Too rapid MCP calls
- **Fix**: Add `time.sleep(5)` between operations
- **Prevention**: Always use 3-5 second delays

### "Type not found in target"
- **Cause**: Type didn't copy or name mismatch
- **Fix**: Query target types, use exact match
- **Prevention**: Verify type exists before creating instances

### "Cannot copy element"
- **Cause**: Missing host, constraints, or curtain wall panel
- **Action**: Log and skip, count failures
- **Expected**: ~10-15% failure rate for complex models

### "No [category] found"
- **Cause**: Using `getElements` instead of `getFamilyInstanceTypes`
- **Fix**: Switch to `getFamilyInstanceTypes` with category parameter

## Timing by Category

| Category | Typical Count | Time |
|----------|--------------|------|
| Wall types | 100-200 | 5 min |
| Door types | 100-200 | 3 min |
| Window types | 30-150 | 2 min |
| Fixtures | 200-400 | 8 min |
| Wall instances | 1000-3000 | 15 min |
| Door instances | 200-700 | 5 min |
| Window instances | 100-400 | 3 min |
| **Total** | | **~45 min** |

## Batch Sizes

| Operation | Batch Size | Delay |
|-----------|------------|-------|
| Type copy | 20 | 3s |
| Instance copy | 50 | 5s |
| Wall creation | 50 | 5s |

## Success Metrics

**From Session 58**:
- 927 types transferred
- 1,184 walls created (1,714 skipped - missing types)
- 450 doors copied (199 skipped - curtain panels)
- 280 windows copied (100%)

**Expected Success Rates**:
- Type transfer: 95%+
- Wall creation: 60-80% (depends on type matching)
- Door/window copy: 80-90% (curtain walls excluded)

## Scripts Reference
- `copy_fixture_families.py` - Type transfer by category
- `build_walls.py` - Wall instance creation with mapping
- `copy_doors_windows.py` - Direct element copy
- `get_walls.py` - Extract wall data
- `get_doors_windows.py` - Extract door/window IDs

---
*Last Updated: 2025-11-24 (Session 59)*
*Based on: Session 58 model transfer (512 Clematis → MF-project-test-3)*
