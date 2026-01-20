# RevitMCPBridge2026 - Usage Guide
## Version 1.0.1.0

Complete guide for using the MCP Bridge API to control your Revit construction documents.

---

## System #1: Annotation Batch Manager

Powerful batch operations for managing text notes across your entire project.

### 1. Find Text Notes by Content

Search for text notes containing specific text.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "findTextNotesByContent",
    "params": {
      "searchPattern": "CODE",
      "caseSensitive": false,
      "useRegex": false
    }
  }'
```

**Parameters:**
- `searchPattern` (required): Text to search for
- `viewId` (optional): Limit search to specific view
- `caseSensitive` (optional): Case-sensitive search (default: false)
- `useRegex` (optional): Use regex pattern (default: false)

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalFound": 5,
    "searchPattern": "CODE",
    "matches": [
      {
        "id": 1983814,
        "text": "CODE REFERENCES:\n• T5-R ZONING...",
        "viewId": 12345,
        "viewName": "Sheet A1.1",
        "typeId": 67890,
        "typeName": "3/32\" Arial"
      }
    ]
  }
}
```

**Use Cases:**
- Find all notes mentioning specific code sections
- Locate notes with specific text patterns
- Audit annotation content across project

### 2. Batch Update Text Notes

Update multiple text notes at once.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "batchUpdateTextNotes",
    "params": {
      "elementIds": ["1983814", "1983815", "1983816"],
      "text": "Updated note text",
      "textTypeId": "67890"
    }
  }'
```

**Parameters:**
- `elementIds` (required): Array of text note IDs to update
- `text` (optional): New text content
- `textTypeId` (optional): New text type ID

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalProcessed": 3,
    "results": [
      {
        "id": "1983814",
        "success": true,
        "oldText": "Original text",
        "newText": "Updated note text",
        "oldTypeId": 12345,
        "newTypeId": 67890
      }
    ]
  }
}
```

**Use Cases:**
- Update text type for multiple notes
- Batch change note content
- Standardize annotation formatting

### 3. Find and Replace Text

Find and replace text across all notes.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "findAndReplaceText",
    "params": {
      "findText": "FBC 2020",
      "replaceText": "FBC 2023",
      "caseSensitive": false,
      "useRegex": false
    }
  }'
```

**Parameters:**
- `findText` (required): Text to find
- `replaceText` (required): Text to replace with
- `viewId` (optional): Limit to specific view
- `caseSensitive` (optional): Case-sensitive (default: false)
- `useRegex` (optional): Use regex (default: false)

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalReplaced": 15,
    "findText": "FBC 2020",
    "replaceText": "FBC 2023",
    "replacements": [
      {
        "id": 1983814,
        "viewName": "Sheet A1.1",
        "oldText": "Per FBC 2020",
        "newText": "Per FBC 2023"
      }
    ]
  }
}
```

**Use Cases:**
- Update code references project-wide
- Change standard terminology
- Fix typos across all annotations

### 4. Get Text Statistics

Get statistics about text notes in your project.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getTextStatistics",
    "params": {}
  }'
```

**Parameters:**
- `viewId` (optional): Limit to specific view

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalTextNotes": 234,
    "uniqueTypes": 5,
    "uniqueViews": 12,
    "byType": [
      {
        "typeId": 67890,
        "typeName": "3/32\" Arial",
        "count": 150
      }
    ],
    "byView": [
      {
        "viewId": 12345,
        "viewName": "Sheet A1.1",
        "count": 45
      }
    ]
  }
}
```

**Use Cases:**
- Analyze annotation distribution
- Find most-used text types
- Identify views with many/few annotations

---

## System #2: Legend/Table Automation

Manage legends and schedules programmatically.

### 1. Get All Legends

List all legend views in the project.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getLegends",
    "params": {}
  }'
```

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalLegends": 3,
    "legends": [
      {
        "id": 123456,
        "name": "ZONING DATA",
        "isTemplate": false,
        "scale": 1
      }
    ]
  }
}
```

**Use Cases:**
- List all project legends
- Find specific legends by name
- Audit legend setup

### 2. Get All Schedules

List all schedules in the project.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getSchedules",
    "params": {}
  }'
```

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalSchedules": 8,
    "schedules": [
      {
        "id": 234567,
        "name": "Door Schedule",
        "isAssemblyView": false,
        "definition": {
          "categoryId": 98765,
          "fieldCount": 8,
          "filterCount": 2,
          "sortGroupFieldCount": 1
        }
      }
    ]
  }
}
```

**Use Cases:**
- List all project schedules
- Find schedules by category
- Audit schedule setup

### 3. Get Schedule Data

Extract data from a schedule (rows and columns).

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getScheduleData",
    "params": {
      "scheduleId": "234567"
    }
  }'
```

**Parameters:**
- `scheduleId` (required): Schedule view ID

**Returns:**
```json
{
  "success": true,
  "result": {
    "scheduleId": 234567,
    "scheduleName": "Door Schedule",
    "rowCount": 25,
    "columnCount": 8,
    "headers": ["Mark", "Type", "Width", "Height", "Material", "Fire Rating", "Level", "Comments"],
    "data": [
      ["101", "A", "3'-0\"", "7'-0\"", "Wood", "1-Hour", "Level 1", "Main Entry"],
      ["102", "B", "3'-0\"", "7'-0\"", "Metal", "2-Hour", "Level 1", "Stair Door"]
    ]
  }
}
```

**Use Cases:**
- Export schedule data to external database
- Generate reports from Revit data
- Sync with spec database
- Create custom schedule views

---

## System #3: Pre-Issue QC Dashboard

Quality control checks before issuing construction documents.

### 1. Get All Sheets

Get complete sheet information.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getAllSheets",
    "params": {}
  }'
```

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalSheets": 25,
    "sheets": [
      {
        "id": 345678,
        "sheetNumber": "A1.1",
        "sheetName": "FIRST FLOOR PLAN",
        "viewCount": 2,
        "placedViews": [123, 456]
      }
    ]
  }
}
```

**Use Cases:**
- Audit all sheets before issue
- Generate sheet index
- Check sheet completion

### 2. Get Unplaced Views

Find views not placed on any sheet.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getUnplacedViews",
    "params": {}
  }'
```

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalViews": 50,
    "placedViews": 45,
    "unplacedViews": 5,
    "views": [
      {
        "id": 456789,
        "name": "3D View - Perspective",
        "viewType": "ThreeD",
        "scale": 1
      }
    ]
  }
}
```

**Use Cases:**
- Find missing views before issue
- Identify work-in-progress views
- Pre-issue QC check

### 3. Get Empty Sheets

Find sheets without any views.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getEmptySheets",
    "params": {}
  }'
```

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalEmptySheets": 2,
    "sheets": [
      {
        "id": 567890,
        "sheetNumber": "A9.9",
        "sheetName": "PLACEHOLDER"
      }
    ]
  }
}
```

**Use Cases:**
- Find incomplete sheets
- Pre-issue QC
- Identify sheets to delete

### 4. Validate Text Sizes

Check for non-standard text sizes.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "validateTextSizes",
    "params": {
      "allowedSizes": [0.0625, 0.09375, 0.125, 0.1875, 0.25]
    }
  }'
```

**Parameters:**
- `allowedSizes` (optional): Array of allowed sizes in inches
  - Default: [1/16", 3/32", 1/8", 3/16", 1/4"]

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalTextNotes": 234,
    "nonStandardCount": 5,
    "allowedSizes": [0.0625, 0.09375, 0.125, 0.1875, 0.25],
    "nonStandardNotes": [
      {
        "id": 678901,
        "text": "Note with wrong size...",
        "viewName": "Sheet A1.1",
        "typeName": "Custom Text",
        "sizeInches": 0.075
      }
    ]
  }
}
```

**Use Cases:**
- Enforce text size standards
- Find non-compliant annotations
- Pre-issue QC check

### 5. Get Project Warnings

Get all Revit warnings.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getProjectWarnings",
    "params": {
      "maxWarnings": 50
    }
  }'
```

**Parameters:**
- `maxWarnings` (optional): Maximum warnings to return (default: 100)

**Returns:**
```json
{
  "success": true,
  "result": {
    "totalWarnings": 23,
    "returnedWarnings": 23,
    "warnings": [
      {
        "severity": "Warning",
        "description": "Room is not in a properly enclosed region",
        "elementIds": [789012, 789013]
      }
    ]
  }
}
```

**Use Cases:**
- Pre-issue QC check
- Identify model issues
- Generate warning report

### 6. Run Comprehensive QC Checks

Run all QC checks at once.

```bash
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{
    "method": "runQCChecks",
    "params": {}
  }'
```

**Returns:**
```json
{
  "success": true,
  "result": {
    "summary": {
      "totalSheets": 25,
      "emptySheets": 2,
      "totalViews": 50,
      "placedViews": 45,
      "unplacedViews": 5,
      "totalWarnings": 23,
      "totalTextNotes": 234
    },
    "checks": {
      "hasEmptySheets": true,
      "hasUnplacedViews": true,
      "hasWarnings": true
    }
  }
}
```

**Use Cases:**
- Pre-issue dashboard
- Quick project health check
- Automated QC reporting

---

## Complete Workflow Examples

### Example 1: Update All Code References

```bash
# Step 1: Find all notes mentioning "FBC 2020"
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "findTextNotesByContent", "params": {"searchPattern": "FBC 2020"}}'

# Step 2: Replace all instances with "FBC 2023"
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "findAndReplaceText", "params": {"findText": "FBC 2020", "replaceText": "FBC 2023"}}'
```

### Example 2: Pre-Issue QC Report

```bash
# Run comprehensive checks
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "runQCChecks", "params": {}}' | python3 -m json.tool > qc_report.json

# Get detailed warnings
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "getProjectWarnings", "params": {}}' | python3 -m json.tool > warnings.json

# Validate text sizes
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "validateTextSizes", "params": {}}' | python3 -m json.tool > text_validation.json
```

### Example 3: Export Schedule Data

```bash
# Step 1: Get all schedules
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "getSchedules", "params": {}}'

# Step 2: Export specific schedule (e.g., Door Schedule ID: 234567)
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "getScheduleData", "params": {"scheduleId": "234567"}}' | \
  python3 -m json.tool > door_schedule_export.json
```

---

## Tips and Best Practices

### Performance
- Use `viewId` parameter to limit searches to specific views when possible
- Batch operations are much faster than individual updates
- Run QC checks off-hours for large projects

### Error Handling
- Always check `success` field in responses
- Log `error` messages for troubleshooting
- Use try-catch in automation scripts

### Regex Patterns
When using `useRegex: true`:
- Find all notes with dates: `\\d{1,2}/\\d{1,2}/\\d{4}`
- Find code references: `[A-Z]{3}\\s*\\d+\\.\\d+`
- Find placeholder text: `\\[.*?\\]`

### Automation Scripts
Create bash scripts for common tasks:

```bash
#!/bin/bash
# pre_issue_qc.sh - Run before issuing docs

echo "Running Pre-Issue QC Checks..."

# 1. Check for unplaced views
echo "Checking for unplaced views..."
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "getUnplacedViews"}' > unplaced_views.json

# 2. Check for empty sheets
echo "Checking for empty sheets..."
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "getEmptySheets"}' > empty_sheets.json

# 3. Validate text sizes
echo "Validating text sizes..."
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "validateTextSizes"}' > text_validation.json

# 4. Get warnings
echo "Getting project warnings..."
curl -s -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "getProjectWarnings"}' > warnings.json

echo "QC checks complete! Review JSON files for results."
```

---

## Next Steps

1. **Deploy the new version (1.0.1.0)**
   - Close Revit
   - Copy new DLL to addins folder
   - Restart Revit and both servers

2. **Test each system**
   - Start with simple searches
   - Try batch operations on test notes
   - Run QC checks on current project

3. **Create your workflows**
   - Build bash scripts for common tasks
   - Integrate with your existing tools
   - Automate repetitive QC checks

4. **Extend the system**
   - Request additional methods as needed
   - Build custom integrations
   - Connect to external databases

---

## Version History

**v1.0.1.0** - Major Feature Release
- Added Annotation Batch Manager (4 methods)
- Added Legend/Table Automation (5 methods)
- Added Pre-Issue QC Dashboard (6 methods)
- Total: 15 new methods for construction document control

**v1.0.0.x** - Initial Development
- Basic text note operations
- Project info retrieval
- Foundation MCP Bridge functionality
