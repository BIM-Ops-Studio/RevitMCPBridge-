using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Manages the human review queue with JSON persistence.
    /// Operations that can't be auto-resolved are queued here for human decision.
    /// </summary>
    public class ReviewQueueManager
    {
        private ReviewQueue _queue;
        private readonly string _queuePath;
        private readonly object _lock = new object();

        public ReviewQueueManager()
        {
            _queuePath = CIPSConfiguration.Instance.GetReviewQueuePath();
            LoadQueue();
        }

        /// <summary>
        /// Get the current queue
        /// </summary>
        public ReviewQueue Queue => _queue;

        /// <summary>
        /// Get count of pending items
        /// </summary>
        public int PendingCount => _queue?.Items.Count(i => i.IsPending) ?? 0;

        /// <summary>
        /// Add an envelope to the review queue
        /// </summary>
        public ReviewItem Enqueue(ConfidenceEnvelope envelope, string reason = null)
        {
            lock (_lock)
            {
                if (_queue == null)
                    _queue = CreateNewQueue();

                // Check queue size limit
                if (_queue.Items.Count >= CIPSConfiguration.Instance.ReviewQueue.MaxSize)
                {
                    // Remove oldest expired items
                    CleanExpired();

                    // If still at limit, remove oldest pending
                    if (_queue.Items.Count >= CIPSConfiguration.Instance.ReviewQueue.MaxSize)
                    {
                        var oldest = _queue.Items.OrderBy(i => i.QueuedAt).FirstOrDefault(i => i.IsPending);
                        if (oldest != null)
                        {
                            _queue.Items.Remove(oldest);
                            Log.Warning("[CIPS] Review queue at capacity, removed oldest item {Id}", oldest.ReviewId);
                        }
                    }
                }

                // Create review item
                var item = ReviewItem.FromEnvelope(envelope,
                    reason ?? $"Confidence {envelope.OverallConfidence:F2} below threshold after {envelope.CurrentPass} passes",
                    CIPSConfiguration.Instance.ReviewQueue.ExpireHours);

                // Generate questions based on confidence factors
                item.Questions = GenerateQuestions(envelope);

                // Generate options from alternatives
                item.Options = GenerateOptions(envelope);

                // Set AI recommendation
                if (envelope.Alternatives.Count > 0)
                {
                    var best = envelope.Alternatives.OrderByDescending(a => a.Confidence).FirstOrDefault();
                    if (best != null)
                    {
                        item.AIRecommendation = best.Description;
                    }
                }

                envelope.Status = ProcessingStatus.InReview;
                _queue.Items.Add(item);
                _queue.LastUpdated = DateTime.UtcNow;

                SaveQueue();

                Log.Information("[CIPS] Added {Method} to review queue. ReviewId: {ReviewId}, Confidence: {Confidence:F2}",
                    envelope.MethodName, item.ReviewId, envelope.OverallConfidence);

                return item;
            }
        }

        /// <summary>
        /// Get all pending review items
        /// </summary>
        public List<ReviewItem> GetPendingItems()
        {
            lock (_lock)
            {
                CleanExpired();
                return _queue?.Items.Where(i => i.IsPending).OrderByDescending(i => i.Priority).ThenBy(i => i.QueuedAt).ToList()
                    ?? new List<ReviewItem>();
            }
        }

        /// <summary>
        /// Get a specific review item by ID
        /// </summary>
        public ReviewItem GetItem(string reviewId)
        {
            lock (_lock)
            {
                return _queue?.Items.FirstOrDefault(i => i.ReviewId == reviewId);
            }
        }

        /// <summary>
        /// Submit a review decision
        /// </summary>
        public bool SubmitDecision(string reviewId, ReviewDecision decision,
            Newtonsoft.Json.Linq.JObject modifiedParams = null, string notes = null)
        {
            lock (_lock)
            {
                var item = GetItem(reviewId);
                if (item == null)
                {
                    Log.Warning("[CIPS] Review item not found: {ReviewId}", reviewId);
                    return false;
                }

                if (!item.IsPending)
                {
                    Log.Warning("[CIPS] Review item already processed: {ReviewId}", reviewId);
                    return false;
                }

                item.ApplyDecision(decision, modifiedParams, notes);
                _queue.LastUpdated = DateTime.UtcNow;
                SaveQueue();

                Log.Information("[CIPS] Review decision submitted. ReviewId: {ReviewId}, Decision: {Decision}",
                    reviewId, decision);

                return true;
            }
        }

        /// <summary>
        /// Get items for a specific workflow
        /// </summary>
        public List<ReviewItem> GetWorkflowItems(string workflowId)
        {
            lock (_lock)
            {
                return _queue?.Items.Where(i => i.Envelope?.WorkflowId == workflowId).ToList()
                    ?? new List<ReviewItem>();
            }
        }

        /// <summary>
        /// Remove expired items
        /// </summary>
        public int CleanExpired()
        {
            lock (_lock)
            {
                if (_queue == null) return 0;

                var expired = _queue.Items.Where(i => i.IsExpired).ToList();
                foreach (var item in expired)
                {
                    _queue.Items.Remove(item);
                }

                if (expired.Count > 0)
                {
                    _queue.LastUpdated = DateTime.UtcNow;
                    SaveQueue();
                    Log.Information("[CIPS] Cleaned {Count} expired review items", expired.Count);
                }

                return expired.Count;
            }
        }

        /// <summary>
        /// Get queue statistics
        /// </summary>
        public QueueStats GetStats()
        {
            lock (_lock)
            {
                if (_queue == null)
                    return new QueueStats();

                return new QueueStats
                {
                    TotalItems = _queue.Items.Count,
                    PendingItems = _queue.Items.Count(i => i.IsPending),
                    ApprovedItems = _queue.Items.Count(i => i.Decision == ReviewDecision.Approve),
                    ModifiedItems = _queue.Items.Count(i => i.Decision == ReviewDecision.Modify),
                    RejectedItems = _queue.Items.Count(i => i.Decision == ReviewDecision.Reject),
                    ExpiredItems = _queue.Items.Count(i => i.IsExpired),
                    AverageConfidence = _queue.Items.Where(i => i.Envelope != null).Average(i => i.Envelope.OverallConfidence),
                    OldestPending = _queue.Items.Where(i => i.IsPending).Min(i => (DateTime?)i.QueuedAt)
                };
            }
        }

        /// <summary>
        /// Generate questions based on confidence factors
        /// </summary>
        private List<string> GenerateQuestions(ConfidenceEnvelope envelope)
        {
            var questions = new List<string>();

            foreach (var factor in envelope.Factors.Where(f => f.Score < 0.7))
            {
                switch (factor.FactorName)
                {
                    case ConfidenceFactorNames.ParameterCompleteness:
                        questions.Add($"Missing parameters: {factor.Reason}");
                        break;
                    case ConfidenceFactorNames.TypeValidation:
                        questions.Add($"Element validation issue: {factor.Reason}");
                        break;
                    case ConfidenceFactorNames.CorrectionHistory:
                        questions.Add($"This operation has failed before: {factor.Reason}");
                        break;
                    case ConfidenceFactorNames.PreFlightCheck:
                        questions.Add($"PreFlight check warning: {factor.Reason}");
                        break;
                    default:
                        if (!string.IsNullOrEmpty(factor.Reason))
                            questions.Add(factor.Reason);
                        break;
                }
            }

            if (questions.Count == 0)
            {
                questions.Add($"Overall confidence ({envelope.OverallConfidence:F2}) is below threshold. Please verify.");
            }

            return questions;
        }

        /// <summary>
        /// Generate options from alternatives
        /// </summary>
        private List<ReviewOption> GenerateOptions(ConfidenceEnvelope envelope)
        {
            var options = new List<ReviewOption>();

            // Add "proceed as-is" option
            options.Add(new ReviewOption
            {
                Id = "approve",
                Label = "Approve as proposed",
                Description = $"Execute {envelope.MethodName} with current parameters",
                Parameters = envelope.Parameters,
                IsRecommended = envelope.OverallConfidence >= 0.5
            });

            // Add alternatives as options
            int altIndex = 0;
            foreach (var alt in envelope.Alternatives.Take(3))
            {
                options.Add(new ReviewOption
                {
                    Id = $"alt_{altIndex++}",
                    Label = alt.Description,
                    Description = $"From {alt.Source}, confidence: {alt.Confidence:F2}",
                    Parameters = alt.Parameters,
                    IsRecommended = alt.Confidence > envelope.OverallConfidence
                });
            }

            // Add reject option
            options.Add(new ReviewOption
            {
                Id = "reject",
                Label = "Reject / Skip",
                Description = "Do not execute this operation"
            });

            return options;
        }

        /// <summary>
        /// Load queue from disk
        /// </summary>
        private void LoadQueue()
        {
            try
            {
                if (File.Exists(_queuePath))
                {
                    var json = File.ReadAllText(_queuePath);
                    _queue = JsonConvert.DeserializeObject<ReviewQueue>(json);
                    Log.Debug("[CIPS] Loaded review queue with {Count} items", _queue?.Items.Count ?? 0);
                }
                else
                {
                    _queue = CreateNewQueue();
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[CIPS] Error loading review queue, creating new");
                _queue = CreateNewQueue();
            }
        }

        /// <summary>
        /// Save queue to disk
        /// </summary>
        private void SaveQueue()
        {
            try
            {
                var json = JsonConvert.SerializeObject(_queue, Formatting.Indented);
                File.WriteAllText(_queuePath, json);
                Log.Debug("[CIPS] Saved review queue with {Count} items", _queue?.Items.Count ?? 0);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[CIPS] Error saving review queue");
            }
        }

        /// <summary>
        /// Create a new empty queue
        /// </summary>
        private ReviewQueue CreateNewQueue()
        {
            return new ReviewQueue
            {
                QueueId = $"queue_{Guid.NewGuid():N}",
                Items = new List<ReviewItem>(),
                CreatedAt = DateTime.UtcNow,
                LastUpdated = DateTime.UtcNow
            };
        }
    }

    /// <summary>
    /// Queue statistics
    /// </summary>
    public class QueueStats
    {
        public int TotalItems { get; set; }
        public int PendingItems { get; set; }
        public int ApprovedItems { get; set; }
        public int ModifiedItems { get; set; }
        public int RejectedItems { get; set; }
        public int ExpiredItems { get; set; }
        public double AverageConfidence { get; set; }
        public DateTime? OldestPending { get; set; }
    }
}
