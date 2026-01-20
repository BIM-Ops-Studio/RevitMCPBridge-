# Error Handling - What To Do When Things Go Wrong

## MCP Connection Errors

### "Cannot access a closed pipe"
- The connection to Revit was interrupted
- Solution: The system will auto-reconnect on next call
- Just retry the operation

### "Timeout" or "Request timed out"
- Revit is busy or has a dialog open
- Solution: Ask user to close any dialogs in Revit
- Then retry

### "Method not found"
- The requested MCP method doesn't exist
- Solution: Use `listMethods` to see available methods
- Check spelling of method name

## Element Placement Errors

### "Element not placed"
- Location might be invalid or conflicting
- Solution: Use `suggestPlacementLocation` first
- Check for existing elements at that location

### "Type not found"
- The family or type doesn't exist in the model
- Solution: Use `getElements` to list available types
- Use exact type name or ID

### "Cannot place on this host"
- Trying to place door without wall, etc.
- Solution: Verify host element exists
- Check location is on a valid host

## View/Sheet Errors

### "View already on sheet"
- Can't place same view twice
- Solution: Use `duplicateView` first
- Then place the duplicate

### "Sheet number exists"
- Duplicate sheet number
- Solution: Use `getSheets` to see existing numbers
- Choose a unique number

## How To Report Errors to User

When an error occurs:
1. State WHAT failed clearly
2. Explain WHY it likely failed
3. Suggest HOW to fix it
4. Offer to retry if appropriate

Example:
"Failed to place room tag at (10, 15). That location overlaps with an existing tag.
I'll find an alternate location... Found clear space at (12, 15). Placing there instead."
