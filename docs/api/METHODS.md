# RevitMCPBridge2026 API Reference

Complete reference for all 437+ MCP methods available through RevitMCPBridge2026.

## Method Categories

| Category | Count | Description |
|----------|-------|-------------|
| [System](#system) | 6 | Version, health, configuration |
| [Elements](#elements) | 14 | Core element operations |
| [Walls](#walls) | 11 | Wall creation and modification |
| [Doors/Windows](#doorswindows) | 13 | Opening placement and configuration |
| [Rooms](#rooms) | 10 | Room creation, tagging, areas |
| [Floors](#floors) | 4 | Floor operations |
| [Ceilings](#ceilings) | 4 | Ceiling operations |
| [Roofs](#roofs) | 4 | Roof operations |
| [Levels](#levels) | 3 | Level management |
| [Grids](#grids) | 5 | Grid creation and dimensioning |
| [Text/Tags](#texttags) | 19 | Text notes and tags |
| [RichText](#richtext) | 7 | Formatted text operations |
| [Dimensions](#dimensions) | 12 | Dimension placement |
| [DetailLines](#detaillines) | 6 | Detail line creation |
| [Schedules](#schedules) | 30 | Schedule creation and data |
| [Legends](#legends) | 4 | Legend views and components |
| [Views](#views) | 12 | View creation and management |
| [Sheets](#sheets) | 11 | Sheet and viewport management |
| [Worksets](#worksets) | 12 | Workset operations |
| [Phases](#phases) | 11 | Phase management |
| [Materials](#materials) | 9 | Material management |
| [Parameters](#parameters) | 12 | Parameter operations |
| [Filters](#filters) | 7 | View filter management |
| [MEP](#mep) | 14 | Mechanical, electrical, plumbing |
| [Structural](#structural) | 14 | Structural elements and loads |
| [Annotations](#annotations) | 14 | Spots, keynotes, symbols |
| [Detail](#detail) | 5 | Filled regions, detail components |
| [BasePoints](#basepoints) | 4 | Project and survey points |
| [Batch](#batch) | 3 | Batch operations |
| [Capture](#capture) | 5 | Viewport capture, camera |
| [Render](#render) | 4 | AI rendering integration |
| [Validation](#validation) | 10 | Verification and QC |
| [Orchestration](#orchestration) | 6 | Workflow orchestration |
| [SelfHealing](#selfhealing) | 9 | Error recovery |
| [Links](#links) | 5 | Revit link management |
| [Revisions](#revisions) | 4 | Revision management |
| [Groups](#groups) | 5 | Group operations |
| [Site](#site) | 4 | Topography and site |
| [SheetPatterns](#sheetpatterns) | 4 | Intelligent sheet numbering |
| [Level3Intelligence](#level3intelligence) | 18 | Learning and memory |
| [Level4Intelligence](#level4intelligence) | 9 | Proactive analysis |
| [Level5Autonomy](#level5autonomy) | 8 | Goal-directed execution |

---

## System

Version, health, and configuration operations.

### getVersion
Get bridge version and Revit information.
```json
{
  "method": "getVersion",
  "params": {}
}
```
**Response:**
```json
{
  "success": true,
  "version": "2.0.0",
  "revitVersion": "2026.2",
  "apiVersion": "2026.0.0",
  "buildDate": "2025-01-15"
}
```

### getConfiguration
Get current bridge configuration.
```json
{
  "method": "getConfiguration",
  "params": {}
}
```

### healthCheck
Check bridge and Revit connectivity.
```json
{
  "method": "healthCheck",
  "params": {}
}
```
**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "revitConnected": true,
  "documentOpen": true,
  "uptime": 3600
}
```

### getStats
Get request statistics and metrics.
```json
{
  "method": "getStats",
  "params": {}
}
```
**Response:**
```json
{
  "success": true,
  "totalRequests": 1542,
  "successfulRequests": 1520,
  "failedRequests": 22,
  "averageResponseTimeMs": 45
}
```

### reloadConfiguration
Reload configuration from appsettings.json.
```json
{
  "method": "reloadConfiguration",
  "params": {}
}
```

### getMethods
List all available MCP methods.
```json
{
  "method": "getMethods",
  "params": {
    "category": "walls"
  }
}
```
**Response:**
```json
{
  "success": true,
  "methods": ["getWalls", "createWall", "getWallTypes", ...],
  "count": 11
}
```

---

## Elements

Core element operations for querying and manipulating Revit elements.

### getElements
Get elements by category or type.
```json
{
  "method": "getElements",
  "params": {
    "category": "Walls",
    "typeFilter": "Basic Wall"
  }
}
```

### getElementById
Get a specific element by ID.
```json
{
  "method": "getElementById",
  "params": {
    "elementId": 123456
  }
}
```

### deleteElement
Delete a single element.
```json
{
  "method": "deleteElement",
  "params": {
    "elementId": 123456
  }
}
```

### deleteElements
Delete multiple elements.
```json
{
  "method": "deleteElements",
  "params": {
    "elementIds": [123456, 123457, 123458]
  }
}
```

### moveElement
Move an element to a new location.
```json
{
  "method": "moveElement",
  "params": {
    "elementId": 123456,
    "x": 10.0,
    "y": 20.0,
    "z": 0.0
  }
}
```

### copyElement
Copy an element.
```json
{
  "method": "copyElement",
  "params": {
    "elementId": 123456,
    "offsetX": 10.0,
    "offsetY": 0.0
  }
}
```

### getElementLocation
Get element location coordinates.
```json
{
  "method": "getElementLocation",
  "params": {
    "elementId": 123456
  }
}
```

---

## Walls

Wall creation and modification methods.

### getWalls
Get all walls in the model or view.
```json
{
  "method": "getWalls",
  "params": {
    "viewId": 123456
  }
}
```

### getWallTypes
Get available wall types.
```json
{
  "method": "getWallTypes",
  "params": {}
}
```

### createWall
Create a new wall.
```json
{
  "method": "createWall",
  "params": {
    "startX": 0.0,
    "startY": 0.0,
    "endX": 20.0,
    "endY": 0.0,
    "levelId": 123456,
    "height": 10.0,
    "wallTypeId": 234567
  }
}
```

### modifyWall
Modify wall properties.
```json
{
  "method": "modifyWall",
  "params": {
    "wallId": 123456,
    "height": 12.0,
    "offset": 0.5
  }
}
```

### deleteWall
Delete a wall.
```json
{
  "method": "deleteWall",
  "params": {
    "wallId": 123456
  }
}
```

### getWallGeometry
Get wall geometry data.
```json
{
  "method": "getWallGeometry",
  "params": {
    "wallId": 123456
  }
}
```

### splitWall
Split a wall at a point.
```json
{
  "method": "splitWall",
  "params": {
    "wallId": 123456,
    "splitPointX": 10.0,
    "splitPointY": 0.0
  }
}
```

### joinWalls
Join two walls.
```json
{
  "method": "joinWalls",
  "params": {
    "wall1Id": 123456,
    "wall2Id": 234567
  }
}
```

---

## Doors/Windows

Opening placement and configuration.

### getDoors
Get all doors.
```json
{
  "method": "getDoors",
  "params": {
    "viewId": 123456
  }
}
```

### getWindows
Get all windows.
```json
{
  "method": "getWindows",
  "params": {}
}
```

### placeDoor
Place a door in a wall.
```json
{
  "method": "placeDoor",
  "params": {
    "wallId": 123456,
    "doorTypeId": 234567,
    "x": 10.0,
    "y": 5.0,
    "levelId": 345678
  }
}
```

### placeWindow
Place a window in a wall.
```json
{
  "method": "placeWindow",
  "params": {
    "wallId": 123456,
    "windowTypeId": 234567,
    "x": 15.0,
    "y": 5.0,
    "sillHeight": 3.0
  }
}
```

### getDoorTypes
Get available door types.
```json
{
  "method": "getDoorTypes",
  "params": {}
}
```

### getWindowTypes
Get available window types.
```json
{
  "method": "getWindowTypes",
  "params": {}
}
```

---

## Rooms

Room creation, tagging, and area operations.

### getRooms
Get all rooms.
```json
{
  "method": "getRooms",
  "params": {
    "levelId": 123456
  }
}
```

### createRoom
Create a new room.
```json
{
  "method": "createRoom",
  "params": {
    "levelId": 123456,
    "x": 10.0,
    "y": 10.0
  }
}
```

### getRoomBoundaries
Get room boundary geometry.
```json
{
  "method": "getRoomBoundaries",
  "params": {
    "roomId": 123456
  }
}
```

### tagRoom
Tag a room.
```json
{
  "method": "tagRoom",
  "params": {
    "roomId": 123456,
    "tagTypeId": 234567
  }
}
```

### tagAllRooms
Tag all untagged rooms.
```json
{
  "method": "tagAllRooms",
  "params": {
    "viewId": 123456
  }
}
```

### getRoomArea
Get room area.
```json
{
  "method": "getRoomArea",
  "params": {
    "roomId": 123456
  }
}
```

---

## Views

View creation and management.

### getViews
Get all views.
```json
{
  "method": "getViews",
  "params": {
    "viewType": "FloorPlan"
  }
}
```

### createFloorPlanView
Create a floor plan view.
```json
{
  "method": "createFloorPlanView",
  "params": {
    "levelId": 123456,
    "name": "Level 1 - Floor Plan"
  }
}
```

### createSectionView
Create a section view.
```json
{
  "method": "createSectionView",
  "params": {
    "startX": 0.0,
    "startY": 0.0,
    "endX": 50.0,
    "endY": 0.0,
    "name": "Section A"
  }
}
```

### duplicateView
Duplicate a view.
```json
{
  "method": "duplicateView",
  "params": {
    "viewId": 123456,
    "newName": "Level 1 - Copy"
  }
}
```

### setViewScale
Set view scale.
```json
{
  "method": "setViewScale",
  "params": {
    "viewId": 123456,
    "scale": 48
  }
}
```

### activateView
Activate a view.
```json
{
  "method": "activateView",
  "params": {
    "viewId": 123456
  }
}
```

---

## Sheets

Sheet and viewport management.

### getSheets
Get all sheets.
```json
{
  "method": "getSheets",
  "params": {}
}
```

### createSheet
Create a new sheet.
```json
{
  "method": "createSheet",
  "params": {
    "sheetNumber": "A-101",
    "sheetName": "Floor Plan - Level 1",
    "titleBlockId": 123456
  }
}
```

### placeViewOnSheet
Place a view on a sheet.
```json
{
  "method": "placeViewOnSheet",
  "params": {
    "sheetId": 123456,
    "viewId": 234567,
    "x": 1.5,
    "y": 1.0
  }
}
```

### getViewportsOnSheet
Get all viewports on a sheet.
```json
{
  "method": "getViewportsOnSheet",
  "params": {
    "sheetId": 123456
  }
}
```

### moveViewport
Move a viewport.
```json
{
  "method": "moveViewport",
  "params": {
    "viewportId": 123456,
    "x": 2.0,
    "y": 1.5
  }
}
```

---

## Schedules

Schedule creation and data operations.

### getSchedules
Get all schedules.
```json
{
  "method": "getSchedules",
  "params": {}
}
```

### createSchedule
Create a new schedule.
```json
{
  "method": "createSchedule",
  "params": {
    "name": "Door Schedule",
    "category": "Doors"
  }
}
```

### getScheduleData
Get schedule data as table.
```json
{
  "method": "getScheduleData",
  "params": {
    "scheduleId": 123456
  }
}
```

### addScheduleField
Add a field to schedule.
```json
{
  "method": "addScheduleField",
  "params": {
    "scheduleId": 123456,
    "fieldName": "Width"
  }
}
```

### addScheduleFilter
Add a filter to schedule.
```json
{
  "method": "addScheduleFilter",
  "params": {
    "scheduleId": 123456,
    "fieldName": "Level",
    "filterType": "Equals",
    "filterValue": "Level 1"
  }
}
```

### exportScheduleToCSV
Export schedule to CSV.
```json
{
  "method": "exportScheduleToCSV",
  "params": {
    "scheduleId": 123456,
    "filePath": "C:\\output\\door_schedule.csv"
  }
}
```

---

## Level 5 Autonomy

Goal-directed execution with self-healing.

### executeGoal
Execute a high-level goal autonomously.
```json
{
  "method": "executeGoal",
  "params": {
    "goalType": "create_sheet_set",
    "parameters": {
      "viewIds": [123456, 234567],
      "sheetPattern": "A-{level}.{sequence}"
    }
  }
}
```

**Supported Goals:**
- `create_sheet_set` - Create complete drawing sheets
- `document_model` - Generate views, tags, schedules
- `place_elements_batch` - Batch element placement
- `export_drawings` - Export to PDF/DWG
- `analyze_model` - Model quality analysis

### approveTask
Approve a pending autonomous task.
```json
{
  "method": "approveTask",
  "params": {
    "taskId": "task-123-456"
  }
}
```

### cancelTask
Cancel a running or pending task.
```json
{
  "method": "cancelTask",
  "params": {
    "taskId": "task-123-456"
  }
}
```

### getAutonomousTasks
Get all autonomous tasks.
```json
{
  "method": "getAutonomousTasks",
  "params": {
    "status": "pending"
  }
}
```

### getTaskResult
Get result of completed task.
```json
{
  "method": "getTaskResult",
  "params": {
    "taskId": "task-123-456"
  }
}
```

### configureAutonomy
Configure autonomy guardrails.
```json
{
  "method": "configureAutonomy",
  "params": {
    "maxElementsPerTask": 100,
    "allowedMethods": ["createWall", "placeDoor"],
    "blockedMethods": ["deleteElements"],
    "requireApprovalFor": ["createSheet"]
  }
}
```

### getAutonomyStats
Get execution statistics.
```json
{
  "method": "getAutonomyStats",
  "params": {}
}
```

### getSupportedGoals
List available goal types.
```json
{
  "method": "getSupportedGoals",
  "params": {}
}
```

---

## Common Response Format

All methods return JSON with this structure:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "elementId": 123456,
  "message": "Operation completed"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "errorType": "InvalidParameter",
  "stackTrace": "..."
}
```

---

## Connection

Connect via named pipe:
```
\\.\pipe\RevitMCPBridge2026
```

Message format:
```json
{
  "method": "methodName",
  "params": { ... }
}
```
