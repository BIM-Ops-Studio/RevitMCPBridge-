# Firm Standards Reference Guide
## Client/Firm-Specific Sheet Organization Standards

**Purpose**: Track which architectural firms use which sheet numbering systems and organizational standards. This allows proper adaptation when working for different clients.

**Last Updated**: 2025-01-18

---

## IDENTIFIED FIRMS/CLIENTS

### Firm 1: Hugh L. Anglin, PE (Florida)

**Title Block Identifier**:
- Professional Engineer License: #36844 PE
- Location: Tamarac, FL / Avon Park, FL
- Contact: hugh@... (various projects)

**Projects**:
- 1700 West Sheffield Road (Single Family Residence, Avon Park, FL)

**Sheet Numbering Standard**: **Pattern A - Decimal with Prefix**
```
Format: [Prefix]-[Category].[Sequence]

General:
  G-00: Cover Sheet
  G-01: General Notes / Site Data

Civil/Site:
  SP1, SP2, SP3: Site Plans, Landscape, Irrigation

Architectural:
  A-1.1: Floor Plan, Schedules, Details, Legend
  A-2.1, A-2.2: Building Elevations
  A-3.1: Building Sections & Details
  A-4.1: Roof Plan & Details
  A-5.1: Enlarged Plans, Elevation and Details

Structural:
  S1: Foundation Plan and Details
  S2: Column & Bond Beam Plan
  S3: Roof Framing Plan and Details

MEP:
  P1, P2: Plumbing
  M1: Mechanical
  E1, E2: Electrical
```

**Characteristics**:
- Separate discipline prefixes (G, SP, A, S, P, M, E)
- Category-based decimal system for architectural
- Simple sequential for structural and MEP
- Complete multi-discipline sets in one PDF

**When to Use**: Small to medium residential projects, Florida-based work

---

### Firm 2: Unknown Firm (Revit 2026 User)

**Title Block Identifier**:
- Created in Autodesk Revit 2026
- Project: Sweetland Project (Main House + ADU)
- Date: October 28, 2025

**Projects**:
- Sweetland Project - Revised CD Set

**Sheet Numbering Standard**: **Pattern C - Three-Digit Sequential**
```
Format: [Discipline][Sequential Number]

Main Building (A100-series):
  A101: Cover Sheet
  A102: General Notes
  A103: New Site Plan
  A104: Foundation Plan
  A105: Proposed Main House (Floor Plan)
  A106: Roof Plan
  A107: Reflected Ceiling Plan
  A108-A109: Exterior Elevations
  A110-A111: Building Sections
  A112: Enlarged Plans & Details
  A113: Door/Window & Details
  A115-A117: Typical Details

Secondary Building (A200-series):
  A201: ADU First Floor Plan
  A202: ADU Second Floor Plan
  A203: ADU Roof Plan
  A204-A205: ADU Reflected Ceiling Plans
  A206: ADU Exterior Elevations
  A207: ADU Building Sections
  A209: Typical Details

Electrical:
  E101: Main House Electrical Plan
  E201-E202: ADU Electrical Plans
```

**Characteristics**:
- Professional three-digit numbering (A101, A102, etc.)
- Multi-building organization by hundreds (A1xx, A2xx)
- Separate Reflected Ceiling Plan sheets
- Architectural + Electrical only (other disciplines in separate PDFs)
- Skipped sheet numbers retained (A114, A208 missing)

**When to Use**: Larger residential projects, multi-building projects, professional/commercial work

---

### Firm 3: Fantal Consulting / Jarvis M. Wyandon, Architect

**Title Block Identifier**:
- Architect: Jarvis M. Wyandon, Architect
- License: AR94338 (Florida)
- Production: Fantal Consulting
- Location: 8400 N. University Drive, Tamarac, FL 33321
- Phone: (561) 571-4255

**Projects**:
- South Golf Cove Residence (Single Family, Port Charlotte, FL)

**Sheet Numbering Standard**: **Pattern D - Hybrid Decimal (Space-Separated)**
```
Format: [Discipline] [Category].[Sequence]

Architectural:
  A 0.0: Cover Sheet
  A 0.1: Abbreviation, Notes & Symbols
  A1.0: Proposed Site Plan
  A2.1: Proposed Ground Floor Plan
  A2.2: Proposed Second Floor Plan
  A2.3: Door/Window Schedule & Details
  A2.4: Proposed Roof Plan
  A3.0: Proposed Ground Floor - RCP
  A3.1: Proposed Second Floor - RCP
  A5.0-A5.1: Proposed Building Elevations
  A6.0: Enlarged Plans/Elevations & Details
  A7.0-A7.1: Building Sections
  A8.0-A8.2: Wall Sections
  A9.0-A9.1: Typical Details

Electrical: (Shown in index but not in this PDF)
Mechanical: (Shown in index but not in this PDF)
Plumbing: (Shown in index but not in this PDF)
```

**Characteristics**:
- **Space between discipline and number** (unique!)
- Zero-based admin sheets (A 0.0, A 0.1)
- Category-based organization (A1=Site, A2=Plans, A3=RCP, A5=Elevations, etc.)
- Number gaps: A4.x not used, jumps from A3 to A5
- Multiple wall section sheets (A8.0-A8.2)
- Separate sheets per floor for multi-story

**When to Use**: Work for Fantal Consulting or similar Florida-based firms

---

## PATTERN COMPARISON MATRIX

| Feature | Pattern A (Hugh Anglin) | Pattern C (Sweetland) | Pattern D (Fantal) |
|---------|------------------------|----------------------|-------------------|
| Format | `A-1.1` | `A101` | `A 0.0` |
| Separator | Hyphen + Dot | None | Space + Dot |
| Admin Sheets | G-00, G-01 | A101, A102 | A 0.0, A 0.1 |
| Site Plans | SP1, SP2, SP3 | A103 | A1.0 |
| Floor Plans | A-1.1 | A105, A201-A202 | A2.1, A2.2 |
| RCP Sheets | Not separate | A107, A204-A205 | A3.0, A3.1 |
| Elevations | A-2.1, A-2.2 | A108-A109 | A5.0, A5.1 |
| Sections | A-3.1 | A110-A111 | A7.0, A7.1 |
| Wall Sections | In details | Not shown | A8.0-A8.2 |
| Details | A-5.1 | A112-A117 | A9.0, A9.1 |
| Multi-Discipline | All in one PDF | Arch+Elec only | Arch only |
| Multi-Building | N/A | A1xx vs A2xx | Not applicable |

---

## RECOGNITION GUIDE

### How to Identify Which Standard to Use

1. **Check Title Block**:
   - Look for firm name, architect name, license number
   - Check project location (may indicate regional standards)
   - Note contact information

2. **Check Cover Sheet**:
   - Sheet index shows complete numbering scheme
   - Discipline organization visible immediately

3. **Pattern Recognition**:
   - Hyphens = Pattern A (Small firm, traditional)
   - Three digits = Pattern C (Professional, scalable)
   - Spaces = Pattern D (Fantal/specific firm standard)

4. **Sheet Content**:
   - RCP separate? → Pattern C or D
   - Multi-discipline in one PDF? → Pattern A
   - Wall sections separate? → Pattern D

---

## REVIT AUTOMATION IMPLICATIONS

### For Automated Sheet Creation

**Must Support**:
1. Multiple numbering format templates
2. Firm/client detection from title block
3. Flexible sheet naming based on pattern
4. Multi-building support (A1xx vs A2xx)
5. Separate vs combined discipline sets

**Configuration System**:
```
Client Profile:
  - Firm Name
  - Numbering Pattern (A, C, D, etc.)
  - Sheet Progression Logic
  - Title Block Template
  - Discipline Organization
```

---

## NEXT STEPS

As more sets are analyzed:
- [ ] Add more firms to reference
- [ ] Identify regional pattern trends
- [ ] Note commercial vs residential differences
- [ ] Document title block variations
- [ ] Create firm template library

---

**Status**: Active Learning
**Firms Cataloged**: 3
**Patterns Identified**: 4 (A, B, C, D)
**Next**: Continue analyzing remaining sets to identify more patterns

