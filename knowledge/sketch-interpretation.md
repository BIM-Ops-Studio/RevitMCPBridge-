# Sketch Interpretation Rules

## Overview
Rules for interpreting hand sketches and converting to Revit elements.

---

## Line Conventions

### By Weight
| Line Weight | Element Type | Typical Size |
|-------------|--------------|--------------|
| Heavy/thick | Exterior wall | 6"-8" |
| Medium | Interior wall | 4"-6" |
| Light | Dimension, annotation | N/A |
| Dashed | Above, hidden, existing | Varies |

### By Pattern
| Pattern | Meaning |
|---------|---------|
| Solid double lines | Wall with thickness shown |
| Single line | Wall (schematic) |
| Hatched | Section cut or poche |
| Dotted | Property line, setback |

---

## Symbol Recognition

### Doors
- **Arc/swing**: Door with direction
- **Double arc**: Double door
- **Sliding marks**: Sliding door
- **Bi-fold marks**: Bi-fold door
- **No arc, just opening**: Cased opening (no door)

### Windows
- **Rectangle in wall**: Window
- **Three lines**: Triple window or storefront
- **Rectangle with X**: Fixed window

### Plumbing
- **Rectangle with tank**: Toilet
- **Oval**: Tub
- **Small rectangle**: Lavatory
- **Double rectangle**: Kitchen sink

### Stairs
- **Parallel lines with arrow**: Stair direction (up)
- **Break line**: Stair continues

### Other
- **Circle with X**: Column
- **Dashed rectangle**: Overhead element
- **Triangle in room**: North arrow or room tag

---

## Scale Detection

### Reference Elements (use to determine scale)
| Element | Standard Size |
|---------|---------------|
| Door (single) | 3'-0" wide |
| Door (entry) | 3'-6" wide |
| Toilet | 18" x 28" |
| Parking space | 9' x 18' |
| Hallway width | 3'-6" to 4'-0" |
| Bedroom (min) | 10' x 10' |

### If Dimensions Shown
- Use marked dimensions as exact
- Calculate scale factor from known to drawn

### If No Dimensions
- Identify a door (assume 3'-0")
- Measure door in sketch units
- Calculate: `scale = 3'-0" / drawn_door_width`
- Apply scale to all measurements

---

## Coordinate System

### Establishing Origin
1. Look for grid intersection (use as 0,0)
2. Or use lower-left corner of building
3. Or use a marked reference point

### Orientation
- Look for north arrow
- Default: up = north
- Note rotation if indicated

### Measurement Method
1. Establish origin point
2. Measure wall endpoints relative to origin
3. Convert to feet using scale factor
4. Create walls with absolute coordinates

---

## Wall Type Mapping

### Based on Location
| Location | Default Type |
|----------|--------------|
| Perimeter | Exterior - CMU or Frame |
| Between units | Demising - Fire rated |
| Within unit | Interior - 2x4 |
| Wet wall (bath/kitchen) | Interior - 2x6 (for plumbing) |
| Shaft | Shaft wall - Fire rated |

### Based on Annotation
- "CMU" or block pattern → CMU wall type
- "GYP" → Interior gypsum
- Rating shown (1-HR, 2-HR) → Fire rated assembly

---

## Element Creation Sequence

### Order Matters
1. **Levels** (if not existing)
2. **Grids** (if shown)
3. **Exterior walls** (perimeter first)
4. **Interior walls** (by location)
5. **Doors** (in walls)
6. **Windows** (in walls)
7. **Fixtures** (after walls complete)
8. **Stairs** (after floor plate defined)

---

## Common Interpretation Errors

### Avoid These
| Error | Cause | Fix |
|-------|-------|-----|
| Walls overlap | Didn't account for thickness | Join at corners |
| Doors in wrong wall | Misidentified host | Check wall direction |
| Scale way off | Used wrong reference | Verify with multiple elements |
| Missing walls | Lines too light | Ask user to clarify |

### When Uncertain
- Ask user to clarify before creating
- Mark uncertainty in response
- Don't guess on fire-rated assemblies

---

## Feedback Storage

When user corrects interpretation:
```python
memory_store_correction(
    what_claude_said="[what I interpreted]",
    what_was_wrong="[why it was wrong]",
    correct_approach="[the right way]",
    project="RevitMCPBridge2026",
    category="sketch-interpretation"
)
```

---

## Quality Checklist

Before creating elements:
- [ ] Scale verified with at least 2 references
- [ ] Origin point established
- [ ] All walls identified
- [ ] Door swings noted
- [ ] Window locations marked
- [ ] Ambiguities clarified with user

---

*Last Updated: 2025-11-24 (Session 59)*
