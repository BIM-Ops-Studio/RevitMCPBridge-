# Commercial Tenant Improvement Sector Module v1.0

## Purpose
For commercial interior build-outs within existing shell buildings. Supports demo/new construction phases.

## Key Features
- 11-sheet permit skeleton
- 1/4" = 1'-0" scale (1:48)
- 3' crop margin (tenant space only)
- Demolition plan support
- Reflected ceiling plan included
- Finish schedule emphasis

## Sheet Set
| Number | Name | Required |
|--------|------|----------|
| T0.01 | Cover Sheet | Yes |
| T0.02 | General Notes | Yes |
| T1.01 | Demolition Plan | Yes |
| T1.02 | Construction Floor Plan | Yes |
| T1.03 | Furniture Plan | Optional |
| T2.01 | Reflected Ceiling Plan | Yes |
| T3.01 | Interior Elevations | Yes |
| T4.01 | Details & Sections | Yes |
| T5.01 | Door Schedule | Yes |
| T5.02 | Finish Schedule | Yes |
| T5.03 | Lighting Schedule | Optional |

## Sector-Specific Settings
- `tenantImprovement.baseBuildingLink`: Expects linked base building
- `tenantImprovement.demoPlanRequired`: Always true for TI
- `tenantImprovement.landlordApproval`: Flag for approval tracking
- `ceilingPlan.required`: True (RCP standard for TI)
- `finishes.finishScheduleRequired`: True

## Phase Support
- Existing phase (base building)
- Demolition phase (remove existing TI)
- New Construction phase (new TI work)

## Known Limitations
- Single level only (maxLevels: 1)
- Base building must be linked, not modeled
- Demo highlighting via phase filter

## Compatibility
- Revit 2024, 2025, 2026
- RevitMCPBridge 1.0+
- Spine v0.2+
