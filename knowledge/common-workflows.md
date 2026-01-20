# Common Workflows

## Project Setup Workflow

### New Project from Template
1. Create new project from office template
2. Set project information (name, number, address, client)
3. Establish levels (Foundation, First Floor, Second Floor, Roof)
4. Set up grids if structural
5. Import/link survey or site plan
6. Create initial views
7. Set up sheets with title block

### Initial Model Setup
1. Create exterior walls at ground floor
2. Copy walls to upper levels
3. Add floors at each level
4. Place roof
5. Add stairs and railings
6. Place doors and windows
7. Add interior partitions
8. Place plumbing fixtures
9. Add casework
10. Place furniture

## Construction Document Workflow

### CD Production Sequence
```
1. Plans → 2. Elevations → 3. Sections → 4. Details → 5. Schedules
```

### Floor Plans
1. Set view range and scale
2. Add dimensions (overall, then detail)
3. Place room tags
4. Add door/window tags
5. Place text notes
6. Add section/detail callouts
7. Place on sheet

### Elevations
1. Adjust crop region
2. Add dimensions (heights, opening locations)
3. Add material tags
4. Note finishes and materials
5. Add detail callouts
6. Place on sheet

### Sections
1. Adjust crop region
2. Add level dimensions
3. Dimension openings and features
4. Add detail callouts
5. Note assemblies
6. Place on sheet

### Details
1. Draft or import detail
2. Add dimensions
3. Add text annotations
4. Add material indications
5. Reference from plans/sections

### Schedules
1. Create schedule with required fields
2. Add filters if needed
3. Sort and group appropriately
4. Format appearance
5. Place on sheet

## Quality Control Workflow

### Self-Check (Before Review)
1. Run Revit warnings check
2. Verify all views on sheets
3. Check dimension strings closed
4. Verify tag/schedule coordination
5. Run clash detection if needed
6. Review print preview

### Coordination Review
1. Export to Navisworks/BIM 360
2. Run clash detection
3. Document clashes
4. Coordinate with other disciplines
5. Update model
6. Re-run clash detection

### Issue for Review
1. Print check set (half-size)
2. Red-line markups
3. Return to drafter
4. Make corrections
5. Verify corrections made
6. Print final set

## Automation Workflows (via Claude Code)

### Batch Element Placement
1. Extract element data from source model (locations, types, rotations)
2. Export to JSON
3. Query available types in target model
4. Create type mapping
5. Place elements with PlaceFamilyInstance
6. Verify placement with screenshots

### Sheet Generation
1. Define sheet list (number, name, views)
2. Create sheets programmatically
3. Place views on sheets
4. Adjust view positions
5. Verify all views placed

### Schedule Creation
1. Define schedule parameters
2. Create schedule with CreateSchedule
3. Add fields
4. Add filters and sorting
5. Format appearance
6. Place on sheet

### Tag Placement
1. Get elements to tag
2. Determine tag family/type
3. Place tags at element locations
4. Adjust leader if needed
5. Verify all elements tagged

### Export Workflows
1. Define export settings
2. Select views/sheets to export
3. Run export (PDF, DWG, IFC)
4. Verify output files
5. Organize in delivery folder

## Deliverable Checklist

### Schematic Design (SD)
- [ ] Site plan
- [ ] Floor plans (all levels)
- [ ] Building elevations (4)
- [ ] Building section (1 min)
- [ ] 3D views/renderings
- [ ] Area calculations

### Design Development (DD)
- All SD items, plus:
- [ ] Enlarged plans (stairs, bathrooms, kitchens)
- [ ] Interior elevations (major rooms)
- [ ] Wall sections
- [ ] Door schedule
- [ ] Window schedule
- [ ] Room finish schedule
- [ ] Outline specifications

### Construction Documents (CD)
- All DD items, plus:
- [ ] Complete dimension strings
- [ ] All details (wall, roof, foundation)
- [ ] Complete schedules
- [ ] General notes
- [ ] Symbols and abbreviations
- [ ] Code analysis
- [ ] Life safety plans

## File Management

### Naming Conventions
```
ProjectNumber_ProjectName_Discipline_Description_Date.ext
Example: 2024-001_SmithResidence_A_FloorPlans_20241115.pdf
```

### Folder Structure
```
Project/
├── 00_Admin/
├── 01_Drawings/
│   ├── Revit/
│   ├── CAD/
│   └── PDF/
├── 02_Specifications/
├── 03_Submittals/
├── 04_Photos/
├── 05_Correspondence/
└── 06_Consultant/
```

### Backup Protocol
- Save locally every 30 minutes
- Sync to cloud daily
- Create dated backup before major changes
- Archive at each phase milestone

---
*Customize workflows based on project type and office standards*
