# AEC Automation - Quick Start Guide

## Prerequisites

- [ ] Revit 2024, 2025, or 2026 installed
- [ ] Python 3.8+ installed
- [ ] RevitMCPBridge add-in installed (see Installation)

## Installation

### Step 1: Install Revit Add-in

1. Close Revit if running
2. Copy `addin/RevitMCPBridge2026.addin` and `addin/RevitMCPBridge2026.dll` to:
   ```
   C:\Users\<USERNAME>\AppData\Roaming\Autodesk\Revit\Addins\2026\
   ```
3. Start Revit
4. Verify: Add-Ins tab should show "MCP Bridge" panel

### Step 2: Verify CLI

```bash
cd beta_package
python cli/aec list
```

Expected output:
```
============================================================
AVAILABLE SECTOR MODULES
============================================================
Sector               Type                 Version
--------------------------------------------------
sfh                  Residential_SFH      1.0.0
duplex               Duplex               1.0.0
multifamily          Multifamily          1.0.0
commercial_ti        Commercial_TI        1.0.0
```

## Your First Run

### Step 1: Open a Revit Project

Open any Revit project in Revit 2026. The project should have:
- At least one title block family loaded
- At least one level defined
- (Optional) Walls, doors, rooms for meaningful output

### Step 2: Run Preflight

```bash
python cli/aec preflight --sector sfh
```

This checks:
- MCP connection to Revit
- Title block availability
- Level mapping
- Model contents

If you see `GREEN (80%+)` or `YELLOW (50-80%)`, you're ready to proceed.

### Step 3: Run Workflow

```bash
python cli/aec run --sector sfh --force
```

The `--force` flag allows proceeding with warnings.

### Step 4: Review Results

Watch the output for:
- Sheets created (with `-xxxx` suffix)
- Views created (with `ZZ_` prefix)
- Exports saved (CSV files)
- Cleanup status (should be `PASS`)

### Step 5: Check Evidence

The run creates an evidence package:
```
evidence/evidence_YYYYMMDD_HHMMSS.zip
```

This contains all artifacts for support purposes.

## Choosing a Sector

| Your Project | Use Sector |
|--------------|------------|
| Single-family home | `--sector sfh` |
| Duplex / Townhouse | `--sector duplex` |
| Apartment building (3+ stories) | `--sector multifamily` |
| Office/retail tenant improvement | `--sector commercial_ti` |

## Adding Firm Overrides

If your firm has custom standards:

```bash
python cli/aec run --sector multifamily --firm arky
```

This applies firm-specific overrides on top of the sector defaults.

## Command Reference

```bash
# List available sectors
aec list

# Run preflight only
aec preflight --sector <sector> [--firm <firm>]

# Run complete workflow
aec run --sector <sector> [--firm <firm>] [--force] [--skip-preflight]

# Validate a specific pack file
aec validate --pack <path>
```

## What Happens During a Run

1. **Resolve Pack**: Core + Sector + Firm → Resolved standards
2. **Preflight**: Check project readiness
3. **Execute**: Create sheets, views, schedules
4. **Verify**: Check postconditions
5. **Cleanup**: Delete all created elements
6. **Collect**: Zip evidence package

## Next Steps

- Read `CONTRACT.md` for guarantees and limitations
- Read `TROUBLESHOOTING.md` if you encounter issues
- Try different sectors to see their sheet sets

---

*Happy automating!*
