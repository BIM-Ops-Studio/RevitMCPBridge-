using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.BuildingModel.Models;
using Serilog;

namespace RevitMCPBridge.BuildingModel.PhaseExecutors
{
    /// <summary>
    /// Phase 1: Project Setup - Initialize project with grids and settings
    /// </summary>
    public class ProjectSetupExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.ProjectSetup;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();

            try
            {
                // Set project info
                var projectParams = new JObject
                {
                    ["projectName"] = context.State.ProjectName,
                    ["buildingType"] = program.BuildingType
                };

                // Note: setProjectInfo would need to exist as an MCP method
                // For now, this is a placeholder for project initialization

                Log.Information("[BuildingModel] Project setup complete: {Name}", context.State.ProjectName);

                return Success(elementIds, $"Project initialized: {context.State.ProjectName}");
            }
            catch (Exception ex)
            {
                return Error($"Project setup failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 2: Levels - Create all floor levels
    /// NOTE: GetOperations intentionally NOT overridden to ensure Execute() is called directly.
    /// This is required because levels need to be stored in registry by NAME, which only
    /// happens in Execute(). CIPS would bypass this registry storage.
    /// </summary>
    public class LevelsExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Levels;

        // GetOperations NOT overridden - returns empty list from base class
        // This ensures Execute() is called directly, not through CIPS
        // because we need to store levelName -> levelId mapping in registry

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();
            var warnings = new List<string>();

            try
            {
                // Step 1: Query existing levels in the project
                var existingLevels = GetExistingLevels(context.UIApp);
                Log.Information("[BuildingModel] Found {Count} existing levels in project", existingLevels.Count);

                for (int i = 0; i < program.NumberOfStories; i++)
                {
                    var levelName = program.LevelNames?.ElementAtOrDefault(i)
                        ?? $"Level {i + 1}";
                    var elevation = program.LevelElevations?.ElementAtOrDefault(i)
                        ?? (i * program.FloorToFloorHeight);

                    // Step 2: Check if a matching level already exists
                    var existingLevel = FindMatchingLevel(existingLevels, levelName, elevation);

                    if (existingLevel != null)
                    {
                        // Use existing level - store in registry
                        context.State.Registry.Levels[levelName] = existingLevel.Value.Id;
                        elementIds.Add(existingLevel.Value.Id);
                        warnings.Add($"Using existing level '{existingLevel.Value.Name}' (ID: {existingLevel.Value.Id}) for '{levelName}'");
                        Log.Information("[BuildingModel] Using existing level {Name} (ID: {Id}) for {TargetName}",
                            existingLevel.Value.Name, existingLevel.Value.Id, levelName);
                    }
                    else
                    {
                        // Create new level
                        var parameters = new JObject
                        {
                            ["name"] = levelName,
                            ["elevation"] = elevation
                        };

                        var ids = ExecuteMCPMethod(context.UIApp, "createLevel", parameters);

                        if (ids.Count > 0)
                        {
                            elementIds.Add(ids[0]);
                            context.State.Registry.Levels[levelName] = ids[0];
                            Log.Information("[BuildingModel] Created new level {Name} at elevation {Elev} (ID: {Id})",
                                levelName, elevation, ids[0]);
                        }
                        else
                        {
                            // Creation returned no ID - try to find it now
                            var refreshedLevels = GetExistingLevels(context.UIApp);
                            var justCreated = FindMatchingLevel(refreshedLevels, levelName, elevation);
                            if (justCreated != null)
                            {
                                context.State.Registry.Levels[levelName] = justCreated.Value.Id;
                                elementIds.Add(justCreated.Value.Id);
                                warnings.Add($"Level '{levelName}' found after creation attempt");
                            }
                        }
                    }
                }

                var message = elementIds.Count > 0
                    ? $"Configured {elementIds.Count} levels ({context.State.Registry.Levels.Count} in registry)"
                    : "No levels configured";

                var result = Success(elementIds, message);
                result.Warnings = warnings;
                return result;
            }
            catch (Exception ex)
            {
                return Error($"Level creation failed: {ex.Message}");
            }
        }

        /// <summary>
        /// Query existing levels from the project via MCP
        /// </summary>
        private List<LevelInfo> GetExistingLevels(Autodesk.Revit.UI.UIApplication uiApp)
        {
            var levels = new List<LevelInfo>();

            try
            {
                var result = MCPServer.ExecuteMethod(uiApp, "getLevels", new JObject());
                var resultObj = JObject.Parse(result);

                if (resultObj["success"]?.Value<bool>() == true)
                {
                    var levelsArray = resultObj["levels"] as JArray;
                    if (levelsArray != null)
                    {
                        foreach (var level in levelsArray)
                        {
                            levels.Add(new LevelInfo
                            {
                                Id = level["levelId"]?.Value<int>() ?? 0,
                                Name = level["name"]?.ToString() ?? "",
                                Elevation = level["elevation"]?.Value<double>() ?? 0
                            });
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Warning("[BuildingModel] Failed to query existing levels: {Error}", ex.Message);
            }

            return levels;
        }

        /// <summary>
        /// Find a level that matches by name or elevation (within tolerance)
        /// </summary>
        private LevelInfo? FindMatchingLevel(List<LevelInfo> levels, string targetName, double targetElevation)
        {
            const double elevationTolerance = 0.1; // feet

            // First try exact name match
            var byName = levels.FirstOrDefault(l =>
                l.Name.Equals(targetName, StringComparison.OrdinalIgnoreCase));
            if (byName.Id > 0) return byName;

            // Then try elevation match (for cases like "Level 1" vs "L1")
            var byElevation = levels.FirstOrDefault(l =>
                Math.Abs(l.Elevation - targetElevation) < elevationTolerance);
            if (byElevation.Id > 0) return byElevation;

            return null;
        }

        private struct LevelInfo
        {
            public int Id;
            public string Name;
            public double Elevation;
        }
    }

    /// <summary>
    /// Phase 3: Floors - Create floor slabs
    /// </summary>
    public class FloorsExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Floors;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();

            try
            {
                // Create floors at each level
                foreach (var levelEntry in context.State.Registry.Levels)
                {
                    var parameters = new JObject
                    {
                        ["levelId"] = levelEntry.Value,
                        ["boundaryPoints"] = JArray.FromObject(program.BuildingFootprint.Select(p =>
                            new double[] { p.X, p.Y, 0 })),
                        ["floorType"] = program.RoofType ?? "Floor - Generic"
                    };

                    var ids = ExecuteMCPMethod(context.UIApp, "createFloor", parameters);
                    elementIds.AddRange(ids);
                }

                return Success(elementIds, $"Created {elementIds.Count} floors");
            }
            catch (Exception ex)
            {
                return Error($"Floor creation failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 4 & 6: Walls - Create exterior or interior walls
    /// </summary>
    public class WallsExecutor : BasePhaseExecutor
    {
        private readonly bool _isExterior;

        public override BuildingPhase Phase =>
            _isExterior ? BuildingPhase.ExteriorWalls : BuildingPhase.InteriorWalls;

        public WallsExecutor(bool isExterior)
        {
            _isExterior = isExterior;
        }

        public override List<MCPOperation> GetOperations(PhaseExecutionContext context)
        {
            var operations = new List<MCPOperation>();
            var program = context.State.Program;

            // Get first level ID for wall placement
            var levelId = context.State.Registry.Levels.Values.FirstOrDefault();

            if (_isExterior)
            {
                // Create walls from building footprint
                var footprint = program.BuildingFootprint;
                if (footprint != null && footprint.Count >= 3)
                {
                    for (int i = 0; i < footprint.Count; i++)
                    {
                        var start = footprint[i];
                        var end = footprint[(i + 1) % footprint.Count];

                        // API expects [x, y, z] array format, not {x, y} object
                        var wallParams = new JObject
                        {
                            ["startPoint"] = new JArray { start.X, start.Y, 0 },
                            ["endPoint"] = new JArray { end.X, end.Y, 0 },
                            ["height"] = program.FloorToFloorHeight
                        };

                        // Add levelId if available
                        if (levelId > 0)
                        {
                            wallParams["levelId"] = levelId;
                        }

                        // Add wall type if specified
                        if (!string.IsNullOrEmpty(program.ExteriorWallType))
                        {
                            wallParams["wallType"] = program.ExteriorWallType;
                        }

                        operations.Add(new MCPOperation(
                            "createWall",
                            wallParams,
                            $"Create exterior wall {i + 1}"
                        ));
                    }
                }
            }
            else
            {
                // Interior walls would come from room layout
                // This is a placeholder - actual implementation would parse room boundaries
            }

            return operations;
        }

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var operations = GetOperations(context);
            var elementIds = new List<int>();

            try
            {
                foreach (var op in operations)
                {
                    var ids = ExecuteMCPMethod(context.UIApp, op.MethodName, op.Parameters);
                    elementIds.AddRange(ids);
                }

                var wallType = _isExterior ? "exterior" : "interior";
                return Success(elementIds, $"Created {elementIds.Count} {wallType} walls");
            }
            catch (Exception ex)
            {
                return Error($"Wall creation failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 5: Roof - Create roof elements
    /// </summary>
    public class RoofExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Roof;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();

            try
            {
                // Get top level
                var topLevel = context.State.Registry.Levels.LastOrDefault();
                if (topLevel.Value == 0)
                {
                    return Error("No levels found - cannot create roof");
                }

                var parameters = new JObject
                {
                    ["levelId"] = topLevel.Value,
                    ["boundaryPoints"] = JArray.FromObject(program.BuildingFootprint.Select(p =>
                        new double[] { p.X, p.Y, program.FloorToFloorHeight * (program.NumberOfStories) })),
                    ["roofType"] = program.RoofType,
                    ["slope"] = program.RoofSlope
                };

                var ids = ExecuteMCPMethod(context.UIApp, "createFootprintRoof", parameters);
                elementIds.AddRange(ids);

                return Success(elementIds, $"Created roof with {elementIds.Count} elements");
            }
            catch (Exception ex)
            {
                return Error($"Roof creation failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 7: Vertical Circulation - Stairs and elevators
    /// </summary>
    public class VerticalCirculationExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.VerticalCirculation;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();
            var warnings = new List<string>();

            try
            {
                // Check if we have stair specs in the program
                if (program.Stairs == null || program.Stairs.Count == 0)
                {
                    // For multi-story buildings, suggest stair location
                    if (program.NumberOfStories > 1)
                    {
                        warnings.Add("Multi-story building detected but no stair specs provided. Consider adding stairs manually.");
                    }
                    return new PhaseExecutionResult
                    {
                        Success = true,
                        Phase = Phase,
                        Message = "No stairs specified in building program",
                        CreatedElementIds = elementIds,
                        Confidence = 1.0,
                        Warnings = warnings
                    };
                }

                // Create stairs from specifications
                foreach (var stair in program.Stairs)
                {
                    var baseLevelId = context.State.Registry.Levels.Values.FirstOrDefault();
                    var topLevelId = context.State.Registry.Levels.Values.Skip(1).FirstOrDefault();

                    if (baseLevelId == 0)
                    {
                        warnings.Add("No base level found for stair placement");
                        continue;
                    }

                    var parameters = new JObject
                    {
                        ["baseLevelId"] = stair.BaseLevelId ?? baseLevelId,
                        ["topLevelId"] = stair.TopLevelId ?? (topLevelId > 0 ? topLevelId : baseLevelId),
                        ["location"] = new JArray { stair.Location?.X ?? 0, stair.Location?.Y ?? 0, 0 },
                        ["width"] = stair.Width ?? 3.0,
                        ["desiredRiserHeight"] = stair.RiserHeight ?? 0.583 // 7 inches default
                    };

                    var ids = ExecuteMCPMethod(context.UIApp, "createStairByComponent", parameters);
                    elementIds.AddRange(ids);
                }

                var result = Success(elementIds, $"Created {elementIds.Count} stairs");
                result.Warnings = warnings;
                return result;
            }
            catch (Exception ex)
            {
                return Error($"Vertical circulation failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 8: Openings - Doors and windows
    /// </summary>
    public class OpeningsExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Openings;

        public override List<MCPOperation> GetOperations(PhaseExecutionContext context)
        {
            var operations = new List<MCPOperation>();
            var program = context.State.Program;

            // Add door operations
            foreach (var door in program.Doors ?? new List<DoorSpec>())
            {
                operations.Add(new MCPOperation(
                    "placeDoor",
                    new JObject
                    {
                        ["wallId"] = door.WallId,
                        ["location"] = new JObject
                        {
                            ["x"] = door.Location?.X ?? 0,
                            ["y"] = door.Location?.Y ?? 0
                        },
                        ["doorType"] = door.DoorType ?? program.DefaultDoorType
                    },
                    $"Place door at ({door.Location?.X}, {door.Location?.Y})"
                ));
            }

            // Add window operations
            foreach (var window in program.Windows ?? new List<WindowSpec>())
            {
                operations.Add(new MCPOperation(
                    "placeWindow",
                    new JObject
                    {
                        ["wallId"] = window.WallId,
                        ["location"] = new JObject
                        {
                            ["x"] = window.Location?.X ?? 0,
                            ["y"] = window.Location?.Y ?? 0
                        },
                        ["windowType"] = window.WindowType ?? program.DefaultWindowType,
                        ["sillHeight"] = window.SillHeight
                    },
                    $"Place window at ({window.Location?.X}, {window.Location?.Y})"
                ));
            }

            return operations;
        }

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var operations = GetOperations(context);
            var elementIds = new List<int>();

            try
            {
                foreach (var op in operations)
                {
                    var ids = ExecuteMCPMethod(context.UIApp, op.MethodName, op.Parameters);
                    elementIds.AddRange(ids);
                }

                return Success(elementIds, $"Placed {elementIds.Count} openings (doors/windows)");
            }
            catch (Exception ex)
            {
                return Error($"Opening placement failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 9: Ceilings
    /// </summary>
    public class CeilingsExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Ceilings;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();
            var warnings = new List<string>();

            try
            {
                // Need at least a level and footprint to create ceiling
                var levelId = context.State.Registry.Levels.Values.FirstOrDefault();
                if (levelId == 0)
                {
                    return Error("No levels found - cannot create ceiling");
                }

                if (program.BuildingFootprint == null || program.BuildingFootprint.Count < 3)
                {
                    return Error("Building footprint required for ceiling creation");
                }

                // Create ceiling from building footprint (covers entire floor)
                var parameters = new JObject
                {
                    ["levelId"] = levelId,
                    ["boundary"] = JArray.FromObject(program.BuildingFootprint.Select(p =>
                        new JArray { p.X, p.Y, 0 })),
                    ["ceilingHeight"] = program.CeilingHeight ?? 8.0 // Default 8' ceiling
                };

                // Add ceiling type if specified
                if (!string.IsNullOrEmpty(program.CeilingType))
                {
                    parameters["ceilingType"] = program.CeilingType;
                }

                var ids = ExecuteMCPMethod(context.UIApp, "createCeiling", parameters);
                elementIds.AddRange(ids);

                // Store in registry
                foreach (var id in ids)
                {
                    context.State.Registry.Ceilings.Add(id);
                }

                var result = Success(elementIds, $"Created {elementIds.Count} ceilings");
                result.Warnings = warnings;
                return result;
            }
            catch (Exception ex)
            {
                return Error($"Ceiling creation failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 10: Fixtures - Plumbing fixtures
    /// </summary>
    public class FixturesExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Fixtures;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();
            var warnings = new List<string>();

            try
            {
                // Check if we have fixture specs in the program
                if (program.Fixtures == null || program.Fixtures.Count == 0)
                {
                    return Success(elementIds, "No fixtures specified in building program");
                }

                var levelId = context.State.Registry.Levels.Values.FirstOrDefault();

                // Place each fixture
                foreach (var fixture in program.Fixtures)
                {
                    var parameters = new JObject
                    {
                        ["familyName"] = fixture.FamilyName ?? "Toilet-Commercial-Wall-3D",
                        ["typeName"] = fixture.TypeName,
                        ["location"] = new JArray { fixture.Location?.X ?? 0, fixture.Location?.Y ?? 0, 0 },
                        ["levelId"] = fixture.LevelId ?? levelId,
                        ["rotation"] = fixture.Rotation ?? 0
                    };

                    var ids = ExecuteMCPMethod(context.UIApp, "placeFamilyInstance", parameters);
                    if (ids.Count > 0)
                    {
                        elementIds.AddRange(ids);
                        context.State.Registry.Fixtures.Add(ids[0]);
                    }
                    else
                    {
                        warnings.Add($"Failed to place fixture: {fixture.FamilyName}");
                    }
                }

                var result = Success(elementIds, $"Placed {elementIds.Count} fixtures");
                result.Warnings = warnings;
                return result;
            }
            catch (Exception ex)
            {
                return Error($"Fixture placement failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 11: Cabinetry - Place kitchen and bathroom cabinets
    /// </summary>
    public class CabinetryExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Cabinetry;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();
            var warnings = new List<string>();

            try
            {
                // Check if we have cabinet specs in the program
                if (program.Cabinets == null || program.Cabinets.Count == 0)
                {
                    return Success(elementIds, "No cabinets specified in building program");
                }

                var levelId = context.State.Registry.Levels.Values.FirstOrDefault();

                // Place each cabinet
                foreach (var cabinet in program.Cabinets)
                {
                    // Determine family based on cabinet type
                    string familyName = cabinet.FamilyName ?? GetDefaultCabinetFamily(cabinet.CabinetType);

                    var parameters = new JObject
                    {
                        ["familyName"] = familyName,
                        ["typeName"] = cabinet.TypeName,
                        ["location"] = new JArray { cabinet.Location?.X ?? 0, cabinet.Location?.Y ?? 0, 0 },
                        ["levelId"] = cabinet.LevelId ?? levelId,
                        ["rotation"] = cabinet.Rotation ?? 0
                    };

                    // Upper cabinets need elevation offset
                    if (cabinet.CabinetType == CabinetType.Upper || cabinet.IsUpperCabinet)
                    {
                        // Upper cabinets typically mounted at 4.5' (54")
                        parameters["elevation"] = cabinet.Elevation ?? 4.5;
                    }

                    var ids = ExecuteMCPMethod(context.UIApp, "placeFamilyInstance", parameters);
                    if (ids.Count > 0)
                    {
                        elementIds.AddRange(ids);
                        context.State.Registry.Cabinets.Add(ids[0]);
                    }
                    else
                    {
                        warnings.Add($"Failed to place cabinet: {familyName} at ({cabinet.Location?.X}, {cabinet.Location?.Y})");
                    }
                }

                var result = Success(elementIds, $"Placed {elementIds.Count} cabinets");
                result.Warnings = warnings;
                return result;
            }
            catch (Exception ex)
            {
                return Error($"Cabinetry placement failed: {ex.Message}");
            }
        }

        private string GetDefaultCabinetFamily(CabinetType? cabinetType)
        {
            return cabinetType switch
            {
                CabinetType.Base => "Base Cabinet-Single Door & Drawer",
                CabinetType.Upper => "Base Cabinet-Upper",
                CabinetType.Tall => "Base Cabinet-Tall",
                CabinetType.Corner => "Base Cabinet-Corner",
                CabinetType.Vanity => "Vanity Cabinet-Single Door",
                _ => "Base Cabinet-Single Door & Drawer"
            };
        }
    }

    /// <summary>
    /// Phase 12: Furniture - Place furniture throughout the building
    /// </summary>
    public class FurnitureExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Furniture;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();
            var warnings = new List<string>();

            try
            {
                // Check if we have furniture specs in the program
                if (program.Furniture == null || program.Furniture.Count == 0)
                {
                    return Success(elementIds, "No furniture specified in building program");
                }

                var levelId = context.State.Registry.Levels.Values.FirstOrDefault();

                // Place each furniture item
                foreach (var furniture in program.Furniture)
                {
                    // Determine family based on furniture type
                    string familyName = furniture.FamilyName ?? GetDefaultFurnitureFamily(furniture.FurnitureType);

                    var parameters = new JObject
                    {
                        ["familyName"] = familyName,
                        ["typeName"] = furniture.TypeName,
                        ["location"] = new JArray { furniture.Location?.X ?? 0, furniture.Location?.Y ?? 0, 0 },
                        ["levelId"] = furniture.LevelId ?? levelId,
                        ["rotation"] = furniture.Rotation ?? 0
                    };

                    var ids = ExecuteMCPMethod(context.UIApp, "placeFamilyInstance", parameters);
                    if (ids.Count > 0)
                    {
                        elementIds.AddRange(ids);
                        context.State.Registry.Furniture.Add(ids[0]);
                    }
                    else
                    {
                        warnings.Add($"Failed to place furniture: {familyName} at ({furniture.Location?.X}, {furniture.Location?.Y})");
                    }
                }

                var result = Success(elementIds, $"Placed {elementIds.Count} furniture items");
                result.Warnings = warnings;
                return result;
            }
            catch (Exception ex)
            {
                return Error($"Furniture placement failed: {ex.Message}");
            }
        }

        private string GetDefaultFurnitureFamily(FurnitureType? furnitureType)
        {
            return furnitureType switch
            {
                FurnitureType.Desk => "Desk",
                FurnitureType.Chair => "Chair-Task",
                FurnitureType.Sofa => "Sofa-Corbu",
                FurnitureType.Table => "Table-Dining Round w Chairs",
                FurnitureType.Bed => "Bed-Standard",
                FurnitureType.Storage => "Shelving",
                FurnitureType.Seating => "Seating-Breuer",
                _ => "Chair-Task"
            };
        }
    }

    /// <summary>
    /// Phase 13: Site elements - Place site components and topography
    /// </summary>
    public class SiteExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Site;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var program = context.State.Program;
            var elementIds = new List<int>();
            var warnings = new List<string>();

            try
            {
                // Check if we have site elements in the program
                if (program.SiteElements == null || program.SiteElements.Count == 0)
                {
                    // If no site elements specified, that's ok - site may not be part of scope
                    return Success(elementIds, "No site elements specified in building program");
                }

                // Place each site element (trees, parking, site furniture, etc.)
                foreach (var siteElement in program.SiteElements)
                {
                    // Determine family based on site element type
                    string familyName = siteElement.FamilyName ?? GetDefaultSiteFamily(siteElement.ElementType);

                    var parameters = new JObject
                    {
                        ["familyName"] = familyName,
                        ["typeName"] = siteElement.TypeName,
                        ["location"] = new JArray { siteElement.Location?.X ?? 0, siteElement.Location?.Y ?? 0, siteElement.Location?.Z ?? 0 },
                        ["rotation"] = siteElement.Rotation ?? 0
                    };

                    var ids = ExecuteMCPMethod(context.UIApp, "placeFamilyInstance", parameters);
                    if (ids.Count > 0)
                    {
                        elementIds.AddRange(ids);
                        context.State.Registry.SiteElements.Add(ids[0]);
                    }
                    else
                    {
                        warnings.Add($"Failed to place site element: {familyName} at ({siteElement.Location?.X}, {siteElement.Location?.Y})");
                    }
                }

                // Create topography if provided
                if (program.TopographyPoints != null && program.TopographyPoints.Count >= 3)
                {
                    var topoParams = new JObject
                    {
                        ["points"] = JArray.FromObject(program.TopographyPoints.Select(p =>
                            new JArray { p.X, p.Y, p.Z }))
                    };

                    var topoIds = ExecuteMCPMethod(context.UIApp, "createTopography", topoParams);
                    if (topoIds.Count > 0)
                    {
                        elementIds.AddRange(topoIds);
                    }
                    else
                    {
                        warnings.Add("Failed to create topography surface");
                    }
                }

                var result = Success(elementIds, $"Placed {elementIds.Count} site elements");
                result.Warnings = warnings;
                return result;
            }
            catch (Exception ex)
            {
                return Error($"Site element placement failed: {ex.Message}");
            }
        }

        private string GetDefaultSiteFamily(SiteElementType? elementType)
        {
            return elementType switch
            {
                SiteElementType.Tree => "RPC Tree - Deciduous",
                SiteElementType.Shrub => "RPC Tree - Shrub",
                SiteElementType.Parking => "Parking-Striped",
                SiteElementType.Bench => "Site-Bench",
                SiteElementType.Light => "Site Light-Bollard",
                SiteElementType.Vehicle => "RPC Vehicle",
                SiteElementType.Person => "RPC People",
                _ => "RPC Tree - Deciduous"
            };
        }
    }

    /// <summary>
    /// Phase 14: Rooms - Create and tag rooms
    /// </summary>
    public class RoomsExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.Rooms;

        public override List<MCPOperation> GetOperations(PhaseExecutionContext context)
        {
            var operations = new List<MCPOperation>();
            var program = context.State.Program;

            foreach (var room in program.Rooms ?? new List<RoomSpec>())
            {
                // Find level ID
                var levelId = 0;
                if (!string.IsNullOrEmpty(room.Level) &&
                    context.State.Registry.Levels.TryGetValue(room.Level, out var id))
                {
                    levelId = id;
                }
                else if (context.State.Registry.Levels.Count > 0)
                {
                    levelId = context.State.Registry.Levels.First().Value;
                }

                operations.Add(new MCPOperation(
                    "createRoom",
                    new JObject
                    {
                        ["levelId"] = levelId,
                        ["location"] = new JObject
                        {
                            ["x"] = room.Location?.X ?? 0,
                            ["y"] = room.Location?.Y ?? 0
                        },
                        ["name"] = room.Name
                    },
                    $"Create room: {room.Name}"
                ));
            }

            return operations;
        }

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var operations = GetOperations(context);
            var elementIds = new List<int>();

            try
            {
                foreach (var op in operations)
                {
                    var ids = ExecuteMCPMethod(context.UIApp, op.MethodName, op.Parameters);
                    elementIds.AddRange(ids);
                }

                return Success(elementIds, $"Created {elementIds.Count} rooms");
            }
            catch (Exception ex)
            {
                return Error($"Room creation failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Phase 15: Views and Documentation
    /// </summary>
    public class ViewsDocumentationExecutor : BasePhaseExecutor
    {
        public override BuildingPhase Phase => BuildingPhase.ViewsDocumentation;

        public override PhaseExecutionResult Execute(PhaseExecutionContext context)
        {
            var elementIds = new List<int>();

            try
            {
                // Create floor plans for each level
                foreach (var levelEntry in context.State.Registry.Levels)
                {
                    var parameters = new JObject
                    {
                        ["levelId"] = levelEntry.Value,
                        ["name"] = $"{levelEntry.Key} - Floor Plan"
                    };

                    var ids = ExecuteMCPMethod(context.UIApp, "createFloorPlan", parameters);
                    elementIds.AddRange(ids);
                }

                return Success(elementIds, $"Created {elementIds.Count} views");
            }
            catch (Exception ex)
            {
                return Error($"View creation failed: {ex.Message}");
            }
        }
    }
}
