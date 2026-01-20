# Annotation Standards

## Keynote System

### Keynote Format
Standard format: [Division].[Section].[Item]
Example: 08.11.01 = Division 08 (Openings), Section 11 (Metal Doors), Item 01

### Keynote Content Requirements
Every keynote should include:
1. WHAT - Description of the element/assembly
2. WHO - Responsible party (Contractor, Owner, etc.)
3. REFERENCE - Related spec section, detail, or schedule

### Keynote Placement Rules
- Place 1/4" to 1/2" away from element (at scale)
- Leader points TO the element
- Leader should be at 30°, 45°, or 60° angle
- Never cross leaders over each other
- Group keynotes in legends when multiple on sheet

### Keynote Examples (Good Format)
```
01 - 6" CMU WALL W/ VERTICAL REBAR @ 32" O.C.
     SEE STRUCTURAL. CONTRACTOR TO COORDINATE
     EMBED LOCATIONS.

02 - IMPACT-RATED ALUMINUM STOREFRONT SYSTEM.
     SEE SPEC SECTION 08 44 13. VERIFY HEAD
     HEIGHT WITH DOOR SCHEDULE.

03 - 5/8" TYPE X GWB ON METAL STUDS @ 16" O.C.
     1-HR FIRE RATING. UL DESIGN NO. U419.
```

## Dimension Standards

### Dimension String Rules
1. ALWAYS close dimension strings (both ends to something)
2. Overall dimension on outside
3. Individual dimensions inside
4. Dimension to FACE OF STUD, not finish (UNO)
5. Grid-to-grid for structural coordination

### Dimension Organization (Outside to Inside)
```
[Overall] → [Major breaks] → [Openings] → [Wall thicknesses]
```

### What to Dimension on Floor Plans
- Overall building dimensions
- Grid line spacing
- All openings (doors, windows)
- Wall offsets and jogs
- Stair width and landing depths
- Column locations
- Equipment requiring coordination

### What to Dimension on Elevations
- Floor-to-floor heights
- Window sill and head heights
- Roof heights and slopes
- Grade to first floor
- Parapet height
- Ceiling heights (interior elevations)

### Dimension Text Standards
| Drawing Scale | Text Height |
|---------------|-------------|
| 1/8" = 1'-0" | 3/32" |
| 1/4" = 1'-0" | 3/32" |
| 1/2" = 1'-0" | 1/8" |
| 3/4" = 1'-0" | 1/8" |
| 1" = 1'-0" | 1/8" |

## Symbol Standards

### Section Marks
- Circle with section number above, sheet number below
- Arrow indicates direction of view
- Reference format: #/A3.1 (Section # / Sheet)

### Detail Marks
- Circle with detail number above, sheet number below
- Reference format: #/A9.1 (Detail # / Sheet)

### Elevation Marks
- Arrow pointing in direction of view
- Letter designation (A, B, C, D or 1, 2, 3, 4)
- Interior elevations reference sheet: A/A6.1

### Door Tags
- Circle or hexagon
- Contains door NUMBER (not type)
- Door number format: 101, 102... (room-based) or sequential

### Window Tags
- Hexagon or diamond shape
- Contains window TYPE letter
- Window type format: A, B, C... (refers to schedule)

### Room Tags
- Rectangle with room name and number
- Room number format: 101, 102... (floor + sequence)
- Place at CENTER of room

## Text Standards

### CRITICAL: Text Heights (ALWAYS USE THESE)
**These are firm standards - never deviate without explicit user approval.**

| Text Type | Height | When to Use |
|-----------|--------|-------------|
| **Regular notes** | **3/32"** | ALL standard text notes, keynotes, labels |
| **Note titles/headers** | **3/16"** | Section headers within notes, emphasis titles |
| **Bigger text/subtitles** | **1/8"** | Subtitles, secondary headers, important callouts |
| Room names | 3/16" | Room name text in tags |
| Room numbers | 1/8" | Room number in tags |
| Dimensions | 3/32" | All dimension text |
| Drawing titles | 1/4" | View titles on sheets |
| Sheet titles | 3/8" | Main sheet title block |
| Keynotes | 3/32" | Keynote legends |

### Text Size Priority (When Placing Notes)
1. **3/32"** = Default for any regular note content
2. **3/16"** = Only for titles/headers WITHIN a note group
3. **1/8"** = For larger callouts or secondary headers
4. Never use random sizes - stick to these three

### Text Formatting
- ALL CAPS for titles and headers
- Sentence case for notes and descriptions
- Left-aligned for paragraphs
- Numbered lists for sequential steps
- Bulleted lists for unordered items

### Standard Abbreviations
| Abbreviation | Meaning |
|--------------|---------|
| UNO | Unless Noted Otherwise |
| TYP. | Typical |
| SIM. | Similar |
| O.C. | On Center |
| NIC | Not In Contract |
| VIF | Verify In Field |
| T.O. | Top Of |
| B.O. | Bottom Of |
| EQ | Equal |
| CLR | Clear |
| MIN | Minimum |
| MAX | Maximum |
| NTS | Not To Scale |
| AFF | Above Finished Floor |
| ABV | Above |
| BLW | Below |
| CONT | Continuous |
| EA | Each |
| GWB | Gypsum Wall Board |
| MTL | Metal |
| STL | Steel |
| CONC | Concrete |
| WD | Wood |
| PVMT | Pavement |
| FND | Foundation |
| FTG | Footing |

## Line Weights

| Line Type | Pen Weight | Use |
|-----------|------------|-----|
| Object cut | 0.50mm (Heavy) | Elements cut by view |
| Object beyond | 0.35mm (Medium) | Visible beyond cut |
| Hidden | 0.18mm (Light) | Hidden elements |
| Dimension | 0.18mm (Light) | Dim lines & text |
| Centerline | 0.18mm (Light) | Center lines |
| Grid | 0.25mm (Medium) | Grid lines |
| Property line | 0.50mm (Heavy) | Site boundaries |
