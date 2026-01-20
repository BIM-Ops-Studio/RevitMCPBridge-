# Template Pack System Specification v1.0

## Overview

Template Packs are the single source of truth for project standards in the AEC automation system. They define **what to build** (standards.json) and **how to prove it worked** (validation.json).

## Directory Structure

```
template_packs/
├── SPEC.md                      # This file - system specification
├── pack_resolver.py             # Core + Sector → Resolved pack
├── pack_adapter.py              # v2 → v1 format adapter
├── preflight_validator.py       # Pre-run readiness checker
│
├── _core/                       # Universal baseline (always included)
│   ├── standards.json           # Core standards (all sectors inherit)
│   ├── validation.json          # Core validation rules
│   └── notes.md                 # Core documentation
│
├── _schemas/                    # JSON schemas for validation
│   ├── standards_pack_v2.schema.json
│   └── validation_pack.schema.json
│
├── _firms/                      # Firm-specific overrides
│   ├── arky.json               # Example: ARKY Architecture
│   └── {firm}.json             # Add your firm here
│
├── multifamily/                 # Sector: 3+ story residential
│   ├── standards.json
│   ├── validation.json
│   └── notes.md
│
├── duplex/                      # Sector: 2-4 attached units
│   ├── standards.json
│   ├── validation.json
│   └── notes.md
│
├── sfh/                         # Sector: Single-family homes
│   ├── standards.json
│   ├── validation.json
│   └── notes.md
│
├── commercial_ti/               # Sector: Tenant improvements
│   ├── standards.json
│   ├── validation.json
│   └── notes.md
│
├── airport/                     # Future sector
├── healthcare/                  # Future sector
├── industrial/                  # Future sector
├── commercial/                  # Future sector
│
└── resolved/                    # Output: resolved packs
    └── resolved_{sector}_{timestamp}.json
```

## Resolution Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   _core/        │     │   {sector}/     │     │   _firms/       │
│   standards.json│  +  │   standards.json│  +  │   {firm}.json   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                         ┌───────▼───────┐
                         │ pack_resolver │
                         │      .py      │
                         └───────┬───────┘
                                 │
                         ┌───────▼───────┐
                         │   Resolved    │
                         │   Pack (v2)   │
                         └───────┬───────┘
                                 │
                         ┌───────▼───────┐
                         │ pack_adapter  │
                         │      .py      │
                         └───────┬───────┘
                                 │
                         ┌───────▼───────┐
                         │   Spine v0.2  │
                         │   Standards   │
                         └───────────────┘
```

## File Specifications

### standards.json

Defines **what to build**:
- `identity`: Pack metadata (name, version, projectType)
- `titleBlocks`: Title block preferences
- `sheets`: Sheet sets (permitSkeleton, fullCD)
- `views`: View template definitions
- `schedules`: Schedule definitions
- `filters`: Preflight checks and code compliance
- `levelMapping`: Level name patterns
- `cropStrategy`: Crop box settings
- `capabilities`: Feature support flags
- `sectorSpecific`: Sector-unique settings

### validation.json

Defines **how to prove it worked**:
- `postconditions.required`: Must pass (blockers)
- `postconditions.optional`: Should pass (warnings)
- `exports.required`: Must produce these files
- `exports.optional`: Nice to have
- `evidence.collect`: Files to include in evidence package

### notes.md

Human-readable documentation:
- Purpose and use case
- Key features
- Sheet set table
- Sector-specific settings
- Known limitations
- Compatibility

## Merge Rules

When resolving Core + Sector + Firm:

1. **Dictionaries**: Deep merge (sector overrides core)
2. **Lists**: Replace (sector list replaces core list)
3. **Scalars**: Replace (last value wins)
4. **Keys starting with _**: Metadata, not merged

## Invocation Methods

```bash
# Method 1: Auto-resolve from sector
aec run --sector multifamily [--firm arky]

# Method 2: Use pre-resolved pack
aec run --pack resolved/resolved_multifamily.json

# Method 3: Legacy v1 standards (deprecated)
aec run --standards ARKY_SFH_v1
```

## Creating a New Sector

1. Create folder: `template_packs/{sector}/`
2. Copy from existing sector or create:
   - `standards.json` with `"_extends": "_core"`
   - `validation.json` with sector-specific checks
   - `notes.md` with documentation
3. Test: `python pack_resolver.py --sector {sector} --report`
4. Validate: `python preflight_validator.py --pack resolved/...`

## Creating Firm Overrides

1. Create: `template_packs/_firms/{firm}.json`
2. Only include fields you want to override
3. Use: `--firm {firm}` when resolving

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-15 | Initial specification |

## Contract

This specification is locked for beta. Changes require version bump.
