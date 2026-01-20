# RevitMCPBridge2026 Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Claude Code / AI Client                       │
│                    (Natural Language Interface)                      │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ MCP Protocol
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Named Pipe Server                            │
│                    \\.\pipe\RevitMCPBridge2026                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      MCPServer.cs                            │    │
│  │  • Request parsing and routing                               │    │
│  │  • Method dispatch (437+ methods)                            │    │
│  │  • Response serialization                                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ Revit Idling Event
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Revit 2026 API                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Method Categories                         │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐    │    │
│  │  │  Walls  │ │  Rooms  │ │  Views  │ │  Intelligence   │    │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘    │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐    │    │
│  │  │  Doors  │ │ Sheets  │ │  MEP    │ │   Structural    │    │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘    │    │
│  │  ... (17 categories total)                                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. MCPServer.cs
Main entry point for MCP communication.

**Responsibilities:**
- Named pipe server lifecycle
- Request/response handling
- Method routing to appropriate handler
- JSON serialization

**Key Methods:**
- `StartServer()` - Initialize named pipe
- `ProcessRequest()` - Route to method handler
- `ExecuteMethod()` - Invoke specific method
- `ListAvailableMethods()` - Return method catalog

### 2. Method Files (*Methods.cs)

Each category has a dedicated method file:

| File | Methods | Purpose |
|------|---------|---------|
| WallMethods.cs | 11 | Wall creation, modification |
| RoomMethods.cs | 10 | Room operations |
| ViewMethods.cs | 12 | View management |
| SheetMethods.cs | 11 | Sheet/viewport |
| ScheduleMethods.cs | 34 | Schedule operations |
| ... | ... | ... |

**Standard Method Pattern:**
```csharp
public static string MethodName(UIApplication uiApp, JObject parameters)
{
    try {
        var doc = uiApp.ActiveUIDocument.Document;

        // Parameter validation
        // Transaction for modifications
        // Return JSON result
    }
    catch (Exception ex) {
        return ErrorResponse(ex);
    }
}
```

### 3. Intelligence Layer

Five levels of autonomy:

```
┌────────────────────────────────────────────────────────────────┐
│ Level 5: Full Autonomy                                          │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ AutonomousExecutor.cs                                       ││
│ │ • GoalPlanner - Task decomposition                          ││
│ │ • SelfHealer - Error recovery                               ││
│ │ • GuardrailSystem - Bounded execution                       ││
│ │ • QualityAssessor - Result verification                     ││
│ └─────────────────────────────────────────────────────────────┘│
├────────────────────────────────────────────────────────────────┤
│ Level 4: Proactive Intelligence                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ProactiveMonitor.cs                                         ││
│ │ • Gap detection                                              ││
│ │ • Suggestion engine                                          ││
│ │ • Model snapshots                                            ││
│ └─────────────────────────────────────────────────────────────┘│
├────────────────────────────────────────────────────────────────┤
│ Level 3: Learning & Memory                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ CorrectionLearner.cs                                        ││
│ │ • Error pattern learning                                     ││
│ │ • Correction storage                                         ││
│ │ • Knowledge export                                           ││
│ └─────────────────────────────────────────────────────────────┘│
├────────────────────────────────────────────────────────────────┤
│ Level 2: Context Awareness                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ChangeTracker.cs                                            ││
│ │ • Element relationship tracking                              ││
│ │ • Session context                                            ││
│ └─────────────────────────────────────────────────────────────┘│
├────────────────────────────────────────────────────────────────┤
│ Level 1: Basic Bridge                                           │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Direct MCP → Revit API translation                          ││
│ │ 437 methods                                                  ││
│ └─────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Processing

```
1. Client sends JSON request
   {"method": "createWall", "params": {...}}

2. Named pipe receives message

3. MCPServer.ProcessRequest parses JSON

4. Method router finds handler
   methodMap["createWall"] -> WallMethods.CreateWall

5. Handler executes in Revit context
   - Validates parameters
   - Creates Transaction
   - Calls Revit API
   - Commits Transaction

6. Response serialized to JSON
   {"success": true, "elementId": 123456}

7. Response sent back through pipe
```

### Transaction Management

All modifications require transactions:

```csharp
using (var trans = new Transaction(doc, "Create Wall"))
{
    trans.Start();

    // Revit API calls
    Wall.Create(doc, curve, wallTypeId, levelId, height, 0, false, false);

    trans.Commit();
}
```

## File Structure

```
RevitMCPBridge2026/
├── src/                        # C# source (70 files)
│   ├── MCPServer.cs           # Named pipe server
│   ├── RevitMCPBridge.cs      # Add-in entry point
│   ├── *Methods.cs            # API method implementations
│   ├── AutonomousExecutor.cs  # Level 5 autonomy
│   ├── ProactiveMonitor.cs    # Level 4 intelligence
│   ├── CorrectionLearner.cs   # Level 3 learning
│   └── ChangeTracker.cs       # Level 2 context
├── knowledge/                  # Domain knowledge (113 files)
│   ├── _index.md              # Knowledge index
│   ├── room-standards.md      # Room sizing
│   ├── code-compliance.md     # Building codes
│   └── ...
├── Properties/                 # Assembly info
├── bin/                        # Build output
├── docs/                       # Documentation
├── tests/                      # Test suites
├── scripts/                    # Build/deploy scripts
└── data/                       # Sample data
```

## Integration Points

### Revit Integration

- **Add-in Manifest**: RevitMCPBridge2026.addin
- **Entry Point**: ExternalApplication.OnStartup
- **Event Hook**: Application.Idling (for async operations)
- **API Version**: Revit 2026 (.NET Framework 4.8)

### External Integrations

- **Stable Diffusion**: python/diffusion_service.py for AI rendering
- **Claude Memory MCP**: Persistent learning storage
- **Floor Plan Vision MCP**: PDF extraction

## Security Considerations

1. **Named Pipe Access**: Local machine only
2. **Transaction Safety**: All operations are transactional
3. **Input Validation**: Parameters validated before execution
4. **Guardrails**: Level 5 autonomy has configurable limits

## Performance

- **Async Operations**: Non-blocking pipe communication
- **Batch Support**: Bulk operations reduce overhead
- **Caching**: Type lookups cached per session
- **Logging**: Serilog for diagnostics

## Extension Points

### Adding New Methods

1. Create method in appropriate *Methods.cs file
2. Register in MCPServer.cs method router
3. Add to ListAvailableMethods catalog
4. Update documentation

### Adding New Intelligence

1. Create new intelligence class
2. Wire into IntelligenceMethods.cs
3. Register endpoints in MCPServer.cs
4. Add MCP method catalog entry
