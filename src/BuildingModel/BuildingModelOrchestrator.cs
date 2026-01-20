using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.BuildingModel.Models;
using RevitMCPBridge.BuildingModel.PhaseExecutors;
using RevitMCPBridge.CIPS;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.BuildingModel
{
    /// <summary>
    /// Main orchestrator for building model creation workflow.
    /// Coordinates 15 phases from project setup to documentation.
    /// Integrates with CIPS for confidence-based execution.
    /// </summary>
    public class BuildingModelOrchestrator
    {
        private static BuildingModelOrchestrator _instance;
        private static readonly object _lock = new object();

        private UIApplication _uiApp;
        private readonly Dictionary<string, BuildingModelState> _workflows = new Dictionary<string, BuildingModelState>();
        private readonly Dictionary<BuildingPhase, IPhaseExecutor> _executors = new Dictionary<BuildingPhase, IPhaseExecutor>();

        /// <summary>
        /// Get the singleton instance
        /// </summary>
        public static BuildingModelOrchestrator Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new BuildingModelOrchestrator();
                        }
                    }
                }
                return _instance;
            }
        }

        private BuildingModelOrchestrator()
        {
            Log.Information("[BuildingModel] Orchestrator created");
        }

        /// <summary>
        /// Initialize with UIApplication context
        /// </summary>
        public void Initialize(UIApplication uiApp)
        {
            _uiApp = uiApp;
            RegisterExecutors();
            Log.Information("[BuildingModel] Orchestrator initialized with {Count} phase executors",
                _executors.Count);
        }

        /// <summary>
        /// Register all phase executors
        /// </summary>
        private void RegisterExecutors()
        {
            _executors[BuildingPhase.ProjectSetup] = new ProjectSetupExecutor();
            _executors[BuildingPhase.Levels] = new LevelsExecutor();
            _executors[BuildingPhase.Floors] = new FloorsExecutor();
            _executors[BuildingPhase.ExteriorWalls] = new WallsExecutor(isExterior: true);
            _executors[BuildingPhase.Roof] = new RoofExecutor();
            _executors[BuildingPhase.InteriorWalls] = new WallsExecutor(isExterior: false);
            _executors[BuildingPhase.VerticalCirculation] = new VerticalCirculationExecutor();
            _executors[BuildingPhase.Openings] = new OpeningsExecutor();
            _executors[BuildingPhase.Ceilings] = new CeilingsExecutor();
            _executors[BuildingPhase.Fixtures] = new FixturesExecutor();
            _executors[BuildingPhase.Cabinetry] = new CabinetryExecutor();
            _executors[BuildingPhase.Furniture] = new FurnitureExecutor();
            _executors[BuildingPhase.Site] = new SiteExecutor();
            _executors[BuildingPhase.Rooms] = new RoomsExecutor();
            _executors[BuildingPhase.ViewsDocumentation] = new ViewsDocumentationExecutor();
        }

        #region Workflow Management

        /// <summary>
        /// Create a new building model workflow
        /// </summary>
        public BuildingModelState CreateWorkflow(BuildingProgram program, string projectName = null)
        {
            EnsureInitialized();

            var state = new BuildingModelState
            {
                ProjectName = projectName ?? $"Building_{DateTime.Now:yyyyMMdd_HHmmss}",
                BuildingType = program.BuildingType,
                Program = program
            };

            _workflows[state.WorkflowId] = state;

            Log.Information("[BuildingModel] Created workflow {WorkflowId} for {Project}",
                state.WorkflowId, state.ProjectName);

            return state;
        }

        /// <summary>
        /// Get a workflow by ID
        /// </summary>
        public BuildingModelState GetWorkflow(string workflowId)
        {
            if (_workflows.TryGetValue(workflowId, out var state))
            {
                return state;
            }
            return null;
        }

        /// <summary>
        /// Get all active workflows
        /// </summary>
        public List<WorkflowSummary> GetAllWorkflows()
        {
            return _workflows.Values.Select(w => w.GetSummary()).ToList();
        }

        #endregion

        #region Phase Execution

        /// <summary>
        /// Execute the next available phase
        /// </summary>
        public PhaseExecutionResult ExecuteNextPhase(string workflowId)
        {
            EnsureInitialized();

            var state = GetWorkflow(workflowId);
            if (state == null)
            {
                return PhaseExecutionResult.Error("Workflow not found");
            }

            var nextPhase = state.GetNextPhase();
            if (!nextPhase.HasValue)
            {
                return new PhaseExecutionResult
                {
                    Success = true,
                    Message = "Workflow complete - no more phases to execute",
                    WorkflowComplete = true
                };
            }

            return ExecutePhase(workflowId, nextPhase.Value);
        }

        /// <summary>
        /// Execute a specific phase
        /// </summary>
        public PhaseExecutionResult ExecutePhase(string workflowId, BuildingPhase phase)
        {
            EnsureInitialized();

            var state = GetWorkflow(workflowId);
            if (state == null)
            {
                return PhaseExecutionResult.Error("Workflow not found");
            }

            // Check dependencies
            if (!state.AreDependenciesSatisfied(phase))
            {
                var phaseDef = PhaseDefinition.GetPhase(phase);
                return PhaseExecutionResult.Error(
                    $"Dependencies not satisfied for {phase}. Required: {string.Join(", ", phaseDef.DependsOn)}");
            }

            // Get executor
            if (!_executors.TryGetValue(phase, out var executor))
            {
                return PhaseExecutionResult.Error($"No executor registered for phase: {phase}");
            }

            // Start phase
            var phaseResult = state.StartPhase(phase);
            Log.Information("[BuildingModel] Starting phase {Phase} for workflow {WorkflowId}",
                phase, workflowId);

            try
            {
                // Build execution context
                var context = new PhaseExecutionContext
                {
                    UIApp = _uiApp,
                    State = state,
                    Phase = phase,
                    PhaseDefinition = PhaseDefinition.GetPhase(phase)
                };

                // Execute through CIPS if enabled
                PhaseExecutionResult result;
                if (CIPSConfiguration.Instance.Enabled && state.UseCIPSValidation)
                {
                    result = ExecuteWithCIPS(executor, context);
                }
                else
                {
                    result = executor.Execute(context);
                }

                // Update state based on result
                if (result.Success)
                {
                    state.CompletePhase(phase, result.CreatedElementIds, result.Confidence);

                    // Update registry
                    UpdateRegistry(state, phase, result.CreatedElementIds);

                    Log.Information("[BuildingModel] Phase {Phase} completed with {Count} elements",
                        phase, result.CreatedElementIds?.Count ?? 0);
                }
                else
                {
                    state.FailPhase(phase, result.Message);
                    Log.Warning("[BuildingModel] Phase {Phase} failed: {Error}",
                        phase, result.Message);
                }

                result.WorkflowComplete = !state.GetNextPhase().HasValue;
                return result;
            }
            catch (Exception ex)
            {
                state.FailPhase(phase, ex.Message);
                Log.Error(ex, "[BuildingModel] Phase {Phase} threw exception", phase);
                return PhaseExecutionResult.Error(ex.Message);
            }
        }

        /// <summary>
        /// Execute all remaining phases
        /// </summary>
        public WorkflowExecutionResult ExecuteAll(string workflowId, bool stopOnError = true)
        {
            EnsureInitialized();

            var state = GetWorkflow(workflowId);
            if (state == null)
            {
                return new WorkflowExecutionResult
                {
                    Success = false,
                    Message = "Workflow not found"
                };
            }

            var results = new List<PhaseExecutionResult>();
            var startTime = DateTime.UtcNow;

            while (true)
            {
                var nextPhase = state.GetNextPhase();
                if (!nextPhase.HasValue)
                {
                    break;
                }

                var result = ExecutePhase(workflowId, nextPhase.Value);
                results.Add(result);

                if (!result.Success && stopOnError)
                {
                    break;
                }
            }

            var duration = DateTime.UtcNow - startTime;
            var successful = results.Count(r => r.Success);
            var failed = results.Count(r => !r.Success);

            return new WorkflowExecutionResult
            {
                Success = failed == 0,
                WorkflowId = workflowId,
                PhasesExecuted = results.Count,
                PhasesSuccessful = successful,
                PhasesFailed = failed,
                TotalElementsCreated = results.Sum(r => r.CreatedElementIds?.Count ?? 0),
                Duration = duration,
                PhaseResults = results,
                Summary = state.GetSummary(),
                Message = failed == 0
                    ? $"Completed {successful} phases successfully"
                    : $"Completed {successful} phases, {failed} failed"
            };
        }

        /// <summary>
        /// Skip a phase
        /// </summary>
        public bool SkipPhase(string workflowId, BuildingPhase phase, string reason = null)
        {
            var state = GetWorkflow(workflowId);
            if (state == null) return false;

            state.SkipPhase(phase, reason);
            Log.Information("[BuildingModel] Skipped phase {Phase}: {Reason}", phase, reason);
            return true;
        }

        #endregion

        #region CIPS Integration

        /// <summary>
        /// Execute a phase through the CIPS confidence system
        /// </summary>
        private PhaseExecutionResult ExecuteWithCIPS(IPhaseExecutor executor, PhaseExecutionContext context)
        {
            // Build operations from executor
            var operations = executor.GetOperations(context);

            if (operations == null || operations.Count == 0)
            {
                // No operations, just run directly
                return executor.Execute(context);
            }

            // Process through CIPS batch
            var cipsOperations = operations.Select(op =>
                (op.MethodName, op.Parameters)).ToList();

            try
            {
                var workflow = CIPSOrchestrator.Instance.ProcessBatch(
                    cipsOperations,
                    $"Phase {context.Phase}",
                    context.State.AutoExecuteHighConfidence);

                // Aggregate results
                var createdElements = new List<int>();
                var allSucceeded = true;
                double totalConfidence = 0;
                int confCount = 0;

                foreach (var envelope in workflow.Operations.Values)
                {
                    if (envelope.Status == ProcessingStatus.Executed ||
                        envelope.Status == ProcessingStatus.Verified)
                    {
                        var elementId = envelope.Result?["elementId"]?.Value<int>();
                        if (elementId.HasValue && elementId.Value > 0)
                        {
                            createdElements.Add(elementId.Value);
                        }

                        // Check for array of elements
                        var elements = envelope.Result?["elements"] as JArray;
                        if (elements != null)
                        {
                            foreach (var elem in elements)
                            {
                                var id = elem["id"]?.Value<int>() ?? elem["elementId"]?.Value<int>();
                                if (id.HasValue && id.Value > 0)
                                {
                                    createdElements.Add(id.Value);
                                }
                            }
                        }
                    }
                    else if (envelope.Status == ProcessingStatus.Failed)
                    {
                        allSucceeded = false;
                    }

                    totalConfidence += envelope.OverallConfidence;
                    confCount++;
                }

                return new PhaseExecutionResult
                {
                    Success = allSucceeded || createdElements.Count > 0,
                    Phase = context.Phase,
                    CreatedElementIds = createdElements,
                    Confidence = confCount > 0 ? totalConfidence / confCount : 0,
                    Message = allSucceeded
                        ? $"Created {createdElements.Count} elements via CIPS"
                        : "Some operations failed - check CIPS review queue"
                };
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[BuildingModel] CIPS execution failed for phase {Phase}", context.Phase);

                // Fall back to direct execution
                return executor.Execute(context);
            }
        }

        #endregion

        #region Registry Updates

        /// <summary>
        /// Update the element registry after a phase completes
        /// </summary>
        private void UpdateRegistry(BuildingModelState state, BuildingPhase phase, List<int> elementIds)
        {
            if (elementIds == null || elementIds.Count == 0) return;

            var registry = state.Registry;

            switch (phase)
            {
                case BuildingPhase.Floors:
                    registry.Floors.AddRange(elementIds);
                    break;
                case BuildingPhase.ExteriorWalls:
                    registry.ExteriorWalls.AddRange(elementIds);
                    break;
                case BuildingPhase.InteriorWalls:
                    registry.InteriorWalls.AddRange(elementIds);
                    break;
                case BuildingPhase.Roof:
                    registry.Roofs.AddRange(elementIds);
                    break;
                case BuildingPhase.Openings:
                    // Could split into doors/windows based on category
                    registry.Doors.AddRange(elementIds);
                    break;
                case BuildingPhase.Ceilings:
                    registry.Ceilings.AddRange(elementIds);
                    break;
                case BuildingPhase.Fixtures:
                    registry.Fixtures.AddRange(elementIds);
                    break;
                case BuildingPhase.Cabinetry:
                    registry.Furniture.AddRange(elementIds); // Cabinets often in furniture
                    break;
                case BuildingPhase.Furniture:
                    registry.Furniture.AddRange(elementIds);
                    break;
                case BuildingPhase.VerticalCirculation:
                    registry.Stairs.AddRange(elementIds);
                    break;
                case BuildingPhase.Rooms:
                    registry.Rooms.AddRange(elementIds);
                    break;
                case BuildingPhase.ViewsDocumentation:
                    registry.Views.AddRange(elementIds);
                    break;
            }
        }

        #endregion

        #region Utilities

        /// <summary>
        /// Get phase definitions
        /// </summary>
        public List<PhaseDefinition> GetPhaseDefinitions()
        {
            return PhaseDefinition.GetAllPhases();
        }

        /// <summary>
        /// Get phase dependency graph
        /// </summary>
        public object GetDependencyGraph()
        {
            var phases = PhaseDefinition.GetAllPhases();

            var nodes = phases.Select(p => new
            {
                id = (int)p.Phase,
                name = p.Name,
                isOptional = p.IsOptional
            }).ToList();

            var edges = new List<object>();
            foreach (var phase in phases)
            {
                foreach (var dep in phase.DependsOn)
                {
                    edges.Add(new
                    {
                        from = (int)dep,
                        to = (int)phase.Phase
                    });
                }
            }

            return new { nodes, edges };
        }

        /// <summary>
        /// Ensure orchestrator is initialized
        /// </summary>
        private void EnsureInitialized()
        {
            if (_uiApp == null)
            {
                throw new InvalidOperationException(
                    "BuildingModelOrchestrator not initialized. Call Initialize(uiApp) first.");
            }
        }

        #endregion
    }

    /// <summary>
    /// Result of executing a single phase
    /// </summary>
    public class PhaseExecutionResult
    {
        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("phase")]
        public BuildingPhase Phase { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }

        [JsonProperty("createdElementIds")]
        public List<int> CreatedElementIds { get; set; } = new List<int>();

        [JsonProperty("confidence")]
        public double Confidence { get; set; }

        [JsonProperty("warnings")]
        public List<string> Warnings { get; set; } = new List<string>();

        [JsonProperty("workflowComplete")]
        public bool WorkflowComplete { get; set; }

        public static PhaseExecutionResult Error(string message)
        {
            return new PhaseExecutionResult
            {
                Success = false,
                Message = message
            };
        }
    }

    /// <summary>
    /// Result of executing the full workflow
    /// </summary>
    public class WorkflowExecutionResult
    {
        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("workflowId")]
        public string WorkflowId { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }

        [JsonProperty("phasesExecuted")]
        public int PhasesExecuted { get; set; }

        [JsonProperty("phasesSuccessful")]
        public int PhasesSuccessful { get; set; }

        [JsonProperty("phasesFailed")]
        public int PhasesFailed { get; set; }

        [JsonProperty("totalElementsCreated")]
        public int TotalElementsCreated { get; set; }

        [JsonProperty("duration")]
        public TimeSpan Duration { get; set; }

        [JsonProperty("phaseResults")]
        public List<PhaseExecutionResult> PhaseResults { get; set; }

        [JsonProperty("summary")]
        public WorkflowSummary Summary { get; set; }
    }
}
