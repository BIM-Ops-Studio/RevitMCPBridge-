# Universal Template System with Firm Profiles

## Overview

This system provides a **single universal Revit template** that adapts to different firm standards through **switchable JSON profiles**. Instead of maintaining multiple templates, you maintain one template and swap profiles to match the firm's conventions.

## Architecture

```
Universal Template (.rte)
        │
        ├── Core Styles (all firms)
        │   ├── Base text types (Arial 3/32", 3/16", 1/4", 3/8")
        │   ├── Standard dimensions
        │   ├── Default view templates
        │   └── Required families
        │
        └── Firm Profile (.json)
            ├── Naming conventions
            ├── Preferred text styles
            ├── Sheet numbering pattern
            ├── View naming rules
            └── Firm-specific settings
```

## File Structure

```
knowledge/standards/firm-profiles/
├── _profile-index.json      # Master index of all profiles
├── _universal-core.json     # Baseline defaults all profiles inherit
├── arky-profile.json        # ARKY - South Florida multi-family
├── fantal-consulting-profile.json  # Fantal - Florida residential
├── bruce-davis-architect-profile.json  # Healthcare, institutional
├── krm-design-profile.json  # Residential/commercial mix
├── haymond-brothers-profile.json    # Idaho residential
├── glidden-spina-profile.json       # Commercial/mixed-use
├── sklarchitecture-profile.json     # Retail/commercial
└── neudesign-profile.json           # Modular/multi-family
```

## MCP Methods

### Profile Management

| Method | Description |
|--------|-------------|
| `listProfiles` | List all available firm profiles |
| `getProfile` | Get details of a specific profile |
| `getCurrentProfile` | Get the currently active profile |
| `setProfile` | Manually set the active profile |
| `detectProfile` | Auto-detect profile from project info |
| `refreshProfiles` | Reload profiles from disk |

### Profile Settings

| Method | Description |
|--------|-------------|
| `getProfileSetting` | Get any setting by path (e.g., "textTypes.primary.notes") |
| `getTextTypeForProfile` | Get the correct text type for category |
| `getDimensionTypeForProfile` | Get the correct dimension type |
| `getSheetNumberFormat` | Get sheet numbering pattern |
| `getViewNamingConvention` | Get view naming rules |

## Usage Examples

### Auto-detect profile at session start

```powershell
# Called automatically when opening a project
$result = Invoke-MCPMethod -Method "detectProfile" -Params @{ autoSet = $true }
# Returns: { detectedProfile: "arky", firmName: "ARKY", matchedOn: "titleblock: ARKY - Title Block" }
```

### Get text style for notes

```powershell
$result = Invoke-MCPMethod -Method "getTextTypeForProfile" -Params @{ category = "notes" }
# Returns: { styleName: "3/32\" Arial", font: "Arial", size: "3/32\"" }
```

### Get sheet numbering pattern

```powershell
$result = Invoke-MCPMethod -Method "getSheetNumberFormat"
# Returns: { pattern: "A-#.#", examples: ["A-0.0", "A-1.0", "A-2.1"] }
```

### Switch profiles manually

```powershell
Invoke-MCPMethod -Method "setProfile" -Params @{ profileId = "fantal-consulting" }
```

## Profile Detection Logic

Profiles are detected in priority order using these checks:

1. **Path Patterns** - Checks if file path contains firm name
2. **Titleblock Families** - Looks for firm-specific titleblock
3. **Project Info** - Checks Author, Client Name, Organization

Example detection config:
```json
{
  "detection": {
    "pathPatterns": ["ARKY", "01 - ARKY"],
    "titleBlockFamilies": ["ARKY - Title Block", "ARKY - Title Block-MIA"],
    "projectInfoPatterns": {
      "author": "ARKY",
      "clientName": null
    }
  }
}
```

## Profile Structure

Each profile JSON contains:

```json
{
  "firmId": "arky",
  "firmName": "ARKY",
  "description": "South Florida residential and multi-family architecture",
  "sourceProject": "GOULDS TOWER-1",

  "detection": {
    "pathPatterns": ["..."],
    "titleBlockFamilies": ["..."],
    "projectInfoPatterns": { "author": "..." }
  },

  "sheetNumbering": {
    "pattern": "A-#.#",
    "examples": ["A-0.0", "A-1.0"],
    "disciplines": { "A": "Architectural" },
    "categories": { "A-0": "Cover and General", "A-1": "Site Plan" }
  },

  "textTypes": {
    "primary": {
      "notes": { "font": "Arial", "size": "3/32\"", "styleName": "3/32\" Arial" },
      "headers": { "font": "Arial", "size": "3/16\"" }
    }
  },

  "dimensionTypes": {
    "default": "Linear - 3/32\" ARchitxt",
    "casework": "GSP 3/32\" CASEWORK"
  },

  "viewTemplates": {
    "floorPlan": "Architectural Plan",
    "rcp": "Architectural Reflected Ceiling Plan"
  },

  "familyNaming": {
    "prefixes": {
      "casework": "CA-",
      "doors": "DR-",
      "plumbingFixtures": "PF-"
    }
  },

  "titleBlocks": [
    { "name": "ARKY - Title Block", "size": "24x36", "use": "Standard" }
  ]
}
```

## Adding a New Firm Profile

### Step 1: Extract from CD Set

Open a completed construction document set from the firm and use MCP methods to extract:

```powershell
# Get all text types
Invoke-MCPMethod -Method "getTextTypes"

# Get all dimension types
Invoke-MCPMethod -Method "getDimensionTypes"

# Get view templates
Invoke-MCPMethod -Method "getViewTemplates"

# Get loaded families
Invoke-MCPMethod -Method "getLoadedFamilies"

# Get sheets for numbering pattern
Invoke-MCPMethod -Method "getAllSheets"
```

### Step 2: Create Profile JSON

Create `firmname-profile.json` with the extracted data, following the structure above.

### Step 3: Update Index

Add the new profile to `_profile-index.json`:

```json
{
  "profiles": {
    "new-firm": {
      "file": "new-firm-profile.json",
      "firmName": "New Firm Name",
      "status": "complete",
      "extractedFrom": "Project Name",
      "projectTypes": ["residential", "commercial"],
      "region": "State/Region"
    }
  },
  "detectionPriority": [..., "new-firm"]
}
```

### Step 4: Refresh

Call `refreshProfiles` to reload from disk.

## Universal Core Defaults

The `_universal-core.json` provides defaults when a profile doesn't specify a setting:

- Sheet sizes: 24x36 (default), 30x42, 36x48
- Text sizes: 3/32" notes, 3/16" headers, 1/4" titles, 3/8" sheet titles
- Required view templates for each building type
- Required family categories

## Integration with Other MCP Methods

Other MCP methods can query the profile system to get firm-specific settings:

```csharp
// In C# MCP method implementation
var textStyle = FirmProfileMethods.GetSettingDirect("textTypes.primary.notes.styleName");
var sheetPattern = FirmProfileMethods.GetSettingDirect("sheetNumbering.pattern");
var currentFirm = FirmProfileMethods.GetCurrentProfileId();
```

## Status

| Profile | Status | Extracted From |
|---------|--------|----------------|
| ARKY | Complete | GOULDS TOWER-1 |
| Fantal Consulting | Complete | AP Builder Residence |
| Bruce Davis Architect | Pending | - |
| KRM Design | Pending | - |
| Haymond Brothers | Pending | - |
| Glidden Spina | Legacy | GSP_BASIC_2018 |
| SKLARchitecture | Legacy | SKLAR TEMPLATE |
| neUdesign | Legacy | ND Template_2019 |

## Notes

- **Legacy profiles** were extracted from older templates, may need updating
- **Pending profiles** need a project opened in Revit to extract styles
- Profiles can be combined - use ARKY's text types with Fantal's sheet numbering if needed
