# RevitMCPBridge2026

A Revit 2026 Add-in that exposes the Revit API through the Model Context Protocol (MCP), enabling AI-assisted automation of Revit tasks.

## Features

- **705+ MCP Methods** across 25+ categories (walls, doors, rooms, views, sheets, intelligence, validation, etc.)
- **5 Levels of Autonomy**:
  - Level 1: Basic Bridge (direct API access)
  - Level 2: Context Awareness (multi-element tracking)
  - Level 3: Learning & Memory (correction learning)
  - Level 4: Proactive Intelligence (gap detection, suggestions)
  - Level 5: Full Autonomy (goal execution, self-healing)
- **Knowledge Base**: 113 files of architectural domain expertise
- **Floor Plan Vision**: PDF-to-Revit conversion pipeline
- **Configuration System**: Centralized settings with hot-reload
- **Comprehensive Testing**: 68 unit tests with NUnit

## Quick Start

### Prerequisites
- Revit 2026
- .NET Framework 4.8
- Visual Studio 2022 (for building)

### Installation (Recommended)

Use the installer script:

```powershell
# From project root
.\scripts\deploy\Install-RevitMCPBridge.ps1
```

This will:
1. Build the project
2. Copy DLL and add-in to Revit folder
3. Copy default configuration

### Manual Installation

```bash
# Build
msbuild RevitMCPBridge2026.csproj /p:Configuration=Release

# Deploy
copy bin\Release\RevitMCPBridge2026.dll "%APPDATA%\Autodesk\Revit\Addins\2026\"
copy RevitMCPBridge2026.addin "%APPDATA%\Autodesk\Revit\Addins\2026\"
copy appsettings.json "%APPDATA%\Autodesk\Revit\Addins\2026\"
```

### Verify Installation

Start Revit and test the connection:

```python
import socket, json

def call_revit(method, params=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 8765))
        s.sendall(json.dumps({"method": method, "params": params or {}}).encode() + b'\n')
        return json.loads(s.recv(65536).decode())

# Check version
print(call_revit("getVersion"))

# Health check
print(call_revit("healthCheck"))
```

## Project Structure

```
RevitMCPBridge2026/
├── src/                        # C# source files
│   ├── MCPServer.cs            # Named pipe server (705+ methods)
│   ├── Configuration/          # Centralized settings
│   │   └── BridgeConfiguration.cs
│   ├── Exceptions/             # Custom exception hierarchy
│   │   └── MCPExceptions.cs
│   ├── Validation/             # Parameter validation
│   │   └── ParameterValidator.cs
│   ├── Helpers/                # Utility classes
│   │   ├── ResponseBuilder.cs  # Fluent JSON responses
│   │   ├── TransactionHelper.cs # Transaction management
│   │   ├── ElementLookup.cs    # Element queries
│   │   ├── GeometryHelper.cs   # Geometry utilities
│   │   └── CorrelatedLogger.cs # Request-correlated logging
│   ├── *Methods.cs             # API method implementations
│   └── AutonomousExecutor.cs   # Level 5 autonomy
├── tests/                      # 68 unit tests
│   ├── Unit/                   # Core unit tests
│   └── Integration/            # Integration tests
├── knowledge/                  # Domain knowledge (113 files)
├── docs/                       # Documentation
│   ├── api/METHODS.md          # API reference
│   ├── QUICKSTART.md           # Quick start guide
│   └── guides/                 # User guides
├── scripts/                    # Build & deploy scripts
│   └── deploy/                 # Installer scripts
├── python/                     # Python integration
└── appsettings.json            # Configuration file
```

## API Categories

| Category | Methods | Description |
|----------|---------|-------------|
| **System** | 6 | Version, health, configuration, stats |
| Walls | 11 | Create, modify, query walls |
| Doors/Windows | 13 | Place, configure openings |
| Rooms | 10 | Room creation, tagging, areas |
| Views | 12 | View creation, manipulation |
| Sheets | 11 | Sheet management, viewports |
| Schedules | 34 | Schedule creation, data export |
| Families | 29 | Family loading, placement |
| Parameters | 29 | Parameter get/set operations |
| Structural | 26 | Beams, columns, foundations |
| MEP | 35 | Ducts, pipes, equipment |
| Details | 33 | Detail lines, regions |
| Filters | 27 | View filters, overrides |
| Materials | 27 | Material management |
| Phases | 24 | Phase management |
| Worksets | 27 | Workset operations |
| Annotations | 33 | Tags, dimensions, text |
| Intelligence | 35 | AI autonomy methods |

## System Methods

New in v2.0: Built-in system monitoring and diagnostics.

```python
# Get version info
call_revit("getVersion")
# {"version": "2.0.0", "revitVersion": "2026.2", ...}

# Health check
call_revit("healthCheck")
# {"status": "healthy", "documentOpen": true, ...}

# Request statistics
call_revit("getStats")
# {"totalRequests": 1542, "averageResponseTimeMs": 45, ...}

# List all methods
call_revit("getMethods")
# {"methods": ["getVersion", "createWall", ...], "count": 705}

# Reload configuration
call_revit("reloadConfiguration")
```

## Configuration

Configure via `appsettings.json`:

```json
{
  "Pipe": {
    "Name": "RevitMCPBridge2026",
    "TimeoutMs": 30000,
    "MaxConnections": 5
  },
  "Logging": {
    "Level": "Information",
    "LogDirectory": "%APPDATA%/RevitMCPBridge/logs",
    "RetainedFileDays": 7
  },
  "Autonomy": {
    "Enabled": true,
    "MaxRetries": 3,
    "MaxElementsPerBatch": 100
  },
  "Version": {
    "Major": 2,
    "Minor": 0,
    "Patch": 0
  }
}
```

Changes take effect after calling `reloadConfiguration` or restarting Revit.

## Autonomy Levels

### Level 1: Basic Bridge
Direct MCP-to-Revit API translation. Each method call executes immediately.

### Level 2: Context Awareness
Tracks relationships between elements, maintains session context.

### Level 3: Learning & Memory
Learns from corrections, stores patterns for future use.

### Level 4: Proactive Intelligence
Detects gaps in workflow, suggests next steps, anticipates needs.

### Level 5: Full Autonomy
Execute high-level goals with self-healing:

```json
{
  "method": "executeGoal",
  "params": {
    "goalType": "create_sheet_set",
    "parameters": {
      "viewIds": [123456, 234567],
      "sheetPattern": "A-{level}.{sequence}"
    }
  }
}
```

**Guardrails:**
```json
{
  "method": "configureAutonomy",
  "params": {
    "maxElementsPerTask": 100,
    "allowedMethods": ["createWall", "placeDoor"],
    "blockedMethods": ["deleteElements"],
    "requireApprovalFor": ["createSheet"]
  }
}
```

## Development

### Building

```bash
# Full build
msbuild RevitMCPBridge2026.csproj /p:Configuration=Release

# Install and build
.\scripts\deploy\Install-RevitMCPBridge.ps1
```

### Testing

```bash
# Run all tests
dotnet test tests/RevitMCPBridge.Tests.csproj

# Run specific test
dotnet test --filter "FullyQualifiedName~WallMethodsTests"

# Run smoke tests
python tests/smoke_test.py
```

### Code Quality

The project includes:
- **Custom Exceptions**: Structured error hierarchy (MCPRevitException)
- **Parameter Validation**: Fluent validation with clear error messages
- **Response Builder**: Consistent JSON response formatting
- **Correlated Logging**: Request tracking with correlation IDs
- **Helper Utilities**: Transaction management, element lookup, geometry helpers

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get running in 5 minutes
- [API Reference](docs/api/METHODS.md) - Complete method documentation
- [Usage Guide](docs/guides/USAGE_GUIDE.md) - Detailed workflows
- [Architecture](docs/ARCHITECTURE.md) - System design

## Troubleshooting

**Connection refused:**
- Ensure Revit 2026 is running
- Check that add-in loaded (Revit ribbon should show MCP Bridge)
- Restart Revit

**Method not found:**
- Verify method name (case-sensitive)
- Run `getMethods` to list available methods
- Ensure latest DLL is installed

**Element operation failed:**
- Check that a document is open
- Verify element IDs are valid
- Check for blocking Revit dialogs

## License

MIT License - see [LICENSE](LICENSE) file.

Created by **Weber Gouin** / **[BIM Ops Studio](https://bimopsstudio.com)**

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to Contribute
- Report bugs and issues
- Suggest new methods or features
- Submit pull requests
- Share your use cases

## Support

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Professional Support**: Contact [BIM Ops Studio](https://bimopsstudio.com) for consulting and custom implementations

## Acknowledgments

This project represents the first open-source bridge connecting Claude AI to Autodesk Revit, enabling AI-assisted BIM automation through the Model Context Protocol.

---

**Version**: 2.0.0
**Revit**: 2025, 2026
**Author**: Weber Gouin / BIM Ops Studio
**Last Updated**: 2026-01
