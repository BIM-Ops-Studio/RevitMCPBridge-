# AEC Automation - Troubleshooting Guide

## Common Issues

### 1. "MCP Bridge NOT connected"

**Symptom:**
```
[1/6] Environment checks...
  ✗ MCP Bridge NOT connected
```

**Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Revit not running | Start Revit and open a project |
| Add-in not loaded | Check Add-Ins tab for "MCP Bridge" panel |
| DLL not copied | Copy DLL to Revit addins folder, restart Revit |
| Modal dialog open | Close any open dialogs in Revit |
| Revit is busy | Wait for current operation to complete, then click in drawing area |

**Verify MCP is loaded:**
1. In Revit, go to Add-Ins tab
2. Look for "MCP Bridge" panel
3. Click "Start Server" if available

### 2. "No suitable title block found"

**Symptom:**
```
[2/6] Template requirements...
  ✗ No suitable title block found
```

**Fix:**
1. In Revit, go to Insert tab
2. Load a title block family (Insert > Load Family)
3. Re-run preflight

### 3. "Sheet number is already in use"

**Symptom:**
```
FAILED: Sheet number is already in use: A1.01-xxxx
```

**Cause:** The model already has sheets with conflicting numbers.

**Fixes:**
1. Use a different run (re-run creates new run_id suffix)
2. Delete existing sheets with the conflicting numbers
3. Use a model without existing sheets

### 4. "Request timed out"

**Symptom:**
```
error: Request timed out
```

**Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Revit is processing | Wait, then click in drawing area to activate |
| Large model | Increase timeout (default: 30s) |
| Modal dialog | Close any open dialogs |

### 5. "Budget EXCEEDS limits"

**Symptom:**
```
Budget: ✗ EXCEEDS limits (40/30 steps)
```

**This is informational only.** The workflow will still run. For large sheet sets (multifamily), the task count may exceed the conservative default limit.

### 6. Cleanup Shows Leftovers

**Symptom:**
```
Leftover: 2
Status: WARN
⚠ Leftovers:
  - sheet #12345: Element not found
```

**Cause:** Elements were deleted by Revit cascade (e.g., deleting a sheet automatically deletes its viewports).

**This is usually fine.** The accounting tracks:
- `deleted`: Explicitly deleted by cleanup
- `cascade_deleted`: Already gone when we tried to delete
- `leftovers`: Failed to delete (true failures)

If `leftovers > 0` with errors other than "not found", investigate manually.

### 7. Empty Schedules

**Symptom:**
```
Doors: 0 (schedule will be empty)
```

**This is expected** if your model has no doors/windows/rooms. The schedules will be created but contain no data.

### 8. Python Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'xxx'
```

**Fix:**
Ensure you're running from the correct directory:
```bash
cd beta_package
python cli/aec list
```

Or use full paths:
```bash
python /path/to/beta_package/cli/aec list
```

## Collecting Logs for Support

### Step 1: Run with Evidence Collection

```bash
python cli/aec run --sector sfh --force
```

### Step 2: Locate Evidence Package

```bash
ls evidence/
# evidence_20251215_004612.zip
```

### Step 3: Send to Support

Include:
1. The evidence ZIP file
2. Revit version (e.g., "Revit 2026.2")
3. Exact error message
4. Steps to reproduce

## FAQ

### Q: Can I run this on an existing project with sheets?

**A:** Yes, but:
- Created sheets will have unique suffixes (`-xxxx`)
- Existing sheets are never modified
- Run cleanup removes only what was created

### Q: Why are elevations always WARN?

**A:** The system can place existing elevation views but cannot create them. Create elevation views manually first if you want them on sheets.

### Q: Why doesn't the schedule appear on the sheet?

**A:** Revit 2026 API doesn't support placing schedule viewports. The schedule is created and exported to CSV instead.

### Q: How do I undo a run?

**A:** The cleanup phase automatically deletes all created elements. If cleanup fails, manually delete elements starting with `ZZ_` prefix.

### Q: Can I keep the created sheets?

**A:** Currently, the workflow always cleans up. To keep sheets:
1. Comment out the cleanup call in spine_v02_adaptive.py
2. Or export the evidence and recreate manually

---

## Still Stuck?

1. Check CONTRACT.md for known limitations
2. Verify all prerequisites are met
3. Try with a simple test model first
4. Collect evidence and contact support

---

*Last Updated: 2025-12-15*
