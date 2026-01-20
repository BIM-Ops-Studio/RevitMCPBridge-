# AEC Automation - Beta Contract v1.0

## Overview

This document defines the **guarantees** and **limitations** of the AEC Permit/CD automation system for beta testers.

---

## What You Get

### Always Produces

| Artifact | Description | Format |
|----------|-------------|--------|
| Sheet List | All sheets created during run | CSV with sha256 hash |
| Door Schedule | Exported door data | CSV with sha256 hash |
| Workflow Report | Complete run audit trail | JSON + NDJSON |
| Evidence Package | All artifacts zipped | ZIP file |

### Workflow Report Contents

```json
{
  "run_id": "8-char hex identifier",
  "status": "pass | warn | fail",
  "timestamps": {
    "started": "ISO8601",
    "ended": "ISO8601"
  },
  "steps": [...],
  "postconditions": [...],
  "cleanup": {
    "status": "pass | warn | fail",
    "created": 24,
    "deleted": 24,
    "leftovers": 0
  }
}
```

---

## May Warn About

These are **expected** warnings that don't indicate failure:

| Warning | Reason | Impact |
|---------|--------|--------|
| `ELEVATION_VIEWPORT_PLACED: warn` | No elevation views exist in model | Elevation sheets created but empty |
| `SCHEDULE_VIEWPORT_PLACED: warn` | Revit 2026 API limitation | Schedule created, exported to CSV, but not placed on sheet |
| `TITLEBLOCK_AVAILABLE: warn` | Preferred title block not found | Using fallback title block |
| `LEVELS_MISSING: warn` | Not all required levels exist | Some floor plan sheets skipped |

**A `WARN` status means the workflow completed successfully with known limitations.**

---

## Never Does

### Guarantees

1. **Never runs unbounded**
   - Budget limits enforced: max 30 workflow steps, 5 minute timeout
   - Exceeds budget = immediate stop, partial cleanup

2. **Never leaves artifacts behind**
   - Cleanup accounting is 100% verified
   - `created == deleted + cascade_deleted + leftovers`
   - Leftover count > 0 triggers `FAIL` status

3. **Never modifies existing content**
   - Only creates new elements (sheets, views, schedules)
   - Never edits existing sheets or views
   - All created elements use `ZZ_` prefix for identification

4. **Never pushes to cloud**
   - All operations are local to the Revit model
   - No data sent externally

5. **Never saves without explicit request**
   - Model changes are in-memory only
   - User must save manually after review

---

## Status Definitions

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `PASS` | All required tasks completed successfully | None - ready for review |
| `WARN` | Completed with optional task failures | Review warnings, usually acceptable |
| `FAIL` | Required task failed or cleanup incomplete | Investigate blockers, may need manual cleanup |

---

## Known Limitations (Revit 2026)

| Feature | Status | Workaround |
|---------|--------|------------|
| Schedule viewport placement | Not supported | Exports to CSV instead |
| Legend viewport placement | Not supported | Skip with warning |
| Elevation creation | Requires existing views | Create elevation views manually first |
| Cloud family loading | Requires UI interaction | Pre-load families to template |

---

## Preflight Requirements

Before running, the system checks:

| Check | Required | Remediation |
|-------|----------|-------------|
| MCP Bridge Connected | **Yes** | Ensure Revit is running with add-in loaded |
| Title Block Available | **Yes** | Load at least one title block family |
| At Least One Level | **Yes** | Create project levels |
| Walls/Extents | No | Crop regions will use defaults |
| Doors/Windows | No | Schedules will be empty but created |

---

## Evidence Package Contents

After each run, collect `evidence_YYYYMMDD_HHMMSS.zip`:

```
evidence_20251215_004612.zip
├── workflow_report_<run_id>.json    # Complete audit
├── workflow_report_<run_id>.ndjson  # Line-by-line audit
├── sheet_list_<run_id>.csv          # Sheets created
├── door_schedule_<run_id>.csv       # Door data export
└── resolved_pack.json               # Standards used
```

**Send this zip file for any support requests.**

---

## Version Compatibility

| Component | Supported Versions |
|-----------|-------------------|
| Revit | 2024, 2025, 2026 |
| RevitMCPBridge | 1.0+ |
| Spine | v0.2+ |
| Template Packs | v2 (v1 deprecated) |

---

## Breaking Changes Policy

This contract is locked for beta. Any changes will be:
1. Documented in release notes
2. Versioned (CONTRACT.md v1.1, v2.0, etc.)
3. Communicated before deployment

---

## Support

For issues during beta:

1. Collect the evidence package (ZIP file)
2. Note the exact error message
3. Include Revit version and project type
4. Contact support with all three items

---

*Last Updated: 2025-12-15*
*Contract Version: 1.0*
