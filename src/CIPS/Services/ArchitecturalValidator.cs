using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Validates operations against architectural rules to catch impossible or improbable interpretations.
    /// This is Enhancement #3: Architectural Validation Rules
    /// </summary>
    public class ArchitecturalValidator
    {
        private readonly UIApplication _uiApp;
        private readonly ValidationRulesConfig _config;

        /// <summary>
        /// Standard factor name for architectural validation
        /// </summary>
        public const string FactorName = "ArchitecturalValidation";

        /// <summary>
        /// Weight for the architectural validation factor
        /// </summary>
        public const double FactorWeight = 0.10;

        public ArchitecturalValidator(UIApplication uiApp = null)
        {
            _uiApp = uiApp;
            _config = CIPSConfiguration.Instance.ValidationRules ?? new ValidationRulesConfig();
        }

        /// <summary>
        /// Validate an operation and return a confidence factor
        /// </summary>
        public ConfidenceFactor Validate(string methodName, JObject parameters)
        {
            if (!_config.Enabled)
            {
                return ConfidenceFactor.Pass(FactorName, 1.0, "Architectural validation disabled");
            }

            try
            {
                var result = ValidateOperation(methodName, parameters);
                result.CalculateScore();

                var reason = result.Passed
                    ? "All architectural rules passed"
                    : result.Summary;

                return new ConfidenceFactor
                {
                    FactorName = FactorName,
                    Score = result.Score,
                    Weight = FactorWeight,
                    Reason = reason,
                    Details = new Dictionary<string, object>
                    {
                        ["violations"] = result.Violations,
                        ["hardFails"] = result.HardFailCount,
                        ["warnings"] = result.WarningCount,
                        ["advisories"] = result.AdvisoryCount
                    }
                };
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[CIPS] Architectural validation error for {Method}", methodName);
                // Return neutral score on error - don't penalize for validation failures
                return ConfidenceFactor.Pass(FactorName, 0.8, $"Validation error: {ex.Message}");
            }
        }

        /// <summary>
        /// Validate an operation and return the full result with violations
        /// </summary>
        public ArchitecturalValidationResult ValidateOperation(string methodName, JObject parameters)
        {
            var result = new ArchitecturalValidationResult();

            // Route to appropriate validator based on method name
            var methodLower = methodName?.ToLower() ?? "";

            if (methodLower.Contains("wall"))
            {
                ValidateWallOperation(parameters, result);
            }
            else if (methodLower.Contains("door"))
            {
                ValidateDoorOperation(parameters, result);
            }
            else if (methodLower.Contains("window"))
            {
                ValidateWindowOperation(parameters, result);
            }
            else if (methodLower.Contains("room"))
            {
                ValidateRoomOperation(parameters, result);
            }

            result.CalculateScore();
            return result;
        }

        private void ValidateWallOperation(JObject parameters, ArchitecturalValidationResult result)
        {
            var rules = _config.Rules.Walls;

            // Check wall length
            double? length = GetLengthFromParameters(parameters);
            if (length.HasValue)
            {
                // Convert to appropriate units for comparison
                double lengthInches = length.Value * 12; // Assume feet input, convert to inches

                // Check minimum length
                if (lengthInches < rules.MinLengthInches)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "wall_min_length",
                        ElementType = "wall",
                        Property = "length",
                        Level = ViolationLevel.HardFail,
                        ExpectedValue = rules.MinLengthInches,
                        ActualValue = lengthInches,
                        Reason = $"Wall length ({lengthInches:F1}\") is below minimum ({rules.MinLengthInches}\")"
                    });
                }

                // Check maximum length
                double lengthFeet = length.Value;
                if (lengthFeet > rules.MaxLengthFeet)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "wall_max_length",
                        ElementType = "wall",
                        Property = "length",
                        Level = ViolationLevel.SoftWarning,
                        ExpectedValue = rules.MaxLengthFeet,
                        ActualValue = lengthFeet,
                        Reason = $"Wall length ({lengthFeet:F1}') exceeds maximum ({rules.MaxLengthFeet}')"
                    });
                }

                // Check unsupported span
                if (lengthFeet > rules.MaxUnsupportedSpanFeet)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "wall_unsupported_span",
                        ElementType = "wall",
                        Property = "span",
                        Level = ViolationLevel.Advisory,
                        ExpectedValue = rules.MaxUnsupportedSpanFeet,
                        ActualValue = lengthFeet,
                        Reason = $"Wall span ({lengthFeet:F1}') may need intermediate support (recommended max: {rules.MaxUnsupportedSpanFeet}')"
                    });
                }
            }
        }

        private void ValidateDoorOperation(JObject parameters, ArchitecturalValidationResult result)
        {
            var rules = _config.Rules.Doors;

            // Check door width
            double? width = GetWidthFromParameters(parameters);
            if (width.HasValue)
            {
                double widthInches = width.Value;

                if (widthInches < rules.MinWidthInches)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "door_min_width",
                        ElementType = "door",
                        Property = "width",
                        Level = ViolationLevel.HardFail,
                        ExpectedValue = rules.MinWidthInches,
                        ActualValue = widthInches,
                        Reason = $"Door width ({widthInches:F0}\") is below minimum ({rules.MinWidthInches}\")"
                    });
                }

                if (widthInches > rules.MaxWidthInches)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "door_max_width",
                        ElementType = "door",
                        Property = "width",
                        Level = ViolationLevel.HardFail,
                        ExpectedValue = rules.MaxWidthInches,
                        ActualValue = widthInches,
                        Reason = $"Door width ({widthInches:F0}\") exceeds maximum ({rules.MaxWidthInches}\")"
                    });
                }

                // Check if standard width
                bool isStandard = rules.StandardWidthsInches.Any(sw => Math.Abs(sw - widthInches) < 0.5);
                if (!isStandard)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "door_nonstandard_width",
                        ElementType = "door",
                        Property = "width",
                        Level = ViolationLevel.Advisory,
                        ExpectedValue = 0,
                        ActualValue = widthInches,
                        Reason = $"Door width ({widthInches:F0}\") is non-standard. Standard widths: {string.Join(", ", rules.StandardWidthsInches)})"
                    });
                }
            }

            // Check door height
            double? height = GetHeightFromParameters(parameters);
            if (height.HasValue)
            {
                double heightInches = height.Value;

                if (heightInches < rules.MinHeightInches)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "door_min_height",
                        ElementType = "door",
                        Property = "height",
                        Level = ViolationLevel.HardFail,
                        ExpectedValue = rules.MinHeightInches,
                        ActualValue = heightInches,
                        Reason = $"Door height ({heightInches:F0}\") is below minimum ({rules.MinHeightInches}\")"
                    });
                }

                if (heightInches > rules.MaxHeightInches)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "door_max_height",
                        ElementType = "door",
                        Property = "height",
                        Level = ViolationLevel.SoftWarning,
                        ExpectedValue = rules.MaxHeightInches,
                        ActualValue = heightInches,
                        Reason = $"Door height ({heightInches:F0}\") exceeds standard maximum ({rules.MaxHeightInches}\")"
                    });
                }
            }
        }

        private void ValidateWindowOperation(JObject parameters, ArchitecturalValidationResult result)
        {
            var rules = _config.Rules.Windows;

            // Check window width
            double? width = GetWidthFromParameters(parameters);
            if (width.HasValue)
            {
                double widthInches = width.Value;

                if (widthInches < rules.MinWidthInches)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "window_min_width",
                        ElementType = "window",
                        Property = "width",
                        Level = ViolationLevel.HardFail,
                        ExpectedValue = rules.MinWidthInches,
                        ActualValue = widthInches,
                        Reason = $"Window width ({widthInches:F0}\") is below minimum ({rules.MinWidthInches}\")"
                    });
                }

                if (widthInches > rules.MaxWidthInches)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "window_max_width",
                        ElementType = "window",
                        Property = "width",
                        Level = ViolationLevel.SoftWarning,
                        ExpectedValue = rules.MaxWidthInches,
                        ActualValue = widthInches,
                        Reason = $"Window width ({widthInches:F0}\") exceeds standard maximum ({rules.MaxWidthInches}\")"
                    });
                }
            }

            // Check sill height
            double? sillHeight = parameters["sillHeight"]?.Value<double>();
            if (sillHeight.HasValue)
            {
                double sillInches = sillHeight.Value;

                if (sillInches < rules.MinSillHeightInches)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "window_min_sill",
                        ElementType = "window",
                        Property = "sillHeight",
                        Level = ViolationLevel.SoftWarning,
                        ExpectedValue = rules.MinSillHeightInches,
                        ActualValue = sillInches,
                        Reason = $"Window sill height ({sillInches:F0}\") is below recommended minimum ({rules.MinSillHeightInches}\")"
                    });
                }
            }
        }

        private void ValidateRoomOperation(JObject parameters, ArchitecturalValidationResult result)
        {
            var rules = _config.Rules.Rooms;

            // Check room area
            double? area = parameters["area"]?.Value<double>();
            if (area.HasValue)
            {
                double areaSqft = area.Value;

                if (areaSqft < rules.MinAreaSqft)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "room_min_area",
                        ElementType = "room",
                        Property = "area",
                        Level = ViolationLevel.HardFail,
                        ExpectedValue = rules.MinAreaSqft,
                        ActualValue = areaSqft,
                        Reason = $"Room area ({areaSqft:F0} sqft) is below minimum ({rules.MinAreaSqft} sqft)"
                    });
                }

                // Check room-type-specific minimums
                string roomType = parameters["roomType"]?.ToString()?.ToLower() ?? "";

                if (roomType.Contains("bath") && areaSqft < rules.BathroomMinSqft)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "bathroom_min_area",
                        ElementType = "room",
                        Property = "area",
                        Level = ViolationLevel.SoftWarning,
                        ExpectedValue = rules.BathroomMinSqft,
                        ActualValue = areaSqft,
                        Reason = $"Bathroom area ({areaSqft:F0} sqft) is below recommended minimum ({rules.BathroomMinSqft} sqft)"
                    });
                }

                if (roomType.Contains("bed") && areaSqft < rules.BedroomMinSqft)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "bedroom_min_area",
                        ElementType = "room",
                        Property = "area",
                        Level = ViolationLevel.SoftWarning,
                        ExpectedValue = rules.BedroomMinSqft,
                        ActualValue = areaSqft,
                        Reason = $"Bedroom area ({areaSqft:F0} sqft) is below recommended minimum ({rules.BedroomMinSqft} sqft)"
                    });
                }

                if (roomType.Contains("kitchen") && areaSqft < rules.KitchenMinSqft)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "kitchen_min_area",
                        ElementType = "room",
                        Property = "area",
                        Level = ViolationLevel.SoftWarning,
                        ExpectedValue = rules.KitchenMinSqft,
                        ActualValue = areaSqft,
                        Reason = $"Kitchen area ({areaSqft:F0} sqft) is below recommended minimum ({rules.KitchenMinSqft} sqft)"
                    });
                }

                if (roomType.Contains("closet") && areaSqft > rules.ClosetMaxSqft)
                {
                    result.Violations.Add(new ValidationViolation
                    {
                        RuleId = "closet_max_area",
                        ElementType = "room",
                        Property = "area",
                        Level = ViolationLevel.Advisory,
                        ExpectedValue = rules.ClosetMaxSqft,
                        ActualValue = areaSqft,
                        Reason = $"Closet area ({areaSqft:F0} sqft) exceeds typical maximum ({rules.ClosetMaxSqft} sqft) - may be misclassified"
                    });
                }
            }
        }

        #region Parameter Extraction Helpers

        private double? GetLengthFromParameters(JObject parameters)
        {
            // Try various ways length might be specified
            if (parameters["length"] != null)
                return parameters["length"].Value<double>();

            // Calculate from start/end points
            var startPoint = parameters["startPoint"] as JObject ?? parameters["start"] as JObject;
            var endPoint = parameters["endPoint"] as JObject ?? parameters["end"] as JObject;

            if (startPoint != null && endPoint != null)
            {
                double x1 = startPoint["x"]?.Value<double>() ?? 0;
                double y1 = startPoint["y"]?.Value<double>() ?? 0;
                double x2 = endPoint["x"]?.Value<double>() ?? 0;
                double y2 = endPoint["y"]?.Value<double>() ?? 0;

                return Math.Sqrt(Math.Pow(x2 - x1, 2) + Math.Pow(y2 - y1, 2));
            }

            return null;
        }

        private double? GetWidthFromParameters(JObject parameters)
        {
            if (parameters["width"] != null)
                return parameters["width"].Value<double>();

            if (parameters["doorWidth"] != null)
                return parameters["doorWidth"].Value<double>();

            if (parameters["windowWidth"] != null)
                return parameters["windowWidth"].Value<double>();

            return null;
        }

        private double? GetHeightFromParameters(JObject parameters)
        {
            if (parameters["height"] != null)
                return parameters["height"].Value<double>();

            if (parameters["doorHeight"] != null)
                return parameters["doorHeight"].Value<double>();

            if (parameters["windowHeight"] != null)
                return parameters["windowHeight"].Value<double>();

            return null;
        }

        #endregion
    }
}
