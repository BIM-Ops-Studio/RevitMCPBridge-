# Multifamily Sector Module v1.0

## Purpose
For 3+ story residential buildings with multiple dwelling units. Optimized for permit sets and CD packages.

## Key Features
- 19-sheet permit skeleton (life safety, unit plans, overall plans)
- 1/8" = 1'-0" scale (1:96) for large building footprints
- 10' crop margin for extensive model extents
- Dynamic level support (up to 10 floors)
- Unit type enlarged plans (Type A, Type B, etc.)

## Sheet Set
| Number | Name | Required |
|--------|------|----------|
| G0.01 | Cover Sheet | Yes |
| G0.02 | Code Analysis | Yes |
| G0.03 | Life Safety Plan | Yes |
| A1.0.1-5 | Floor Plans L1-L5 | Yes (L4-L5 optional) |
| A1.1.x | Unit Type Plans | Optional |
| A2.0.x | Elevations | Yes |
| A3.0.1 | Building Sections | Yes |
| A5.0.x | Schedules | Yes |

## Sector-Specific Settings
- `unitPlanning.dynamicUnits`: Auto-detect unit types from model
- `lifeSafety.exitPathRequired`: Code analysis for egress
- `accessibility.adaCompliance`: ADA unit verification

## Known Limitations
- Elevation viewport placement requires existing elevation views
- Schedule viewport placement not supported in Revit 2026
- Unit boundaries detected by room names, not explicit geometry

## Compatibility
- Revit 2024, 2025, 2026
- RevitMCPBridge 1.0+
- Spine v0.2+
