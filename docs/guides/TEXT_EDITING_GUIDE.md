# Revit TEXT Editing Capabilities

## Overview
The RevitMCPBridge now supports full TEXT element editing in Revit. You can query, create, modify, and delete TextNote elements directly from Claude Code in WSL.

## New MCP Methods

### 1. getTextElements
Query text notes from the document with optional filters.

**Parameters:**
- `viewId` (optional): Filter by specific view ID
- `searchText` (optional): Filter by text content
- `includeTextNotes` (optional): Include TextNote elements (default: true)

**Example Request:**
```json
{
  "method": "get_text_elements",
  "params": {
    "viewId": "1234567",
    "searchText": "Revision"
  }
}
```

**Example Response:**
```json
{
  "success": true,
  "result": {
    "count": 3,
    "textElements": [
      {
        "id": 9876543,
        "type": "TextNote",
        "text": "Revision 1: Updated per building dept comments",
        "viewId": 1234567,
        "viewName": "A-101 - FLOOR PLAN",
        "position": { "x": 10.5, "y": 20.3, "z": 0.0 },
        "width": 12.0,
        "lineCount": 1
      }
    ]
  }
}
```

### 2. createTextNote
Create a new text note in a view.

**Parameters:**
- `viewId` (required): View ID where text will be created
- `text` (required): Text content
- `x`, `y`, `z` (optional): Position coordinates (default: 0, 0, 0)

**Example Request:**
```json
{
  "method": "create_text_note",
  "params": {
    "viewId": "1234567",
    "text": "NEW NOTE: SEE STRUCTURAL DRAWINGS",
    "x": 15.0,
    "y": 25.0,
    "z": 0.0
  }
}
```

### 3. modifyTextNote
Modify existing text note content.

**Parameters:**
- `elementId` (required): ID of text note to modify
- `text` (required): New text content

**Example Request:**
```json
{
  "method": "modify_text_note",
  "params": {
    "elementId": "9876543",
    "text": "UPDATED: Coordination required with MEP"
  }
}
```

### 4. deleteTextNote
Delete a text note element.

**Parameters:**
- `elementId` (required): ID of text note to delete

**Example Request:**
```json
{
  "method": "delete_text_note",
  "params": {
    "elementId": "9876543"
  }
}
```

## Helper Scripts

Three bash scripts are available in `/tmp/` for easy text editing:

### get_text_notes.sh
```bash
# Get all text notes
./get_text_notes.sh

# Get text notes from specific view
./get_text_notes.sh 1234567

# Search for text notes containing "Revision"
./get_text_notes.sh "" "Revision"

# Search in specific view
./get_text_notes.sh 1234567 "Revision"
```

### create_text_note.sh
```bash
# Create text note at origin
./create_text_note.sh 1234567 "New annotation"

# Create text note at specific position
./create_text_note.sh 1234567 "New annotation" 10.5 20.3 0
```

### modify_text_note.sh
```bash
./modify_text_note.sh 9876543 "Updated text content"
```

## Workflow for Building Department Comments

### Step 1: Find text notes that need updating
```bash
# Search for all revision-related notes
./get_text_notes.sh "" "Revision"

# Or get all text notes on a specific sheet view
./get_text_notes.sh 1316918
```

### Step 2: Modify existing notes
```bash
# Update note with element ID 9876543
./modify_text_note.sh 9876543 "Revision 1: Updated stairwell dimensions per comment #12"
```

### Step 3: Add new notes where needed
```bash
# Add new annotation to sheet
./create_text_note.sh 1316918 "SEE SHEET A-201 FOR ADDITIONAL DETAILS" 50 75 0
```

## Integration with HTTP Bridge

All methods are automatically routed through the HTTP bridge server at `http://172.24.224.1:8765`.

You can call them directly via curl:
```bash
curl -X POST http://172.24.224.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"method": "get_text_elements", "params": {"searchText": "Revision"}}'
```

## Next Steps for Building Department Comments

1. **Close Revit completely**
2. **Run deployment:** `powershell.exe -File D:\RevitMCPBridge2026\deploy.ps1`
3. **Restart Revit** and open your project
4. **Start MCP Bridge server** from Revit ribbon
5. **Start HTTP server:** `python D:\revit-mcp-server\http_server.py`
6. **Test text editing:**
   ```bash
   ./tmp/get_text_notes.sh
   ```

## Implementation Details

- All text operations execute on Revit's main thread using ExternalEvent
- Transactions automatically wrap all create/modify/delete operations
- Thread-safe execution with 30-second timeout
- Full error handling and validation
- Returns detailed results with element IDs, positions, and metadata

## Building Department Comment Response Process

1. **Identify comments requiring text changes** (from building dept review)
2. **Use get_text_notes.sh** to find existing text on relevant sheets
3. **Use modify_text_note.sh** to update existing notes
4. **Use create_text_note.sh** to add new required annotations
5. **Verify changes** in Revit before resubmitting

## NOA (Notice of Acceptance) Handling

For Miami-Dade NOA requirements:
- Use text editing to add NOA numbers to schedules
- Create text notes referencing NOA approvals
- Update product specifications with NOA information

Example:
```bash
# Add NOA reference to door schedule notes
./create_text_note.sh 1234567 "Impact doors: Miami-Dade NOA 12-0615.09" 100 50 0
```
