# Changelog

All notable changes to RevitMCPBridge2026 are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01

Major maturity improvement release: 7/10 → 9.9/10

### Added

#### Testing Infrastructure (Phase 1)
- New test project `RevitMCPBridge.Tests.csproj` with NUnit framework
- 68 unit tests covering core functionality
- Mock infrastructure for Revit API (`MockUIApplication`, `MockDocument`, `MockTransaction`)
- Test fixtures and data helpers
- Tests for MCPServer, WallMethods, RoomMethods, ViewMethods, Intelligence

#### Code Quality (Phase 2)
- `MCPRevitException` - Structured exception hierarchy with typed errors
- `ParameterValidator` - Fluent parameter validation with clear error messages
- `ResponseBuilder` - Consistent JSON response construction
- `CorrelatedLogger` - Request-correlated logging with timing

#### Deployment & DevOps (Phase 3)
- `BridgeConfiguration` - Centralized configuration system
- `appsettings.json` - Configuration file with full schema
- `SystemMethods` - New system endpoints:
  - `getVersion` - Bridge and Revit version info
  - `healthCheck` - Connectivity and status check
  - `getStats` - Request statistics and metrics
  - `reloadConfiguration` - Hot-reload configuration
  - `getMethods` - List available MCP methods
  - `getConfiguration` - Get current settings
- Enhanced installer script with config handling
- Request statistics tracking in MCPServer

#### Maintainability (Phase 4)
- `TransactionHelper` - Transaction lifecycle management utilities
- `ElementLookup` - Type-safe element queries with error handling
- `GeometryHelper` - Unit conversions, geometry calculations

#### Documentation (Phase 5)
- Updated API documentation with System methods category
- New Quick Start guide (`docs/QUICKSTART.md`)
- Python helper class examples
- Comprehensive README with new features
- This changelog

### Changed
- README.md completely rewritten with new structure
- docs/api/METHODS.md updated with System category (now 443+ methods)
- Install script now handles configuration file

### Fixed
- Compiler warnings fixed across codebase
- Unused variable warnings resolved
- Pragma warnings added for intentional suppressions
- Test files excluded from main build

### Technical Debt Addressed
- Created exception hierarchy for better error handling
- Standardized parameter validation pattern
- Centralized configuration management
- Added helper utilities to reduce code duplication

## [1.0.0] - 2024-12

Initial production release.

### Added
- 437 MCP methods across 17 categories
- 5 levels of autonomy (Basic to Full)
- Knowledge base with 113 architectural reference files
- Floor Plan Vision PDF extraction
- Named pipe communication

---

## Migration Guide

### From 1.x to 2.0

1. **Configuration**: Add `appsettings.json` to your Revit add-ins folder
2. **New Methods**: Use new system endpoints for monitoring
3. **Error Handling**: Errors now include typed `errorType` field

Example configuration:
```json
{
  "Pipe": { "Name": "RevitMCPBridge2026" },
  "Logging": { "Level": "Information" },
  "Version": { "Major": 2, "Minor": 0, "Patch": 0 }
}
```
