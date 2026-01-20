using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// An item in the human review queue.
    /// Contains all context needed for a human to make a decision.
    /// </summary>
    public class ReviewItem
    {
        /// <summary>
        /// Unique identifier for this review item
        /// </summary>
        [JsonProperty("reviewId")]
        public string ReviewId { get; set; }

        /// <summary>
        /// The confidence envelope being reviewed
        /// </summary>
        [JsonProperty("envelope")]
        public ConfidenceEnvelope Envelope { get; set; }

        /// <summary>
        /// Why this item needs human review
        /// </summary>
        [JsonProperty("reason")]
        public string Reason { get; set; }

        /// <summary>
        /// Specific questions for the reviewer
        /// </summary>
        [JsonProperty("questions")]
        public List<string> Questions { get; set; } = new List<string>();

        /// <summary>
        /// Suggested options for the reviewer
        /// </summary>
        [JsonProperty("options")]
        public List<ReviewOption> Options { get; set; } = new List<ReviewOption>();

        /// <summary>
        /// AI's recommended option (if any)
        /// </summary>
        [JsonProperty("aiRecommendation")]
        public string AIRecommendation { get; set; }

        /// <summary>
        /// When this item was queued
        /// </summary>
        [JsonProperty("queuedAt")]
        public DateTime QueuedAt { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// When this item expires (optional)
        /// </summary>
        [JsonProperty("expiresAt")]
        public DateTime? ExpiresAt { get; set; }

        /// <summary>
        /// When this item was reviewed (null if pending)
        /// </summary>
        [JsonProperty("reviewedAt")]
        public DateTime? ReviewedAt { get; set; }

        /// <summary>
        /// The reviewer's decision
        /// </summary>
        [JsonProperty("decision")]
        public ReviewDecision? Decision { get; set; }

        /// <summary>
        /// Modified parameters if reviewer chose to modify
        /// </summary>
        [JsonProperty("modifiedParameters")]
        public JObject ModifiedParameters { get; set; }

        /// <summary>
        /// Reviewer's notes
        /// </summary>
        [JsonProperty("reviewerNotes")]
        public string ReviewerNotes { get; set; }

        /// <summary>
        /// Priority level (higher = more urgent)
        /// </summary>
        [JsonProperty("priority")]
        public int Priority { get; set; } = 0;

        /// <summary>
        /// Check if this item has expired
        /// </summary>
        [JsonIgnore]
        public bool IsExpired => ExpiresAt.HasValue && DateTime.UtcNow > ExpiresAt.Value;

        /// <summary>
        /// Check if this item is pending review
        /// </summary>
        [JsonIgnore]
        public bool IsPending => !ReviewedAt.HasValue && !IsExpired;

        /// <summary>
        /// Create a new review item from an envelope
        /// </summary>
        public static ReviewItem FromEnvelope(ConfidenceEnvelope envelope, string reason, int expireHours = 24)
        {
            return new ReviewItem
            {
                ReviewId = $"rev_{Guid.NewGuid():N}",
                Envelope = envelope,
                Reason = reason,
                QueuedAt = DateTime.UtcNow,
                ExpiresAt = DateTime.UtcNow.AddHours(expireHours)
            };
        }

        /// <summary>
        /// Apply a review decision
        /// </summary>
        public void ApplyDecision(ReviewDecision decision, JObject modifiedParams = null, string notes = null)
        {
            Decision = decision;
            ReviewedAt = DateTime.UtcNow;
            ModifiedParameters = modifiedParams;
            ReviewerNotes = notes;

            // Update envelope status based on decision
            switch (decision)
            {
                case ReviewDecision.Approve:
                    Envelope.Status = ProcessingStatus.Approved;
                    break;
                case ReviewDecision.Modify:
                    Envelope.Status = ProcessingStatus.Approved;
                    if (modifiedParams != null)
                        Envelope.Parameters = modifiedParams;
                    break;
                case ReviewDecision.Reject:
                    Envelope.Status = ProcessingStatus.Rejected;
                    break;
                case ReviewDecision.Skip:
                    Envelope.Status = ProcessingStatus.Skipped;
                    break;
            }
        }
    }

    /// <summary>
    /// A suggested option for the reviewer
    /// </summary>
    public class ReviewOption
    {
        [JsonProperty("id")]
        public string Id { get; set; }

        [JsonProperty("label")]
        public string Label { get; set; }

        [JsonProperty("description")]
        public string Description { get; set; }

        [JsonProperty("parameters")]
        public JObject Parameters { get; set; }

        [JsonProperty("isRecommended")]
        public bool IsRecommended { get; set; }
    }

    /// <summary>
    /// Possible decisions a reviewer can make
    /// </summary>
    public enum ReviewDecision
    {
        /// <summary>
        /// Approve the operation as proposed
        /// </summary>
        Approve,

        /// <summary>
        /// Approve with modified parameters
        /// </summary>
        Modify,

        /// <summary>
        /// Reject this operation entirely
        /// </summary>
        Reject,

        /// <summary>
        /// Skip for now, decide later
        /// </summary>
        Skip
    }

    /// <summary>
    /// The human review queue
    /// </summary>
    public class ReviewQueue
    {
        [JsonProperty("queueId")]
        public string QueueId { get; set; }

        [JsonProperty("workflowId")]
        public string WorkflowId { get; set; }

        [JsonProperty("projectContext")]
        public string ProjectContext { get; set; }

        [JsonProperty("items")]
        public List<ReviewItem> Items { get; set; } = new List<ReviewItem>();

        [JsonProperty("createdAt")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        [JsonProperty("lastUpdated")]
        public DateTime LastUpdated { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// Get count of pending items
        /// </summary>
        [JsonIgnore]
        public int PendingCount => Items.FindAll(i => i.IsPending).Count;
    }
}
