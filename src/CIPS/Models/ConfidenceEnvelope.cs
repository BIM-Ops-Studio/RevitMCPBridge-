using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// Core data structure that wraps any AI decision with confidence scoring.
    /// This enables multi-pass processing where uncertain operations can be
    /// re-evaluated with additional context or escalated to human review.
    /// </summary>
    public class ConfidenceEnvelope
    {
        /// <summary>
        /// Unique identifier for this operation
        /// </summary>
        [JsonProperty("operationId")]
        public string OperationId { get; set; }

        /// <summary>
        /// The MCP method to execute (e.g., "createWall", "placeDoor")
        /// </summary>
        [JsonProperty("methodName")]
        public string MethodName { get; set; }

        /// <summary>
        /// Original parameters for the method
        /// </summary>
        [JsonProperty("parameters")]
        public JObject Parameters { get; set; }

        /// <summary>
        /// Overall confidence score (0.0 to 1.0)
        /// </summary>
        [JsonProperty("overallConfidence")]
        public double OverallConfidence { get; set; }

        /// <summary>
        /// Individual factors that contributed to the confidence score
        /// </summary>
        [JsonProperty("factors")]
        public List<ConfidenceFactor> Factors { get; set; } = new List<ConfidenceFactor>();

        /// <summary>
        /// Alternative interpretations or parameter variations
        /// </summary>
        [JsonProperty("alternatives")]
        public List<Alternative> Alternatives { get; set; } = new List<Alternative>();

        /// <summary>
        /// Current processing pass (1, 2, 3...)
        /// </summary>
        [JsonProperty("currentPass")]
        public int CurrentPass { get; set; } = 1;

        /// <summary>
        /// Current processing status
        /// </summary>
        [JsonProperty("status")]
        public ProcessingStatus Status { get; set; } = ProcessingStatus.Pending;

        /// <summary>
        /// IDs of other operations this depends on
        /// </summary>
        [JsonProperty("dependencies")]
        public List<string> Dependencies { get; set; } = new List<string>();

        /// <summary>
        /// Result from execution (if executed)
        /// </summary>
        [JsonProperty("result")]
        public JObject Result { get; set; }

        /// <summary>
        /// Error message if execution failed
        /// </summary>
        [JsonProperty("error")]
        public string Error { get; set; }

        /// <summary>
        /// Reasoning chain showing why this confidence was calculated.
        /// This is Enhancement #1: Explainable Reasoning
        /// </summary>
        [JsonProperty("reasoningChain")]
        public ReasoningChain Reasoning { get; set; }

        /// <summary>
        /// Verification report from post-execution checks.
        /// This is Enhancement #6: Verification Loops
        /// </summary>
        [JsonProperty("verificationReport")]
        public VerificationReport VerificationReport { get; set; }

        /// <summary>
        /// When this envelope was created
        /// </summary>
        [JsonProperty("createdAt")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// When this operation was processed
        /// </summary>
        [JsonProperty("processedAt")]
        public DateTime? ProcessedAt { get; set; }

        /// <summary>
        /// Workflow ID this belongs to (for batch operations)
        /// </summary>
        [JsonProperty("workflowId")]
        public string WorkflowId { get; set; }

        /// <summary>
        /// Create a new envelope with a generated ID
        /// </summary>
        public static ConfidenceEnvelope Create(string methodName, JObject parameters, string workflowId = null)
        {
            return new ConfidenceEnvelope
            {
                OperationId = $"op_{Guid.NewGuid():N}",
                MethodName = methodName,
                Parameters = parameters,
                WorkflowId = workflowId ?? $"wf_{Guid.NewGuid():N}",
                CreatedAt = DateTime.UtcNow
            };
        }

        /// <summary>
        /// Get the confidence level category
        /// </summary>
        public ConfidenceLevel GetLevel(double highThreshold = 0.85, double mediumThreshold = 0.60)
        {
            if (OverallConfidence >= highThreshold)
                return ConfidenceLevel.High;
            if (OverallConfidence >= mediumThreshold)
                return ConfidenceLevel.Medium;
            return ConfidenceLevel.Low;
        }

        /// <summary>
        /// Mark as executed with result
        /// </summary>
        public void MarkExecuted(JObject result)
        {
            Result = result;
            ProcessedAt = DateTime.UtcNow;
            Status = ProcessingStatus.Executed;
        }

        /// <summary>
        /// Mark as failed with error
        /// </summary>
        public void MarkFailed(string error)
        {
            Error = error;
            ProcessedAt = DateTime.UtcNow;
            Status = ProcessingStatus.Failed;
        }

        /// <summary>
        /// Advance to next pass
        /// </summary>
        public void AdvancePass()
        {
            CurrentPass++;
            Status = CurrentPass == 2 ? ProcessingStatus.Pass2_Queued :
                     CurrentPass == 3 ? ProcessingStatus.Pass3_Queued :
                     ProcessingStatus.InReview;
        }
    }

    /// <summary>
    /// Processing status for an operation
    /// </summary>
    public enum ProcessingStatus
    {
        Pending,
        Pass1_Queued,
        Pass1_Complete,
        Pass2_Queued,
        Pass2_Complete,
        Pass3_Queued,
        Pass3_Complete,
        Executing,
        Executed,
        Verified,
        VerificationFailed,
        NeedsVerification,
        InReview,
        Approved,
        Rejected,
        Failed,
        Skipped
    }

    /// <summary>
    /// Confidence level category
    /// </summary>
    public enum ConfidenceLevel
    {
        High,
        Medium,
        Low
    }

    /// <summary>
    /// An alternative interpretation or parameter set
    /// </summary>
    public class Alternative
    {
        [JsonProperty("description")]
        public string Description { get; set; }

        [JsonProperty("parameters")]
        public JObject Parameters { get; set; }

        [JsonProperty("confidence")]
        public double Confidence { get; set; }

        [JsonProperty("source")]
        public string Source { get; set; }  // "correction_history", "pattern_match", "ai_suggestion"
    }
}
