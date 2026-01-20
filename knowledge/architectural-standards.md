# Architectural Standards & Conventions

## Construction Document Standards

### Sheet Numbering System
```
[Discipline][Sheet Type][Number]

Disciplines:
- A = Architectural
- S = Structural
- M = Mechanical
- E = Electrical
- P = Plumbing

Sheet Types (Architectural):
- 0 = General, Symbols, Abbreviations
- 1 = Plans
- 2 = Elevations
- 3 = Sections
- 4 = Details
- 5 = Schedules
- 6 = Interior Elevations
- 7 = Ceiling Plans
- 8 = Roof Plans
- 9 = 3D Views

Examples:
- A101 = Architectural Floor Plan 1
- A201 = Building Elevations
- A501 = Door Schedule
```

### Drawing Scale Standards
| Drawing Type | Typical Scale |
|--------------|---------------|
| Site Plan | 1" = 20'-0" to 1" = 50'-0" |
| Floor Plans | 1/8" = 1'-0" or 1/4" = 1'-0" |
| Elevations | 1/8" = 1'-0" or 1/4" = 1'-0" |
| Building Sections | 1/4" = 1'-0" |
| Wall Sections | 3/4" = 1'-0" or 1" = 1'-0" |
| Details | 1-1/2" = 1'-0" or 3" = 1'-0" |

### Line Weights
| Line Type | Weight | Use |
|-----------|--------|-----|
| Object (cut) | Heavy (5-6) | Elements cut by view plane |
| Object (beyond) | Medium (3-4) | Elements beyond cut plane |
| Hidden | Light (1-2) | Hidden elements |
| Centerline | Light (1-2) | Center lines |
| Dimension | Light (1-2) | Dimensions, text |

## Annotation Standards

### Text Heights
| Text Type | Height | Use |
|-----------|--------|-----|
| Room Names | 3/16" | Room tags |
| Room Numbers | 1/8" | Room numbers |
| Dimensions | 3/32" | Dimension text |
| Notes | 3/32" | General notes |
| Titles | 1/4" | Drawing titles |
| Sheet Titles | 3/8" | Sheet title block |

### Dimension Standards
- Dimension to face of stud, not finish
- String dimensions from grid to grid
- Individual dimensions for openings
- Always close dimension strings
- Avoid duplicate dimensions

### Symbol Standards
```
Door Tags: Circle with door number
Window Tags: Hexagon with window type
Room Tags: Rectangle with name/number
Section Marks: Circle with section number/sheet
Detail Marks: Circle with detail number/sheet
Elevation Marks: Arrow with elevation letter
```

## Common Family Types

### Casework
- Base Cabinet (various widths: 12", 15", 18", 21", 24", 30", 33", 36", 42", 48")
- Base Cabinet - Corner
- Base Cabinet - Sink
- Upper Cabinet (same widths)
- Counter Top (24" depth standard)
- Tall Cabinet / Pantry

### Plumbing Fixtures
- Water Closet / Toilet (Domestic-3D)
- Lavatory / Sink (Vanity, Pedestal)
- Bathtub (Rectangular-3D, 60"x32" standard)
- Shower (36"x36", 48"x36")
- Kitchen Sink (Single, Double)
- Urinal

### Furniture
- Bed (Twin, Full, Queen, King)
- Nightstand
- Dresser
- Desk
- Chair (Task, Dining, Lounge)
- Sofa
- Table (Dining, Coffee, End)

### Doors
- Single Flush (various widths: 2'-6", 2'-8", 3'-0")
- Double Flush
- Sliding
- Pocket
- Bi-fold

### Windows
- Fixed
- Casement
- Double Hung
- Sliding
- Awning

## View Templates

### Plan Views
- Floor Plan (furniture, fixtures visible)
- Ceiling Plan (ceiling grid, lights, diffusers)
- Electrical Plan (outlets, switches, panels)
- Furniture Plan (just furniture)

### Section/Elevation
- Building Section (full building cut)
- Wall Section (detailed wall assembly)
- Interior Elevation (cabinet faces, tile)

## Quality Control Checklist

### Before Issuing
- [ ] All views placed on sheets
- [ ] Title blocks complete
- [ ] Dimensions complete and coordinated
- [ ] Notes and legends placed
- [ ] Schedules complete
- [ ] Room tags in all rooms
- [ ] Door/window tags match schedules
- [ ] Section/detail marks reference correct sheets
- [ ] Scale noted on all views
- [ ] North arrow on plans

---
*Fill in specific office standards as needed*
