using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// Records a human decision for learning purposes.
    /// Over time, these records help improve confidence scoring accuracy.
    /// </summary>
    public class FeedbackRecord
    {
        /// <summary>
        /// Unique identifier for this feedback record
        /// </summary>
        [JsonProperty("feedbackId")]
        public string FeedbackId { get; set; }

        /// <summary>
        /// The operation ID this feedback relates to
        /// </summary>
        [JsonProperty("operationId")]
        public string OperationId { get; set; }

        /// <summary>
        /// The MCP method name
        /// </summary>
        [JsonProperty("methodName")]
        public string MethodName { get; set; }

        /// <summary>
        /// Original parameters proposed by AI
        /// </summary>
        [JsonProperty("originalParameters")]
        public JObject OriginalParameters { get; set; }

        /// <summary>
        /// Parameters after human modification (may be same as original)
        /// </summary>
        [JsonProperty("approvedParameters")]
        public JObject ApprovedParameters { get; set; }

        /// <summary>
        /// AI's original confidence score
        /// </summary>
        [JsonProperty("originalConfidence")]
        public double OriginalConfidence { get; set; }

        /// <summary>
        /// The human's decision
        /// </summary>
        [JsonProperty("humanDecision")]
        public ReviewDecision HumanDecision { get; set; }

        /// <summary>
        /// Whether the AI was correct (approved without modification)
        /// </summary>
        [JsonProperty("aiWasCorrect")]
        public bool AIWasCorrect { get; set; }

        /// <summary>
        /// Human's rationale for their decision
        /// </summary>
        [JsonProperty("rationale")]
        public string Rationale { get; set; }

        /// <summary>
        /// Key characteristics of the operation for pattern matching
        /// </summary>
        [JsonProperty("characteristics")]
        public Dictionary<string, object> Characteristics { get; set; } = new Dictionary<string, object>();

        /// <summary>
        /// When this feedback was recorded
        /// </summary>
        [JsonProperty("recordedAt")]
        public DateTime RecordedAt { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// Whether this has been applied to learning
        /// </summary>
        [JsonProperty("appliedToLearning")]
        public bool AppliedToLearning { get; set; }

        /// <summary>
        /// Create a feedback record from a review item
        /// </summary>
        public static FeedbackRecord FromReviewItem(ReviewItem reviewItem)
        {
            var aiWasCorrect = reviewItem.Decision == ReviewDecision.Approve;

            return new FeedbackRecord
            {
                FeedbackId = $"fb_{Guid.NewGuid():N}",
                OperationId = reviewItem.Envelope.OperationId,
                MethodName = reviewItem.Envelope.MethodName,
                OriginalParameters = reviewItem.Envelope.Parameters,
                ApprovedParameters = reviewItem.ModifiedParameters ?? reviewItem.Envelope.Parameters,
                OriginalConfidence = reviewItem.Envelope.OverallConfidence,
                HumanDecision = reviewItem.Decision ?? ReviewDecision.Skip,
                AIWasCorrect = aiWasCorrect,
                Rationale = reviewItem.ReviewerNotes,
                RecordedAt = DateTime.UtcNow
            };
        }
    }

    /// <summary>
    /// Summary statistics for feedback learning
    /// </summary>
    public class FeedbackStats
    {
        [JsonProperty("methodName")]
        public string MethodName { get; set; }

        [JsonProperty("totalFeedback")]
        public int TotalFeedback { get; set; }

        [JsonProperty("approvedCount")]
        public int ApprovedCount { get; set; }

        [JsonProperty("modifiedCount")]
        public int ModifiedCount { get; set; }

        [JsonProperty("rejectedCount")]
        public int RejectedCount { get; set; }

        [JsonProperty("averageOriginalConfidence")]
        public double AverageOriginalConfidence { get; set; }

        [JsonProperty("accuracyRate")]
        public double AccuracyRate { get; set; }

        [JsonProperty("suggestedThresholdAdjustment")]
        public double SuggestedThresholdAdjustment { get; set; }
    }

    /// <summary>
    /// A learned pattern from feedback or session learning.
    /// Enhanced for Enhancement #5: Session Learning
    /// </summary>
    public class LearnedPattern
    {
        [JsonProperty("patternId")]
        public string PatternId { get; set; }

        [JsonProperty("methodName")]
        public string MethodName { get; set; }

        /// <summary>
        /// Alias for MethodName - method or "all" for universal patterns
        /// </summary>
        [JsonProperty("appliesTo")]
        public string AppliesTo
        {
            get => MethodName;
            set => MethodName = value;
        }

        [JsonProperty("description")]
        public string Description { get; set; }

        /// <summary>
        /// Where this pattern was learned from (e.g., "Human decision on O03")
        /// </summary>
        [JsonProperty("learnedFrom")]
        public string LearnedFrom { get; set; }

        /// <summary>
        /// Conditions that trigger this pattern (e.g., parameter values, ranges)
        /// </summary>
        [JsonProperty("conditions")]
        public Dictionary<string, object> Conditions { get; set; } = new Dictionary<string, object>();

        /// <summary>
        /// How much to adjust confidence when pattern matches
        /// </summary>
        [JsonProperty("confidenceAdjustment")]
        public double ConfidenceAdjustment { get; set; }

        /// <summary>
        /// How many feedback records support this pattern
        /// </summary>
        [JsonProperty("sampleCount")]
        public int SampleCount { get; set; }

        /// <summary>
        /// How many times this pattern has been applied
        /// </summary>
        [JsonProperty("timesApplied")]
        public int TimesApplied { get; set; }

        [JsonProperty("createdAt")]
        public DateTime CreatedAt { get; set; }

        [JsonProperty("lastUpdated")]
        public DateTime LastUpdated { get; set; }

        /// <summary>
        /// Check if this pattern matches the given parameters
        /// </summary>
        public bool Matches(JObject parameters)
        {
            if (Conditions == null || Conditions.Count == 0)
                return false;

            foreach (var condition in Conditions)
            {
                var paramValue = parameters[condition.Key];
                if (paramValue == null)
                    return false;

                // Simple equality check
                var conditionValue = condition.Value?.ToString();
                var paramStrValue = paramValue.ToString();

                if (!string.Equals(conditionValue, paramStrValue, StringComparison.OrdinalIgnoreCase))
                    return false;
            }

            TimesApplied++;
            return true;
        }

        /// <summary>
        /// Create a pattern from a human review decision (Enhancement #5)
        /// </summary>
        public static LearnedPattern FromReviewDecision(ReviewItem item, ReviewDecision decision)
        {
            var pattern = new LearnedPattern
            {
                PatternId = Guid.NewGuid().ToString(),
                LearnedFrom = $"Human {decision} on {item.ReviewId}",
                AppliesTo = item.Envelope?.MethodName ?? "all",
                CreatedAt = DateTime.UtcNow
            };

            // Extract conditions from the parameters
            if (item.Envelope?.Parameters != null)
            {
                foreach (var prop in item.Envelope.Parameters.Properties())
                {
                    // Only include "structural" parameters that define the pattern
                    if (IsPatternRelevantParameter(prop.Name))
                    {
                        pattern.Conditions[prop.Name] = prop.Value.ToString();
                    }
                }
            }

            // Set confidence adjustment based on decision
            switch (decision)
            {
                case ReviewDecision.Approve:
                    pattern.ConfidenceAdjustment = 0.15;
                    pattern.Description = "Similar operations approved by user";
                    break;
                case ReviewDecision.Modify:
                    pattern.ConfidenceAdjustment = 0.05;
                    pattern.Description = "Similar operations required modification";
                    break;
                case ReviewDecision.Reject:
                    pattern.ConfidenceAdjustment = -0.20;
                    pattern.Description = "Similar operations rejected by user";
                    break;
            }

            return pattern;
        }

        private static bool IsPatternRelevantParameter(string paramName)
        {
            // Parameters that help identify patterns
            var relevantParams = new[]
            {
                "wallTypeId", "wallTypeName", "doorTypeId", "windowTypeId",
                "roomType", "levelId", "levelName", "thickness", "width", "height"
            };

            return relevantParams.Any(p => paramName.Equals(p, StringComparison.OrdinalIgnoreCase));
        }
    }
}
