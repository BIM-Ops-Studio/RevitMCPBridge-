# Construction Document Standards

This file defines office standards for construction documents. Claude reads this at the start of every session and applies these rules automatically.

---

## Project Context Rules

### New Construction vs. Renovation
- **New Construction**: Do NOT use "NEW" prefix - everything is new by default
- **New Construction**: Do NOT include "EXISTING TO REMAIN" keynotes
- **Renovation**: Use "NEW", "EXIST", "DEMO" prefixes to distinguish work
- Always ask or verify project type if unclear

---

## Keynotes

### Content Standards
- Include WHO is responsible (Contractor, Owner, Subcontractor)
- Include WHAT to coordinate with (MEP, Structural, Architectural)
- Reference related documents (schedules, specs, MEP drawings)
- Include manufacturer specification requirements
- Note code compliance where applicable

### Language Conventions
- Use "SHALL" for requirements (Contractor SHALL install...)
- Use "UNO" for Unless Noted Otherwise
- Use "O.C." for On Center
- Use "TYP." for Typical
- Use "SIM." for Similar
- Use "NIC" for Not In Contract
- Avoid passive voice - be direct about responsibility

### Placement Rules
- Place keynote NEAR the element it references (not on top of it)
- Use LEADER LINE to connect keynote to specific element
- Leader should point TO the element, not away from it
- Do not let keynotes overlap other annotations
- Maintain clear reading path - left to right, top to bottom

### Legend Organization
- Equal spacing between all keynotes (0.09 feet / ~1 inch recommended)
- Sequential numbering with NO gaps
- Border around legend content
- Title at top (e.g., "PLAN KEYNOTES:")
- Group related keynotes if possible (plumbing together, electrical together)

---

## Annotation Placement

### General Rules
- Annotations should not overlap model elements
- Annotations should not overlap other annotations
- Maintain consistent text orientation (readable from bottom or right of sheet)
- Use leaders when annotation cannot be placed directly adjacent to element

### Room Tags
- Center in room when possible
- Offset from center only to avoid conflicts
- Include room name and number

### Door/Window Tags
- Place on swing side of door when possible
- Maintain consistent offset from opening
- Tag should not overlap the opening symbol

### Dimension Strings
- Close all dimension strings (no open-ended dimensions)
- Dimension to face of stud, not finish, UNO
- String dimensions from grid to grid for structural coordination
- Individual dimensions for openings
- Avoid duplicate dimensions

---

## Leaders

### Style Rules
- Use straight leaders with one bend maximum
- Leader should be shortest practical length
- Arrow points TO the element being noted
- Do not cross leaders over each other when possible
- Leader angle should be 30, 45, or 60 degrees (not random)

### When to Use Leaders
- Keynotes pointing to specific elements
- Notes that reference specific locations
- Tags that cannot fit adjacent to element

---

## Text Notes

### Formatting
- Use sentence case for general notes
- Use ALL CAPS for titles and headers
- Consistent text height throughout document
- Left-align paragraph text
- Number or bullet multi-item notes

### General Notes Location
- Typically on sheet A0.1 or first architectural sheet
- Can also appear on relevant discipline sheets
- Reference general notes from detail sheets

---

## Sheet Organization

### Sheet Numbering
```
[Discipline][Sheet Type].[Sequence]

A1.1 = Architectural Plans, Sheet 1
A2.1 = Architectural Elevations, Sheet 1
A3.1 = Architectural Sections, Sheet 1
```

### Standard Sheet Types
| Number | Content |
|--------|---------|
| X0.X | Cover, General, Code |
| X1.X | Plans |
| X2.X | Elevations |
| X3.X | Sections |
| X4.X | Details |
| X5.X | Schedules |
| X6.X | Interior Elevations |
| X7.X | Ceiling Plans |

### Title Block
- Always complete all title block fields
- Date should reflect issue date
- Include revision history for reissues

---

## Schedules

### Door Schedule Requirements
- Mark (door number)
- Width and Height
- Type/Style
- Frame Material
- Hardware Set
- Fire Rating (if applicable)
- Comments/Notes

### Window Schedule Requirements
- Mark (window type)
- Width and Height
- Type (fixed, casement, double-hung, etc.)
- Frame Material
- Glass Type
- Head Height
- Comments/Notes

### Room Finish Schedule
- Room Number
- Room Name
- Floor Finish
- Base
- Wall Finish (North, South, East, West or general)
- Ceiling Finish
- Ceiling Height

---

## Quality Checks Before Issuing

### Annotations
- [ ] All rooms tagged
- [ ] All doors tagged and in schedule
- [ ] All windows tagged and in schedule
- [ ] Keynotes placed at relevant elements
- [ ] No overlapping annotations
- [ ] All text readable (not too small)

### Dimensions
- [ ] All dimension strings closed
- [ ] No duplicate dimensions
- [ ] Critical dimensions shown
- [ ] Opening sizes dimensioned

### References
- [ ] Section marks reference correct sheets
- [ ] Detail marks reference correct sheets
- [ ] Elevation marks placed and referenced
- [ ] Door/window tags match schedule

### Sheets
- [ ] All views placed on sheets
- [ ] Title block complete
- [ ] Scale noted on all views
- [ ] North arrow on plans

---

## Revit-Specific Standards

### View Naming
- Use descriptive names: "PROPOSED GROUND FLOOR PLAN" not "Level 1"
- Include level in name for clarity
- Working views prefixed with "Working_" or in separate folder

### Family Naming
- Use consistent naming convention
- Include key parameters in name when helpful
- Example: "Door-Single_Flush-3068" for 3'-0" x 6'-8" door

---

## Office-Specific Standards

*Add your firm's specific standards here as they come up*

### [Section for future standards]
-
-
-

---

## Learned Corrections

*This section captures specific corrections made during work sessions*

### 2024-12-19: Keynote Placement
- **Issue**: Placed keynotes at approximate locations
- **Correct**: Keynotes must point at SPECIFIC elements with leaders, not float in general areas

---

*Last Updated: 2024-12-19*
*Update this file as new standards are established*
