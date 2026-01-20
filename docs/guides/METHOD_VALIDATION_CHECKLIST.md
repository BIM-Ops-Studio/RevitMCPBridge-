# RevitMCPBridge2026 - Method Validation Checklist

## Purpose

This checklist ensures every MCP method is implemented consistently, safely, and reliably. Use this before marking any method as "complete" or when validating existing methods.

---

## Quick Validation Checklist

For each method, verify ALL items below:

### ✅ 1. Method Signature
- [ ] Method is `public static string`
- [ ] Takes `UIApplication uiApp` as first parameter
- [ ] Takes `JObject parameters` as second parameter
- [ ] Method name matches architecture document exactly
- [ ] XML documentation comment exists above method

### ✅ 2. Parameter Extraction
- [ ] All required parameters are extracted from JObject
- [ ] Parameter extraction includes null checks
- [ ] Invalid/missing parameters return error JSON
- [ ] Optional parameters have documented defaults
- [ ] Parameter types are validated (int, string, array, etc.)

### ✅ 3. Revit API Access
- [ ] `var app = uiApp.Application;` (if needed)
- [ ] `var doc = uiApp.ActiveUIDocument.Document;` (if needed)
- [ ] Document null check performed if critical
- [ ] Element IDs converted using `.Value` (Revit 2026)
- [ ] No deprecated API methods used

### ✅ 4. Transaction Management
- [ ] Transaction created with descriptive name
- [ ] `trans.Start()` called before modifications
- [ ] Try-catch wraps all operations
- [ ] `trans.Commit()` called on success
- [ ] `trans.RollBack()` called in catch block
- [ ] No modifications outside transaction

### ✅ 5. Error Handling
- [ ] Try-catch block wraps all risky operations
- [ ] Catch block returns error JSON
- [ ] Error messages are descriptive and helpful
- [ ] No unhandled exceptions possible
- [ ] Transaction rollback prevents partial changes

### ✅ 6. Return Format
- [ ] Success returns: `{success: true, data: {...}}`
- [ ] Error returns: `{success: false, error: "message"}`
- [ ] Field names are consistent with other methods
- [ ] All element IDs converted to int using `.Value`
- [ ] JSON is properly serialized with JsonConvert

### ✅ 7. Documentation
- [ ] XML comment describes method purpose
- [ ] Parameters are documented
- [ ] Return format is documented
- [ ] Special requirements noted (view type, phase, etc.)
- [ ] TODO comments removed when complete

### ✅ 8. Testing
- [ ] Unit test exists in `/tests/` directory
- [ ] Test passes with valid input data
- [ ] Test handles invalid input gracefully
- [ ] Test verifies transaction rollback on error
- [ ] Integrated into workflow test (if applicable)

---

## Detailed Validation Sections

### Section A: Code Structure Validation

#### A1. Method Template Compliance
```csharp
public static string MethodName(UIApplication uiApp, JObject parameters)
{
    var app = uiApp.Application;
    var doc = uiApp.ActiveUIDocument.Document;

    using (Transaction trans = new Transaction(doc, "Operation Name"))
    {
        trans.Start();
        try
        {
            // 1. Parameter extraction
            // 2. Validation
            // 3. Operation
            // 4. Build response

            trans.Commit();
            return JsonConvert.SerializeObject(new { success = true, data = result });
        }
        catch (Exception ex)
        {
            trans.RollBack();
            return JsonConvert.SerializeObject(new { success = false, error = ex.Message });
        }
    }
}
```

**Check:**
- [ ] Follows exact template structure
- [ ] No deviations from pattern
- [ ] Clear 4-step flow in try block

#### A2. Namespace and Using Statements
```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
```

**Check:**
- [ ] All required namespaces included
- [ ] No unused using statements
- [ ] Newtonsoft.Json.Linq for JObject
- [ ] Correct Revit namespaces

---

### Section B: Parameter Validation

#### B1. Required Parameter Pattern
```csharp
// Extract required parameter
var elementId = parameters["elementId"]?.Value<int>();
if (elementId == null)
{
    return @"{""success"": false, ""error"": ""elementId parameter is required""}";
}

var elem = doc.GetElement(new ElementId(elementId.Value));
if (elem == null)
{
    return @"{""success"": false, ""error"": ""Element not found""}";
}
```

**Check:**
- [ ] Null check after extraction
- [ ] Descriptive error message
- [ ] Early return on missing parameter
- [ ] Element existence verified before use

#### B2. Optional Parameter Pattern
```csharp
// Extract optional parameter with default
var includeSystem = parameters["includeSystem"]?.Value<bool>() ?? false;
var maxResults = parameters["maxResults"]?.Value<int>() ?? 100;
```

**Check:**
- [ ] Uses `??` operator for defaults
- [ ] Default is reasonable for operation
- [ ] Documented in XML comment

#### B3. Array Parameter Pattern
```csharp
// Extract array parameter
var pointsArray = parameters["points"]?.Value<JArray>();
if (pointsArray == null || pointsArray.Count < 2)
{
    return @"{""success"": false, ""error"": ""points array requires at least 2 points""}";
}

var points = pointsArray.Select(p => {
    var arr = p.Value<JArray>();
    return new XYZ(arr[0].Value<double>(), arr[1].Value<double>(), arr[2].Value<double>());
}).ToList();
```

**Check:**
- [ ] Array null check performed
- [ ] Array length validated
- [ ] Each element properly converted
- [ ] Descriptive error on invalid format

---

### Section C: Transaction Safety

#### C1. Transaction Lifecycle
**Check:**
- [ ] Transaction created before any modifications
- [ ] Transaction name describes the operation
- [ ] `using` statement ensures disposal
- [ ] Start called before operations
- [ ] Commit called only on success
- [ ] Rollback called on any error

#### C2. Read-Only Operations
For methods that only read data (no modifications):
```csharp
public static string GetElementInfo(UIApplication uiApp, JObject parameters)
{
    var doc = uiApp.ActiveUIDocument.Document;

    try
    {
        // NO TRANSACTION NEEDED - read-only
        var elementId = parameters["elementId"]?.Value<int>();
        // ... read operations only ...

        return JsonConvert.SerializeObject(new { success = true, data = result });
    }
    catch (Exception ex)
    {
        return JsonConvert.SerializeObject(new { success = false, error = ex.Message });
    }
}
```

**Check:**
- [ ] No transaction for read-only operations
- [ ] Try-catch still wraps operations
- [ ] No modifications to document/elements

---

### Section D: Revit 2026 API Compliance

#### D1. ElementId Conversion
```csharp
// CORRECT for Revit 2026
var elementId = new ElementId(idValue);
var intValue = (int)element.Id.Value;

// INCORRECT (old API)
var elementId = new ElementId(idValue);  // Still OK
var intValue = element.Id.IntegerValue;  // WRONG - doesn't exist in 2026
```

**Check:**
- [ ] Uses `.Value` instead of `.IntegerValue`
- [ ] Casts to int: `(int)element.Id.Value`

#### D2. StructuralType Namespace
```csharp
// CORRECT for Revit 2026
var instance = doc.Create.NewFamilyInstance(
    location, type, wall, level,
    Autodesk.Revit.DB.Structure.StructuralType.NonStructural
);

// INCORRECT (old API)
var instance = doc.Create.NewFamilyInstance(
    location, type, wall, level,
    StructuralType.NonStructural  // Won't compile in 2026
);
```

**Check:**
- [ ] Full namespace path used for StructuralType
- [ ] `Autodesk.Revit.DB.Structure.StructuralType`

#### D3. Room Boundaries
```csharp
// CORRECT for Revit 2026
var modelCurve = doc.Create.NewModelCurve(line, sketchPlane);
var roomBoundaryCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_RoomSeparationLines);
if (roomBoundaryCat != null)
{
    var graphicsStyle = roomBoundaryCat.GetGraphicsStyle(GraphicsStyleType.Projection);
    if (graphicsStyle != null) { modelCurve.LineStyle = graphicsStyle; }
}

// INCORRECT (old API)
var sketch = doc.Create.NewRoomBoundaryLine(view.SketchPlane, line, view);  // Doesn't exist
```

**Check:**
- [ ] Uses NewModelCurve instead of NewRoomBoundaryLine
- [ ] Applies room boundary line style
- [ ] Null checks for categories and styles

#### D4. Tag References
```csharp
// CORRECT for Revit 2026
var refs = tag.GetTaggedReferences();
if (refs != null && refs.Count > 0)
{
    var elemId = refs[0].ElementId;
    var taggedId = (int)elemId.Value;
}

// INCORRECT (old API)
var taggedId = tag.TaggedLocalElementId.IntegerValue;  // Doesn't exist
```

**Check:**
- [ ] Uses GetTaggedReferences() method
- [ ] Handles reference collection properly
- [ ] Null checks for references

---

### Section E: Data Response Validation

#### E1. Success Response Format
```csharp
var result = new
{
    success = true,
    elementId = (int)newElement.Id.Value,
    elementType = newElement.GetType().Name,
    location = new[] { location.X, location.Y, location.Z },
    parameters = parameterData
};
return JsonConvert.SerializeObject(result);
```

**Check:**
- [ ] `success = true` field present
- [ ] Data fields use meaningful names
- [ ] Element IDs converted to int
- [ ] Arrays/lists properly formatted
- [ ] Nested objects allowed but kept simple

#### E2. Error Response Format
```csharp
catch (Exception ex)
{
    trans.RollBack();
    return JsonConvert.SerializeObject(new
    {
        success = false,
        error = ex.Message
    });
}
```

**Check:**
- [ ] `success = false` field present
- [ ] `error` field contains description
- [ ] Error message is helpful (not just "Error")
- [ ] No sensitive info in error message

#### E3. Consistency Check
**Check:**
- [ ] Field names match similar methods
- [ ] `elementId` not `element_id` or `id`
- [ ] Boolean values lowercase: `true`/`false`
- [ ] Consistent array formatting across methods

---

### Section F: Common Pitfalls

#### F1. Avoid These Mistakes

**WRONG - Transaction not committed:**
```csharp
try
{
    // operations...
    return JsonConvert.SerializeObject(new { success = true });
    // Missing: trans.Commit();
}
```

**WRONG - Modifications outside transaction:**
```csharp
var elem = doc.GetElement(elementId);
elem.get_Parameter(BuiltInParameter.XXX).Set(value);  // Not in transaction!

using (Transaction trans = new Transaction(doc))
{
    trans.Start();
    // ... other operations ...
    trans.Commit();
}
```

**WRONG - No rollback on error:**
```csharp
try
{
    trans.Start();
    // operations...
    trans.Commit();
}
catch (Exception ex)
{
    // Missing: trans.RollBack();
    return error;
}
```

**WRONG - Using old API:**
```csharp
var id = element.Id.IntegerValue;  // Doesn't exist in 2026
```

**Check:**
- [ ] None of these mistakes present
- [ ] Commit is always called on success
- [ ] Rollback is always called on error
- [ ] All modifications are in transaction
- [ ] Using Revit 2026 API correctly

---

## Testing Validation

### Test Requirements Checklist

For each method, ensure:

#### Unit Test Exists
- [ ] Test file in `/tests/test_<category>.py`
- [ ] Test function named `test_<methodName>()`
- [ ] Test includes docstring describing purpose
- [ ] Test can run independently

#### Valid Input Test
- [ ] Test with correct, valid parameters
- [ ] Verifies `success = true` response
- [ ] Checks returned data fields exist
- [ ] Validates data types and values
- [ ] Prints success confirmation

#### Invalid Input Test
- [ ] Test with missing required parameters
- [ ] Test with wrong parameter types
- [ ] Test with out-of-range values
- [ ] Verifies `success = false` response
- [ ] Verifies error message is descriptive

#### Transaction Safety Test
- [ ] Intentionally cause error during operation
- [ ] Verify transaction was rolled back
- [ ] Confirm document is unchanged
- [ ] Verify no partial modifications

#### Integration Test (if applicable)
- [ ] Method tested as part of workflow
- [ ] Output from this method used by next
- [ ] Complete workflow succeeds
- [ ] Cleanup performed at end

---

## Sign-Off Template

When a method passes all checks, document it:

```markdown
## Method: [MethodName]
**Date Validated:** 2025-01-13
**Validated By:** [Your Name/AI Assistant]
**Status:** ✅ PASSED

### Validation Results:
- ✅ Code Structure: PASS
- ✅ Parameter Validation: PASS
- ✅ Transaction Safety: PASS
- ✅ Revit 2026 API: PASS
- ✅ Error Handling: PASS
- ✅ Return Format: PASS
- ✅ Documentation: PASS
- ✅ Unit Test: PASS
- ✅ Integration Test: PASS (if applicable)

### Test Results:
- Valid input test: PASS
- Invalid input test: PASS
- Error rollback test: PASS
- Integration test: PASS/N/A

### Notes:
[Any special considerations, quirks, or gotchas]

---
```

---

## Priority Validation Order

When validating multiple methods, use this priority:

### Priority 1: Critical Methods (Validate First)
1. Element creation methods (CreateWall, CreateDoor, etc.)
2. Element modification methods (ModifyWall, SetParameter, etc.)
3. Element deletion methods (DeleteWall, DeleteElement, etc.)

### Priority 2: Query Methods (Validate Second)
1. Get element info methods (GetWallInfo, GetRoomInfo, etc.)
2. Get collections methods (GetAllWalls, GetViewsInProject, etc.)
3. Filter/search methods (FilterElements, FindByName, etc.)

### Priority 3: Utility Methods (Validate Last)
1. Type management (GetWallTypes, GetDoorFamilies, etc.)
2. Project info (GetProjectInfo, GetLevels, etc.)
3. View management (GetAllViews, GetViewTypes, etc.)

---

## Batch Validation Workflow

For validating many methods at once:

1. **Group by Category**
   - Validate all Wall methods together
   - Validate all Room methods together
   - Etc.

2. **Run Category Tests**
   - Execute all tests for one category
   - Fix any failures before moving to next
   - Document results in validation log

3. **Integration Testing**
   - Run workflow tests combining multiple methods
   - Verify methods work together correctly
   - Check for unexpected interactions

4. **Regression Testing**
   - Re-run all tests after any fix
   - Ensure no new breaks introduced
   - Update test expectations if needed

---

## Quick Reference: Common Validation Failures

| Issue | Check | Fix |
|-------|-------|-----|
| "IntegerValue doesn't exist" | D1. ElementId Conversion | Use `.Value` instead |
| "StructuralType inaccessible" | D2. StructuralType Namespace | Use full namespace path |
| "NewRoomBoundaryLine doesn't exist" | D3. Room Boundaries | Use NewModelCurve + line style |
| "TaggedLocalElementId doesn't exist" | D4. Tag References | Use GetTaggedReferences() |
| "Transaction not committed" | C1. Transaction Lifecycle | Add trans.Commit() before return |
| "Changes persisted despite error" | C1. Transaction Lifecycle | Add trans.RollBack() in catch |
| Method returns "Not yet implemented" | All sections | Implement according to TODO comment |
| Test fails with null reference | B. Parameter Validation | Add null checks before use |
| JSON parsing error | E. Data Response | Check JsonConvert usage |

---

## Version History

**Version 1.0.0** - 2025-01-13
- Initial validation checklist
- Covers all 414 methods across 12 categories
- Revit 2026 API compliance checks
- Transaction safety validation
- Testing requirements

---

**Related Documents:**
- `TESTING_FRAMEWORK.md` - Testing strategy and templates
- `MCP_SERVER_ARCHITECTURE.md` - Complete method inventory
- Individual method source files in `/src/`
