# Pattern Recognition Quick Guide
## Instant Sheet Numbering System Identification

**Purpose**: Quickly identify which sheet numbering standard to use when setting up a Revit project for a specific client.

**Last Updated**: 2025-01-18

---

## QUICK REFERENCE TABLE

| Visual Pattern | Name | Example Sheets | Firm Type | When to Use |
|---------------|------|----------------|-----------|-------------|
| `A-1.1` | Pattern A: Hyphen-Decimal | G-00, SP1, A-1.1, S1, E1 | Small firms, traditional | Florida residential, small projects |
| `A101` | Pattern C: Three-Digit | A101, A102, A201, E101 | Professional, large firms | Professional work, multi-building |
| `A 0.0` | Pattern D: Space-Decimal | A 0.0, A1.0, A2.1, A5.0 | Specific firms (Fantal) | Fantal Consulting clients |
| `A000` | Pattern C-Zero | A000, A101, S101 | Bluebeam users | Sunset Bay type projects |

---

## IDENTIFICATION FLOWCHART

```
START: Look at first architectural sheet number
  │
  ├─ Contains HYPHEN (-)? ────────────────► Pattern A (Hyphen-Decimal)
  │                                          Example: A-1.1, G-00, SP1
  │
  ├─ Contains SPACE before number? ────────► Pattern D (Space-Decimal)
  │                                          Example: A 0.0, A1.0, A2.1
  │
  ├─ Three consecutive digits? ────────────► Pattern C (Three-Digit)
  │                                          Example: A101, A102, A201
  │   │
  │   ├─ Starts with A000? ───────────────► Pattern C-Zero variant
  │   │                                      Example: A000, A101, S101
  │   │
  │   └─ Starts with A101? ───────────────► Standard Pattern C
  │                                          Example: A101, A102, E101
  │
  └─ Something else? ──────────────────────► Check title block for firm
                                             Document as new pattern
```

---

## PATTERN DETAILS

### Pattern A: Hyphen-Decimal (Traditional)

**Visual**: `G-00`, `A-1.1`, `A-2.2`, `SP1`, `S1`, `E1`

**Structure**:
- Prefix with hyphen for major disciplines: `G-`, `A-`, `SP`
- Decimal for architectural sheets: `A-[category].[sequence]`
- Simple numbers for other disciplines: `S1`, `P1`, `M1`, `E1`

**Recognition**:
- ✓ Hyphen after discipline letter
- ✓ Separate prefixes for site (SP, C, etc.)
- ✓ Mix of decimal and simple numbering

**Complete Set Example**:
```
G-00    Cover Sheet
G-01    General Notes
SP1     Site Plan
SP2     Landscape Plan
A-1.1   Floor Plan
A-2.1   Elevations
A-3.1   Sections
A-4.1   Roof Plan
A-5.1   Details
S1      Foundation
S2      Framing
P1      Plumbing
M1      Mechanical
E1-E2   Electrical
```

**Characteristics**:
- Complete multi-discipline sets
- Clear discipline separation
- Category-based architectural organization

---

### Pattern C: Three-Digit Sequential (Professional)

**Visual**: `A101`, `A102`, `A201`, `E101`, `S101`

**Structure**:
- Three consecutive digits: `[Discipline][Hundreds][Tens][Ones]`
- Hundreds digit for major grouping (building, floor, etc.)
- Sequential tens and ones

**Recognition**:
- ✓ Always 3-4 characters total
- ✓ No hyphens or spaces
- ✓ Clean professional appearance

**Complete Set Example**:
```
Main Building (A100-series):
  A101    Cover Sheet
  A102    General Notes
  A103    Site Plan
  A104    Foundation
  A105    Floor Plan
  A106    Roof Plan
  A107    RCP
  A108-109 Elevations
  A110-111 Sections
  A112-117 Details

Secondary Building (A200-series):
  A201    ADU Floor Plan 1
  A202    ADU Floor Plan 2
  A203    ADU Roof
  A206    ADU Elevations

Electrical:
  E101    Main House
  E201    ADU
```

**Characteristics**:
- Scalable to 99 sheets per discipline
- Multi-building support (A1xx vs A2xx)
- Often separate PDFs per discipline
- May skip numbers (A114 deleted → leave gap)

**Variants**:
- **Pattern C-Zero**: Uses `A000` for cover instead of `A101`

---

### Pattern D: Space-Decimal (Fantal Style)

**Visual**: `A 0.0`, `A 0.1`, `A1.0`, `A2.1`, `A5.0`

**Structure**:
- SPACE between discipline and number
- Decimal system with category logic
- Zero-based admin sheets

**Recognition**:
- ✓ Space in the sheet number
- ✓ Admin sheets start with 0 (A 0.0, A 0.1)
- ✓ Categories may skip (no A4.x, jumps to A5.x)

**Complete Set Example**:
```
A 0.0   Cover Sheet
A 0.1   Abbreviations, Notes & Symbols
A1.0    Site Plan
A2.1    Ground Floor Plan
A2.2    Second Floor Plan
A2.3    Door/Window Schedules
A2.4    Roof Plan
A3.0    Ground Floor RCP
A3.1    Second Floor RCP
A5.0-5.1 Elevations (note: no A4.x)
A6.0    Enlarged Plans
A7.0-7.1 Building Sections
A8.0-8.2 Wall Sections
A9.0-9.1 Details
```

**Characteristics**:
- Unique space separator
- Zero-based admin (A 0.x)
- Category logic with intentional gaps
- Separate wall section category (A8.x)

---

## TITLE BLOCK RECOGNITION

### How to Quickly Identify the Firm/Standard

**Look for these on the cover sheet**:

1. **Firm Name/Logo** (top right or bottom)
2. **Architect License Number** (usually bottom right)
3. **Project Location** (may indicate regional standards)
4. **Software Creator** (Revit vs Bluebeam vs AutoCAD)

### Known Firm Identifiers

| Firm Name | License/Identifier | Pattern | Location |
|-----------|-------------------|---------|----------|
| Hugh L. Anglin, PE | #36844 PE | Pattern A | Tamarac/Avon Park, FL |
| Fantal Consulting | Jarvis Wyandon AR94338 | Pattern D | Tamarac, FL |
| [Unknown Revit 2026] | Multiple projects | Pattern C | Various |
| [Sunset Bay] | Bluebeam creator | Pattern C-Zero | Various |

---

## DECISION MATRIX

### "Which pattern should I use for this project?"

**Ask these questions**:

1. **Is this a new client?**
   - YES → Check title block, identify firm
   - NO → Use established client pattern

2. **What size is the project?**
   - Small (< 20 sheets) → Pattern A or D acceptable
   - Large (20+ sheets) → Pattern C recommended
   - Multi-building → Pattern C strongly recommended

3. **Is this multi-discipline or arch-only?**
   - Multi-discipline in one PDF → Pattern A
   - Separate discipline PDFs → Pattern C or D

4. **Does the client have a template?**
   - YES → Match their template exactly
   - NO → Recommend Pattern C (most professional/scalable)

5. **What region?**
   - Florida residential → Check for Pattern A or D
   - Commercial anywhere → Pattern C
   - California/specific state → May have state requirements

---

## SHEET PROGRESSION LOGIC

### Typical Sheet Order (All Patterns)

1. **Admin Sheets** (Cover, Notes, Symbols)
2. **Site Plans** (if in arch set)
3. **Foundation** (if in arch set)
4. **Floor Plans** (ground → upper → roof)
5. **Reflected Ceiling Plans** (if separate)
6. **Elevations** (typically 2-4 elevations)
7. **Building Sections**
8. **Wall Sections** (if separate)
9. **Enlarged Plans**
10. **Interior Elevations** (if applicable)
11. **Details** (general → specific)
12. **Schedules** (door/window/finish)

**Pattern-Specific Order**:
- **Pattern A**: Site gets own prefix (SP), Foundation in structural (S)
- **Pattern C**: Site in arch (A103), Foundation may be A104
- **Pattern D**: Site always A1.0, Foundation in A104 or structural

---

## COMMON MISTAKES TO AVOID

❌ **Don't mix patterns** - Pick one and stick to it
❌ **Don't renumber after deleting sheets** - Leave gaps (A113 → A115 is OK)
❌ **Don't forget discipline consistency** - If E101 for main, use E201 for secondary
❌ **Don't ignore client standards** - Always match their existing sets
❌ **Don't assume** - Check the title block and sheet index first

---

## QUICK SETUP CHECKLIST

When starting a new Revit project:

- [ ] Check if client has existing CD sets
- [ ] Identify pattern from their sets
- [ ] Note title block style
- [ ] Set up sheet browser to match pattern
- [ ] Create sheet naming template
- [ ] Verify with client before proceeding

---

**For Revit Automation**:
This guide should be referenced when auto-generating sheet numbers to ensure client-specific standards are followed.

**Status**: Active Reference
**Patterns Documented**: 4 (A, C, C-Zero, D)
**Firms Cataloged**: 4
**Last Update**: 2025-01-18

