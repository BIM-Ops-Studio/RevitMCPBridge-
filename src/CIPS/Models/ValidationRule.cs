using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// Violation severity levels for architectural validation
    /// </summary>
    public enum ViolationLevel
    {
        /// <summary>Cannot proceed - physically impossible or critically wrong</summary>
        HardFail,
        /// <summary>Unusual but possible - flag for review</summary>
        SoftWarning,
        /// <summary>Technically valid but unusual - log for awareness</summary>
        Advisory
    }

    /// <summary>
    /// A single architectural validation rule
    /// </summary>
    public class ValidationRule
    {
        [JsonProperty("ruleId")]
        public string RuleId { get; set; }

        [JsonProperty("elementType")]
        public string ElementType { get; set; }  // wall, door, window, room

        [JsonProperty("property")]
        public string Property { get; set; }      // length, width, area, thickness

        [JsonProperty("operator")]
        public string Operator { get; set; }      // min, max, range, equals, oneOf

        [JsonProperty("value")]
        public double Value { get; set; }

        [JsonProperty("maxValue")]
        public double? MaxValue { get; set; }     // For range operator

        [JsonProperty("validValues")]
        public List<double> ValidValues { get; set; }  // For oneOf operator

        [JsonProperty("level")]
        public ViolationLevel Level { get; set; } = ViolationLevel.SoftWarning;

        [JsonProperty("message")]
        public string Message { get; set; }       // Custom message template

        /// <summary>
        /// Check if a value violates this rule
        /// </summary>
        public ValidationViolation Check(double actualValue)
        {
            bool violated = false;
            string reason = "";

            switch (Operator?.ToLower())
            {
                case "min":
                    violated = actualValue < Value;
                    reason = $"{Property} ({actualValue:F2}) is below minimum ({Value:F2})";
                    break;

                case "max":
                    violated = actualValue > Value;
                    reason = $"{Property} ({actualValue:F2}) exceeds maximum ({Value:F2})";
                    break;

                case "range":
                    violated = actualValue < Value || actualValue > (MaxValue ?? Value);
                    reason = $"{Property} ({actualValue:F2}) is outside range ({Value:F2} - {MaxValue:F2})";
                    break;

                case "equals":
                    violated = Math.Abs(actualValue - Value) > 0.001;
                    reason = $"{Property} ({actualValue:F2}) must equal ({Value:F2})";
                    break;

                case "oneof":
                    if (ValidValues != null && ValidValues.Count > 0)
                    {
                        violated = !ValidValues.Exists(v => Math.Abs(v - actualValue) < 0.001);
                        reason = $"{Property} ({actualValue:F2}) must be one of [{string.Join(", ", ValidValues)}]";
                    }
                    break;
            }

            if (violated)
            {
                return new ValidationViolation
                {
                    RuleId = RuleId,
                    ElementType = ElementType,
                    Property = Property,
                    Level = Level,
                    ExpectedValue = Value,
                    ActualValue = actualValue,
                    Reason = string.IsNullOrEmpty(Message) ? reason : Message
                };
            }

            return null;
        }
    }

    /// <summary>
    /// A violation detected by a validation rule
    /// </summary>
    public class ValidationViolation
    {
        [JsonProperty("ruleId")]
        public string RuleId { get; set; }

        [JsonProperty("elementType")]
        public string ElementType { get; set; }

        [JsonProperty("property")]
        public string Property { get; set; }

        [JsonProperty("level")]
        public ViolationLevel Level { get; set; }

        [JsonProperty("expectedValue")]
        public double ExpectedValue { get; set; }

        [JsonProperty("actualValue")]
        public double ActualValue { get; set; }

        [JsonProperty("reason")]
        public string Reason { get; set; }
    }

    /// <summary>
    /// Result of validating an operation against architectural rules
    /// </summary>
    public class ArchitecturalValidationResult
    {
        [JsonProperty("passed")]
        public bool Passed => HardFailCount == 0;

        [JsonProperty("score")]
        public double Score { get; set; } = 1.0;

        [JsonProperty("violations")]
        public List<ValidationViolation> Violations { get; set; } = new List<ValidationViolation>();

        [JsonProperty("hardFailCount")]
        public int HardFailCount => Violations?.FindAll(v => v.Level == ViolationLevel.HardFail).Count ?? 0;

        [JsonProperty("warningCount")]
        public int WarningCount => Violations?.FindAll(v => v.Level == ViolationLevel.SoftWarning).Count ?? 0;

        [JsonProperty("advisoryCount")]
        public int AdvisoryCount => Violations?.FindAll(v => v.Level == ViolationLevel.Advisory).Count ?? 0;

        [JsonProperty("summary")]
        public string Summary
        {
            get
            {
                if (Violations == null || Violations.Count == 0)
                    return "All architectural rules passed";

                var parts = new List<string>();
                if (HardFailCount > 0) parts.Add($"{HardFailCount} hard fail(s)");
                if (WarningCount > 0) parts.Add($"{WarningCount} warning(s)");
                if (AdvisoryCount > 0) parts.Add($"{AdvisoryCount} advisory");

                return string.Join(", ", parts);
            }
        }

        /// <summary>
        /// Calculate score based on violations (1.0 = perfect, 0.0 = completely failed)
        /// </summary>
        public void CalculateScore()
        {
            if (Violations == null || Violations.Count == 0)
            {
                Score = 1.0;
                return;
            }

            // Hard fails reduce score by 0.3 each
            // Warnings reduce score by 0.1 each
            // Advisories reduce score by 0.02 each
            double penalty = (HardFailCount * 0.3) + (WarningCount * 0.1) + (AdvisoryCount * 0.02);
            Score = Math.Max(0.0, 1.0 - penalty);
        }
    }

    /// <summary>
    /// Configuration for architectural validation rules
    /// </summary>
    public class ValidationRulesConfig
    {
        [JsonProperty("enabled")]
        public bool Enabled { get; set; } = true;

        [JsonProperty("rules")]
        public ValidationRulesSet Rules { get; set; } = new ValidationRulesSet();
    }

    /// <summary>
    /// Set of rules organized by element type
    /// </summary>
    public class ValidationRulesSet
    {
        [JsonProperty("walls")]
        public WallValidationRules Walls { get; set; } = new WallValidationRules();

        [JsonProperty("doors")]
        public DoorValidationRules Doors { get; set; } = new DoorValidationRules();

        [JsonProperty("windows")]
        public WindowValidationRules Windows { get; set; } = new WindowValidationRules();

        [JsonProperty("rooms")]
        public RoomValidationRules Rooms { get; set; } = new RoomValidationRules();
    }

    public class WallValidationRules
    {
        [JsonProperty("minLengthInches")]
        public double MinLengthInches { get; set; } = 6;

        [JsonProperty("maxLengthFeet")]
        public double MaxLengthFeet { get; set; } = 100;

        [JsonProperty("validThicknessesInches")]
        public List<double> ValidThicknessesInches { get; set; } = new List<double> { 4, 6, 8, 10, 12 };

        [JsonProperty("maxUnsupportedSpanFeet")]
        public double MaxUnsupportedSpanFeet { get; set; } = 30;
    }

    public class DoorValidationRules
    {
        [JsonProperty("minWidthInches")]
        public double MinWidthInches { get; set; } = 24;

        [JsonProperty("maxWidthInches")]
        public double MaxWidthInches { get; set; } = 48;

        [JsonProperty("standardWidthsInches")]
        public List<double> StandardWidthsInches { get; set; } = new List<double> { 28, 30, 32, 34, 36 };

        [JsonProperty("minHeightInches")]
        public double MinHeightInches { get; set; } = 78;

        [JsonProperty("maxHeightInches")]
        public double MaxHeightInches { get; set; } = 96;

        [JsonProperty("minDistanceFromCornerInches")]
        public double MinDistanceFromCornerInches { get; set; } = 4;
    }

    public class WindowValidationRules
    {
        [JsonProperty("minWidthInches")]
        public double MinWidthInches { get; set; } = 12;

        [JsonProperty("maxWidthInches")]
        public double MaxWidthInches { get; set; } = 120;

        [JsonProperty("minHeightInches")]
        public double MinHeightInches { get; set; } = 12;

        [JsonProperty("minSillHeightInches")]
        public double MinSillHeightInches { get; set; } = 18;

        [JsonProperty("maxSillHeightInches")]
        public double MaxSillHeightInches { get; set; } = 48;
    }

    public class RoomValidationRules
    {
        [JsonProperty("minAreaSqft")]
        public double MinAreaSqft { get; set; } = 25;

        [JsonProperty("minDimensionFeet")]
        public double MinDimensionFeet { get; set; } = 4;

        [JsonProperty("bathroomMinSqft")]
        public double BathroomMinSqft { get; set; } = 35;

        [JsonProperty("bedroomMinSqft")]
        public double BedroomMinSqft { get; set; } = 70;

        [JsonProperty("closetMaxSqft")]
        public double ClosetMaxSqft { get; set; } = 100;

        [JsonProperty("kitchenMinSqft")]
        public double KitchenMinSqft { get; set; } = 50;

        [JsonProperty("ceilingHeightMinFeet")]
        public double CeilingHeightMinFeet { get; set; } = 8;

        [JsonProperty("ceilingHeightMaxFeet")]
        public double CeilingHeightMaxFeet { get; set; } = 12;
    }
}
