using Newtonsoft.Json;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// Represents a single factor that contributes to the overall confidence score.
    /// Each factor has a score (0-1), a weight (how much it contributes), and a reason.
    /// </summary>
    public class ConfidenceFactor
    {
        /// <summary>
        /// Name of this factor (e.g., "ParameterValidation", "CorrectionHistory")
        /// </summary>
        [JsonProperty("factorName")]
        public string FactorName { get; set; }

        /// <summary>
        /// Score for this factor (0.0 to 1.0)
        /// </summary>
        [JsonProperty("score")]
        public double Score { get; set; }

        /// <summary>
        /// Weight of this factor in overall calculation (should sum to 1.0 across all factors)
        /// </summary>
        [JsonProperty("weight")]
        public double Weight { get; set; }

        /// <summary>
        /// Human-readable reason for this score
        /// </summary>
        [JsonProperty("reason")]
        public string Reason { get; set; }

        /// <summary>
        /// Additional details (optional)
        /// </summary>
        [JsonProperty("details")]
        public object Details { get; set; }

        /// <summary>
        /// Weighted contribution to overall score
        /// </summary>
        [JsonIgnore]
        public double WeightedScore => Score * Weight;

        /// <summary>
        /// Create a factor with full score (1.0)
        /// </summary>
        public static ConfidenceFactor Pass(string name, double weight, string reason)
        {
            return new ConfidenceFactor
            {
                FactorName = name,
                Score = 1.0,
                Weight = weight,
                Reason = reason
            };
        }

        /// <summary>
        /// Create a factor with zero score (0.0)
        /// </summary>
        public static ConfidenceFactor Fail(string name, double weight, string reason)
        {
            return new ConfidenceFactor
            {
                FactorName = name,
                Score = 0.0,
                Weight = weight,
                Reason = reason
            };
        }

        /// <summary>
        /// Create a factor with partial score
        /// </summary>
        public static ConfidenceFactor Partial(string name, double weight, double score, string reason)
        {
            return new ConfidenceFactor
            {
                FactorName = name,
                Score = score,
                Weight = weight,
                Reason = reason
            };
        }
    }

    /// <summary>
    /// Standard factor names used in confidence calculation
    /// </summary>
    public static class ConfidenceFactorNames
    {
        public const string ParameterCompleteness = "ParameterCompleteness";
        public const string TypeValidation = "TypeValidation";
        public const string ElementExists = "ElementExists";
        public const string CorrectionHistory = "CorrectionHistory";
        public const string PatternMatch = "PatternMatch";
        public const string PreFlightCheck = "PreFlightCheck";
        public const string ContextAlignment = "ContextAlignment";
        public const string SourceClarity = "SourceClarity";
        public const string AlternativeSpread = "AlternativeSpread";
        public const string ArchitecturalValidation = "ArchitecturalValidation";
    }

    /// <summary>
    /// Standard weights for confidence factors.
    /// Weights are adjusted to include Architectural Validation while summing to 1.0
    /// </summary>
    public static class ConfidenceWeights
    {
        public const double PreFlightCheck = 0.22;
        public const double CorrectionHistory = 0.22;
        public const double ParameterCompleteness = 0.18;
        public const double TypeValidation = 0.14;
        public const double PatternMatch = 0.14;
        public const double ArchitecturalValidation = 0.10;
    }
}
