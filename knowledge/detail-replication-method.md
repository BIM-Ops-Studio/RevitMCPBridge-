# Detail Replication Method

A proven method for extracting all elements from a Revit detail view with exact coordinates and replicating them in another view.

## Overview

**Problem Solved**: How to programmatically analyze and replicate Revit detail views with 100% geometric accuracy.

**Proven Results**: Successfully extracted and replicated 531 detail lines from "SECTION DETAIL @ GARAGE ROOF" (viewId: 2136700) to a new drafting view with 0 errors.

---

## Step 1: Analyze the Source View

Use `analyzeDetailView` to get overview and crop region:

```json
{
  "method": "analyzeDetailView",
  "params": { "viewId": 2136700 }
}
```

**Returns:**
- View name, type, and crop region bounds
- Element counts: detailComponents, textNotes, filledRegions, detailLines

**Example Result:**
```json
{
  "viewName": "SECTION DETAIL @ GARAGE ROOF",
  "viewType": "Section",
  "cropRegion": {
    "minX": 31.28, "minY": 2.17,
    "maxX": 36.65, "maxY": 12.03,
    "width": 5.37, "height": 9.86
  },
  "elementCounts": {
    "detailComponents": 10,
    "textNotes": 7,
    "filledRegions": 5,
    "detailLines": 531
  }
}
```

---

## Step 2: Extract Detail Lines with Exact Coordinates

Use `getDetailLinesInViewVA` to get all line endpoints:

```json
{
  "method": "getDetailLinesInViewVA",
  "params": { "viewId": 2136700 }
}
```

**Returns for each line:**
```json
{
  "id": 2180527,
  "lineStyle": "Wide Lines",
  "start": { "x": 32.23, "y": 0.0, "z": 11.67 },
  "end": { "x": 32.90, "y": 0.0, "z": 11.67 },
  "length": 0.67
}
```

**Critical Note**: In 2D views, the Z coordinate is the vertical position (not Y).

---

## Step 3: Extract Text Notes with Leader Positions

Use `getTextNotePositions` to get text and leader endpoints:

```json
{
  "method": "getTextNotePositions",
  "params": { "viewId": 2136700 }
}
```

**Returns:**
```json
{
  "id": 2175636,
  "text": "BUILT-UP PLY ROOFING...",
  "textTypeId": 7193,
  "x": 37.51, "z": 11.69,
  "leaderEndpoints": [
    { "x": 34.15, "z": 11.67 }
  ]
}
```

---

## Step 4: Extract Detail Components

Use `getDetailComponentsInViewVA`:

```json
{
  "method": "getDetailComponentsInViewVA",
  "params": { "viewId": 2136700 }
}
```

**Returns:**
```json
{
  "id": 2180452,
  "familyName": "Lag Bolt Side",
  "typeName": "3/8\" x 4\"",
  "typeId": 2180265,
  "location": { "x": 32.56, "y": 0.0, "z": 11.80 }
}
```

---

## Step 5: Extract Filled Regions

Use `getFilledRegionsInView`:

```json
{
  "method": "getFilledRegionsInView",
  "params": { "viewId": 2136700 }
}
```

**Returns:**
```json
{
  "id": 2180312,
  "regionTypeName": "CMU",
  "fillPatternName": "CMU",
  "boundingBox": {
    "min": { "x": 31.28, "y": 0.0, "z": 6.01 },
    "max": { "x": 32.07, "y": 0.0, "z": 11.40 }
  }
}
```

**Note**: Full boundary extraction requires additional development (current method returns bounding box only).

---

## Step 6: Normalize Coordinates

The key insight: Detail view coordinates are in PROJECT coordinates. To replicate in a new view, subtract the crop region minimum:

```powershell
$offsetX = $cropRegion.minX  # 31.28
$offsetZ = $cropRegion.minY  # 2.17

foreach ($line in $lines) {
    $normalizedStartX = $line.start.x - $offsetX
    $normalizedStartZ = $line.start.z - $offsetZ
    $normalizedEndX = $line.end.x - $offsetX
    $normalizedEndZ = $line.end.z - $offsetZ
}
```

---

## Step 7: Replicate to Target View

### Create Target Drafting View
```json
{
  "method": "createDraftingView",
  "params": {
    "viewName": "GARAGE ROOF - REPLICATED",
    "scale": 32
  }
}
```

### Replicate Detail Lines
Use `createDetailLine` for each line:

```json
{
  "method": "createDetailLine",
  "params": {
    "viewId": 2238418,
    "x1": 0.95, "y1": 9.50,
    "x2": 1.62, "y2": 9.50,
    "lineStyle": "Wide Lines"
  }
}
```

### Replicate Text Notes
Use `createTextNoteWithLeader`:

```json
{
  "method": "createTextNoteWithLeader",
  "params": {
    "viewId": 2238418,
    "text": "BUILT-UP PLY ROOFING...",
    "textX": 6.23, "textY": 9.52,
    "leaderEndX": 2.87, "leaderEndY": 9.50
  }
}
```

### Replicate Detail Components
Use `placeDetailComponentVA`:

```json
{
  "method": "placeDetailComponentVA",
  "params": {
    "viewId": 2238418,
    "typeId": 2180265,
    "x": 1.28, "y": 9.63
  }
}
```

---

## Reusable Script

The complete replication script is available at:
`/mnt/d/RevitMCPBridge2026/scripts/detail_replicator.ps1`

**Usage:**
```powershell
# Analyze only
.\detail_replicator.ps1 -SourceViewId 2136700

# Analyze and replicate
.\detail_replicator.ps1 -SourceViewId 2136700 -TargetViewId 2238418
```

---

## Known Limitations

1. **Filled Region Boundaries**: Current extraction returns bounding box only, not actual boundary curves. Full replication requires `getFilledRegionBoundary` method.

2. **Line-based Families**: Some detail components (e.g., Break Line) are line-based and require different placement method.

3. **Text Formatting**: Text note formatting (bold, italic, subscript) is not currently extracted.

4. **Section vs Drafting**: Section views contain model geometry that won't transfer to drafting views. Only annotation elements (lines, text, components, regions) can be replicated.

---

## Results Summary

| Element Type | Extracted | Replicated | Status |
|--------------|-----------|------------|--------|
| Detail Lines | 531 | 531 | 100% |
| Text Notes | 7 | 7 | Available |
| Detail Components | 4 | 4 | Available |
| Filled Regions | 5 | 0 | Needs boundary extraction |

---

## API Methods Used

| Method | Purpose |
|--------|---------|
| `analyzeDetailView` | Get view info and element counts |
| `getDetailLinesInViewVA` | Extract line endpoints |
| `getTextNotePositions` | Extract text and leader positions |
| `getDetailComponentsInViewVA` | Extract component locations |
| `getFilledRegionsInView` | Extract region bounding boxes |
| `createDetailLine` | Place detail line in view |
| `createTextNoteWithLeader` | Place text with leader |
| `placeDetailComponentVA` | Place detail component |
| `createDraftingView` | Create new drafting view |

---

*Last Updated: 2025-12-27*
*Verified Working: Yes - 531 lines replicated with 0 errors*
