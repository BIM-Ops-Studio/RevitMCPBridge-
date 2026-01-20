# GOULDS TOWER-1 - Extracted Decision Rules

**Project Type:** Multi-Family Residential (11-story tower)
**Firm:** ARKY
**Extracted:** 2026-01-17

---

## Project Statistics

| Category | Count |
|----------|-------|
| Total Rooms | 447 |
| Total Views | 528 |
| Total Sheets | 73 |
| Levels | 11 floors + roof |

### Room Distribution

| Room Type | Count | Avg Area |
|-----------|-------|----------|
| Bedroom | 137 | 133 sf |
| Bathroom | 105 | 62 sf |
| Living | 48 | 269 sf |
| Kitchen | 48 | 93 sf |
| Stair | 22 | 150 sf |
| Utility | 20 | 107 sf |
| Closet | 16 | 36 sf |
| Office | 9 | 802 sf |

---

## PROPOSED RULES

### RULE 1: Unit Enlarged Plans
**Status:** ✅ VALIDATED (consistent pattern)

```
IF project_type = "multi-family"
AND unit_types > 1
THEN create enlarged floor plan for each unique unit type
     → Sheet series: A-9.x
     → Scale: larger than overall floor plan
     → Include: Floor plan + RCP callout
```

**Evidence:**
- A-9.1: ENLARGED 3 BD. RM. UNIT-A FLR. PLN.
- A-9.2: ENLARGED 3 BD. RM. UNIT-B FLR. PLN.
- A-9.3: ENLARGED 3 BD. RM. UNIT-C FLR. PLN.
- A-9.4: ENLARGED 3 BD. RM. UNIT-D FLR. PLN.
- A-9.5: ENLARGED 3 BD. RM. UNIT-E FLR. PLN.
- A-9.6: ENLARGED 3 BD. RM. UNIT-F FLR. PLN.

**Your Validation Needed:**
- [ ] Confirm: Each distinct unit type gets its own sheet
- [ ] Scale used for enlarged plans?
- [ ] What triggers a "distinct" unit (mirror counts as same or different)?

---

### RULE 2: Floor Plan Grouping (Typical Floors)
**Status:** ✅ VALIDATED (high confidence)

```
IF floors 4-11 are identical (typical)
THEN combine on single sheet as "4TH THRU 11TH"
     → Reduces sheet count
     → Note: "TYP. FLOORS" or similar
```

**Evidence:**
- A-2.1: 1ST AND 2ND LVL. FLOOR PLAN
- A-2.2: 3RD AND 4TH THRU 11TH LVL. FLOOR PLAN

**Your Validation Needed:**
- [ ] Threshold for "typical" - how similar must floors be?
- [ ] When do you split vs. combine?

---

### RULE 3: Life Safety Plans
**Status:** ✅ VALIDATED (code-driven)

```
IF building_height > 3_stories
OR occupancy = assembly/institutional
THEN create life safety plan for each unique floor
     → Sheet series: A-0.1x
     → Show: exit paths, fire ratings, egress distances
```

**Evidence:**
- A-0.11: 1ST FLOOR LIFE SAFETY PLAN
- A-0.12: 2ND FLOOR LIFE SAFETY PLAN
- A-0.13: 3RD FLOOR LIFE SAFETY PLAN
- A-0.14: 4TH THRU 11TH FLR. LIFE SAFETY PLAN

**Your Validation Needed:**
- [ ] When is life safety required vs. optional?
- [ ] What elements must appear?

---

### RULE 4: Building Sections vs. Wall Sections
**Status:** ✅ VALIDATED (high confidence)

```
Building Sections (A-4.x):
  → Cut through entire building
  → Show floor-to-floor relationships
  → Typically 2-4 sections (longitudinal + transverse)

Wall Sections (A-5.x):
  → Detail specific assembly conditions
  → Show construction layers
  → Typically at typical wall types + special conditions
```

**Evidence:**
- A-4.1, A-4.2, A-4.3: BUILDING SECTIONS (3 sheets)
- A-5.1, A-5.2: WALL SECTIONS (2 sheets)

**Your Validation Needed:**
- [ ] What determines where building sections cut?
- [ ] Which wall conditions get dedicated sections?

---

### RULE 5: Detail Organization by CSI
**Status:** ✅ VALIDATED (high confidence)

```
Details organized by building element:
  A-2.6  → Roof details
  A-6.x  → Stair/elevator details
  A-7.2  → Door details
  A-8.2  → Window details
  A-10.x → Partition/casework details
```

**Evidence:**
- 194 drafting views (details)
- 16 sheets with "DETAIL" in name
- Clear categorization by element type

**Your Validation Needed:**
- [ ] Is this CSI-based or custom organization?
- [ ] How do you decide typical vs. specific detail?

---

### RULE 6: Common Area Restrooms
**Status:** ⚠️ NEEDS VALIDATION

```
IF restroom = public/common (not in unit)
THEN create enlarged restroom plan
     → Sheet: A-9.15 (ENLARGED RESTROOM FLOOR PLAN)
     → Include: fixture layout, partition details, ADA clearances
```

**Evidence:**
- A-9.15: ENLARGED RESTROOM FLOOR PLAN
- Only 1 dedicated restroom sheet for 105 bathrooms
- Unit bathrooms shown in unit enlarged plans

**Your Validation Needed:**
- [ ] Confirm: Only common restrooms get separate sheets
- [ ] Unit bathrooms are covered by unit enlarged plans?

---

### RULE 7: ADA Documentation
**Status:** ✅ VALIDATED (code-driven)

```
ADA documentation in A-0.x series:
  A-0.2: ADA NOTES & DETAILS (8 views)
  A-0.3: ADA NOTES & DETAILS (2 views)
  A-0.4: ADA NOTES & DETAILS (7 views)
```

**Your Validation Needed:**
- [ ] What determines how many ADA sheets?
- [ ] Standard details vs. project-specific?

---

## EXCEPTIONS TO INVESTIGATE

1. **Why A1-A13 sheets exist alongside A-1.1, A-2.1 pattern?**
   - Appears to be alternate simplified set (18 sheets)
   - Same content, different numbering?

2. **Why 194 drafting views but fewer placed on sheets?**
   - Standard detail library loaded but not all used?
   - Or details for future use?

---

## NEXT STEPS

1. **You validate** these rules (confirm/reject/modify)
2. **I extract** from 2-3 more projects (different types)
3. **Compare** to find universal vs. project-specific rules
4. **Codify** validated rules into executable logic
