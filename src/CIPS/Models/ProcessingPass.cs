using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// Represents a single processing pass in the multi-pass workflow.
    /// Each pass evaluates operations with accumulated context from previous passes.
    /// </summary>
    public class ProcessingPass
    {
        /// <summary>
        /// Pass number (1, 2, 3...)
        /// </summary>
        [JsonProperty("passNumber")]
        public int PassNumber { get; set; }

        /// <summary>
        /// Confidence threshold for this pass
        /// </summary>
        [JsonProperty("threshold")]
        public double Threshold { get; set; }

        /// <summary>
        /// Context boost applied from previous passes
        /// </summary>
        [JsonProperty("contextBoost")]
        public double ContextBoost { get; set; }

        /// <summary>
        /// Operations queued for this pass
        /// </summary>
        [JsonProperty("queuedOperations")]
        public List<string> QueuedOperations { get; set; } = new List<string>();

        /// <summary>
        /// Operations executed in this pass
        /// </summary>
        [JsonProperty("executedOperations")]
        public List<string> ExecutedOperations { get; set; } = new List<string>();

        /// <summary>
        /// Operations held for next pass
        /// </summary>
        [JsonProperty("heldOperations")]
        public List<string> HeldOperations { get; set; } = new List<string>();

        /// <summary>
        /// Operations sent to human review
        /// </summary>
        [JsonProperty("reviewOperations")]
        public List<string> ReviewOperations { get; set; } = new List<string>();

        /// <summary>
        /// When this pass started
        /// </summary>
        [JsonProperty("startedAt")]
        public DateTime? StartedAt { get; set; }

        /// <summary>
        /// When this pass completed
        /// </summary>
        [JsonProperty("completedAt")]
        public DateTime? CompletedAt { get; set; }

        /// <summary>
        /// Pass status
        /// </summary>
        [JsonProperty("status")]
        public PassStatus Status { get; set; } = PassStatus.Pending;

        /// <summary>
        /// Summary of pass results
        /// </summary>
        [JsonProperty("summary")]
        public PassSummary Summary { get; set; }
    }

    /// <summary>
    /// Status of a processing pass
    /// </summary>
    public enum PassStatus
    {
        Pending,
        InProgress,
        Completed,
        Skipped
    }

    /// <summary>
    /// Summary of a pass's results
    /// </summary>
    public class PassSummary
    {
        [JsonProperty("totalOperations")]
        public int TotalOperations { get; set; }

        [JsonProperty("executedCount")]
        public int ExecutedCount { get; set; }

        [JsonProperty("heldCount")]
        public int HeldCount { get; set; }

        [JsonProperty("reviewCount")]
        public int ReviewCount { get; set; }

        [JsonProperty("failedCount")]
        public int FailedCount { get; set; }

        [JsonProperty("averageConfidence")]
        public double AverageConfidence { get; set; }

        [JsonProperty("executionTimeMs")]
        public long ExecutionTimeMs { get; set; }
    }

    /// <summary>
    /// Tracks the state of a multi-pass workflow
    /// </summary>
    public class WorkflowState
    {
        /// <summary>
        /// Unique workflow identifier
        /// </summary>
        [JsonProperty("workflowId")]
        public string WorkflowId { get; set; }

        /// <summary>
        /// Description of this workflow
        /// </summary>
        [JsonProperty("description")]
        public string Description { get; set; }

        /// <summary>
        /// All operations in this workflow
        /// </summary>
        [JsonProperty("operations")]
        public Dictionary<string, ConfidenceEnvelope> Operations { get; set; } = new Dictionary<string, ConfidenceEnvelope>();

        /// <summary>
        /// Processing passes
        /// </summary>
        [JsonProperty("passes")]
        public List<ProcessingPass> Passes { get; set; } = new List<ProcessingPass>();

        /// <summary>
        /// Current pass number
        /// </summary>
        [JsonProperty("currentPass")]
        public int CurrentPass { get; set; } = 0;

        /// <summary>
        /// Maximum passes before escalating to human review
        /// </summary>
        [JsonProperty("maxPasses")]
        public int MaxPasses { get; set; } = 3;

        /// <summary>
        /// Current workflow status
        /// </summary>
        [JsonProperty("status")]
        public WorkflowStatus Status { get; set; } = WorkflowStatus.Created;

        /// <summary>
        /// When workflow was created
        /// </summary>
        [JsonProperty("createdAt")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// When workflow was last updated
        /// </summary>
        [JsonProperty("lastUpdated")]
        public DateTime LastUpdated { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// Project context (e.g., "Vincent Apartments - Unit 3B")
        /// </summary>
        [JsonProperty("projectContext")]
        public string ProjectContext { get; set; }

        /// <summary>
        /// Source information (e.g., "floor_plan_unit_3b.pdf")
        /// </summary>
        [JsonProperty("sourceInfo")]
        public string SourceInfo { get; set; }

        /// <summary>
        /// Create a new workflow
        /// </summary>
        public static WorkflowState Create(string description = null, int maxPasses = 3)
        {
            return new WorkflowState
            {
                WorkflowId = $"wf_{Guid.NewGuid():N}",
                Description = description,
                MaxPasses = maxPasses,
                CreatedAt = DateTime.UtcNow,
                LastUpdated = DateTime.UtcNow
            };
        }

        /// <summary>
        /// Add an operation to this workflow
        /// </summary>
        public void AddOperation(ConfidenceEnvelope envelope)
        {
            envelope.WorkflowId = WorkflowId;
            Operations[envelope.OperationId] = envelope;
            LastUpdated = DateTime.UtcNow;
        }

        /// <summary>
        /// Get operations by status
        /// </summary>
        public List<ConfidenceEnvelope> GetOperationsByStatus(ProcessingStatus status)
        {
            var result = new List<ConfidenceEnvelope>();
            foreach (var op in Operations.Values)
            {
                if (op.Status == status)
                    result.Add(op);
            }
            return result;
        }
    }

    /// <summary>
    /// Workflow status
    /// </summary>
    public enum WorkflowStatus
    {
        Created,
        Pass1_InProgress,
        Pass1_Complete,
        Pass2_InProgress,
        Pass2_Complete,
        Pass3_InProgress,
        Pass3_Complete,
        AwaitingReview,
        Completed,
        Failed,
        Cancelled
    }
}
