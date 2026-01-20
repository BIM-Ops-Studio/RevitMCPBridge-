# Project Templates & Standards

## Revit Template Contents

### Standard Levels
| Level Name | Elevation | Description |
|------------|-----------|-------------|
| T.O. Footing | -1'-0" | Top of foundation footing |
| First Floor | 0'-0" | Ground floor (reference) |
| Second Floor | 10'-0" | Upper floor (adjust per project) |
| Roof | 20'-0" | Roof bearing (adjust per project) |
| T.O. Roof | 22'-0" | Top of roof structure |

### Standard Views

#### Floor Plans
- First Floor Plan (1/4" = 1'-0")
- Second Floor Plan (1/4" = 1'-0")
- Roof Plan (1/8" = 1'-0")
- Site Plan (1" = 20'-0")

#### Ceiling Plans
- First Floor RCP (1/4" = 1'-0")
- Second Floor RCP (1/4" = 1'-0")

#### Elevations
- North Elevation
- South Elevation
- East Elevation
- West Elevation

#### Sections
- Building Section 1 (Longitudinal)
- Building Section 2 (Transverse)

#### 3D Views
- Default 3D
- Camera 1 (Exterior)

### Pre-loaded Families

#### Doors
- Single Flush: 2'-6", 2'-8", 3'-0"
- Double Flush: 5'-0", 6'-0"
- Sliding Glass: 6'-0", 8'-0"

#### Windows
- Fixed: 3'-0"x4'-0", 4'-0"x5'-0"
- Double Hung: 2'-6"x4'-0", 3'-0"x5'-0"
- Casement: 2'-0"x3'-0"

#### Casework
- Base Cabinet: 12", 15", 18", 24", 30", 36"
- Upper Cabinet: 12", 15", 18", 24", 30", 36"
- Counter Top: 24" depth
- Tall Cabinet: 24", 30"

#### Plumbing Fixtures
- Toilet-Domestic-3D
- Tub-Rectangular-3D
- Sink-Vanity-Round
- Sink-Kitchen-Double

#### Furniture
- Bed-Residential (Twin, Full, Queen, King)
- Sofa
- Chair-Task
- Table-Dining
- Desk

### View Templates

#### Architectural Plan
- Detail level: Medium
- Visual style: Hidden Line
- Discipline: Architectural
- Show: Furniture, Fixtures, Casework
- Hide: Structural framing, MEP

#### Reflected Ceiling Plan
- Detail level: Medium
- Visual style: Hidden Line
- Show: Ceilings, Lights, Diffusers
- Hide: Furniture, Casework

#### Elevation
- Detail level: Medium
- Visual style: Hidden Line
- Show: All architectural elements

#### Section
- Detail level: Fine
- Visual style: Hidden Line
- Far clip: Active

## Sheet Setup

### Title Block Information
```
Project Name: [PROJECT_NAME]
Project Number: [PROJECT_NUMBER]
Project Address: [ADDRESS]
Client: [CLIENT_NAME]
Architect: [FIRM_NAME]
Sheet Number: [SHEET_NUMBER]
Sheet Name: [SHEET_NAME]
Date: [ISSUE_DATE]
Drawn By: [INITIALS]
Checked By: [INITIALS]
Scale: [AS_NOTED]
```

### Standard Sheet Sizes
| Size | Dimensions | Use |
|------|------------|-----|
| ARCH D | 24" x 36" | Full set |
| ARCH C | 18" x 24" | Half-size prints |
| ANSI B | 11" x 17" | Submittals |

### Sheet Organization
```
G001 - Cover Sheet
G002 - Code Analysis
G003 - Life Safety Plan

A001 - General Notes, Symbols
A101 - First Floor Plan
A102 - Second Floor Plan
A103 - Roof Plan
A201 - North & South Elevations
A202 - East & West Elevations
A301 - Building Sections
A401 - Wall Sections
A501 - Door & Window Schedules
A502 - Room Finish Schedule
A601 - Interior Elevations
A701 - Details
```

## Parameter Standards

### Shared Parameters
| Parameter | Type | Category | Use |
|-----------|------|----------|-----|
| Mark | Text | Doors, Windows | Instance ID |
| Comments | Text | All | Notes |
| Phase Created | Phase | Elements | Phasing |
| Workset | Text | Elements | Workset ID |

### Project Parameters
| Parameter | Type | Use |
|-----------|------|-----|
| Room Finish - Floor | Text | Room schedule |
| Room Finish - Base | Text | Room schedule |
| Room Finish - Wall | Text | Room schedule |
| Room Finish - Ceiling | Text | Room schedule |

## Line Styles

### Standard Lines
| Name | Weight | Color | Pattern |
|------|--------|-------|---------|
| Thin Lines | 1 | Black | Solid |
| Medium Lines | 3 | Black | Solid |
| Wide Lines | 5 | Black | Solid |
| Hidden | 1 | Black | Hidden |
| Centerline | 1 | Black | Center |
| Demolition | 3 | Gray | Solid |

### Annotation Lines
| Name | Weight | Color | Use |
|------|--------|-------|-----|
| Dimension | 1 | Black | Dimensions |
| Leader | 1 | Black | Text leaders |

## Fill Patterns

### Solid Fills
- Solid Black
- Solid Gray (50%)
- Solid White

### Hatch Patterns
- Diagonal Up
- Diagonal Down
- Crosshatch
- Sand
- Earth
- Concrete
- Insulation

## Browser Organization

### View Organization
```
Views (all)
├── Floor Plans
│   ├── Working Views
│   └── Sheet Views
├── Ceiling Plans
├── Elevations
├── Sections
├── 3D Views
├── Legends
└── Schedules
```

### Sheet Organization
```
Sheets (all)
├── General
├── Architectural
├── Structural
├── Mechanical
├── Electrical
└── Plumbing
```

## Automation Setup

### MCP-Ready Configuration
For projects that will use Claude Code automation:

1. **Consistent naming** - Use standard family/type names
2. **Complete families** - Load all needed types upfront
3. **Clean template** - Remove unused families/views
4. **Documented standards** - This file stays with project

### Common Automation Tasks
- Batch place elements from JSON
- Generate sheets from list
- Create schedules programmatically
- Export to multiple formats
- Tag all elements of category

---
*Customize template based on project type (residential, commercial, etc.)*
