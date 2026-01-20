# Revit Best Practices - Domain Knowledge

## Annotation Rules

### Text Placement
- NEVER place text on top of model elements
- NEVER place text overlapping other text
- Minimum clearance: 0.1 feet (about 1 inch at 1/4" scale)
- Leaders should point TO the element, not away
- Text should be readable from bottom or right of sheet

### Room Tags
- Place at CENTER of room when possible
- If room is L-shaped, place in largest portion
- Room tag should not overlap doors or windows
- Include both room NAME and NUMBER

### Door/Window Tags
- Place on the SWING side of doors
- Consistent offset from opening (typically 1'-0")
- Tag should not overlap the opening symbol

### Dimensions
- Always CLOSE dimension strings (no open ends)
- Dimension to face of stud, not finish
- String dimensions from grid to grid
- Individual dimensions for openings

## Sheet Organization

### Standard Sheet Numbering
- A0.X = General, Cover, Code
- A1.X = Floor Plans
- A2.X = Elevations
- A3.X = Sections
- A4.X = Details
- A5.X = Schedules
- A6.X = Interior Elevations
- A7.X = Ceiling Plans

### View Placement
- Plans: North arrow pointing UP or to the right
- Scale noted on every view
- View titles below each view
- Consistent margins from sheet border

## Element Counts (Typical Residential)
- Small house (1500 SF): 8-12 rooms, 15-20 doors, 10-15 windows
- Medium house (2500 SF): 12-18 rooms, 20-30 doors, 15-25 windows
- Large house (4000+ SF): 18-25 rooms, 30-45 doors, 25-35 windows

## Common Issues to Flag
1. Rooms without tags
2. Doors without tags
3. Windows without tags
4. Overlapping annotations
5. Missing dimensions on exterior walls
6. Sheets without views
7. Views not on any sheet
8. Duplicate room numbers
9. Missing north arrow on plans
10. Missing scale notation

## Quality Thresholds
- 100% rooms tagged = Good
- 100% doors tagged = Good
- 100% windows tagged = Good
- 0 overlapping annotations = Good
- All sheets have views = Good
