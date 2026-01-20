using System.Collections.Generic;
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.BuildingModel.Models;

namespace RevitMCPBridge.BuildingModel.PhaseExecutors
{
    /// <summary>
    /// Context passed to phase executors
    /// </summary>
    public class PhaseExecutionContext
    {
        public UIApplication UIApp { get; set; }
        public BuildingModelState State { get; set; }
        public BuildingPhase Phase { get; set; }
        public PhaseDefinition PhaseDefinition { get; set; }
    }

    /// <summary>
    /// Operation to be executed via MCP
    /// </summary>
    public class MCPOperation
    {
        public string MethodName { get; set; }
        public JObject Parameters { get; set; }
        public string Description { get; set; }

        public MCPOperation(string method, JObject parameters, string description = null)
        {
            MethodName = method;
            Parameters = parameters ?? new JObject();
            Description = description ?? method;
        }
    }

    /// <summary>
    /// Interface for phase executors
    /// </summary>
    public interface IPhaseExecutor
    {
        /// <summary>
        /// The phase this executor handles
        /// </summary>
        BuildingPhase Phase { get; }

        /// <summary>
        /// Get the MCP operations this phase will execute
        /// Used for CIPS batch processing
        /// </summary>
        List<MCPOperation> GetOperations(PhaseExecutionContext context);

        /// <summary>
        /// Execute the phase directly (without CIPS)
        /// </summary>
        PhaseExecutionResult Execute(PhaseExecutionContext context);

        /// <summary>
        /// Validate phase inputs before execution
        /// </summary>
        Models.ValidationResult Validate(PhaseExecutionContext context);
    }

    /// <summary>
    /// Base class for phase executors with common functionality
    /// </summary>
    public abstract class BasePhaseExecutor : IPhaseExecutor
    {
        public abstract BuildingPhase Phase { get; }

        public virtual List<MCPOperation> GetOperations(PhaseExecutionContext context)
        {
            // Default: return empty list, executor handles internally
            return new List<MCPOperation>();
        }

        public abstract PhaseExecutionResult Execute(PhaseExecutionContext context);

        public virtual Models.ValidationResult Validate(PhaseExecutionContext context)
        {
            // Default: validate required inputs exist
            var definition = context.PhaseDefinition ?? PhaseDefinition.GetPhase(Phase);
            var program = context.State.Program;

            foreach (var input in definition.RequiredInputs)
            {
                if (!HasInput(input, program, context.State))
                {
                    return new Models.ValidationResult
                    {
                        Rule = $"Required input: {input}",
                        Passed = false,
                        Message = $"Missing required input: {input}"
                    };
                }
            }

            return new Models.ValidationResult { Rule = "InputValidation", Passed = true };
        }

        /// <summary>
        /// Check if a required input exists
        /// </summary>
        protected virtual bool HasInput(string inputName, BuildingProgram program, BuildingModelState state)
        {
            // Check common inputs
            switch (inputName.ToLower())
            {
                case "projectname":
                    return !string.IsNullOrEmpty(state.ProjectName);
                case "buildingtype":
                    return !string.IsNullOrEmpty(program.BuildingType);
                case "numberofstories":
                    return program.NumberOfStories > 0;
                case "floortofloorheight":
                    return program.FloorToFloorHeight > 0;
                case "buildingfootprint":
                    return program.BuildingFootprint?.Count >= 3;
                case "levelids":
                    return state.Registry.Levels.Count > 0;
                case "wallids":
                    return state.Registry.ExteriorWalls.Count > 0 ||
                           state.Registry.InteriorWalls.Count > 0;
                default:
                    // Check in user parameters
                    return state.UserParameters?[inputName] != null;
            }
        }

        /// <summary>
        /// Execute an MCP method and return element IDs
        /// </summary>
        protected List<int> ExecuteMCPMethod(UIApplication uiApp, string method, JObject parameters)
        {
            var result = MCPServer.ExecuteMethod(uiApp, method, parameters);
            var resultObj = JObject.Parse(result);

            var elementIds = new List<int>();

            if (resultObj["success"]?.Value<bool>() == true)
            {
                // Check for type-specific ID properties (APIs return levelId, wallId, etc.)
                var idPropertyNames = new[] {
                    "elementId", "levelId", "wallId", "floorId", "roofId",
                    "roomId", "doorId", "windowId", "ceilingId", "viewId",
                    "sheetId", "gridId", "columnId", "beamId", "familyInstanceId"
                };

                foreach (var propName in idPropertyNames)
                {
                    var id = resultObj[propName]?.Value<int>();
                    if (id.HasValue && id.Value > 0)
                    {
                        elementIds.Add(id.Value);
                        break; // Only add once per response
                    }
                }

                // Array of elements
                var elements = resultObj["elements"] as JArray;
                if (elements != null)
                {
                    foreach (var elem in elements)
                    {
                        // Check all common ID property names in array elements
                        int? id = null;
                        foreach (var propName in new[] { "id", "elementId", "levelId", "wallId", "floorId", "roomId" })
                        {
                            id = elem[propName]?.Value<int>();
                            if (id.HasValue && id.Value > 0) break;
                        }
                        if (id.HasValue && id.Value > 0)
                        {
                            elementIds.Add(id.Value);
                        }
                    }
                }

                // Array of IDs
                var ids = resultObj["ids"] as JArray;
                if (ids != null)
                {
                    foreach (var id in ids)
                    {
                        var val = id.Value<int>();
                        if (val > 0)
                        {
                            elementIds.Add(val);
                        }
                    }
                }
            }

            return elementIds;
        }

        /// <summary>
        /// Create a success result
        /// </summary>
        protected PhaseExecutionResult Success(List<int> elementIds, string message = null)
        {
            return new PhaseExecutionResult
            {
                Success = true,
                Phase = Phase,
                CreatedElementIds = elementIds ?? new List<int>(),
                Confidence = 1.0,
                Message = message ?? $"Phase {Phase} completed successfully"
            };
        }

        /// <summary>
        /// Create an error result
        /// </summary>
        protected PhaseExecutionResult Error(string message)
        {
            return new PhaseExecutionResult
            {
                Success = false,
                Phase = Phase,
                Message = message
            };
        }
    }
}
