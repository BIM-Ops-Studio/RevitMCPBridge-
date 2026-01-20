# Quality Control Checklists

## WORKFLOW: "QC Check" or "Quality Control"

When user requests a QC check, run through these items systematically.

---

## Model Completeness Check

### Rooms
1. Call `getRooms` to list all rooms
2. Check for: Name, Number, Area calculated
3. Flag: Rooms with 0 area (not bounded)
4. Flag: Duplicate room numbers
5. Flag: Rooms without tags

### Doors
1. Call `getDoors` to list all doors
2. Check each door has: Mark, Type, Width, Height
3. Flag: Untagged doors
4. Flag: Doors not in any schedule
5. Verify: Door schedule count matches placed doors

### Windows
1. Call `getWindows` to list all windows
2. Check each window has: Type, Size
3. Flag: Untagged windows
4. Flag: Windows not in any schedule
5. Verify: Window schedule count matches placed windows

### Walls
1. Call `getWalls` to get wall info
2. Flag: Walls with unjoined ends
3. Flag: Very short wall segments (< 6")
4. Flag: Overlapping walls

---

## Annotation Completeness Check

### Tags
- [ ] All rooms have room tags
- [ ] All doors have door tags
- [ ] All windows have window tags
- [ ] Door tags match door schedule
- [ ] Window tags match window schedule

### Dimensions
- [ ] Building overall dimensions present
- [ ] All dimension strings are closed
- [ ] Opening dimensions shown
- [ ] No duplicate dimensions
- [ ] Level heights dimensioned on elevations/sections

### Notes & Keynotes
- [ ] General notes on first sheet
- [ ] Key plans show major elements
- [ ] Keynotes have leaders pointing to elements
- [ ] No floating keynotes (not pointing to anything)

---

## Sheet Completeness Check

### Required Sheets (Minimum CD Set)
- [ ] Cover sheet with index
- [ ] Site plan
- [ ] Floor plan (each level)
- [ ] Roof plan
- [ ] Building elevations (4)
- [ ] Building sections (2 minimum)
- [ ] Wall sections
- [ ] Door schedule
- [ ] Window schedule
- [ ] Room finish schedule

### Sheet Content
For each sheet, verify:
- [ ] Title block complete (project name, number, date)
- [ ] Sheet number follows standard
- [ ] All views have titles
- [ ] Scale noted on each view
- [ ] North arrow on plans
- [ ] Views fit within border

---

## Cross-Reference Check

### Section Marks
1. Find all section marks on plans
2. Verify each points to valid sheet
3. Flag: Section marks pointing to wrong sheet
4. Flag: Sections without section marks on plans

### Detail Marks
1. Find all detail callouts
2. Verify each points to valid detail sheet
3. Flag: Details not referenced anywhere
4. Flag: Callouts pointing to wrong detail

### Elevation Marks
1. Find all interior elevation marks
2. Verify each elevation exists
3. Flag: Elevation marks without matching views

---

## Coordination Check

### Structural
- [ ] Grid lines match between Arch and Structural
- [ ] Floor openings coordinated (stairs, shafts)
- [ ] Column locations shown on Arch plans
- [ ] Beam locations noted where affecting ceiling

### MEP
- [ ] Plumbing fixture locations coordinate with Arch
- [ ] Electrical panel locations shown
- [ ] HVAC equipment locations shown
- [ ] Ceiling heights accommodate ductwork

---

## Phase-Specific Checklists

### Schematic Design (SD) - QC
- [ ] Site plan shows building footprint
- [ ] All floor plans complete
- [ ] 4 elevations complete
- [ ] At least 1 building section
- [ ] Area calculations match program
- [ ] Basic room layout correct

### Design Development (DD) - QC
All SD items PLUS:
- [ ] Door schedule started
- [ ] Window schedule started
- [ ] Room finish schedule started
- [ ] Interior elevations for key rooms
- [ ] Wall sections show major assemblies
- [ ] Stairs fully detailed

### Construction Documents (CD) - QC
All DD items PLUS:
- [ ] All rooms tagged
- [ ] All doors tagged and scheduled
- [ ] All windows tagged and scheduled
- [ ] Complete dimension strings
- [ ] All details drafted
- [ ] Cross-references verified
- [ ] Code compliance items shown
- [ ] General notes complete
- [ ] Specifications coordinated

---

## Common Errors to Flag

### Critical (Must Fix)
- Missing egress path
- Fire-rated door not shown rated
- Stair dimensions out of code
- Accessibility route blocked
- Structural opening not coordinated

### Major (Should Fix)
- Untagged rooms
- Missing dimensions
- Section marks pointing wrong
- Duplicate room numbers
- Schedules don't match model

### Minor (Nice to Fix)
- Inconsistent text heights
- Leaders crossing
- Minor alignment issues
- Spelling errors in notes

---

## QC Report Format

When reporting QC results, organize as:

```
## QC CHECK RESULTS

### Summary
- Total issues: X
- Critical: X
- Major: X
- Minor: X

### Critical Issues
1. [Issue description] - Location: [where]
2. ...

### Major Issues
1. [Issue description] - Location: [where]
2. ...

### Minor Issues
1. [Issue description] - Location: [where]
2. ...

### Recommendations
1. [What to fix first]
2. [Next priority]
```
