# Revit API Lessons Learned

This file captures lessons learned from working with the Revit API.

## Element Placement

### PlaceFamilyInstance Issues
- **Tub-Rectangular-3D**: Does not place at specified XYZ location correctly
  - All tubs end up at (-1.14, 0.00) regardless of input coordinates
  - Issue needs investigation - may be related to family origin point

### Family Type Matching
- Element names from one model rarely match type names in another
- Use explicit TYPE_MAP with hardcoded IDs for reliable matching
- Always query available types first with GetElementsByCategory

### Z-Elevation
- Upper cabinets (Base Cabinet-Upper) have built-in elevation offsets
- Elements 24-31 at Z=4.5 is expected behavior for upper cabinets
- Floor-level elements should be at Z=0

## Family Loading

### Cloud Families (Revit 2026+)
- Local folder `C:\ProgramData\Autodesk\RVT 2026\Libraries\` no longer contains families
- Families are cloud-based, accessed via Insert > Load Autodesk Family
- API access via `PostableCommand.LoadAutodeskFamily` (ID: 32990)
- PostCommand opens dialog but cannot pass parameters - requires user interaction

### loadFamily Method
- Works with local .rfa files only
- Check if family already loaded before attempting to load
- Returns family ID and all available types

## MCP Server

### Timeout Issues
- PostCommand queues actions for after API call returns
- If Revit is busy or has dialog open, commands timeout
- Always check with simple command (getLevels) first

### ExecuteInRevitContext
- Uses Idling event which won't fire if Revit is busy
- Modal dialogs block all MCP commands

## Viewport Placement

### Empty Views Cannot Be Placed on Sheets
- **EMPTY views** (views with no content) CANNOT be placed on sheets via API
- `Viewport.Create` returns null for empty views
- `CanAddViewToSheet` returns true but placement still fails
- Once a view has content, it CAN be placed regardless of how it was created

### View Content Transfer Between Documents
The standard `copyElementsBetweenDocuments` FAILS for view-specific elements (TextNotes, DetailLines, etc.) with error: "Some of the elements cannot be copied, because they are view-specific"

**Solution**: Use `copyViewContentBetweenDocuments` method which uses the correct API:
```csharp
ElementTransformUtils.CopyElements(sourceView, elementIds, targetView, Transform.Identity, options)
```

### Complete Workflow for Transferring Legends/DraftingViews
1. In DESTINATION project, create NEW DraftingView with:
   - **SAME NAME** as the source view
   - **SAME SCALE** as the source view (critical for text/element sizing)
2. Use `copyViewContentBetweenDocuments` to copy all content:
   ```json
   {"method": "copyViewContentBetweenDocuments", "params": {
     "sourceDocumentName": "Source Project",
     "targetDocumentName": "Target Project",
     "sourceViewId": 12345,
     "targetViewId": 67890
   }}
   ```
3. Now the view CAN be placed on sheets via `placeViewOnSheet`

**Key insight**: Views with content can be placed. Empty views cannot.

## Best Practices

1. Always verify element placement with screenshots
2. Query available types before placing elements
3. Use explicit type IDs, not fuzzy name matching
4. Check for modal dialogs before running commands
5. Test with simple commands to verify MCP connectivity
6. For transferring legends between projects, create new view first then paste content
