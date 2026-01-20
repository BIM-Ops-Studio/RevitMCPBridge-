# Rule Comparison Analysis

**Generated:** 2026-01-17
**Projects Analyzed:** 4

---

## Projects Included

| Project | Firm | Type | Rooms | Views | Sheets |
|---------|------|------|-------|-------|--------|
| 512 CLEMATIS | SOP | multi-family | 694 | 2370 | 370 |
| GOULDS TOWER-1 | ARKY | multi-family | 447 | 528 | 73 |
| SOUTH GOLF COVE RESIDENCE | Fantal | single-family | 22 | 360 | 23 |
| BETHESDA HOSPITAL RN STATION | BD | healthcare/renovation | 34 | 371 | 59 |

---

## Rule Classification Summary

### ✅ Universal Rules (Apply to All Project Types)

| Rule | Presence | Project Types | Confidence |
|------|----------|---------------|------------|
| LIFE_SAFETY_PLANS | 3/4 | multi-family, healthcare | HIGH |
| MULTI_DISCIPLINE_INTEGRATION | 2/4 | multi-family, healthcare | MEDIUM |

### 🏢 Multi-Family Specific Rules

| Rule | Presence | Confidence |
|------|----------|------------|
| UNIT_ENLARGED_PLANS | 2/2 | HIGH |
| TYPICAL_FLOOR_GROUPING | 2/2 | HIGH |
| BATHROOM_KITCHEN_TYPES | 1/2 | MEDIUM |
| AMENITY_ENLARGED_PLANS | 1/2 | MEDIUM |

### 🏠 Single-Family Specific Rules

| Rule | Presence | Confidence |
|------|----------|------------|
| FLOOR_PLAN_PER_LEVEL | 1/1 | HIGH |
| ELEVATION_GROUPING | 1/1 | HIGH |
| RCP_PER_LEVEL | 1/1 | HIGH |
| SECTION_ORGANIZATION | 1/1 | HIGH |

### 🏥 Healthcare Specific Rules

| Rule | Presence | Confidence |
|------|----------|------------|
| HEALTHCARE_LIFE_SAFETY | 1/1 | HIGH |
| HEALTHCARE_ICRA | 1/1 | HIGH |
| HEALTHCARE_UL_DETAILS | 1/1 | HIGH |
| HEALTHCARE_MEDICAL_GAS | 1/1 | HIGH |

### 🔧 Renovation Specific Rules

| Rule | Presence | Confidence |
|------|----------|------------|
| RENOVATION_DEMO_PLANS | 1/1 | HIGH |
| RENOVATION_PHASING | 1/1 | HIGH |

### 🏛️ Firm-Specific Rules

| Rule | Firm | Project |
|------|------|---------|
| PARTIAL_ELEVATIONS | SOP | 512 CLEMATIS |
| FLOOR_PLAN_SUB_TYPES | SOP | 512 CLEMATIS |
| DETAIL_ORGANIZATION | ARKY | GOULDS TOWER-1 |
| ADA_DOCUMENTATION | ARKY | GOULDS TOWER-1 |
| INTERIOR_ENLARGED_ELEVATIONS | BD | BETHESDA HOSPITAL |

---

## Cross-Type Pattern Analysis

### Sheet Numbering Patterns by Firm

| Firm | Pattern | Example |
|------|---------|---------|
| SOP | Discipline.Category.Sheet | A1.1.1, ALS.2.1 |
| ARKY | Discipline-Category.Sheet | A-2.1, A-5.3 |
| Fantal | Discipline.Sheet | A2.1, A5.0 |
| BD | DisciplineSheet (no separator) | A100, E212 |

### Common Elements Across All Projects

1. **Cover/Index sheets** - All projects have A0/A000 series
2. **Floor plans** - A1/A100 series universally used
3. **Door schedules** - Present in all projects
4. **Detail sheets** - All have dedicated detail organization

### Healthcare-Unique Elements

- **ICRA Plans** - Infection Control Risk Assessment (required for healthcare renovation)
- **Medical Gas** - Separate plans under plumbing discipline
- **UL Details** - Fire-rated assembly documentation
- **Clean/Soiled Rooms** - Healthcare-specific room types

### Renovation-Unique Elements

- **Demo Plans** - Required for all disciplines (A, E, M, P)
- **Phasing** - Phase I/II variants of each plan type
- **Existing Conditions** - Baseline documentation

---

## Rule Details by Category

### LIFE_SAFETY_PLANS
**Status:** Near-Universal (3/4 projects)

| Project | Type | Sheet Pattern |
|---------|------|---------------|
| 512 CLEMATIS | multi-family | ALS.x.x series |
| GOULDS TOWER-1 | multi-family | A-0.1x series |
| BETHESDA HOSPITAL | healthcare | LS102 |

**Note:** Single-family (South Golf Cove) did not have dedicated life safety - likely due to project size/occupancy.

### SECTION_ORGANIZATION
**Status:** Varies by project type

| Project | Building Sections | Wall Sections |
|---------|-------------------|---------------|
| 512 CLEMATIS | A4.x | A5.x |
| GOULDS TOWER-1 | A-4.x | A-5.x |
| SOUTH GOLF COVE | A7.x | A8.x |
| BETHESDA HOSPITAL | N/A (renovation) | N/A |

**Note:** Healthcare renovation project had no building/wall sections - interior refresh only.

### UNIT_ENLARGED_PLANS (Multi-Family)

| Project | Series | Unit Types |
|---------|--------|------------|
| 512 CLEMATIS | A9.x | 14 unit types (A-N) |
| GOULDS TOWER-1 | A-9.x | Multiple unit types |

### HEALTHCARE_ICRA
**Condition:** Healthcare renovation projects
**Action:** Create Infection Control Risk Assessment plan showing containment barriers, negative pressure zones, and construction phasing to protect patients.

---

## Recommendations

### Ready for Codification (HIGH confidence)

1. **LIFE_SAFETY_PLANS** - Multi-family and healthcare projects
2. **UNIT_ENLARGED_PLANS** - Multi-family projects
3. **RENOVATION_DEMO_PLANS** - All renovation projects
4. **RENOVATION_PHASING** - Projects with phased construction
5. **HEALTHCARE_ICRA** - Healthcare renovation projects
6. **HEALTHCARE_UL_DETAILS** - Healthcare or high fire-rating projects

### Need More Data

1. **SECTION_ORGANIZATION** - Varies too much, need more projects
2. Single-family patterns - Only 1 project in dataset
3. Commercial/office patterns - No projects yet

### Next Steps

1. Extract 1-2 more healthcare projects to validate healthcare rules
2. Extract commercial/office project to expand type coverage
3. Codify HIGH confidence rules into CIPS
4. Test rules on new projects of matching type
