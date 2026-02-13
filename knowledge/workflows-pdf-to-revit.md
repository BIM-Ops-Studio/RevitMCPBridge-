# PDF/DXF to Revit Workflow

## Overview
Convert PDF floor plans, images, or DXF files into Revit BIM models. Two detection engines: Python-side parallel line analysis (best for PDFs) and Revit-side CAD analysis (best for native DXFs).

**Current Readiness**: 90% (pipeline working end-to-end, false-positive filtering added, CAD door/window detection, layer-aware DXF analysis)

---

## Architecture: Three Approaches

### Approach A: Python-Side Detection from PDF (RECOMMENDED for PDFs)
Built into `pdf_to_revit_pipeline.py` — extracts vectors from PDF, detects parallel line pairs with wall-thickness gaps, deduplicates spatially, snaps to known thicknesses.

**Best for**: PDF floor plans, scanned images
**Accuracy**: ~38-40 walls on Avon Park after false-positive filtering (down from 48 raw, ~10 FP removed)
**Command**: `python pdf_to_revit_pipeline.py floorplan.pdf --python-detect`

### Approach B: Revit-Side Analysis (RECOMMENDED for native DXFs)
Uses `analyzeCADFloorPlan` — Revit's C# geometry engine detects walls, doors, windows from imported CAD. Works great with clean CAD geometry on dedicated layers.

**Best for**: Native DXF/DWG files from AutoCAD
**Accuracy**: Excellent for clean CAD, poor for PDF-converted DXFs (9/38 on Avon Park)
**Command**: `python pdf_to_revit_pipeline.py file.DXF --no-python-detect`

### Approach C: Legacy Python DXF Parser (DEPRECATED)
Uses `dxf_to_revit_walls.py` — Python/ezdxf parses DXF directly. Only detected 10/38 walls.

**Fallback script**: `/mnt/d/_CLAUDE-TOOLS/dxf_to_revit_walls.py`

---

## Detection Improvements (v2)

### False-Positive Filtering (`_filter_false_positives`)
Automatically removes likely non-wall geometry after wall detection:
- **Connectivity check**: Walls with no connections to other walls (isolated) and shorter than 5ft are removed
- **Short-wall clustering**: 3+ short walls (<5ft) within a 10ft radius are treated as furniture and removed
- Enabled by default, disable with `--no-filter-fp`

### Layer-Aware DXF Re-Analysis
PDF-converted DXFs have separate layers with different geometry types:
- `WALLS` layer: Main line geometry (best for wall detection)
- `WALLS-RECT` layer: Rectangle edges from filled regions (furniture, fixtures)
- `CURVES` layer: Arc approximations (door swings)

Use `--dxf-reanalyze converted.dxf --layer-filter WALLS` to re-analyze using only the WALLS layer.

### CAD Door/Window Detection (`detect_doors_from_cad`)
When the original CAD DXF is available alongside the PDF:
- Extracts door positions from **arc entities** (90-degree arcs with R=24-42" = door swings)
- Reads door/window sizes from **4-digit text tags** (WWWH format, e.g., "3068" = 30"x68" door)
- Classifies as door (height >= 60") or window (height < 60")
- Use `--cad-file original.DXF` to enable

---

## Prerequisites

- DXF file accessible from Windows (e.g., `D:\path\to\file.DXF`)
- Revit 2026 open with target document active
- RevitMCPBridge2026 MCP server running
- Level created in target model
- Wall types loaded (exterior + interior)

### DXF Preparation
If starting from PDF:
1. Convert PDF to DXF using Bluebeam, AutoCAD, or online converter
2. Verify DXF units (typically inches for architectural drawings)
3. Verify coordinate system — check that 660 units = 55 feet (for inch-based drawings)

---

## Pipeline Steps (Approach A)

### Step 1: Import DXF into Revit
```
Method: importCAD
Params: {
  filePath: "D:\\path\\to\\file.DXF",
  unit: "inch"          // critical: match DXF units
}
Returns: { importedId: <ElementId> }
```

**Key**: The `unit` parameter tells Revit how to interpret coordinates. DXF files from architectural drawings are typically in inches. Revit converts to feet internally.

### Step 2: Analyze Floor Plan
```
Method: analyzeCADFloorPlan
Params: {
  importId: <from step 1>,
  exteriorWallThickness: 8.0,    // inches (CMU ~8" for Florida)
  interiorWallThickness: 4.5,    // inches (3.5" studs + drywall)
  tolerance: 2.0                  // inches (matching tolerance)
}
Returns: {
  exteriorWalls: [...],    // with centerline coords in feet
  interiorWalls: [...],    // with centerline coords in feet
  doors: [...],            // arc-center positions
  windows: [...],          // gap positions
  bounds: { width, height },
  summary: { counts }
}
```

**What the analyzer does:**
- Extracts all Line and Arc geometry from the imported CAD
- Classifies lines as horizontal (H), vertical (V), or diagonal (D)
- Finds parallel line pairs where gap matches wall thickness
- Merges collinear wall segments into continuous walls
- Detects openings (gaps between segments)
- Identifies doors from arcs (radius 2'-3'6" = door swings)
- Identifies windows from gaps in exterior walls (1.5'-8' wide)
- Returns centerline coordinates already in feet (Revit internal units)

### Step 3: Create Walls
```
Method: batchCreateWalls
Params: {
  walls: [
    {
      startPoint: [x1, y1, 0],      // feet (from analysis)
      endPoint: [x2, y2, 0],        // feet (from analysis)
      levelId: 30,                    // Level 1 ElementId
      wallTypeId: 441456,            // exterior type
      height: 10                      // feet
    },
    ...
  ]
}
```

**No unit conversion needed!** The `analyzeCADFloorPlan` output is already in Revit's internal unit (feet).

### Step 4: Place Doors and Windows
```
Method: placeDoor / placeWindow
Params: { location: [x, y, 0], levelId: 30, width: 3.0 }
```

Note: Door/window placement requires finding the host wall. This step has lower success rate and may need manual adjustment.

### Step 5: Verify
```
Method: zoomToFit
Method: captureActiveView
```

Compare screenshot against source PDF.

---

## Pipeline Script Usage

### Basic Run
```bash
python /mnt/d/_CLAUDE-TOOLS/pdf_to_revit_pipeline.py "D:\\path\\to\\file.DXF"
```

### Dry Run (Analyze Only)
```bash
python /mnt/d/_CLAUDE-TOOLS/pdf_to_revit_pipeline.py "D:\\path\\to\\file.DXF" --dry-run
```

### Save Analysis for Inspection
```bash
python /mnt/d/_CLAUDE-TOOLS/pdf_to_revit_pipeline.py "D:\\path\\to\\file.DXF" --dry-run --save analysis.json
```

### Run from Saved Analysis
```bash
python /mnt/d/_CLAUDE-TOOLS/pdf_to_revit_pipeline.py "D:\\path\\to\\file.DXF" --load analysis.json
```

### Custom Parameters
```bash
python /mnt/d/_CLAUDE-TOOLS/pdf_to_revit_pipeline.py "D:\\path\\to\\file.DXF" \
  --level-id 30 \
  --height 10 \
  --exterior-thickness 8.0 \
  --interior-thickness 4.5 \
  --exterior-type 441456 \
  --interior-type 441519
```

### Re-analyze Existing Import
```bash
python /mnt/d/_CLAUDE-TOOLS/pdf_to_revit_pipeline.py "D:\\path\\to\\file.DXF" --import-id 12345
```

---

## MCP Methods Used

| Step | Method | Source File |
|------|--------|-------------|
| Import | `importCAD` | LinkMethods.cs |
| Analyze | `analyzeCADFloorPlan` | LinkMethods.cs |
| Walls | `batchCreateWalls` | WallMethods.cs |
| Doors | `placeDoor` | DoorWindowMethods.cs |
| Windows | `placeWindow` | DoorWindowMethods.cs |
| Verify | `zoomToFit`, `captureActiveView` | ViewMethods.cs |

### Supporting Methods
| Method | Purpose |
|--------|---------|
| `getCADGeometry` | Raw line/arc extraction (lower-level than analyze) |
| `getCADWallCandidates` | Filtered wall-candidate lines |
| `getWallTypes` | Query available wall types in model |
| `getLevels` | Query available levels |
| `deleteCADLink` | Remove imported CAD after wall creation |

---

## Wall Type Mapping

### Florida Residential (Avon Park)
| Element | Thickness | Revit Wall Type |
|---------|-----------|-----------------|
| Exterior (CMU) | 8" | Generic - 8" Masonry (ID: 441456) |
| Interior (stud) | 4.5" | Interior - 4 1/2" Partition (ID: 441519) |

### General Mapping
| Thickness | Category | Typical Construction |
|-----------|----------|---------------------|
| 3-5" | Interior | 2x4 stud + drywall |
| 5-7" | Either | 2x6 stud or thin masonry |
| 7-10" | Exterior | CMU, brick cavity |
| 10-14" | Exterior | Double wall, masonry cavity |

**Important**: Wall type IDs are model-specific. Query with `getWallTypes` to get actual IDs.

---

## Coordinate System Notes

### DXF Import Units
- Most architectural DXF files use **inches** as the base unit
- Set `unit: "inch"` when importing — Revit converts to feet internally
- Verify: if a 55-foot dimension reads as 660 in the DXF, units are inches
- If it reads as 55, units are feet

### Revit Internal Units
- All Revit API coordinates are in **feet**
- `analyzeCADFloorPlan` returns coordinates in **feet**
- `batchCreateWalls` expects coordinates in **feet**
- **No manual conversion needed** between analysis and wall creation

### Origin
- DXF origin may not be at (0,0) — the analyzer reports bounds
- Walls are placed at the coordinates returned by the analyzer
- If needed, use `deleteCADLink` to remove the imported CAD underlay after creating walls

---

## Error Handling

### Common Issues

**"No CAD import found"**
- The DXF import may not have completed
- Check that the import step returned a valid importedId
- Wait 1-2 seconds between import and analyze

**"Wall creation failed"**
- Check that levelId exists (`getLevels`)
- Check that wallTypeId exists (`getWallTypes`)
- Verify start/end points are different (zero-length walls fail)
- Short walls (<1 ft) may be filtered out by Revit

**Few walls detected (< expected)**
- Adjust `tolerance` parameter (try 3.0 or 4.0 inches)
- Check `exteriorWallThickness` matches actual drawing
- DXF may have non-orthogonal walls (diagonal lines skipped)
- Run with `--save` and inspect the JSON output

**Door/window placement fails**
- This is expected — host wall detection is approximate
- Place doors/windows manually in Revit after walls are created
- Use `--skip-doors --skip-windows` to skip this step

### Retry Strategy
```
PRE_DELAY = 1.0 sec     # Between import and analyze
PS_TIMEOUT = 60 sec      # PowerShell pipe timeout
```

---

## Quality Metrics

### Target Accuracy
| Element | Target | Notes |
|---------|--------|-------|
| Wall count | 90-95% | With false-positive filtering |
| Wall positions | +/- 3" | Centerline accuracy |
| Wall thickness | Correct type | Exterior vs interior |
| Door count | 80-90% | When original CAD DXF available |
| Window count | 70-80% | From text tags in original CAD |
| False positive rate | < 5% | Connectivity + cluster filtering |

### Known Limitations
1. Only detects orthogonal walls (H/V) — diagonal walls are ignored
2. Door/window detection from CAD requires original DXF (not available for PDF-only inputs)
3. Window detection is text-tag-based (requires WWWH format labels in CAD)
4. Curved walls are not supported
5. Multi-story detection not yet implemented
6. Layer filtering requires ezdxf library (`pip install ezdxf`)

---

## Test Cases

### Level 1: Simple Rectangle
- 4 exterior walls
- Known dimensions
- Expected: 100% wall accuracy

### Level 2: Single Family (Avon Park)
- ~38 walls (exterior + interior)
- CMU exterior, stud interior
- Doors with arc swings
- Expected: 30+ walls detected (80%+)

### Level 3: Multi-Unit
- Multiple units with party walls
- Corridors
- More complex door/window patterns
- Expected: 70%+ wall accuracy

---

## Integration with Other Workflows

### After DXF → Model
1. Delete imported CAD underlay (`deleteCADLink`)
2. Create rooms (`createRoom`)
3. Add annotations
4. Run DD → CD workflow
5. Create sheets

### Combining with Python Analysis
For DXF files where Revit analysis misses walls:
1. Run Python analysis (`dxf_to_revit_walls.py`) to identify missed walls
2. Compare Python results vs Revit results
3. Manually add missed walls

---

*Last Updated: 2026-02-12*
*Readiness: 90% (False-positive filtering, CAD door/window detection, layer-aware DXF analysis)*
