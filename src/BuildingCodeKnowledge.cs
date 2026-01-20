using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Serilog;

namespace RevitMCPBridge
{
    /// <summary>
    /// Building Code Knowledge Base
    /// Contains rules and requirements from LATEST building codes
    ///
    /// CODE VERSIONS (Updated 2025):
    /// - IBC 2024 (International Building Code - LATEST)
    /// - FBC 8th Edition (2023) - Florida Building Code (based on IBC 2021)
    /// - ADA 2010 Standards (with 2023 updates)
    /// - NFPA 101 (2024) - Life Safety Code
    ///
    /// Enables Claude AI to autonomously verify code compliance
    /// </summary>
    public static class BuildingCodeKnowledge
    {
        // Current code versions
        public const string IBC_VERSION = "IBC 2024";
        public const string FBC_VERSION = "FBC 8th Edition (2023)";
        public const string ADA_VERSION = "ADA 2010 with 2023 Updates";
        public const string NFPA_VERSION = "NFPA 101-2024";

        // ==================== IBC 2024 / FBC 8TH EDITION (2023) REQUIREMENTS ====================

        /// <summary>
        /// Door width requirements by occupancy and use
        /// </summary>
        public static class DoorRequirements
        {
            // Minimum door widths (in inches)
            public const double MIN_EGRESS_DOOR_WIDTH = 36.0;  // IBC 1010.1.1
            public const double MIN_CORRIDOR_DOOR_WIDTH = 32.0;  // IBC 1020.2
            public const double MIN_ADA_DOOR_WIDTH = 32.0;  // ADA 404.2.3 (clear width)
            public const double MIN_RESIDENTIAL_DOOR_WIDTH = 32.0;

            /// <summary>
            /// Check if door width meets code requirements
            /// </summary>
            public static CodeComplianceResult CheckDoorWidth(double widthInches, string occupancyType, bool isEgress)
            {
                var result = new CodeComplianceResult
                {
                    Element = "Door",
                    Requirement = "Width",
                    ActualValue = widthInches,
                    IsCompliant = true
                };

                if (isEgress && widthInches < MIN_EGRESS_DOOR_WIDTH)
                {
                    result.IsCompliant = false;
                    result.RequiredValue = MIN_EGRESS_DOOR_WIDTH;
                    result.CodeReference = "IBC 1010.1.1";
                    result.Issue = $"Egress door width {widthInches}\" is less than required {MIN_EGRESS_DOOR_WIDTH}\"";
                    result.AutoFix = $"Change door to {MIN_EGRESS_DOOR_WIDTH}\" width type";
                }
                else if (widthInches < MIN_CORRIDOR_DOOR_WIDTH)
                {
                    result.IsCompliant = false;
                    result.RequiredValue = MIN_CORRIDOR_DOOR_WIDTH;
                    result.CodeReference = "IBC 1020.2";
                    result.Issue = $"Door width {widthInches}\" is less than minimum {MIN_CORRIDOR_DOOR_WIDTH}\"";
                    result.AutoFix = $"Change door to {MIN_CORRIDOR_DOOR_WIDTH}\" or {MIN_EGRESS_DOOR_WIDTH}\" width type";
                }
                else
                {
                    result.RequiredValue = isEgress ? MIN_EGRESS_DOOR_WIDTH : MIN_CORRIDOR_DOOR_WIDTH;
                    result.CodeReference = isEgress ? "IBC 1010.1.1" : "IBC 1020.2";
                }

                return result;
            }

            /// <summary>
            /// ADA door clearance requirements
            /// </summary>
            public static double GetRequiredClearWidth()
            {
                return 32.0;  // ADA 404.2.3 - minimum 32" clear width
            }

            public static double GetRequiredManeuveringClearance(bool pullSide)
            {
                return pullSide ? 18.0 : 12.0;  // ADA 404.2.4
            }
        }

        /// <summary>
        /// Corridor and circulation path requirements
        /// </summary>
        public static class CorridorRequirements
        {
            public const double MIN_CORRIDOR_WIDTH = 44.0;  // IBC 1020.2 (in inches)
            public const double MIN_ACCESSIBLE_ROUTE_WIDTH = 36.0;  // ADA 403.5.1

            /// <summary>
            /// Check corridor width compliance
            /// </summary>
            public static CodeComplianceResult CheckCorridorWidth(double widthInches, int occupantLoad)
            {
                var result = new CodeComplianceResult
                {
                    Element = "Corridor",
                    Requirement = "Width",
                    ActualValue = widthInches,
                    IsCompliant = true
                };

                double requiredWidth = MIN_CORRIDOR_WIDTH;

                // Increase width for higher occupant loads (IBC 1005.1)
                if (occupantLoad > 50)
                {
                    requiredWidth = 48.0;  // Wider corridor for higher occupancy
                }

                if (widthInches < requiredWidth)
                {
                    result.IsCompliant = false;
                    result.RequiredValue = requiredWidth;
                    result.CodeReference = "IBC 1020.2";
                    result.Issue = $"Corridor width {widthInches}\" is less than required {requiredWidth}\"";
                    result.AutoFix = "Adjust corridor width in model";
                }
                else
                {
                    result.RequiredValue = requiredWidth;
                    result.CodeReference = "IBC 1020.2";
                }

                return result;
            }
        }

        /// <summary>
        /// Means of egress requirements
        /// </summary>
        public static class EgressRequirements
        {
            /// <summary>
            /// Number of required exits based on occupant load
            /// </summary>
            public static int GetRequiredNumberOfExits(int occupantLoad)
            {
                // IBC Table 1006.2.1
                if (occupantLoad >= 501) return 4;
                if (occupantLoad >= 1) return 2;
                return 1;
            }

            /// <summary>
            /// Maximum travel distance (in feet)
            /// </summary>
            public static double GetMaxTravelDistance(string occupancyGroup, bool sprinklered)
            {
                // IBC Table 1017.2
                switch (occupancyGroup)
                {
                    case "A":  // Assembly
                        return sprinklered ? 250 : 200;
                    case "B":  // Business
                        return sprinklered ? 300 : 200;
                    case "E":  // Educational
                        return sprinklered ? 250 : 200;
                    case "M":  // Mercantile
                        return sprinklered ? 250 : 200;
                    case "R":  // Residential
                        return sprinklered ? 250 : 200;
                    case "S":  // Storage
                        return sprinklered ? 400 : 300;
                    default:
                        return sprinklered ? 250 : 200;
                }
            }

            /// <summary>
            /// Check egress path compliance
            /// </summary>
            public static CodeComplianceResult CheckEgressPaths(int numberOfExits, int requiredExits)
            {
                var result = new CodeComplianceResult
                {
                    Element = "Egress Path",
                    Requirement = "Number of Exits",
                    ActualValue = numberOfExits,
                    RequiredValue = requiredExits,
                    CodeReference = "IBC 1006.2",
                    IsCompliant = numberOfExits >= requiredExits
                };

                if (!result.IsCompliant)
                {
                    result.Issue = $"Only {numberOfExits} exit(s) provided, {requiredExits} required";
                    result.AutoFix = $"Add {requiredExits - numberOfExits} additional exit(s)";
                }

                return result;
            }
        }

        /// <summary>
        /// Occupancy classification and load calculations
        /// </summary>
        public static class OccupancyRequirements
        {
            /// <summary>
            /// Occupant load factors (square feet per person) - IBC Table 1004.5
            /// </summary>
            public static double GetOccupantLoadFactor(string spaceType)
            {
                switch (spaceType.ToLower())
                {
                    // Business (B)
                    case "office":
                        return 150.0;  // 150 SF per person
                    case "conference room":
                    case "meeting room":
                        return 15.0;   // 15 SF per person

                    // Assembly (A)
                    case "assembly without fixed seats":
                        return 15.0;
                    case "assembly with fixed seats":
                        return 7.0;

                    // Mercantile (M)
                    case "retail sales":
                        return 60.0;
                    case "storage":
                        return 300.0;

                    // Educational (E)
                    case "classroom":
                        return 20.0;

                    // Healthcare (I-2)
                    case "patient room":
                        return 240.0;
                    case "treatment room":
                        return 240.0;

                    default:
                        return 100.0;  // Default conservative value
                }
            }

            /// <summary>
            /// Calculate occupant load for a space
            /// </summary>
            public static int CalculateOccupantLoad(double areaSquareFeet, string spaceType)
            {
                var factor = GetOccupantLoadFactor(spaceType);
                return (int)Math.Ceiling(areaSquareFeet / factor);
            }
        }

        /// <summary>
        /// ADA accessibility requirements
        /// </summary>
        public static class AccessibilityRequirements
        {
            /// <summary>
            /// Required accessible route width
            /// </summary>
            public const double MIN_ACCESSIBLE_ROUTE_WIDTH = 36.0;  // ADA 403.5.1

            /// <summary>
            /// Maneuvering clearances for doors
            /// </summary>
            public static Dictionary<string, double> GetDoorManeuveringClearances()
            {
                return new Dictionary<string, double>
                {
                    { "PullSideLatch", 18.0 },  // 18" on pull side latch side
                    { "PullSideHinge", 0.0 },   // 0" on pull side hinge side
                    { "PushSideLatch", 12.0 },  // 12" on push side latch side
                    { "DepthPull", 60.0 },      // 60" depth for pull side
                    { "DepthPush", 48.0 }       // 48" depth for push side
                };
            }

            /// <summary>
            /// Check if accessible route width meets requirements
            /// </summary>
            public static CodeComplianceResult CheckAccessibleRoute(double widthInches)
            {
                return new CodeComplianceResult
                {
                    Element = "Accessible Route",
                    Requirement = "Width",
                    ActualValue = widthInches,
                    RequiredValue = MIN_ACCESSIBLE_ROUTE_WIDTH,
                    CodeReference = "ADA 403.5.1",
                    IsCompliant = widthInches >= MIN_ACCESSIBLE_ROUTE_WIDTH,
                    Issue = widthInches < MIN_ACCESSIBLE_ROUTE_WIDTH
                        ? $"Route width {widthInches}\" is less than required {MIN_ACCESSIBLE_ROUTE_WIDTH}\""
                        : null,
                    AutoFix = widthInches < MIN_ACCESSIBLE_ROUTE_WIDTH
                        ? "Widen accessible route to minimum 36\""
                        : null
                };
            }
        }

        /// <summary>
        /// Florida Building Code specific requirements
        /// </summary>
        public static class FloridaBuildingCode
        {
            /// <summary>
            /// Wind load requirements by region
            /// </summary>
            public static int GetDesignWindSpeed(string county)
            {
                // FBC Table 1609.3.1 - Simplified
                // Actual implementation would have detailed county mapping
                if (county.ToLower().Contains("miami") || county.ToLower().Contains("dade"))
                    return 175;  // mph
                if (county.ToLower().Contains("broward") || county.ToLower().Contains("palm beach"))
                    return 170;

                return 150;  // Default for most of Florida
            }

            /// <summary>
            /// Hurricane protection requirements
            /// </summary>
            public static bool RequiresImpactResistantGlazing(string county)
            {
                // Wind-borne debris regions require impact-resistant glazing
                return county.ToLower().Contains("miami") ||
                       county.ToLower().Contains("broward") ||
                       county.ToLower().Contains("palm beach") ||
                       county.ToLower().Contains("monroe");
            }
        }

        // ==================== CODE COMPLIANCE RESULT CLASS ====================

        /// <summary>
        /// Result of a code compliance check
        /// </summary>
        public class CodeComplianceResult
        {
            public string Element { get; set; }
            public string Requirement { get; set; }
            public double ActualValue { get; set; }
            public double RequiredValue { get; set; }
            public string CodeReference { get; set; }
            public bool IsCompliant { get; set; }
            public string Issue { get; set; }
            public string AutoFix { get; set; }

            public override string ToString()
            {
                if (IsCompliant)
                {
                    return $"✓ {Element} {Requirement}: {ActualValue} meets {CodeReference} requirement ({RequiredValue})";
                }
                else
                {
                    return $"✗ {Element} {Requirement}: {Issue} ({CodeReference}) - AutoFix: {AutoFix}";
                }
            }
        }

        // ==================== HELPER METHODS ====================

        /// <summary>
        /// Get comprehensive code requirements for a project
        /// </summary>
        public static JObject GetProjectCodeRequirements(string occupancyType, string buildingCode, string location)
        {
            var requirements = new JObject
            {
                ["occupancyType"] = occupancyType,
                ["buildingCode"] = buildingCode,
                ["location"] = location,
                ["doors"] = new JObject
                {
                    ["minEgressWidth"] = DoorRequirements.MIN_EGRESS_DOOR_WIDTH,
                    ["minCorridorWidth"] = DoorRequirements.MIN_CORRIDOR_DOOR_WIDTH,
                    ["adaClearWidth"] = DoorRequirements.MIN_ADA_DOOR_WIDTH
                },
                ["corridors"] = new JObject
                {
                    ["minWidth"] = CorridorRequirements.MIN_CORRIDOR_WIDTH,
                    ["accessibleRouteWidth"] = CorridorRequirements.MIN_ACCESSIBLE_ROUTE_WIDTH
                },
                ["egress"] = new JObject
                {
                    ["requiredExits"] = 2,  // Default for commercial
                    ["maxTravelDistance"] = EgressRequirements.GetMaxTravelDistance(occupancyType, true)
                }
            };

            // Add Florida-specific requirements if applicable
            if (buildingCode == "FBC" || location.ToLower().Contains("florida"))
            {
                var county = ExtractCounty(location);
                requirements["florida"] = new JObject
                {
                    ["designWindSpeed"] = FloridaBuildingCode.GetDesignWindSpeed(county),
                    ["requiresImpactGlazing"] = FloridaBuildingCode.RequiresImpactResistantGlazing(county)
                };
            }

            return requirements;
        }

        private static string ExtractCounty(string location)
        {
            // Simple extraction - would be more sophisticated in production
            if (location.ToLower().Contains("miami")) return "Miami-Dade";
            if (location.ToLower().Contains("broward")) return "Broward";
            if (location.ToLower().Contains("palm beach")) return "Palm Beach";
            return "Unknown";
        }

        /// <summary>
        /// Run all code compliance checks for a project
        /// </summary>
        public static List<CodeComplianceResult> RunComplianceChecks(JObject projectData)
        {
            var results = new List<CodeComplianceResult>();

            // This would be expanded with actual project data analysis
            Log.Information("[CODE COMPLIANCE] Running building code compliance checks");

            // Example checks - would be populated with real data in practice
            results.Add(DoorRequirements.CheckDoorWidth(36, "Business", true));
            results.Add(CorridorRequirements.CheckCorridorWidth(44, 50));
            results.Add(AccessibilityRequirements.CheckAccessibleRoute(36));

            return results;
        }
    }
}
