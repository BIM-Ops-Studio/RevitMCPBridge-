# Construction Document Checklist

A comprehensive checklist for architectural construction document sets.
**Designed for automation via RevitMCPBridge MCP methods.**

---

## MASTER SHEET LIST (Industry Standard)

### Common Sheet Numbering Conventions
| Convention | Example | Common In |
|------------|---------|-----------|
| Dot Notation | A1.0, A1.1 | Mid-size firms |
| Hyphen | A-101, A-102 | AIA standard |
| Simple | A100, A101 | Small projects |
| Sub-numbered | A3.0.1, A3.0.2 | Large projects |

### Required Sheets by Category [MCP: `getSheets()`]

| Category | Content | Min Sheets | Required |
|----------|---------|------------|----------|
| **General** | Cover, Notes, Symbols | 1-2 | ✓ |
| **Site** | Site Plan | 1 | ✓ |
| **Floor Plans** | Each level + Roof | 2+ | ✓ |
| **RCP** | Reflected Ceiling Plans | 1+ | Commercial ✓ |
| **Elevations** | All 4 sides | 1-2 | ✓ |
| **Sections** | Building Sections | 1-2 | ✓ |
| **Wall Sections** | Typical assemblies | 1-3 | ✓ |
| **Details** | Construction details | 2+ | ✓ |
| **Schedules** | Door, Window, Finish | 1-2 | ✓ |

### NCS (National CAD Standard) Sheet Categories
```
G = General (Cover, Code, Life Safety)
H = Hazardous Materials
V = Survey/Mapping
B = Geotechnical
C = Civil
L = Landscape
S = Structural
A = Architectural
I = Interiors
Q = Equipment
F = Fire Protection
P = Plumbing
D = Process
M = Mechanical
E = Electrical
W = Distributed Energy
T = Telecommunications
R = Resource
X = Other Disciplines
Z = Contractor/Shop Drawings
O = Operations
```

### Typical A-Sheet Breakdown (AIA/NCS Standard)
```
A0## = General, Symbols, Schedules
A1## = Plans (Site, Floor, Roof)
A2## = Elevations
A3## = Sections
A4## = Large Scale Plans (Enlarged)
A5## = Interior Elevations
A6## = Schedules (alternate location)
A7## = Vertical Circulation
A8## = Exterior Details
A9## = Interior Details
```

---

## COVER SHEET / GENERAL (A0.0)

### Project Information [MCP: `getProjectInfo`]
- [ ] Project name ← `getProjectInfo().name`
- [ ] Project address ← `getProjectInfo().address`
- [ ] Legal description (manual)
- [ ] Owner name and contact ← `getProjectInfo().clientName`
- [ ] Architect name, license number ← `getProjectInfo().organizationName`
- [ ] Project team list (consultants, engineers)

### Sheet Index [MCP: `getSheets`, `createSheetList`]
- [ ] Sheet index with sheet numbers and titles ← `createSheetList()`
- [ ] Drawing issue dates ← `getProjectInfo().issueDate`
- [ ] Revision history (manual or `getRevisions`)

### Code Summary [Manual - consider adding to Project Info]
- [ ] Occupancy classification
- [ ] Construction type
- [ ] Sprinklered (Y/N)
- [ ] Allowable area calculation
- [ ] Building height
- [ ] Number of stories
- [ ] Gross building area ← `getAreaSchedules()`

### Standards References
- [ ] Applicable codes listed (FBC 2023, IRC, etc.)
- [ ] Location map / vicinity map
- [ ] General notes
- [ ] Abbreviations list (A0.1)
- [ ] Symbol legend (A0.1)
- [ ] Life safety plan (if required)

---

## SITE PLAN (A1.0)

### Property & Setbacks [Manual/Civil]
- [ ] Property lines with dimensions
- [ ] Setback lines (front, side, rear)
- [ ] Easements
- [ ] Building footprint with dimensions to property lines

### Site Elements [MCP: `getElements(category='Site')`]
- [ ] Existing structures (if any)
- [ ] Parking layout with accessible spaces
- [ ] Driveways and curb cuts
- [ ] Sidewalks and walkways
- [ ] Landscaping (trees, planters, lawn areas)
- [ ] Fencing and gates
- [ ] Dumpster/trash enclosure location
- [ ] Signage locations

### Utilities & Grading [Civil Coordination]
- [ ] Site utilities (water, sewer, electric, gas connections)
- [ ] Stormwater management (retention, swales, drains)
- [ ] Grading and spot elevations
- [ ] Finish floor elevation (FFE) ← `getLevels()`

### Drawing Standards
- [ ] North arrow ← `getViewByName()` check for north symbol
- [ ] Scale noted
- [ ] Site lighting shown

---

## FLOOR PLANS (A2.x)

### Required Plans [MCP: `getViewsByType('FloorPlan')`, `getLevels()`]
- [ ] All levels including basement/crawl space ← `getLevels()` vs views
- [ ] Roof plan (A2.4 or separate) ← `getViewByName('Roof Plan')`

### Rooms [MCP: `getRooms()`, `getRoomByName()`]
- [ ] Room names and numbers ← `getRooms()` verify all rooms named/numbered
- [ ] Room dimensions (in schedule or on plan)
- [ ] Room areas ← `getRooms().area`

### Doors & Windows [MCP: `getDoors()`, `getWindows()`]
- [ ] Door swings shown ← `getDoors()`
- [ ] Door numbers/tags ← verify `mark` parameter populated
- [ ] Window locations and tags ← `getWindows()` with marks

### Walls [MCP: `getWalls()`, `getWallTypes()`]
- [ ] Wall types identified ← `getWalls()` check type names
- [ ] Partition locations
- [ ] Rated walls/assemblies indicated (fire rating in type name)

### Dimensions [MCP: `getDimensions()` if available]
- [ ] Overall building dimensions
- [ ] Room dimensions

### Vertical Circulation [MCP: `getStairs()`]
- [ ] Stairs with UP/DN arrows, riser count
- [ ] Elevators and shafts

### Structure [Coordinate with S-sheets]
- [ ] Column grid lines ← `getGrids()`
- [ ] Structural elements visible (beams, columns)

### MEP Coordination [Show on A or separate M/P/E]
- [ ] Mechanical equipment locations
- [ ] Plumbing fixtures ← `getElements(category='PlumbingFixtures')`
- [ ] Electrical panels (general location)

### Finishes & Casework
- [ ] Built-in casework and millwork
- [ ] Floor finish changes/transitions
- [ ] Floor drains

### References [MCP: Verify callouts have targets]
- [ ] Section cut references ← `getSections()` verify on sheets
- [ ] Detail callouts
- [ ] Interior elevation references
- [ ] North arrow and scale

---

## ROOF PLAN (A2.4)

### Roof Geometry [MCP: `getRoofs()`]
- [ ] Roof outline and overhangs ← `getRoofs()` geometry
- [ ] Roof slopes with arrows and ratios ← `getRoofSlope()`
- [ ] Ridge, valley, hip lines
- [ ] Parapet walls ← `getWalls()` filter by height

### Drainage [Show on plan]
- [ ] Roof drains and overflow drains
- [ ] Scuppers and downspout locations
- [ ] Crickets and saddles

### Penetrations & Equipment
- [ ] Roof penetrations (vents, pipes, equipment)
- [ ] Mechanical equipment on roof ← `getElements(category='MechanicalEquipment')`
- [ ] Access hatches/doors
- [ ] Roof anchors/fall protection
- [ ] Roof walkway pads
- [ ] Solar panel layout (if applicable)

### Materials & Notes
- [ ] Roof materials noted (in type or annotation)
- [ ] Expansion joints shown

### References
- [ ] Section references to A7.x and A8.x

---

## EXTERIOR ELEVATIONS (A5.x)

### Required Elevations [MCP: `getElevations()`]
- [ ] All four elevations created ← `getElevations()` count ≥ 4
- [ ] Placed on sheets A5.0, A5.1 ← `getViewportsOnSheet()`

### Vertical Dimensions [MCP: `getLevels()`]
- [ ] Finish floor lines with elevations ← `getLevels()` values
- [ ] Grade line elevation
- [ ] Roof ridges and eaves with elevations
- [ ] Top of parapet elevations

### Openings [MCP: Count matches floor plans]
- [ ] Window openings shown ← count vs `getWindows()`
- [ ] Door openings shown ← count vs `getDoors()`

### Materials & Finishes [Annotation]
- [ ] Exterior materials noted (keynotes or text)
- [ ] Control joints
- [ ] Expansion joints

### Accessories
- [ ] Downspouts
- [ ] Light fixtures
- [ ] Address numbers
- [ ] Signage
- [ ] Louvers and vents
- [ ] Mechanical equipment screens
- [ ] Railing types

### References
- [ ] Wall section references to A8.x
- [ ] Detail callouts to A9.x or AD-###

---

## BUILDING SECTIONS (A7.x)

### Required Sections [MCP: `getSections()`]
- [ ] Longitudinal section(s) ← `getSections()` through length
- [ ] Transverse section(s) ← `getSections()` through width
- [ ] Placed on sheets A7.0, A7.1 ← `getViewportsOnSheet()`

### Vertical Dimensions [MCP: `getLevels()`]
- [ ] Floor-to-floor heights ← compute from `getLevels()`
- [ ] Ceiling heights (coordinate with RCP)
- [ ] Level markers shown

### Assemblies Shown [Visual verification]
- [ ] Roof structure/assembly shown
- [ ] Foundation shown
- [ ] Wall assemblies indicated
- [ ] Floor assemblies indicated

### Vertical Elements
- [ ] Stairs in section ← `getStairs()`
- [ ] Elevator shafts
- [ ] Mechanical shafts

### References
- [ ] Grid lines shown ← `getGrids()`
- [ ] Detail references to A8.x (wall sections)

---

## WALL SECTIONS (A8.x)

### Required Wall Sections [MCP: `getSections()` filter by type]
- [ ] Typical wall section for each exterior wall type ← `getWallTypes()` exterior
- [ ] Placed on sheets A8.0, A8.1, A8.2 ← `getViewportsOnSheet()`

### Full Assembly (Foundation to Roof)
- [ ] Foundation/footing shown
- [ ] Slab edge/foundation wall connection
- [ ] Floor-to-wall connection
- [ ] Roof edge/parapet details

### Opening Details [AD sheets or A9.x]
- [ ] Window head, jamb, sill details
- [ ] Door head, jamb, threshold details

### Waterproofing & Insulation
- [ ] Flashing details
- [ ] Waterproofing details (below grade)
- [ ] Insulation locations and R-values
- [ ] Air barrier/vapor barrier shown

### Annotations
- [ ] Material callouts (keynotes)
- [ ] Dimensions
- [ ] Fire-rated assembly details (if applicable)

---

## REFLECTED CEILING PLANS (A3.x)

### Required RCPs [MCP: `getViewsByType('CeilingPlan')`]
- [ ] RCP for each floor level ← compare `getLevels()` to RCP views
- [ ] Placed on sheets A3.0, A3.1 ← `getViewportsOnSheet()`

### Ceiling Information [MCP: `getCeilings()`]
- [ ] Ceiling heights noted ← `getCeilings()` + room height
- [ ] Ceiling materials/types shown
- [ ] Ceiling grid layout (if ACT)
- [ ] Ceiling soffits and bulkheads

### MEP Coordination [Show ceiling-mounted items]
- [ ] Light fixture locations ← `getElements(category='LightingFixtures')`
- [ ] Diffusers and return grilles
- [ ] Sprinkler heads
- [ ] Access panels
- [ ] Smoke detectors
- [ ] Exit signs
- [ ] Speakers/PA system
- [ ] Ceiling-mounted equipment

### References
- [ ] Section references for ceiling details

---

## INTERIOR ELEVATIONS (A5## or separate sheets)

### Required Interior Elevations [MCP: `getViewsByType('Elevation')` filter interior]
- [ ] Kitchen elevations - all walls ← `getRooms()` where name='Kitchen'
- [ ] Bathroom elevations - all walls ← `getRooms()` where name contains 'Bath'
- [ ] Laundry room elevations
- [ ] Special rooms (lobby, conference if commercial)

### Casework & Millwork
- [ ] Casework elevations ← `getElements(category='Casework')`
- [ ] Countertop heights (36" standard, 34" accessible)
- [ ] Backsplash heights (typically 18"-20")
- [ ] Upper cabinet heights

### Accessories & Coordination
- [ ] Mirror and accessory locations
- [ ] Outlet and switch locations (coordinate with E sheets)
- [ ] Tile patterns/layouts where applicable

### Annotations
- [ ] Material callouts (keynotes or text)
- [ ] Dimensions

---

## SCHEDULES [MCP: `getAllSchedules()`, `getScheduleData()`]

### Door Schedule [MCP: `getDoorSchedule()` or create with `createSchedule()`]
**Required Fields:**
| Field | Source | MCP Verifiable |
|-------|--------|----------------|
| Door Mark | Instance | `getDoors().mark` |
| Width | Type | `getDoors().width` |
| Height | Type | `getDoors().height` |
| Type/Style | Type | `getDoors().typeName` |
| Material | Type parameter | Check exists |
| Frame Type | Type parameter | Check exists |
| Frame Material | Type parameter | Check exists |
| Hardware Set | Instance parameter | Check exists |
| Fire Rating | Type parameter | If rated wall |
| Glazing | Type parameter | If applicable |
| Remarks | Instance parameter | Optional |

**Verification:** `getDoors()` count = schedule row count

### Window Schedule [MCP: `getWindowSchedule()` or create]
**Required Fields:**
| Field | Source | MCP Verifiable |
|-------|--------|----------------|
| Window Mark | Instance | `getWindows().mark` |
| Width | Type | `getWindows().width` |
| Height | Type | `getWindows().height` |
| Type | Type | casement, DH, fixed |
| Frame Material | Type parameter | |
| Glazing Type | Type parameter | Impact, Low-E, etc. |
| U-value | Type parameter | Energy code |
| SHGC | Type parameter | Energy code |
| Operation | Type parameter | |
| Remarks | Instance parameter | |

**Verification:** `getWindows()` count = schedule row count

### Room/Finish Schedule [MCP: `getRooms()`]
**Required Fields:**
| Field | Source | MCP Verifiable |
|-------|--------|----------------|
| Room Number | `getRooms().number` | ✓ |
| Room Name | `getRooms().name` | ✓ |
| Area | `getRooms().area` | ✓ |
| Floor Finish | Room parameter | ✓ |
| Base Type | Room parameter | ✓ |
| Wall Finish | Room parameter | ✓ |
| Ceiling Finish | Room parameter | ✓ |
| Ceiling Height | Room parameter | ✓ |
| Remarks | Room parameter | |

**Verification:** All rooms have finishes populated (no blanks)

### Additional Required Schedules
| Schedule | Category | Required | MCP Method |
|----------|----------|----------|------------|
| Sheet Index | Sheets | ✓ | `getSheets()` |
| Plumbing Fixture | Plumbing | Commercial | `getElements(category='PlumbingFixtures')` |
| Lighting Fixture | Lighting | Commercial | `getElements(category='LightingFixtures')` |
| Equipment | Equipment | As needed | `getElements(category='SpecialtyEquipment')` |
| Hardware Sets | Custom | ✓ | Manual or legend |
| Key Legend | Custom | If keyed | Manual |

### Schedule Verification Checklist
- [ ] All schedules placed on sheets ← `getViewportsOnSheet()`
- [ ] Schedule row count matches element count
- [ ] No blank required fields
- [ ] Consistent naming/numbering
- [ ] Sorted appropriately (by mark or location)

---

## STAIR AND RAILING DETAILS [MCP: `getStairs()`, `getRailings()`]

### Stair Views Required
- [ ] Stair plans at each level ← `getStairs()` verify on floor plans
- [ ] Stair sections (minimum 1 per stair)
- [ ] Enlarged stair plan if complex

### Code Compliance [IBC Chapter 10]
| Item | Requirement | MCP Check |
|------|-------------|-----------|
| Tread depth | 11" min (10" residential) | `getStairs().treadDepth` |
| Riser height | 7" max (7-3/4" residential) | `getStairs().riserHeight` |
| Stair width | 44" min (36" <50 occ.) | `getStairs().width` |
| Headroom | 6'-8" min | Verify in section |
| Handrail height | 34"-38" | `getRailings().height` |
| Guard height | 42" min (36" residential) | `getRailings().height` |
| Landing depth | = stair width | `getStairs().landingLength` |

### Details Required
- [ ] Nosing detail (1" max projection, ½" min radius)
- [ ] Handrail profile detail (graspable 1¼"-2")
- [ ] Handrail extensions (12" top, tread + 12" bottom)
- [ ] Intermediate rails (4" sphere rule)
- [ ] Post spacing and attachment
- [ ] ADA-compliant extensions shown

---

## ACCESSIBILITY (ADA/FHA) [Partially MCP Verifiable]

### Site Accessibility
- [ ] Accessible route shown on plans
- [ ] Accessible parking spaces (1 per 25, van accessible)
- [ ] Curb ramps (1:12 max slope)

### Door Requirements [MCP: `getDoors()`]
| Item | Requirement | MCP Check |
|------|-------------|-----------|
| Clear width | 32" min | `getDoors().width` ≥ 34" nominal |
| Maneuvering clearance | 18" pull side, 12" push | Manual |
| Hardware height | 34"-48" AFF | Manual |
| Threshold | ½" max (¾" exterior) | Manual |
| Closers | 5 sec. sweep, 3 lb. max | Manual |

### Circulation [MCP: Partial]
- [ ] Hallway widths ← `getWalls()` spacing ≥ 36" (44" typical)
- [ ] Turning radius at doors (60" circle or T-turn)
- [ ] No protruding objects >4" (27"-80" height)

### Accessible Restrooms [MCP: `getRooms()` filter bathrooms]
| Item | Requirement | MCP Check |
|------|-------------|-----------|
| 60" turning | Clear floor space | Room area check |
| Toilet clearance | 60" wide, 56" deep | Manual |
| Lavatory knee space | 27" high, 8" deep, 30" wide | Manual |
| Grab bars | 42" side, 36" rear | Manual |
| Mirror | 40" max to bottom | Manual |

### Counters & Signage
- [ ] Counter heights (34" max at accessible section)
- [ ] Knee clearance (27" high, 17" deep)
- [ ] Accessible signage (60" centerline, tactile)
- [ ] Visual alarms (in common areas & restrooms)

---

## FIRE/LIFE SAFETY [MCP: Partial - requires code calculations]

### Egress Requirements [IBC Chapter 10]
| Item | Requirement | MCP Check |
|------|-------------|-----------|
| Number of exits | 2 min (≥500 SF or >49 occ.) | `getRooms()` check SF |
| Exit separation | ½ diagonal | Manual measurement |
| Travel distance | 200'-300' (by occ.) | Path analysis |
| Common path | 75' max (sprinklered) | Manual |
| Dead-end corridor | 50' max (sprinklered) | Manual |
| Exit width | 0.2" per occ. (stair), 0.15" (other) | Calculate |

### Exit Identification
- [ ] Exit locations marked on plans
- [ ] Exit signage shown ← `getElements(category='LightingFixtures')` filter exit
- [ ] Emergency lighting shown
- [ ] Exit discharge path to public way

### Fire-Rated Construction [MCP: `getWalls()` check type names]
- [ ] Fire-rated walls identified (keyword search in type names)
- [ ] Fire-rated doors and frames ← `getDoors()` check fire rating param
- [ ] Opening protectives shown
- [ ] Fire dampers at rated penetrations
- [ ] Smoke barriers (if Group I or high-rise)
- [ ] Area of refuge (if not sprinklered high-rise)

### Fire Protection Systems
- [ ] Sprinkler coverage indicated (if sprinklered)
- [ ] Standpipe locations (if >3 stories)
- [ ] Fire extinguisher locations (75' travel)
- [ ] Fire alarm devices (pull stations, horns/strobes)
- [ ] Smoke detectors
- [ ] CO detectors (where fuel-burning appliances)

---

## STRUCTURAL (Coordinate with Engineer)

- [ ] Foundation plan
- [ ] Framing plans (floor, roof)
- [ ] Structural sections
- [ ] Column schedule
- [ ] Beam schedule
- [ ] Footing schedule
- [ ] Connection details
- [ ] Hold-down and anchor bolt locations
- [ ] Shear wall schedule
- [ ] Structural notes

---

## MECHANICAL/HVAC (Coordinate with Engineer)

- [ ] Equipment schedules
- [ ] Duct layouts
- [ ] Diffuser and grille locations
- [ ] Thermostat locations
- [ ] Outside air intake
- [ ] Exhaust locations
- [ ] Refrigerant piping (if split systems)
- [ ] Mechanical room layouts
- [ ] Equipment clearances
- [ ] Mechanical details

---

## ELECTRICAL (Coordinate with Engineer)

- [ ] Panel locations and schedules
- [ ] Meter location
- [ ] Service entrance
- [ ] Receptacle layouts
- [ ] Switch layouts
- [ ] Lighting layouts
- [ ] Lighting fixture schedule
- [ ] Circuit assignments
- [ ] Emergency/standby power
- [ ] Fire alarm system
- [ ] Low voltage systems
- [ ] Electrical details

---

## PLUMBING (Coordinate with Engineer)

- [ ] Fixture schedule
- [ ] Fixture locations on plans
- [ ] Water heater location and specs
- [ ] Piping diagrams (riser diagrams)
- [ ] Cleanout locations
- [ ] Backflow preventers
- [ ] Shut-off valves
- [ ] Hose bibs
- [ ] Floor drains
- [ ] Roof drains
- [ ] Gas piping (if applicable)
- [ ] Plumbing details

---

## FLORIDA-SPECIFIC REQUIREMENTS

- [ ] Product approvals for windows/doors
- [ ] Impact-rated glazing or shutters (HVHZ)
- [ ] Wind load design noted
- [ ] Roof tie-down/uplift connections
- [ ] Flood zone compliance (if applicable)
- [ ] Energy code compliance (Form R402/R405)
- [ ] Termite protection noted
- [ ] FL Building Code edition noted
- [ ] NOA numbers for products (HVHZ)
- [ ] Concrete/masonry specifications for hurricane
- [ ] Secondary water barrier (HVHZ roofs)

---

## QUALITY CONTROL - FINAL REVIEW [MCP: Mostly Automatable]

### Sheet Verification [MCP: `getSheets()`, `getViewportsOnSheet()`]
- [ ] All sheets numbered correctly ← `getSheets()` check sequence
- [ ] Sheet titles match index ← Compare schedule to sheet data
- [ ] Revision blocks updated ← `getRevisions()` check dates
- [ ] All views placed on sheets ← Orphan view detection

### Drawing Standards [MCP: View property checks]
- [ ] North arrows on all plans ← Check for north symbol family
- [ ] Scales noted and correct ← `getViews().scale`
- [ ] Dimensions add up correctly ← Manual spot check

### Cross-Reference Verification [MCP: Automatable]
- [ ] Door tags match schedule ← `getDoors().count` = schedule rows
- [ ] Window tags match schedule ← `getWindows().count` = schedule rows
- [ ] Room names/numbers consistent ← `getRooms()` no duplicates
- [ ] Section cuts reference correct details
- [ ] Detail callouts have corresponding details
- [ ] No orphan references

### Coordination [Manual]
- [ ] Consultant drawings coordinated
- [ ] Specifications match drawings
- [ ] Code review complete
- [ ] Client review/approval obtained

---

## AUTOMATION SUMMARY

### Fully Automatable via MCP
These checks can run automatically with existing MCP methods:

| Check | Method | Pass Criteria |
|-------|--------|---------------|
| Required sheets exist | `getSheets()` | All required sheets present |
| All levels have plans | `getLevels()` vs `getViewsByType('FloorPlan')` | 1:1 match |
| All rooms named | `getRooms()` | No blank names |
| All rooms numbered | `getRooms()` | No blank numbers |
| Doors have marks | `getDoors()` | All marks populated |
| Windows have marks | `getWindows()` | All marks populated |
| Schedules match elements | Count comparison | Exact match |
| Views on sheets | `getViewportsOnSheet()` | No orphan views |
| Project info complete | `getProjectInfo()` | Required fields populated |

### Semi-Automatable (Needs Logic)
These require additional code but data is available:

| Check | Data Source | Logic Needed |
|-------|-------------|--------------|
| Stair code compliance | `getStairs()` | Compare to IBC limits |
| Door clearances | `getDoors()` | Spatial analysis |
| Fire-rated walls | `getWalls()` | Keyword search in type |
| Accessible bathrooms | `getRooms()` | Area ≥ minimum |
| Travel distance | Room locations | Path calculation |

### Manual Review Required
These items cannot be automated and require visual review:

- Dimension accuracy
- Detail completeness
- Material callouts correct
- Flashing/waterproofing shown correctly
- Section/elevation alignment
- Consultant coordination
- Client approval

---

## CHECKLIST AUTOMATION SCRIPT (Proposed)

```
// Pseudo-code for CD Checklist Automation
function runCDChecklist(doc) {
    results = {};

    // Sheet verification
    sheets = getSheets();
    results.sheets = checkRequiredSheets(sheets, REQUIRED_SHEETS);

    // Element verification
    doors = getDoors();
    results.doors = {
        count: doors.length,
        marksComplete: doors.filter(d => d.mark).length,
        passRate: (marksComplete / count) * 100
    };

    windows = getWindows();
    results.windows = checkWindowMarks(windows);

    rooms = getRooms();
    results.rooms = {
        total: rooms.length,
        named: rooms.filter(r => r.name).length,
        numbered: rooms.filter(r => r.number).length
    };

    // Schedule verification
    schedules = getAllSchedules();
    results.schedules = verifyScheduleCounts(schedules, doors, windows, rooms);

    // Generate report
    return generateChecklistReport(results);
}
```

---

*Last Updated: 2025-12-30*
*Based on IBC 2021, Florida Building Code 8th Edition (2023), ADA 2010*
*Automation via RevitMCPBridge2026*
