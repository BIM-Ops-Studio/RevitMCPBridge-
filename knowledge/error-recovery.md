# Error Recovery Patterns

## General Principles

### When Errors Occur
1. **Stop immediately** - Don't continue blindly
2. **Report clearly** - State what went wrong
3. **Assess impact** - What was affected?
4. **Propose solution** - Suggest fix or rollback
5. **Get approval** - For significant recovery actions

### Severity Levels
| Level | Description | Action |
|-------|-------------|--------|
| Low | Warning, non-blocking | Note and continue |
| Medium | Error, but recoverable | Stop, fix, continue |
| High | Critical, data at risk | Stop, report, wait |

## Common Errors & Solutions

### MCP Connection Errors

**Error: Request timed out**
- Cause: Revit busy, dialog open, or Idling event not firing
- Solution:
  1. Check for modal dialogs in Revit
  2. Click in Revit drawing area to activate
  3. Close any open dialogs
  4. Retry command

**Error: Pipe not found**
- Cause: MCP server not running or Revit not open
- Solution:
  1. Check if Revit is running
  2. Verify MCP server started (check Revit ribbon)
  3. Restart Revit if needed

**Error: Method not found**
- Cause: DLL not updated or method not registered
- Solution:
  1. Rebuild project
  2. Copy DLL to Revit addins folder
  3. Restart Revit

### Element Placement Errors

**Error: Element not placed at correct location**
- Cause: Family origin point, level association, or coordinate system issue
- Solution:
  1. Verify input coordinates are correct
  2. Check element's actual location with GetElementLocation
  3. May need to adjust for family origin offset
  4. Check level association

**Error: Type not found**
- Cause: Family not loaded or type name mismatch
- Solution:
  1. Query available types with GetElementsByCategory
  2. Use exact type name or ID
  3. Load missing family if needed

**Error: Cannot place element**
- Cause: Invalid host, location outside model bounds, or constraint violation
- Solution:
  1. Check if host element exists (wall for door, floor for furniture)
  2. Verify location is within model bounds
  3. Check for conflicting elements

### Transaction Errors

**Error: Transaction not started**
- Cause: Attempting to modify document outside transaction
- Solution: All modifications must be in Transaction block

**Error: Transaction failed to commit**
- Cause: Invalid operation or constraint violation
- Solution:
  1. Check Revit warnings
  2. Verify operation is valid
  3. May need to modify approach

### Build Errors

**Error: CS0152 - Duplicate case label**
- Cause: Same method registered twice in switch
- Solution: Comment out or remove duplicate case

**Error: CS0246 - Type not found**
- Cause: Missing using statement or reference
- Solution: Add appropriate using directive

**Error: CS0618 - Obsolete API**
- Cause: Using deprecated Revit API
- Solution: Use recommended replacement API

## Recovery Procedures

### Rollback Element Changes
```python
# If elements were placed incorrectly
1. Get list of placed element IDs
2. Call deleteElements with those IDs
3. Verify deletion successful
4. Re-attempt with corrected parameters
```

### Restore from Backup
1. Close Revit (don't save if corrupted)
2. Locate backup file (.0001, .0002, etc.)
3. Rename backup to .rvt
4. Open and verify
5. Resume work

### Clear Stuck State
If Revit becomes unresponsive to MCP:
1. Close any dialogs manually
2. Click in drawing area
3. Try simple command (getLevels)
4. If still stuck, restart Revit

## Prevention Strategies

### Before Major Operations
1. Save the model
2. Note current element count
3. Test with single element first
4. Verify approach works before batch

### During Operations
1. Track progress with todos
2. Verify each step before continuing
3. Take screenshots at key points
4. Report any unexpected results

### After Operations
1. Verify results match expectations
2. Check for Revit warnings
3. Save if successful
4. Document what was done

## When to Ask User

### Always Ask
- Before deleting multiple elements
- Before overwriting existing work
- When error is ambiguous
- When multiple recovery options exist

### Don't Ask, Just Report
- Single element placement failed (try again)
- Build warning (note and continue)
- Non-critical timeout (retry once)

## Escalation Path

1. **Self-resolve**: Try known fix
2. **Report & suggest**: Inform user, propose solution
3. **Wait for input**: Stop and ask for direction
4. **Manual intervention**: User needs to act in Revit directly

---
*Update with new error patterns as they're discovered*
