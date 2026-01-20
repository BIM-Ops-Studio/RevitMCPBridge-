using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace RevitMCPBridge.BuildingModel.Models
{
    /// <summary>
    /// The 15 phases of building model orchestration in execution order.
    /// </summary>
    public enum BuildingPhase
    {
        /// <summary>Phase 1: Project setup with levels, units, and grids</summary>
        ProjectSetup = 1,

        /// <summary>Phase 2: Create all levels</summary>
        Levels = 2,

        /// <summary>Phase 3: Create floor slabs</summary>
        Floors = 3,

        /// <summary>Phase 4: Create exterior walls</summary>
        ExteriorWalls = 4,

        /// <summary>Phase 5: Create roof elements</summary>
        Roof = 5,

        /// <summary>Phase 6: Create interior walls</summary>
        InteriorWalls = 6,

        /// <summary>Phase 7: Stairs and elevators</summary>
        VerticalCirculation = 7,

        /// <summary>Phase 8: Doors and windows</summary>
        Openings = 8,

        /// <summary>Phase 9: Ceiling elements</summary>
        Ceilings = 9,

        /// <summary>Phase 10: Plumbing fixtures</summary>
        Fixtures = 10,

        /// <summary>Phase 11: Kitchen and bath cabinetry</summary>
        Cabinetry = 11,

        /// <summary>Phase 12: Furniture placement</summary>
        Furniture = 12,

        /// <summary>Phase 13: Site elements</summary>
        Site = 13,

        /// <summary>Phase 14: Room boundaries and tags</summary>
        Rooms = 14,

        /// <summary>Phase 15: Views and sheets</summary>
        ViewsDocumentation = 15
    }

    /// <summary>
    /// Status of a phase execution
    /// </summary>
    public enum PhaseStatus
    {
        NotStarted,
        InProgress,
        Completed,
        Failed,
        Skipped,
        RequiresReview
    }

    /// <summary>
    /// Definition of a building phase with its requirements and outputs
    /// </summary>
    public class PhaseDefinition
    {
        [JsonProperty("phase")]
        public BuildingPhase Phase { get; set; }

        [JsonProperty("name")]
        public string Name { get; set; }

        [JsonProperty("description")]
        public string Description { get; set; }

        [JsonProperty("requiredInputs")]
        public List<string> RequiredInputs { get; set; } = new List<string>();

        [JsonProperty("outputs")]
        public List<string> Outputs { get; set; } = new List<string>();

        [JsonProperty("dependsOn")]
        public List<BuildingPhase> DependsOn { get; set; } = new List<BuildingPhase>();

        [JsonProperty("validationRules")]
        public List<string> ValidationRules { get; set; } = new List<string>();

        [JsonProperty("mcpMethods")]
        public List<string> MCPMethods { get; set; } = new List<string>();

        [JsonProperty("estimatedElementCount")]
        public int EstimatedElementCount { get; set; }

        [JsonProperty("isOptional")]
        public bool IsOptional { get; set; }

        /// <summary>
        /// Get all phase definitions for the complete building workflow
        /// </summary>
        public static List<PhaseDefinition> GetAllPhases()
        {
            return new List<PhaseDefinition>
            {
                new PhaseDefinition
                {
                    Phase = BuildingPhase.ProjectSetup,
                    Name = "Project Setup",
                    Description = "Initialize project with units, grids, and base settings",
                    RequiredInputs = new List<string>
                    {
                        "projectName",
                        "buildingType",
                        "numberOfStories",
                        "buildingFootprint"
                    },
                    Outputs = new List<string> { "projectInfo", "gridSystem", "baseLevel" },
                    DependsOn = new List<BuildingPhase>(),
                    ValidationRules = new List<string>
                    {
                        "Project name is set",
                        "Units are configured (feet/inches or metric)",
                        "Base level exists"
                    },
                    MCPMethods = new List<string> { "setProjectInfo", "createGrid" },
                    EstimatedElementCount = 10
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Levels,
                    Name = "Levels",
                    Description = "Create all floor levels with correct elevations",
                    RequiredInputs = new List<string>
                    {
                        "numberOfStories",
                        "floorToFloorHeight",
                        "levelNames"
                    },
                    Outputs = new List<string> { "levelIds", "levelElevations" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.ProjectSetup },
                    ValidationRules = new List<string>
                    {
                        "All levels created",
                        "Level elevations are correct",
                        "Level names follow convention"
                    },
                    MCPMethods = new List<string> { "createLevel", "getLevels" },
                    EstimatedElementCount = 5
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Floors,
                    Name = "Floors",
                    Description = "Create floor slabs at each level",
                    RequiredInputs = new List<string>
                    {
                        "levelIds",
                        "floorBoundary",
                        "floorType"
                    },
                    Outputs = new List<string> { "floorIds", "floorAreas" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.Levels },
                    ValidationRules = new List<string>
                    {
                        "Floors created at each level",
                        "Floor boundaries are closed",
                        "Floor type is appropriate"
                    },
                    MCPMethods = new List<string> { "createFloor", "getFloorTypes" },
                    EstimatedElementCount = 5
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.ExteriorWalls,
                    Name = "Exterior Walls",
                    Description = "Create building envelope with exterior walls",
                    RequiredInputs = new List<string>
                    {
                        "levelIds",
                        "wallGeometry",
                        "exteriorWallType"
                    },
                    Outputs = new List<string> { "exteriorWallIds", "wallHeights" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.Floors },
                    ValidationRules = new List<string>
                    {
                        "Walls form closed boundary",
                        "Wall heights reach next level",
                        "Correct wall type used (exterior)"
                    },
                    MCPMethods = new List<string> { "createWall", "getWallTypes" },
                    EstimatedElementCount = 20
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Roof,
                    Name = "Roof",
                    Description = "Create roof elements over the building",
                    RequiredInputs = new List<string>
                    {
                        "topLevelId",
                        "roofBoundary",
                        "roofType",
                        "roofSlope"
                    },
                    Outputs = new List<string> { "roofId", "roofArea" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.ExteriorWalls },
                    ValidationRules = new List<string>
                    {
                        "Roof covers building footprint",
                        "Roof type is appropriate",
                        "Slope direction is correct"
                    },
                    MCPMethods = new List<string> { "createFootprintRoof", "createExtrusionRoof" },
                    EstimatedElementCount = 3
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.InteriorWalls,
                    Name = "Interior Walls",
                    Description = "Create interior partition walls",
                    RequiredInputs = new List<string>
                    {
                        "levelIds",
                        "interiorWallGeometry",
                        "interiorWallTypes"
                    },
                    Outputs = new List<string> { "interiorWallIds", "roomDefinitions" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.ExteriorWalls },
                    ValidationRules = new List<string>
                    {
                        "Walls connect to exterior walls",
                        "Room boundaries are defined",
                        "Correct wall types used"
                    },
                    MCPMethods = new List<string> { "createWall", "getWallTypes" },
                    EstimatedElementCount = 50
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.VerticalCirculation,
                    Name = "Vertical Circulation",
                    Description = "Create stairs, elevators, and vertical openings",
                    RequiredInputs = new List<string>
                    {
                        "levelIds",
                        "stairLocations",
                        "elevatorLocations"
                    },
                    Outputs = new List<string> { "stairIds", "elevatorIds", "shaftIds" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.InteriorWalls },
                    ValidationRules = new List<string>
                    {
                        "Stairs connect all levels",
                        "Elevator shafts are aligned",
                        "Egress requirements met"
                    },
                    MCPMethods = new List<string> { "createStairs", "createOpening" },
                    EstimatedElementCount = 10,
                    IsOptional = true
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Openings,
                    Name = "Openings",
                    Description = "Place doors and windows in walls",
                    RequiredInputs = new List<string>
                    {
                        "wallIds",
                        "doorLocations",
                        "windowLocations",
                        "doorTypes",
                        "windowTypes"
                    },
                    Outputs = new List<string> { "doorIds", "windowIds" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.InteriorWalls },
                    ValidationRules = new List<string>
                    {
                        "Doors hosted in walls",
                        "Windows at correct sill height",
                        "Egress doors meet code"
                    },
                    MCPMethods = new List<string> { "placeDoor", "placeWindow" },
                    EstimatedElementCount = 40
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Ceilings,
                    Name = "Ceilings",
                    Description = "Create ceiling elements",
                    RequiredInputs = new List<string>
                    {
                        "levelIds",
                        "ceilingBoundaries",
                        "ceilingType",
                        "ceilingHeight"
                    },
                    Outputs = new List<string> { "ceilingIds" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.InteriorWalls },
                    ValidationRules = new List<string>
                    {
                        "Ceilings cover all rooms",
                        "Correct ceiling height",
                        "Appropriate ceiling type"
                    },
                    MCPMethods = new List<string> { "createCeiling", "getCeilingTypes" },
                    EstimatedElementCount = 15,
                    IsOptional = true
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Fixtures,
                    Name = "Fixtures",
                    Description = "Place plumbing fixtures and appliances",
                    RequiredInputs = new List<string>
                    {
                        "fixtureLocations",
                        "fixtureTypes"
                    },
                    Outputs = new List<string> { "fixtureIds" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.Openings },
                    ValidationRules = new List<string>
                    {
                        "Fixtures in appropriate rooms",
                        "Clearances maintained",
                        "ADA compliance where required"
                    },
                    MCPMethods = new List<string> { "placeFamilyInstance" },
                    EstimatedElementCount = 20,
                    IsOptional = true
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Cabinetry,
                    Name = "Cabinetry",
                    Description = "Place kitchen and bath cabinetry",
                    RequiredInputs = new List<string>
                    {
                        "cabinetLocations",
                        "cabinetTypes"
                    },
                    Outputs = new List<string> { "cabinetIds" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.Fixtures },
                    ValidationRules = new List<string>
                    {
                        "Cabinets against walls",
                        "Counter heights correct",
                        "Appliance clearances"
                    },
                    MCPMethods = new List<string> { "placeFamilyInstance" },
                    EstimatedElementCount = 30,
                    IsOptional = true
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Furniture,
                    Name = "Furniture",
                    Description = "Place furniture for visualization",
                    RequiredInputs = new List<string>
                    {
                        "furnitureLocations",
                        "furnitureTypes"
                    },
                    Outputs = new List<string> { "furnitureIds" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.Cabinetry },
                    ValidationRules = new List<string>
                    {
                        "Furniture fits in rooms",
                        "Circulation maintained"
                    },
                    MCPMethods = new List<string> { "placeFamilyInstance" },
                    EstimatedElementCount = 25,
                    IsOptional = true
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Site,
                    Name = "Site",
                    Description = "Create site elements and context",
                    RequiredInputs = new List<string>
                    {
                        "siteBoundary",
                        "topography"
                    },
                    Outputs = new List<string> { "siteId", "topographyId" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.ProjectSetup },
                    ValidationRules = new List<string>
                    {
                        "Site boundary defined",
                        "Building within setbacks"
                    },
                    MCPMethods = new List<string> { "createTopography", "createBuildingPad" },
                    EstimatedElementCount = 5,
                    IsOptional = true
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.Rooms,
                    Name = "Rooms",
                    Description = "Create rooms and apply tags",
                    RequiredInputs = new List<string>
                    {
                        "roomLocations",
                        "roomNames"
                    },
                    Outputs = new List<string> { "roomIds", "roomAreas" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.InteriorWalls },
                    ValidationRules = new List<string>
                    {
                        "All enclosed areas have rooms",
                        "Room names assigned",
                        "Areas calculated"
                    },
                    MCPMethods = new List<string> { "createRoom", "tagRoom", "getRooms" },
                    EstimatedElementCount = 15
                },

                new PhaseDefinition
                {
                    Phase = BuildingPhase.ViewsDocumentation,
                    Name = "Views & Documentation",
                    Description = "Create views, sheets, and annotations",
                    RequiredInputs = new List<string>
                    {
                        "viewTypes",
                        "sheetList"
                    },
                    Outputs = new List<string> { "viewIds", "sheetIds" },
                    DependsOn = new List<BuildingPhase> { BuildingPhase.Rooms },
                    ValidationRules = new List<string>
                    {
                        "Floor plans for each level",
                        "Required views created",
                        "Views placed on sheets"
                    },
                    MCPMethods = new List<string>
                    {
                        "createFloorPlan", "createCeilingPlan", "createSection",
                        "create3DView", "createSheet", "placeViewOnSheet"
                    },
                    EstimatedElementCount = 20,
                    IsOptional = true
                }
            };
        }

        /// <summary>
        /// Get phase definition by phase enum
        /// </summary>
        public static PhaseDefinition GetPhase(BuildingPhase phase)
        {
            var all = GetAllPhases();
            return all.Find(p => p.Phase == phase);
        }
    }

    /// <summary>
    /// Result of a phase execution
    /// </summary>
    public class PhaseResult
    {
        [JsonProperty("phase")]
        public BuildingPhase Phase { get; set; }

        [JsonProperty("status")]
        public PhaseStatus Status { get; set; }

        [JsonProperty("startedAt")]
        public DateTime StartedAt { get; set; }

        [JsonProperty("completedAt")]
        public DateTime? CompletedAt { get; set; }

        [JsonProperty("createdElementIds")]
        public List<int> CreatedElementIds { get; set; } = new List<int>();

        [JsonProperty("errorMessage")]
        public string ErrorMessage { get; set; }

        [JsonProperty("warnings")]
        public List<string> Warnings { get; set; } = new List<string>();

        [JsonProperty("validationResults")]
        public List<ValidationResult> ValidationResults { get; set; } = new List<ValidationResult>();

        [JsonProperty("cipsConfidence")]
        public double CIPSConfidence { get; set; }

        [JsonProperty("duration")]
        public TimeSpan? Duration => CompletedAt.HasValue ? CompletedAt.Value - StartedAt : (TimeSpan?)null;
    }

    /// <summary>
    /// Validation result for a phase
    /// </summary>
    public class ValidationResult
    {
        [JsonProperty("rule")]
        public string Rule { get; set; }

        [JsonProperty("passed")]
        public bool Passed { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }
    }
}
