# Duplex/Townhouse Sector Module v1.0

## Purpose
For 2-4 attached dwelling units (duplexes, townhouses, row houses). Supports per-unit documentation.

## Key Features
- 9-sheet permit skeleton with per-unit plans
- 1/4" = 1'-0" scale (1:48)
- 5' crop margin
- Per-unit schedules (Door Schedule A, Door Schedule B)
- Demising wall verification

## Sheet Set
| Number | Name | Required |
|--------|------|----------|
| A0.01 | Cover Sheet | Yes |
| A0.02 | Code Analysis | Yes |
| A1.01 | First Floor - Unit A | Yes |
| A1.02 | First Floor - Unit B | Yes |
| A1.03 | Second Floor - Unit A | Optional |
| A1.04 | Second Floor - Unit B | Optional |
| A2.01 | Building Elevations | Yes |
| A5.01 | Door Schedule - Unit A | Yes |
| A5.02 | Door Schedule - Unit B | Yes |

## Sector-Specific Settings
- `unitPlanning.unitCount`: Number of units (2-4)
- `unitPlanning.unitLabels`: ["A", "B"] or ["A", "B", "C", "D"]
- `unitPlanning.perUnitSchedules`: Create separate schedules per unit
- `demising.demisingWallRequired`: Verify fire separation

## Per-Unit Workflow
The module creates separate views and schedules for each unit:
- `ZZ_Plan_L1_A_xxxx` - Unit A first floor
- `ZZ_Plan_L1_B_xxxx` - Unit B first floor
- `Door Schedule A xxxx` - Unit A doors
- `Door Schedule B xxxx` - Unit B doors

## Known Limitations
- Unit boundaries inferred from room names
- Demising wall detection is heuristic-based

## Compatibility
- Revit 2024, 2025, 2026
- RevitMCPBridge 1.0+
- Spine v0.2+
