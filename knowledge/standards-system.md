# Multi-Firm Standards System

This system allows Claude to automatically detect and apply the correct drafting standards based on the project being worked on.

## Quick Reference

| MCP Method | Purpose |
|------------|---------|
| `detectProfile` | Auto-detect firm from project |
| `setProfile` | Manually switch profile |
| `getCurrentProfile` | Get active profile |
| `listProfiles` | List all available profiles |
| `getProfileSetting` | Get any profile setting |

---

## How It Works

```
Project Opened → detectProfile (auto) → Load Profile → Apply Rules
```

### MCP Integration

The profile system is fully integrated via 11 MCP methods in `FirmProfileMethods.cs`:

```json
// At session start:
{ "method": "detectProfile", "params": { "autoSet": true } }

// Get current profile:
{ "method": "getCurrentProfile" }

// Get specific setting:
{ "method": "getProfileSetting", "params": { "setting": "textTypes.primary.notes" } }
```

### Detection Priority
1. **Path patterns**: File path contains firm folder name
2. **Title block family**: Each firm has their own title block
3. **Project info**: Author, Client Name, Organization matches pattern
4. **Default fallback**: Uses "arky" profile if no match

---

## Profile Location

All firm profiles stored in: `knowledge/standards/firm-profiles/`

### Profile Files

| File | Description |
|------|-------------|
| `_profile-index.json` | Master index of all profiles |
| `_universal-core.json` | Baseline defaults all profiles inherit |
| `arky-profile.json` | ARKY - South Florida multi-family |
| `fantal-consulting-profile.json` | Fantal - Florida residential |
| `bruce-davis-architect-profile.json` | BDA - Healthcare/institutional |
| `krm-design-profile.json` | KRM - Residential/commercial |
| `haymond-brothers-profile.json` | HBC - Idaho residential |
| `glidden-spina-profile.json` | GSP - Commercial/mixed-use |
| `sklarchitecture-profile.json` | SKLAR - Retail/commercial |
| `neudesign-profile.json` | ND - Modular/multi-family |

---

## Available Profiles

| Profile ID | Firm | Status | Project Types | Region |
|------------|------|--------|---------------|--------|
| `arky` | ARKY | Complete | Multi-family, Single-family | South Florida |
| `fantal-consulting` | Fantal Consulting | Complete | Single-family, Restaurant | Florida |
| `bruce-davis-architect` | Bruce Davis Architect | Skeleton | Healthcare, Institutional | Multi-state |
| `krm-design` | KRM Design | Skeleton | Residential, Commercial | South Florida |
| `haymond-brothers` | Haymond Brothers | Skeleton | Single-family, ADU | Idaho |
| `glidden-spina` | Glidden Spina + Partners | Legacy | Commercial, Mixed-use | National |
| `sklarchitecture` | SKLARchitecture | Legacy | Retail, Commercial | National |
| `neudesign` | neUdesign Projects | Legacy | Modular, Multi-family | National |

---

## Session Start Procedure

Claude should do this at every session start:

```
1. Call detectProfile with autoSet=true
2. Get project info (name, number, client)
3. Match against known detection patterns
4. If match found → Report "Detected [PROFILE] standards"
5. If no match → Use default profile, offer to analyze
```

### Example Detection Response

```json
{
  "success": true,
  "detectedProfile": "arky",
  "firmName": "ARKY",
  "confidence": "high",
  "matchedOn": "titleblock: ARKY - Title Block"
}
```

---

## Using Profile Settings

### Get Text Style

```json
{ "method": "getTextTypeForProfile", "params": { "category": "notes" } }
// Returns: { styleName: "3/32\" Arial", font: "Arial", size: "3/32\"" }
```

### Get Dimension Style

```json
{ "method": "getDimensionTypeForProfile", "params": { "category": "default" } }
// Returns: { dimensionType: "Linear - 3/32\" ARchitxt" }
```

### Get Sheet Numbering

```json
{ "method": "getSheetNumberFormat" }
// Returns: { pattern: "A-#.#", examples: ["A-0.0", "A-1.0"] }
```

### Get View Naming

```json
{ "method": "getViewNamingConvention" }
// Returns: { prefix: "PROPOSED", floorPlanFormat: "PROPOSED {LEVEL} FLOOR PLAN" }
```

---

## Profile Structure

Each profile JSON contains:

```json
{
  "firmId": "arky",
  "firmName": "ARKY",

  "detection": {
    "pathPatterns": ["ARKY"],
    "titleBlockFamilies": ["ARKY - Title Block"],
    "projectInfoPatterns": { "author": "ARKY" }
  },

  "sheetNumbering": {
    "pattern": "A-#.#",
    "categories": { "A-0": "Cover", "A-1": "Site" }
  },

  "textTypes": {
    "primary": {
      "notes": { "styleName": "3/32\" Arial" }
    }
  },

  "dimensionTypes": {
    "default": "Linear - 3/32\" ARchitxt"
  },

  "viewTemplates": {
    "floorPlan": "Architectural Plan"
  },

  "familyNaming": {
    "prefixes": { "casework": "CA-", "doors": "DR-" }
  }
}
```

---

## Creating New Profiles

When a new firm's conventions are identified:

### Step 1: Open Project in Revit

Open a completed CD set from the firm.

### Step 2: Extract Styles

```powershell
# Get all text types
Invoke-MCPMethod -Method "getTextTypes"

# Get dimension types
Invoke-MCPMethod -Method "getDimensionTypes"

# Get view templates
Invoke-MCPMethod -Method "getViewTemplates"

# Get sheets for numbering pattern
Invoke-MCPMethod -Method "getAllSheets"
```

### Step 3: Create Profile File

Create `firmname-profile.json` in `knowledge/standards/firm-profiles/`

### Step 4: Update Index

Add to `_profile-index.json`

### Step 5: Refresh

```json
{ "method": "refreshProfiles" }
```

---

## User Commands

Users can say:
- "Use [Firm] standards" → `setProfile`
- "What standards am I using?" → `getCurrentProfile`
- "List available standards" → `listProfiles`
- "Detect standards for this project" → `detectProfile`

---

## C# Integration

Other MCP methods can query profiles directly:

```csharp
// Get setting
var textStyle = FirmProfileMethods.GetSettingDirect("textTypes.primary.notes.styleName");

// Get current profile
var profileId = FirmProfileMethods.GetCurrentProfileId();
```

---

*Last Updated: 2026-01-17*
*Profile System Version: 1.0*
