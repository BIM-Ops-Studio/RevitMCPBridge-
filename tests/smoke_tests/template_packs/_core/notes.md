# Core Universal Template Pack v1.0

## Purpose
Universal baseline that applies to ALL project types. Sector modules extend this core.

## Included
- Basic sheet numbering (standard A101 format)
- Universal view templates (floor plan, elevation, section, detail)
- Common schedules (door, window, room)
- Standard annotation types
- Basic preflight checks
- Default crop strategy (model extents + 5' margin)

## Not Included (add via sector modules)
- Project-type specific sheets (unit plans, life safety, etc.)
- Industry-specific schedules
- Specialized view templates
- Code compliance checks specific to building type

## Usage
```bash
# Resolve with a sector module
python pack_resolver.py --sector multifamily --output my_project.json

# Run preflight validation
python preflight_validator.py --pack my_project.json
```

## Extending
To create a firm-specific override:
1. Create `_firms/your_firm.json`
2. Override only the fields you want to change
3. Use `--firm your_firm` when resolving

## Compatibility
- Revit 2024, 2025, 2026
- RevitMCPBridge 1.0+
- Spine v0.2+
