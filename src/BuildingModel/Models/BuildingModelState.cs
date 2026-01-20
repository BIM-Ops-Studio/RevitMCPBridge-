using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge.BuildingModel.Models
{
    /// <summary>
    /// State tracking for a building model orchestration workflow.
    /// Tracks all phases, inputs, outputs, and progress.
    /// </summary>
    public class BuildingModelState
    {
        #region Identity

        [JsonProperty("workflowId")]
        public string WorkflowId { get; set; } = Guid.NewGuid().ToString("N").Substring(0, 8);

        [JsonProperty("projectName")]
        public string ProjectName { get; set; }

        [JsonProperty("buildingType")]
        public string BuildingType { get; set; }

        [JsonProperty("createdAt")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        [JsonProperty("lastUpdatedAt")]
        public DateTime LastUpdatedAt { get; set; } = DateTime.UtcNow;

        #endregion

        #region Progress Tracking

        [JsonProperty("currentPhase")]
        public BuildingPhase? CurrentPhase { get; set; }

        [JsonProperty("phaseResults")]
        public Dictionary<BuildingPhase, PhaseResult> PhaseResults { get; set; }
            = new Dictionary<BuildingPhase, PhaseResult>();

        [JsonProperty("overallStatus")]
        public WorkflowStatus OverallStatus { get; set; } = WorkflowStatus.NotStarted;

        [JsonProperty("totalElementsCreated")]
        public int TotalElementsCreated { get; set; }

        #endregion

        #region Element Registry

        /// <summary>
        /// Registry of all created elements by category
        /// </summary>
        [JsonProperty("elementRegistry")]
        public ElementRegistry Registry { get; set; } = new ElementRegistry();

        #endregion

        #region Inputs

        /// <summary>
        /// Building program/design inputs provided by user
        /// </summary>
        [JsonProperty("buildingProgram")]
        public BuildingProgram Program { get; set; } = new BuildingProgram();

        /// <summary>
        /// Additional user-provided parameters
        /// </summary>
        [JsonProperty("userParameters")]
        public JObject UserParameters { get; set; } = new JObject();

        #endregion

        #region Configuration

        [JsonProperty("skipOptionalPhases")]
        public bool SkipOptionalPhases { get; set; }

        [JsonProperty("autoExecuteHighConfidence")]
        public bool AutoExecuteHighConfidence { get; set; } = true;

        [JsonProperty("stopOnError")]
        public bool StopOnError { get; set; } = true;

        [JsonProperty("useCIPSValidation")]
        public bool UseCIPSValidation { get; set; } = true;

        #endregion

        #region Status Methods

        /// <summary>
        /// Get the next phase to execute
        /// </summary>
        public BuildingPhase? GetNextPhase()
        {
            var allPhases = PhaseDefinition.GetAllPhases();

            foreach (var phaseDef in allPhases)
            {
                if (PhaseResults.ContainsKey(phaseDef.Phase))
                {
                    var result = PhaseResults[phaseDef.Phase];
                    if (result.Status == PhaseStatus.Completed ||
                        result.Status == PhaseStatus.Skipped)
                    {
                        continue;
                    }
                }

                // Check if optional phase should be skipped
                if (SkipOptionalPhases && phaseDef.IsOptional)
                {
                    continue;
                }

                // Check dependencies
                if (AreDependenciesSatisfied(phaseDef.Phase))
                {
                    return phaseDef.Phase;
                }
            }

            return null;
        }

        /// <summary>
        /// Check if all dependencies for a phase are satisfied
        /// </summary>
        public bool AreDependenciesSatisfied(BuildingPhase phase)
        {
            var phaseDef = PhaseDefinition.GetPhase(phase);
            if (phaseDef == null) return false;

            foreach (var dep in phaseDef.DependsOn)
            {
                if (!PhaseResults.ContainsKey(dep))
                    return false;

                var depResult = PhaseResults[dep];
                if (depResult.Status != PhaseStatus.Completed &&
                    depResult.Status != PhaseStatus.Skipped)
                {
                    return false;
                }
            }

            return true;
        }

        /// <summary>
        /// Get overall progress percentage
        /// </summary>
        public double GetProgressPercentage()
        {
            var allPhases = PhaseDefinition.GetAllPhases();
            var relevantPhases = SkipOptionalPhases
                ? allPhases.Where(p => !p.IsOptional).ToList()
                : allPhases;

            if (relevantPhases.Count == 0) return 0;

            int completed = relevantPhases.Count(p =>
                PhaseResults.ContainsKey(p.Phase) &&
                (PhaseResults[p.Phase].Status == PhaseStatus.Completed ||
                 PhaseResults[p.Phase].Status == PhaseStatus.Skipped));

            return (double)completed / relevantPhases.Count * 100;
        }

        /// <summary>
        /// Get summary of workflow state
        /// </summary>
        public WorkflowSummary GetSummary()
        {
            var completedPhases = PhaseResults.Values
                .Where(r => r.Status == PhaseStatus.Completed)
                .ToList();

            var failedPhases = PhaseResults.Values
                .Where(r => r.Status == PhaseStatus.Failed)
                .ToList();

            return new WorkflowSummary
            {
                WorkflowId = WorkflowId,
                ProjectName = ProjectName,
                Status = OverallStatus,
                Progress = GetProgressPercentage(),
                CurrentPhase = CurrentPhase?.ToString(),
                CompletedPhaseCount = completedPhases.Count,
                FailedPhaseCount = failedPhases.Count,
                TotalElementsCreated = TotalElementsCreated,
                Duration = DateTime.UtcNow - CreatedAt,
                NextPhase = GetNextPhase()?.ToString(),
                AverageConfidence = completedPhases.Any()
                    ? completedPhases.Average(p => p.CIPSConfidence)
                    : 0
            };
        }

        #endregion

        #region State Mutations

        /// <summary>
        /// Start a phase
        /// </summary>
        public PhaseResult StartPhase(BuildingPhase phase)
        {
            CurrentPhase = phase;
            OverallStatus = WorkflowStatus.InProgress;
            LastUpdatedAt = DateTime.UtcNow;

            var result = new PhaseResult
            {
                Phase = phase,
                Status = PhaseStatus.InProgress,
                StartedAt = DateTime.UtcNow
            };

            PhaseResults[phase] = result;
            return result;
        }

        /// <summary>
        /// Complete a phase
        /// </summary>
        public void CompletePhase(BuildingPhase phase, List<int> elementIds, double confidence)
        {
            if (!PhaseResults.ContainsKey(phase))
            {
                StartPhase(phase);
            }

            var result = PhaseResults[phase];
            result.Status = PhaseStatus.Completed;
            result.CompletedAt = DateTime.UtcNow;
            result.CreatedElementIds = elementIds ?? new List<int>();
            result.CIPSConfidence = confidence;

            TotalElementsCreated += result.CreatedElementIds.Count;
            LastUpdatedAt = DateTime.UtcNow;

            // Check if workflow is complete
            var nextPhase = GetNextPhase();
            if (!nextPhase.HasValue)
            {
                OverallStatus = WorkflowStatus.Completed;
            }
        }

        /// <summary>
        /// Fail a phase
        /// </summary>
        public void FailPhase(BuildingPhase phase, string error)
        {
            if (!PhaseResults.ContainsKey(phase))
            {
                StartPhase(phase);
            }

            var result = PhaseResults[phase];
            result.Status = PhaseStatus.Failed;
            result.CompletedAt = DateTime.UtcNow;
            result.ErrorMessage = error;

            LastUpdatedAt = DateTime.UtcNow;

            if (StopOnError)
            {
                OverallStatus = WorkflowStatus.Failed;
            }
        }

        /// <summary>
        /// Skip a phase
        /// </summary>
        public void SkipPhase(BuildingPhase phase, string reason = null)
        {
            var result = new PhaseResult
            {
                Phase = phase,
                Status = PhaseStatus.Skipped,
                StartedAt = DateTime.UtcNow,
                CompletedAt = DateTime.UtcNow
            };

            if (!string.IsNullOrEmpty(reason))
            {
                result.Warnings.Add($"Skipped: {reason}");
            }

            PhaseResults[phase] = result;
            LastUpdatedAt = DateTime.UtcNow;
        }

        #endregion
    }

    /// <summary>
    /// Overall workflow status
    /// </summary>
    public enum WorkflowStatus
    {
        NotStarted,
        InProgress,
        Paused,
        Completed,
        Failed,
        Cancelled
    }

    /// <summary>
    /// Summary of workflow state
    /// </summary>
    public class WorkflowSummary
    {
        [JsonProperty("workflowId")]
        public string WorkflowId { get; set; }

        [JsonProperty("projectName")]
        public string ProjectName { get; set; }

        [JsonProperty("status")]
        public WorkflowStatus Status { get; set; }

        [JsonProperty("progress")]
        public double Progress { get; set; }

        [JsonProperty("currentPhase")]
        public string CurrentPhase { get; set; }

        [JsonProperty("nextPhase")]
        public string NextPhase { get; set; }

        [JsonProperty("completedPhaseCount")]
        public int CompletedPhaseCount { get; set; }

        [JsonProperty("failedPhaseCount")]
        public int FailedPhaseCount { get; set; }

        [JsonProperty("totalElementsCreated")]
        public int TotalElementsCreated { get; set; }

        [JsonProperty("duration")]
        public TimeSpan Duration { get; set; }

        [JsonProperty("averageConfidence")]
        public double AverageConfidence { get; set; }
    }

    /// <summary>
    /// Registry of all created elements organized by category
    /// </summary>
    public class ElementRegistry
    {
        [JsonProperty("levels")]
        public Dictionary<string, int> Levels { get; set; } = new Dictionary<string, int>();

        [JsonProperty("floors")]
        public List<int> Floors { get; set; } = new List<int>();

        [JsonProperty("exteriorWalls")]
        public List<int> ExteriorWalls { get; set; } = new List<int>();

        [JsonProperty("interiorWalls")]
        public List<int> InteriorWalls { get; set; } = new List<int>();

        [JsonProperty("roofs")]
        public List<int> Roofs { get; set; } = new List<int>();

        [JsonProperty("doors")]
        public List<int> Doors { get; set; } = new List<int>();

        [JsonProperty("windows")]
        public List<int> Windows { get; set; } = new List<int>();

        [JsonProperty("rooms")]
        public List<int> Rooms { get; set; } = new List<int>();

        [JsonProperty("ceilings")]
        public List<int> Ceilings { get; set; } = new List<int>();

        [JsonProperty("fixtures")]
        public List<int> Fixtures { get; set; } = new List<int>();

        [JsonProperty("furniture")]
        public List<int> Furniture { get; set; } = new List<int>();

        [JsonProperty("cabinets")]
        public List<int> Cabinets { get; set; } = new List<int>();

        [JsonProperty("stairs")]
        public List<int> Stairs { get; set; } = new List<int>();

        [JsonProperty("siteElements")]
        public List<int> SiteElements { get; set; } = new List<int>();

        [JsonProperty("views")]
        public List<int> Views { get; set; } = new List<int>();

        [JsonProperty("sheets")]
        public List<int> Sheets { get; set; } = new List<int>();

        /// <summary>
        /// Get all element IDs
        /// </summary>
        public List<int> GetAllElementIds()
        {
            var all = new List<int>();
            all.AddRange(Levels.Values);
            all.AddRange(Floors);
            all.AddRange(ExteriorWalls);
            all.AddRange(InteriorWalls);
            all.AddRange(Roofs);
            all.AddRange(Doors);
            all.AddRange(Windows);
            all.AddRange(Rooms);
            all.AddRange(Ceilings);
            all.AddRange(Fixtures);
            all.AddRange(Furniture);
            all.AddRange(Cabinets);
            all.AddRange(Stairs);
            all.AddRange(SiteElements);
            all.AddRange(Views);
            all.AddRange(Sheets);
            return all;
        }
    }

    /// <summary>
    /// Building program - the design input for the orchestrator
    /// </summary>
    public class BuildingProgram
    {
        #region General

        [JsonProperty("buildingType")]
        public string BuildingType { get; set; } = "SingleFamilyResidential";

        [JsonProperty("numberOfStories")]
        public int NumberOfStories { get; set; } = 1;

        [JsonProperty("floorToFloorHeight")]
        public double FloorToFloorHeight { get; set; } = 10.0; // feet

        [JsonProperty("totalBuildingArea")]
        public double TotalBuildingArea { get; set; } // sq ft

        #endregion

        #region Geometry

        [JsonProperty("buildingFootprint")]
        public List<Point2D> BuildingFootprint { get; set; } = new List<Point2D>();

        [JsonProperty("footprintWidth")]
        public double FootprintWidth { get; set; }

        [JsonProperty("footprintLength")]
        public double FootprintLength { get; set; }

        #endregion

        #region Levels

        [JsonProperty("levelNames")]
        public List<string> LevelNames { get; set; } = new List<string>();

        [JsonProperty("levelElevations")]
        public List<double> LevelElevations { get; set; } = new List<double>();

        #endregion

        #region Wall Types

        [JsonProperty("exteriorWallType")]
        public string ExteriorWallType { get; set; } = "Basic Wall - Exterior";

        [JsonProperty("interiorWallType")]
        public string InteriorWallType { get; set; } = "Basic Wall - Interior";

        #endregion

        #region Room Program

        [JsonProperty("rooms")]
        public List<RoomSpec> Rooms { get; set; } = new List<RoomSpec>();

        #endregion

        #region Openings

        [JsonProperty("defaultDoorType")]
        public string DefaultDoorType { get; set; } = "Single-Flush : 36\" x 84\"";

        [JsonProperty("defaultWindowType")]
        public string DefaultWindowType { get; set; } = "Fixed : 36\" x 48\"";

        [JsonProperty("doors")]
        public List<DoorSpec> Doors { get; set; } = new List<DoorSpec>();

        [JsonProperty("windows")]
        public List<WindowSpec> Windows { get; set; } = new List<WindowSpec>();

        #endregion

        #region Roof

        [JsonProperty("roofType")]
        public string RoofType { get; set; } = "Basic Roof - Generic";

        [JsonProperty("roofSlope")]
        public double RoofSlope { get; set; } = 4.0; // rise per 12 run

        #endregion

        #region Ceilings

        [JsonProperty("ceilingType")]
        public string CeilingType { get; set; }

        [JsonProperty("ceilingHeight")]
        public double? CeilingHeight { get; set; }

        #endregion

        #region Vertical Circulation

        [JsonProperty("stairs")]
        public List<StairSpec> Stairs { get; set; } = new List<StairSpec>();

        #endregion

        #region Fixtures & Furnishings

        [JsonProperty("fixtures")]
        public List<FixtureSpec> Fixtures { get; set; } = new List<FixtureSpec>();

        [JsonProperty("cabinets")]
        public List<CabinetSpec> Cabinets { get; set; } = new List<CabinetSpec>();

        [JsonProperty("furniture")]
        public List<FurnitureSpec> Furniture { get; set; } = new List<FurnitureSpec>();

        #endregion

        #region Site

        [JsonProperty("siteElements")]
        public List<SiteElementSpec> SiteElements { get; set; } = new List<SiteElementSpec>();

        [JsonProperty("topographyPoints")]
        public List<Point3D> TopographyPoints { get; set; } = new List<Point3D>();

        #endregion
    }

    /// <summary>
    /// 2D point for footprint definitions
    /// </summary>
    public class Point2D
    {
        [JsonProperty("x")]
        public double X { get; set; }

        [JsonProperty("y")]
        public double Y { get; set; }

        public Point2D() { }
        public Point2D(double x, double y) { X = x; Y = y; }
    }

    /// <summary>
    /// Room specification for the building program
    /// </summary>
    public class RoomSpec
    {
        [JsonProperty("name")]
        public string Name { get; set; }

        [JsonProperty("level")]
        public string Level { get; set; }

        [JsonProperty("area")]
        public double Area { get; set; } // sq ft

        [JsonProperty("minWidth")]
        public double MinWidth { get; set; }

        [JsonProperty("minLength")]
        public double MinLength { get; set; }

        [JsonProperty("roomType")]
        public string RoomType { get; set; } // bedroom, bathroom, kitchen, etc.

        [JsonProperty("location")]
        public Point2D Location { get; set; }

        [JsonProperty("boundaries")]
        public List<Point2D> Boundaries { get; set; }
    }

    /// <summary>
    /// Door specification
    /// </summary>
    public class DoorSpec
    {
        [JsonProperty("wallId")]
        public int? WallId { get; set; }

        [JsonProperty("location")]
        public Point2D Location { get; set; }

        [JsonProperty("doorType")]
        public string DoorType { get; set; }

        [JsonProperty("width")]
        public double Width { get; set; } = 36; // inches

        [JsonProperty("height")]
        public double Height { get; set; } = 84; // inches
    }

    /// <summary>
    /// Window specification
    /// </summary>
    public class WindowSpec
    {
        [JsonProperty("wallId")]
        public int? WallId { get; set; }

        [JsonProperty("location")]
        public Point2D Location { get; set; }

        [JsonProperty("windowType")]
        public string WindowType { get; set; }

        [JsonProperty("width")]
        public double Width { get; set; } = 36; // inches

        [JsonProperty("height")]
        public double Height { get; set; } = 48; // inches

        [JsonProperty("sillHeight")]
        public double SillHeight { get; set; } = 36; // inches
    }

    /// <summary>
    /// 3D point for topography and site elements
    /// </summary>
    public class Point3D
    {
        [JsonProperty("x")]
        public double X { get; set; }

        [JsonProperty("y")]
        public double Y { get; set; }

        [JsonProperty("z")]
        public double Z { get; set; }

        public Point3D() { }
        public Point3D(double x, double y, double z) { X = x; Y = y; Z = z; }
    }

    /// <summary>
    /// Stair specification
    /// </summary>
    public class StairSpec
    {
        [JsonProperty("baseLevelId")]
        public int? BaseLevelId { get; set; }

        [JsonProperty("topLevelId")]
        public int? TopLevelId { get; set; }

        [JsonProperty("location")]
        public Point2D Location { get; set; }

        [JsonProperty("width")]
        public double? Width { get; set; }

        [JsonProperty("riserHeight")]
        public double? RiserHeight { get; set; }

        [JsonProperty("stairType")]
        public string StairType { get; set; }
    }

    /// <summary>
    /// Plumbing fixture specification
    /// </summary>
    public class FixtureSpec
    {
        [JsonProperty("familyName")]
        public string FamilyName { get; set; }

        [JsonProperty("typeName")]
        public string TypeName { get; set; }

        [JsonProperty("location")]
        public Point2D Location { get; set; }

        [JsonProperty("levelId")]
        public int? LevelId { get; set; }

        [JsonProperty("rotation")]
        public double? Rotation { get; set; }

        [JsonProperty("fixtureType")]
        public string FixtureType { get; set; } // toilet, sink, tub, shower
    }

    /// <summary>
    /// Cabinet type enumeration
    /// </summary>
    public enum CabinetType
    {
        Base,
        Upper,
        Tall,
        Corner,
        Vanity
    }

    /// <summary>
    /// Cabinet specification
    /// </summary>
    public class CabinetSpec
    {
        [JsonProperty("familyName")]
        public string FamilyName { get; set; }

        [JsonProperty("typeName")]
        public string TypeName { get; set; }

        [JsonProperty("location")]
        public Point2D Location { get; set; }

        [JsonProperty("levelId")]
        public int? LevelId { get; set; }

        [JsonProperty("rotation")]
        public double? Rotation { get; set; }

        [JsonProperty("cabinetType")]
        public CabinetType? CabinetType { get; set; }

        [JsonProperty("isUpperCabinet")]
        public bool IsUpperCabinet { get; set; }

        [JsonProperty("elevation")]
        public double? Elevation { get; set; }
    }

    /// <summary>
    /// Furniture type enumeration
    /// </summary>
    public enum FurnitureType
    {
        Desk,
        Chair,
        Sofa,
        Table,
        Bed,
        Storage,
        Seating
    }

    /// <summary>
    /// Furniture specification
    /// </summary>
    public class FurnitureSpec
    {
        [JsonProperty("familyName")]
        public string FamilyName { get; set; }

        [JsonProperty("typeName")]
        public string TypeName { get; set; }

        [JsonProperty("location")]
        public Point2D Location { get; set; }

        [JsonProperty("levelId")]
        public int? LevelId { get; set; }

        [JsonProperty("rotation")]
        public double? Rotation { get; set; }

        [JsonProperty("furnitureType")]
        public FurnitureType? FurnitureType { get; set; }
    }

    /// <summary>
    /// Site element type enumeration
    /// </summary>
    public enum SiteElementType
    {
        Tree,
        Shrub,
        Parking,
        Bench,
        Light,
        Vehicle,
        Person
    }

    /// <summary>
    /// Site element specification
    /// </summary>
    public class SiteElementSpec
    {
        [JsonProperty("familyName")]
        public string FamilyName { get; set; }

        [JsonProperty("typeName")]
        public string TypeName { get; set; }

        [JsonProperty("location")]
        public Point3D Location { get; set; }

        [JsonProperty("rotation")]
        public double? Rotation { get; set; }

        [JsonProperty("elementType")]
        public SiteElementType? ElementType { get; set; }
    }
}
