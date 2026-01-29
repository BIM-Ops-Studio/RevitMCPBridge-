# RevitMCPBridge2026 - Project Context for Claude Code

## Knowledge Base Imports (Core - Always Loaded)
@knowledge/_index.md
@knowledge/user-preferences.md
@knowledge/voice-corrections.md
@knowledge/session-handoff.md
@knowledge/error-recovery.md
@knowledge/revit-api-lessons.md

## Knowledge Base Overview
The `knowledge/` folder contains **99 files (~1 MB)** of architectural domain expertise. The `_index.md` file provides a complete listing organized by category.

### Knowledge + MCP Integration
```
Knowledge Base (WHAT)     +     MCP Methods (HOW)     =     Intelligent Revit Automation
- Room sizes                    - createWalls()              - Correctly sized rooms
- Code requirements             - placeDoor()                - Code-compliant design
- Material specs                - createSchedule()           - Proper specifications
- Best practices                - setParameter()             - Professional output
```

### When to Read Knowledge Files

| Task | Read These Files |
|------|------------------|
| **Design a room/space** | room-standards.md, [building-type].md |
| **Place elements** | kitchen-bath-design.md, door-hardware.md |
| **Check code** | code-compliance.md, egress-design.md, accessibility-detailed.md |
| **Florida project** | florida-requirements.md |
| **MEP coordination** | mep-coordination.md, [specific-system].md |
| **Documentation** | cd-standards.md, annotation-standards.md |
| **Materials/specs** | material-selection.md, specifications.md |
| **Structural** | structural-basics.md, foundation-types.md |

### Knowledge File Categories (99 files)
| Category | Count | Key Files |
|----------|-------|-----------|
| Building Types | 17 | single-family-residential, multi-family-design, office-design, healthcare-design |
| Structural/Envelope | 12 | wall-assemblies, roof-assemblies, foundation-types, exterior-envelope |
| MEP Systems | 10 | hvac-systems, electrical-systems, plumbing-systems, fire-protection |
| Interior/Finishes | 9 | kitchen-bath-design, door-hardware, millwork-standards |
| Codes/Regulatory | 9 | code-compliance, egress-design, accessibility-detailed, florida-requirements |
| Project Delivery | 10 | construction-admin, cost-estimating, specifications |
| Documentation | 7 | cd-standards, annotation-standards, detail-library |
| Revit/Technical | 8 | revit-workflows, batch-operations, error-handling |
| Workflows | 4 | common-workflows, workflows-pdf-to-revit |
| Emerging Tech | 6 | mass-timber, modular-prefab, renewable-energy, resilient-design |

### Workflow: Using Knowledge with MCP

**Example: "Add a master bathroom"**
```
1. Read: knowledge/kitchen-bath-design.md (clearances, fixtures)
2. Read: knowledge/room-standards.md (minimum sizes)
3. Read: knowledge/plumbing-systems.md (fixture requirements)
4. Execute: createWalls() with proper dimensions
5. Execute: placeFamilyInstance() for toilet, vanity, tub
6. Execute: createRoom() and tagRoom()
```

**Example: "Check egress compliance"**
```
1. Read: knowledge/egress-design.md (travel distance, exit width)
2. Read: knowledge/code-compliance.md (occupancy, construction type)
3. Execute: getRooms() to get occupant loads
4. Calculate: required exit capacity
5. Execute: getElements(Doors) to verify exits
```

## Session Start: Standards Detection
At the start of every session involving Revit work:
1. Read the live system state to see what project is open
2. Get project info from Revit (name, number, client)
3. Match against firm profiles in `knowledge/standards/`
4. Load and apply the matching standards profile
5. If unknown project: offer to analyze and create new profile

## Project Overview
This is a **Revit 2026 Add-in** that exposes the Revit API through the Model Context Protocol (MCP), enabling AI-assisted automation of Revit tasks via natural language.

## Key Facts
- **Total Methods**: 705 (25+ categories including intelligence, validation, compliance)
- **Current Progress**: 705/705 methods registered (100%)
- **Language**: C# (.NET Framework 4.8)
- **Target**: Autodesk Revit 2026
- **Architecture**: MCP Server → Named Pipe → Revit API

## Project Structure
```
RevitMCPBridge2026/
├── src/
│   ├── RevitMCPBridge.cs          # Main entry point, command handler
│   ├── MCPServer.cs                # Named pipe server (282 registrations)
│   ├── WallMethods.cs              # 11/11 methods ✅
│   ├── DoorWindowMethods.cs        # 13/13 methods ✅
│   ├── RoomMethods.cs              # 10/10 methods ✅
│   ├── ViewMethods.cs              # 12/12 methods ✅
│   ├── SheetMethods.cs             # 11/11 methods ✅
│   ├── TextTagMethods.cs           # 12/12 methods ✅
│   ├── ScheduleMethods.cs          # 34/34 methods ✅
│   ├── FamilyMethods.cs            # 29/29 methods ✅
│   ├── ParameterMethods.cs         # 29/29 methods ✅
│   ├── StructuralMethods.cs        # 26/26 methods ✅
│   ├── MEPMethods.cs               # 35/35 methods ✅
│   ├── DetailMethods.cs            # 33/33 methods ✅
│   ├── FilterMethods.cs            # 27/27 methods ✅
│   ├── MaterialMethods.cs          # 27/27 methods ✅
│   ├── PhaseMethods.cs             # 24/24 methods ✅
│   ├── WorksetMethods.cs           # 27/27 methods ✅
│   ├── AnnotationMethods.cs        # 33/33 methods ✅
│   ├── SheetPatternMethods.cs      # 11/11 methods ✅ (intelligent sheet numbering)
│   ├── ViewportCaptureMethods.cs   # 7/7 methods ✅ (NEW: viewport capture/camera)
│   ├── RenderMethods.cs            # 7/7 methods ✅ (NEW: AI rendering integration)
│   └── ProjectSetupMethods.cs      # Project initialization utilities
├── python/
│   └── diffusion_service.py        # Stable Diffusion integration (ComfyUI/A1111)
├── RevitMCPBridge2026.addin        # Revit add-in manifest
├── RevitMCPBridge2026.csproj       # Project file
├── IMPLEMENTATION_PROGRESS.md      # Detailed progress tracker
├── SESSION_STATE.md                # Current session state
└── CLAUDE.md                       # This file
```

## Project Status: COMPLETE
All 17 original categories implemented (412 methods) plus:
- SheetPatternMethods (11 methods) - intelligent sheet numbering patterns
- ViewportCaptureMethods (7 methods) - viewport capture, camera control
- RenderMethods (7 methods) - AI rendering via Stable Diffusion

**Total: 705 MCP-accessible methods**

## Build & Deploy Process
```bash
# Build the project
cd /mnt/d/RevitMCPBridge2026
msbuild RevitMCPBridge2026.csproj /p:Configuration=Release

# DLL location after build
# bin/Release/RevitMCPBridge2026.dll

# To deploy (requires Revit restart):
# Copy DLL to: %APPDATA%\Autodesk\Revit\Addins\2026\
```

## Revit 2026 API Changes to Remember
1. **ScheduleFieldId**: Use `ScheduleFieldId` instead of `int` for field references
2. **OutlineSegments**: Property removed - don't use in ScheduleDefinition
3. **ElementId**: Always use `new ElementId(int)` for element IDs
4. **Transactions**: All document modifications must be in Transaction blocks

## Common Patterns in This Codebase

### Method Structure
```csharp
public static string MethodName(UIApplication uiApp, JObject parameters)
{
    try
    {
        var doc = uiApp.ActiveUIDocument.Document;

        // Parameter validation
        if (parameters["requiredParam"] == null)
        {
            return JsonConvert.SerializeObject(new
            {
                success = false,
                error = "requiredParam is required"
            });
        }

        // Parse parameters
        var paramValue = parameters["requiredParam"].ToString();

        // Transaction for modifications
        using (var trans = new Transaction(doc, "Operation Name"))
        {
            trans.Start();

            // Revit API operations here

            trans.Commit();

            // Return success
            return JsonConvert.SerializeObject(new
            {
                success = true,
                // ... result data
            });
        }
    }
    catch (Exception ex)
    {
        return JsonConvert.SerializeObject(new
        {
            success = false,
            error = ex.Message,
            stackTrace = ex.StackTrace
        });
    }
}
```

### Method Registration
All methods must be registered in `RevitMCPBridge.cs`:
```csharp
methodMap["MethodName"] = NamespaceMethods.MethodName;
```

## Workflow Instructions for Claude

### When Starting a Session
1. **ALWAYS READ** `SESSION_STATE.md` first to know where we left off
2. Review `IMPLEMENTATION_PROGRESS.md` to see overall status
3. Check for any build errors or pending tasks
4. Ask user if they want to continue from last session or start something new

### When Implementing Methods
1. **Create Todo List**: Use TodoWrite to track the batch (5-10 methods)
2. **Read Source File**: Read the relevant Methods.cs file to see framework
3. **Implement One at a Time**: Complete each method fully before moving to next
4. **Build After Batch**: Run MSBuild after completing the batch
5. **Fix Errors**: Address any compilation errors immediately
6. **Update Progress**: Update IMPLEMENTATION_PROGRESS.md and SESSION_STATE.md
7. **Mark Todos Complete**: Mark each todo as completed as you finish

### When Building
```bash
cd /mnt/d/RevitMCPBridge2026
msbuild RevitMCPBridge2026.csproj /p:Configuration=Release /v:minimal
```

**Expected Warnings**: 20-30 assembly version conflicts (harmless, ignore them)
**Success**: "Build succeeded. 0 Error(s)"

### When Updating Progress Files
- **SESSION_STATE.md**: Update current session, next tasks, build status
- **IMPLEMENTATION_PROGRESS.md**: Update method counts, session log, quick stats

## MCP Server Information
The MCP server is **already configured globally** in the user's Claude Code setup. No need to reconfigure it.

**MCP Endpoints Available**:
- Aider (3 instances): ollama, llama4, quasar
- SQLite: Database operations
- Playwright: Browser automation
- IDE Integration: VS Code diagnostics

## Important Reminders
- 🚫 **NEVER** create new files unless explicitly needed
- ✅ **ALWAYS** prefer editing existing files
- ✅ **ALWAYS** read SESSION_STATE.md at start of session
- ✅ **ALWAYS** use TodoWrite for tracking batch implementation
- ✅ **ALWAYS** build after completing a batch
- ✅ **ALWAYS** update both progress files when batch is complete
- 🔧 **Framework exists** for all 414 methods (placeholder code already there)
- 📝 **Consistent patterns** - follow existing method structure

## User Preferences
- **Work Style**: Small batches, steady progress
- **Communication**: Direct, technical, no fluff
- **Documentation**: Keep progress files updated
- **Speed**: Prioritize getting methods working over perfection

## Quick Commands
```bash
# Navigate to project
cd /mnt/d/RevitMCPBridge2026

# Build
msbuild RevitMCPBridge2026.csproj /p:Configuration=Release /v:minimal

# Check what's changed
git status

# Find method in code
grep -r "MethodName" src/

# Count implemented vs total methods
# (check IMPLEMENTATION_PROGRESS.md)
```

## Success Criteria for Each Session
✅ All methods in batch implemented
✅ Project builds with 0 errors
✅ Progress files updated
✅ Session state documented
✅ Todos marked complete

---

**Last Updated**: 2025-01-14
**Current Session**: 2 (completed)
**Next Session**: 3 (ScheduleMethods Batch 3)
