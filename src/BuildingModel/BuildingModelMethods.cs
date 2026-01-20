using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.BuildingModel.Models;
using Serilog;

namespace RevitMCPBridge.BuildingModel
{
    /// <summary>
    /// MCP method endpoints for the Building Model Orchestration system.
    /// All methods use the bmo_ prefix (Building Model Orchestration).
    /// </summary>
    public static class BuildingModelMethods
    {
        /// <summary>
        /// Register building model orchestration methods
        /// </summary>
        public static void Register(Dictionary<string, Func<UIApplication, JObject, string>> registry)
        {
            Log.Information("[BuildingModel] Register() called - starting registration");

            // Workflow management
            registry["bmo_createWorkflow"] = CreateWorkflow;
            registry["bmo_getWorkflow"] = GetWorkflow;
            registry["bmo_listWorkflows"] = ListWorkflows;

            // Phase execution
            registry["bmo_executeNextPhase"] = ExecuteNextPhase;
            registry["bmo_executePhase"] = ExecutePhase;
            registry["bmo_executeAll"] = ExecuteAll;
            registry["bmo_skipPhase"] = SkipPhase;

            // Information
            registry["bmo_getPhaseDefinitions"] = GetPhaseDefinitions;
            registry["bmo_getDependencyGraph"] = GetDependencyGraph;
            registry["bmo_getProgress"] = GetProgress;
            registry["bmo_debug"] = DebugWorkflow;

            // Simple test method
            registry["bmo_ping"] = (uiApp, parameters) =>
            {
                return JsonConvert.SerializeObject(new { success = true, message = "BMO is alive!", timestamp = DateTime.Now });
            };

            Log.Information("[BuildingModel] Registered 12 MCP methods (including bmo_ping, bmo_debug)");
        }

        /// <summary>
        /// Create a new building model workflow.
        /// Parameters:
        /// - projectName: (optional) Name for the project
        /// - buildingType: Type of building (SingleFamilyResidential, MultiFamilyResidential, etc.)
        /// - numberOfStories: Number of floors
        /// - floorToFloorHeight: Height in feet (default: 10)
        /// - buildingFootprint: Array of {x, y} points defining the building outline
        /// - rooms: (optional) Array of room specifications
        /// - skipOptionalPhases: (optional) Skip optional phases like furniture (default: false)
        /// </summary>
        public static string CreateWorkflow(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var program = new BuildingProgram
                {
                    BuildingType = parameters["buildingType"]?.ToString() ?? "SingleFamilyResidential",
                    NumberOfStories = parameters["numberOfStories"]?.Value<int>() ?? 1,
                    FloorToFloorHeight = parameters["floorToFloorHeight"]?.Value<double>() ?? 10.0
                };

                // Parse footprint
                var footprintArray = parameters["buildingFootprint"] as JArray;
                if (footprintArray != null)
                {
                    foreach (var point in footprintArray)
                    {
                        program.BuildingFootprint.Add(new Point2D(
                            point["x"]?.Value<double>() ?? 0,
                            point["y"]?.Value<double>() ?? 0
                        ));
                    }
                }

                // Parse level names if provided
                var levelNamesArray = parameters["levelNames"] as JArray;
                if (levelNamesArray != null)
                {
                    program.LevelNames = levelNamesArray.Select(l => l.ToString()).ToList();
                }

                // Parse wall types
                program.ExteriorWallType = parameters["exteriorWallType"]?.ToString() ?? program.ExteriorWallType;
                program.InteriorWallType = parameters["interiorWallType"]?.ToString() ?? program.InteriorWallType;

                // Parse rooms
                var roomsArray = parameters["rooms"] as JArray;
                if (roomsArray != null)
                {
                    foreach (var room in roomsArray)
                    {
                        program.Rooms.Add(new RoomSpec
                        {
                            Name = room["name"]?.ToString(),
                            Level = room["level"]?.ToString(),
                            Area = room["area"]?.Value<double>() ?? 0,
                            RoomType = room["roomType"]?.ToString(),
                            Location = room["location"] != null ? new Point2D(
                                room["location"]["x"]?.Value<double>() ?? 0,
                                room["location"]["y"]?.Value<double>() ?? 0
                            ) : null
                        });
                    }
                }

                // Create the workflow
                var projectName = parameters["projectName"]?.ToString();
                var state = BuildingModelOrchestrator.Instance.CreateWorkflow(program, projectName);

                // Apply options
                state.SkipOptionalPhases = parameters["skipOptionalPhases"]?.Value<bool>() ?? false;
                state.AutoExecuteHighConfidence = parameters["autoExecuteHighConfidence"]?.Value<bool>() ?? true;
                state.StopOnError = parameters["stopOnError"]?.Value<bool>() ?? true;
                state.UseCIPSValidation = parameters["useCIPSValidation"]?.Value<bool>() ?? true;

                return JsonConvert.SerializeObject(new
                {
                    success = true,
                    workflowId = state.WorkflowId,
                    projectName = state.ProjectName,
                    buildingType = state.BuildingType,
                    phaseCount = PhaseDefinition.GetAllPhases().Count,
                    nextPhase = state.GetNextPhase()?.ToString(),
                    message = "Workflow created. Use bmo_executeNextPhase or bmo_executeAll to build."
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Get a workflow by ID.
        /// Parameters:
        /// - workflowId: ID of the workflow
        /// </summary>
        public static string GetWorkflow(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var workflowId = parameters["workflowId"]?.ToString();
                if (string.IsNullOrEmpty(workflowId))
                {
                    return Error("'workflowId' is required");
                }

                var state = BuildingModelOrchestrator.Instance.GetWorkflow(workflowId);
                if (state == null)
                {
                    return Error($"Workflow not found: {workflowId}");
                }

                return JsonConvert.SerializeObject(new
                {
                    success = true,
                    workflow = new
                    {
                        workflowId = state.WorkflowId,
                        projectName = state.ProjectName,
                        buildingType = state.BuildingType,
                        status = state.OverallStatus.ToString(),
                        progress = state.GetProgressPercentage(),
                        currentPhase = state.CurrentPhase?.ToString(),
                        nextPhase = state.GetNextPhase()?.ToString(),
                        totalElementsCreated = state.TotalElementsCreated,
                        createdAt = state.CreatedAt,
                        phaseResults = state.PhaseResults.ToDictionary(
                            kvp => kvp.Key.ToString(),
                            kvp => new
                            {
                                status = kvp.Value.Status.ToString(),
                                elementCount = kvp.Value.CreatedElementIds.Count,
                                confidence = kvp.Value.CIPSConfidence,
                                error = kvp.Value.ErrorMessage
                            }
                        ),
                        registry = new
                        {
                            levels = state.Registry.Levels.Count,
                            floors = state.Registry.Floors.Count,
                            exteriorWalls = state.Registry.ExteriorWalls.Count,
                            interiorWalls = state.Registry.InteriorWalls.Count,
                            doors = state.Registry.Doors.Count,
                            windows = state.Registry.Windows.Count,
                            rooms = state.Registry.Rooms.Count
                        }
                    }
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// List all workflows.
        /// </summary>
        public static string ListWorkflows(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var workflows = BuildingModelOrchestrator.Instance.GetAllWorkflows();

                return JsonConvert.SerializeObject(new
                {
                    success = true,
                    count = workflows.Count,
                    workflows = workflows
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Execute the next available phase.
        /// Parameters:
        /// - workflowId: ID of the workflow
        /// </summary>
        public static string ExecuteNextPhase(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var workflowId = parameters["workflowId"]?.ToString();
                if (string.IsNullOrEmpty(workflowId))
                {
                    return Error("'workflowId' is required");
                }

                var result = BuildingModelOrchestrator.Instance.ExecuteNextPhase(workflowId);

                return JsonConvert.SerializeObject(new
                {
                    success = result.Success,
                    phase = result.Phase.ToString(),
                    message = result.Message,
                    elementCount = result.CreatedElementIds?.Count ?? 0,
                    confidence = result.Confidence,
                    workflowComplete = result.WorkflowComplete,
                    warnings = result.Warnings
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Execute a specific phase.
        /// Parameters:
        /// - workflowId: ID of the workflow
        /// - phase: Phase number (1-15) or phase name
        /// </summary>
        public static string ExecutePhase(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var workflowId = parameters["workflowId"]?.ToString();
                if (string.IsNullOrEmpty(workflowId))
                {
                    return Error("'workflowId' is required");
                }

                // Parse phase
                BuildingPhase phase;
                var phaseParam = parameters["phase"];
                if (phaseParam == null)
                {
                    return Error("'phase' is required (number 1-15 or phase name)");
                }

                if (phaseParam.Type == JTokenType.Integer)
                {
                    phase = (BuildingPhase)phaseParam.Value<int>();
                }
                else if (!Enum.TryParse(phaseParam.ToString(), true, out phase))
                {
                    return Error($"Invalid phase: {phaseParam}. Use 1-15 or phase name.");
                }

                var result = BuildingModelOrchestrator.Instance.ExecutePhase(workflowId, phase);

                return JsonConvert.SerializeObject(new
                {
                    success = result.Success,
                    phase = result.Phase.ToString(),
                    message = result.Message,
                    elementCount = result.CreatedElementIds?.Count ?? 0,
                    elementIds = result.CreatedElementIds,
                    confidence = result.Confidence,
                    workflowComplete = result.WorkflowComplete,
                    warnings = result.Warnings
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Execute all remaining phases.
        /// Parameters:
        /// - workflowId: ID of the workflow
        /// - stopOnError: (optional) Stop if a phase fails (default: true)
        /// </summary>
        public static string ExecuteAll(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var workflowId = parameters["workflowId"]?.ToString();
                if (string.IsNullOrEmpty(workflowId))
                {
                    return Error("'workflowId' is required");
                }

                var stopOnError = parameters["stopOnError"]?.Value<bool>() ?? true;

                var result = BuildingModelOrchestrator.Instance.ExecuteAll(workflowId, stopOnError);

                return JsonConvert.SerializeObject(new
                {
                    success = result.Success,
                    workflowId = result.WorkflowId,
                    message = result.Message,
                    phasesExecuted = result.PhasesExecuted,
                    phasesSuccessful = result.PhasesSuccessful,
                    phasesFailed = result.PhasesFailed,
                    totalElementsCreated = result.TotalElementsCreated,
                    durationMs = result.Duration.TotalMilliseconds,
                    summary = result.Summary
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Skip a phase.
        /// Parameters:
        /// - workflowId: ID of the workflow
        /// - phase: Phase number (1-15) or phase name
        /// - reason: (optional) Reason for skipping
        /// </summary>
        public static string SkipPhase(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var workflowId = parameters["workflowId"]?.ToString();
                if (string.IsNullOrEmpty(workflowId))
                {
                    return Error("'workflowId' is required");
                }

                // Parse phase
                BuildingPhase phase;
                var phaseParam = parameters["phase"];
                if (phaseParam == null)
                {
                    return Error("'phase' is required");
                }

                if (phaseParam.Type == JTokenType.Integer)
                {
                    phase = (BuildingPhase)phaseParam.Value<int>();
                }
                else if (!Enum.TryParse(phaseParam.ToString(), true, out phase))
                {
                    return Error($"Invalid phase: {phaseParam}");
                }

                var reason = parameters["reason"]?.ToString();

                var success = BuildingModelOrchestrator.Instance.SkipPhase(workflowId, phase, reason);

                return JsonConvert.SerializeObject(new
                {
                    success = success,
                    phase = phase.ToString(),
                    reason = reason,
                    message = success ? $"Phase {phase} skipped" : "Failed to skip phase"
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Debug endpoint - get detailed workflow state including footprint and registry.
        /// Parameters:
        /// - workflowId: ID of the workflow
        /// </summary>
        public static string DebugWorkflow(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var workflowId = parameters["workflowId"]?.ToString();
                if (string.IsNullOrEmpty(workflowId))
                {
                    return Error("'workflowId' is required");
                }

                var state = BuildingModelOrchestrator.Instance.GetWorkflow(workflowId);
                if (state == null)
                {
                    return Error($"Workflow not found: {workflowId}");
                }

                return JsonConvert.SerializeObject(new
                {
                    success = true,
                    workflowId = state.WorkflowId,
                    buildingProgram = new
                    {
                        buildingType = state.Program.BuildingType,
                        numberOfStories = state.Program.NumberOfStories,
                        floorToFloorHeight = state.Program.FloorToFloorHeight,
                        footprintCount = state.Program.BuildingFootprint?.Count ?? 0,
                        footprintPoints = state.Program.BuildingFootprint?.Select(p => new { x = p.X, y = p.Y }),
                        exteriorWallType = state.Program.ExteriorWallType,
                        interiorWallType = state.Program.InteriorWallType
                    },
                    registry = new
                    {
                        levels = state.Registry.Levels, // Full dictionary
                        floors = state.Registry.Floors,
                        exteriorWalls = state.Registry.ExteriorWalls,
                        interiorWalls = state.Registry.InteriorWalls
                    },
                    useCIPSValidation = state.UseCIPSValidation
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Get all phase definitions.
        /// </summary>
        public static string GetPhaseDefinitions(UIApplication uiApp, JObject parameters)
        {
            try
            {
                var phases = PhaseDefinition.GetAllPhases();

                return JsonConvert.SerializeObject(new
                {
                    success = true,
                    count = phases.Count,
                    phases = phases.Select(p => new
                    {
                        number = (int)p.Phase,
                        name = p.Name,
                        description = p.Description,
                        requiredInputs = p.RequiredInputs,
                        outputs = p.Outputs,
                        dependsOn = p.DependsOn.Select(d => d.ToString()),
                        mcpMethods = p.MCPMethods,
                        validationRules = p.ValidationRules,
                        isOptional = p.IsOptional
                    })
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Get the phase dependency graph.
        /// </summary>
        public static string GetDependencyGraph(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var graph = BuildingModelOrchestrator.Instance.GetDependencyGraph();

                return JsonConvert.SerializeObject(new
                {
                    success = true,
                    graph = graph
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Get workflow progress.
        /// Parameters:
        /// - workflowId: ID of the workflow
        /// </summary>
        public static string GetProgress(UIApplication uiApp, JObject parameters)
        {
            try
            {
                EnsureInitialized(uiApp);

                var workflowId = parameters["workflowId"]?.ToString();
                if (string.IsNullOrEmpty(workflowId))
                {
                    return Error("'workflowId' is required");
                }

                var state = BuildingModelOrchestrator.Instance.GetWorkflow(workflowId);
                if (state == null)
                {
                    return Error($"Workflow not found: {workflowId}");
                }

                var summary = state.GetSummary();

                return JsonConvert.SerializeObject(new
                {
                    success = true,
                    workflowId = workflowId,
                    progress = summary.Progress,
                    status = summary.Status.ToString(),
                    currentPhase = summary.CurrentPhase,
                    nextPhase = summary.NextPhase,
                    completedPhases = summary.CompletedPhaseCount,
                    failedPhases = summary.FailedPhaseCount,
                    totalElements = summary.TotalElementsCreated,
                    averageConfidence = summary.AverageConfidence,
                    duration = summary.Duration.ToString(@"hh\:mm\:ss")
                }, Formatting.Indented);
            }
            catch (Exception ex)
            {
                return Error(ex.Message);
            }
        }

        /// <summary>
        /// Ensure the orchestrator is initialized
        /// </summary>
        private static void EnsureInitialized(UIApplication uiApp)
        {
            BuildingModelOrchestrator.Instance.Initialize(uiApp);
        }

        /// <summary>
        /// Create error response
        /// </summary>
        private static string Error(string message)
        {
            return JsonConvert.SerializeObject(new
            {
                success = false,
                error = message
            });
        }
    }
}
