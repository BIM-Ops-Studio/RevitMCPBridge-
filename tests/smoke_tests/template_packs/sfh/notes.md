# Single-Family Home Sector Module v1.0

## Purpose
For single-family residential projects (detached homes). Streamlined sheet set for permit and CD packages.

## Key Features
- 6-sheet permit skeleton (minimal required set)
- 1/4" = 1'-0" scale (1:48) standard residential
- 5' crop margin
- Simple level structure (L1, L2 optional, Roof)

## Sheet Set
| Number | Name | Required |
|--------|------|----------|
| A0.01 | Cover Sheet | Yes |
| A0.02 | General Notes | Yes |
| A1.01 | First Floor Plan | Yes |
| A1.02 | Second Floor Plan | Optional |
| A2.01 | Building Elevations | Optional |
| A5.01 | Door Schedule | Yes |

## Sector-Specific Settings
- `garageIncluded`: Detects garage in model
- `basementLevel`: Supports basement if present
- `roofPlan.required`: Based on complexity

## Extends Core With
- Residential-appropriate scales
- Standard SFH sheet numbering
- Basic permit requirements

## Known Limitations
- Second floor sheets only created if L2 level exists
- Roof plan optional (not in permit skeleton)

## Compatibility
- Revit 2024, 2025, 2026
- RevitMCPBridge 1.0+
- Spine v0.2+
