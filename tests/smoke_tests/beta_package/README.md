# AEC Automation Beta Package

## Contents

```
beta_package/
├── README.md                 # This file
├── addin/                    # Revit add-in files
│   └── RevitMCPBridge2026/   # Copy to Revit addins folder
├── cli/                      # Command-line tools
│   └── aec                   # Main runner (Python)
├── template_packs/           # Standards packs (copy from smoke_tests)
├── docs/
│   ├── QUICKSTART.md         # Getting started guide
│   ├── TROUBLESHOOTING.md    # Common issues and fixes
│   └── CONTRACT.md           # Beta contract and guarantees
└── logs/                     # Store logs here
```

## Quick Install

### 1. Install Revit Add-in

Copy the contents of `addin/RevitMCPBridge2026/` to:
```
C:\Users\<USERNAME>\AppData\Roaming\Autodesk\Revit\Addins\2026\
```

Restart Revit. You should see "MCP Bridge" in the Add-Ins tab.

### 2. Setup CLI

Requires Python 3.8+.

```bash
# From beta_package directory
python cli/aec list           # Verify installation
```

### 3. Run First Test

```bash
# Open a Revit project first, then:
python cli/aec run --sector sfh --force
```

## Golden Path

The recommended workflow:

1. **Start from seed template** (optional but recommended)
2. **Open your Revit project**
3. **Run preflight** to check readiness
4. **Run workflow** with appropriate sector
5. **Review results** in Revit
6. **Collect evidence** for support if needed

```bash
# Full workflow
python cli/aec preflight --sector multifamily
python cli/aec run --sector multifamily --firm arky

# Evidence is automatically collected to evidence/ folder
```

## Available Sectors

| Sector | Description |
|--------|-------------|
| `sfh` | Single-family homes |
| `duplex` | 2-4 attached units |
| `multifamily` | 3+ story residential |
| `commercial_ti` | Tenant improvements |

## Support

1. Collect the evidence ZIP from `evidence/` folder
2. Note the error message
3. Include Revit version
4. Contact support

---

**Beta Version: 1.0**
**Date: 2025-12-15**
