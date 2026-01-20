using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Learns from human review decisions to improve future confidence scoring.
    /// Stores feedback history and extracts patterns for threshold adjustment.
    /// Enhanced with Session Learning (Enhancement #5)
    /// </summary>
    public class FeedbackLearner
    {
        private List<FeedbackRecord> _feedbackHistory;
        private List<LearnedPattern> _patterns;
        private readonly string _historyPath;
        private readonly object _lock = new object();

        /// <summary>
        /// Current session context for session-specific learning (Enhancement #5)
        /// </summary>
        public SessionContext CurrentSession { get; private set; }

        public FeedbackLearner()
        {
            _historyPath = CIPSConfiguration.Instance.GetFeedbackHistoryPath();
            Load();
        }

        /// <summary>
        /// Record a human review decision
        /// </summary>
        public void RecordFeedback(ReviewItem reviewItem)
        {
            if (reviewItem?.Envelope == null || !reviewItem.Decision.HasValue)
                return;

            lock (_lock)
            {
                var record = FeedbackRecord.FromReviewItem(reviewItem);

                // Extract characteristics for pattern matching
                record.Characteristics = ExtractCharacteristics(reviewItem.Envelope);

                _feedbackHistory.Add(record);
                Save();

                Log.Information("[CIPS] Recorded feedback for {Method}. AICorrect: {Correct}",
                    record.MethodName, record.AIWasCorrect);

                // Try to extract patterns if we have enough samples
                TryExtractPatterns(record.MethodName);

                // Sync to Memory MCP if AI was wrong
                if (!record.AIWasCorrect)
                {
                    SyncCorrectionToMemoryMCP(record, reviewItem);
                }
            }
        }

        /// <summary>
        /// Sync a correction to the Memory MCP for cross-session persistence
        /// </summary>
        private void SyncCorrectionToMemoryMCP(FeedbackRecord record, ReviewItem reviewItem)
        {
            try
            {
                var memoryBridge = MemoryMCPBridge.Instance;
                if (!memoryBridge.IsAvailable)
                    return;

                var whatClaudeSaid = $"Method {record.MethodName} with confidence {record.OriginalConfidence:P0}";
                var whatWasWrong = record.HumanDecision == ReviewDecision.Reject
                    ? "AI action was rejected by user"
                    : "AI action required modification by user";
                var correctApproach = reviewItem.ModifiedParameters != null
                    ? $"Use modified parameters: {reviewItem.ModifiedParameters}"
                    : reviewItem.ReviewerNotes ?? "Follow user's manual approach";

                // Fire and forget - don't block feedback recording
                _ = memoryBridge.StoreCorrectionAsync(
                    whatClaudeSaid,
                    whatWasWrong,
                    correctApproach,
                    "revit-cips"
                );

                Log.Debug("[CIPS] Syncing correction to Memory MCP for {Method}", record.MethodName);
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[CIPS] Failed to sync correction to Memory MCP: {Error}", ex.Message);
            }
        }

        /// <summary>
        /// Get confidence adjustment based on feedback patterns
        /// </summary>
        public double GetConfidenceAdjustment(string methodName, JObject parameters)
        {
            lock (_lock)
            {
                var matchingPatterns = GetMatchingPatterns(methodName, parameters);
                if (matchingPatterns.Count == 0)
                    return 0;

                // Average the adjustments from matching patterns
                var adjustment = matchingPatterns.Average(p => p.ConfidenceAdjustment);

                // Clamp to configured maximum
                var maxAdj = CIPSConfiguration.Instance.Feedback.MaxAdjustment;
                return Math.Max(-maxAdj, Math.Min(maxAdj, adjustment));
            }
        }

        /// <summary>
        /// Get patterns that match the given operation
        /// </summary>
        public List<LearnedPattern> GetMatchingPatterns(string methodName, JObject parameters)
        {
            lock (_lock)
            {
                if (_patterns == null || _patterns.Count == 0)
                    return new List<LearnedPattern>();

                return _patterns
                    .Where(p => p.MethodName.Equals(methodName, StringComparison.OrdinalIgnoreCase))
                    .Where(p => MatchesConditions(p.Conditions, parameters))
                    .ToList();
            }
        }

        /// <summary>
        /// Get statistics for a specific method
        /// </summary>
        public FeedbackStats GetMethodStats(string methodName)
        {
            lock (_lock)
            {
                var methodFeedback = _feedbackHistory
                    .Where(f => f.MethodName.Equals(methodName, StringComparison.OrdinalIgnoreCase))
                    .ToList();

                if (methodFeedback.Count == 0)
                    return null;

                var approved = methodFeedback.Count(f => f.HumanDecision == ReviewDecision.Approve);
                var modified = methodFeedback.Count(f => f.HumanDecision == ReviewDecision.Modify);
                var rejected = methodFeedback.Count(f => f.HumanDecision == ReviewDecision.Reject);
                var correct = methodFeedback.Count(f => f.AIWasCorrect);

                return new FeedbackStats
                {
                    MethodName = methodName,
                    TotalFeedback = methodFeedback.Count,
                    ApprovedCount = approved,
                    ModifiedCount = modified,
                    RejectedCount = rejected,
                    AverageOriginalConfidence = methodFeedback.Average(f => f.OriginalConfidence),
                    AccuracyRate = (double)correct / methodFeedback.Count,
                    SuggestedThresholdAdjustment = CalculateSuggestedAdjustment(methodFeedback)
                };
            }
        }

        /// <summary>
        /// Get all feedback history
        /// </summary>
        public List<FeedbackRecord> GetHistory(int limit = 100)
        {
            lock (_lock)
            {
                return _feedbackHistory
                    .OrderByDescending(f => f.RecordedAt)
                    .Take(limit)
                    .ToList();
            }
        }

        /// <summary>
        /// Get overall statistics
        /// </summary>
        public OverallFeedbackStats GetOverallStats()
        {
            lock (_lock)
            {
                if (_feedbackHistory.Count == 0)
                {
                    return new OverallFeedbackStats();
                }

                var byMethod = _feedbackHistory
                    .GroupBy(f => f.MethodName)
                    .Select(g => new { Method = g.Key, Count = g.Count(), AccuracyRate = g.Count(f => f.AIWasCorrect) / (double)g.Count() })
                    .OrderByDescending(x => x.Count)
                    .ToList();

                return new OverallFeedbackStats
                {
                    TotalFeedback = _feedbackHistory.Count,
                    TotalCorrect = _feedbackHistory.Count(f => f.AIWasCorrect),
                    OverallAccuracyRate = _feedbackHistory.Count(f => f.AIWasCorrect) / (double)_feedbackHistory.Count,
                    UniqueMethods = byMethod.Count,
                    TopMethods = byMethod.Take(5).Select(x => $"{x.Method}: {x.Count} ({x.AccuracyRate:P0})").ToList(),
                    PatternCount = _patterns?.Count ?? 0,
                    FirstFeedback = _feedbackHistory.Min(f => f.RecordedAt),
                    LastFeedback = _feedbackHistory.Max(f => f.RecordedAt)
                };
            }
        }

        /// <summary>
        /// Extract characteristics from an envelope for pattern matching
        /// </summary>
        private Dictionary<string, object> ExtractCharacteristics(ConfidenceEnvelope envelope)
        {
            var characteristics = new Dictionary<string, object>
            {
                ["methodName"] = envelope.MethodName,
                ["originalConfidence"] = envelope.OverallConfidence,
                ["passCount"] = envelope.CurrentPass
            };

            // Extract parameter characteristics
            if (envelope.Parameters != null)
            {
                foreach (var prop in envelope.Parameters.Properties())
                {
                    var value = prop.Value;
                    if (value.Type == JTokenType.Integer || value.Type == JTokenType.Float)
                    {
                        characteristics[$"param_{prop.Name}"] = value.ToObject<double>();
                    }
                    else if (value.Type == JTokenType.String)
                    {
                        characteristics[$"param_{prop.Name}"] = value.ToString();
                    }
                    else if (value.Type == JTokenType.Boolean)
                    {
                        characteristics[$"param_{prop.Name}"] = value.ToObject<bool>();
                    }
                }
            }

            // Extract factor characteristics
            foreach (var factor in envelope.Factors)
            {
                characteristics[$"factor_{factor.FactorName}"] = factor.Score;
            }

            return characteristics;
        }

        /// <summary>
        /// Try to extract patterns from feedback for a method
        /// </summary>
        private void TryExtractPatterns(string methodName)
        {
            var minSamples = CIPSConfiguration.Instance.Feedback.MinSamplesToLearn;
            var methodFeedback = _feedbackHistory
                .Where(f => f.MethodName.Equals(methodName, StringComparison.OrdinalIgnoreCase))
                .ToList();

            if (methodFeedback.Count < minSamples)
                return;

            // Simple pattern: if AI is consistently wrong for this method, reduce confidence
            var wrongCount = methodFeedback.Count(f => !f.AIWasCorrect);
            var wrongRate = (double)wrongCount / methodFeedback.Count;

            if (wrongRate > 0.3) // More than 30% wrong
            {
                var existingPattern = _patterns.FirstOrDefault(p =>
                    p.MethodName.Equals(methodName, StringComparison.OrdinalIgnoreCase) &&
                    p.Description.StartsWith("Method accuracy pattern"));

                var adjustment = -wrongRate * CIPSConfiguration.Instance.Feedback.MaxAdjustment;

                if (existingPattern != null)
                {
                    existingPattern.ConfidenceAdjustment = adjustment;
                    existingPattern.SampleCount = methodFeedback.Count;
                    existingPattern.LastUpdated = DateTime.UtcNow;
                }
                else
                {
                    _patterns.Add(new LearnedPattern
                    {
                        PatternId = $"pat_{Guid.NewGuid():N}",
                        MethodName = methodName,
                        Description = $"Method accuracy pattern: {wrongRate:P0} error rate",
                        Conditions = new Dictionary<string, object>(),
                        ConfidenceAdjustment = adjustment,
                        SampleCount = methodFeedback.Count,
                        CreatedAt = DateTime.UtcNow,
                        LastUpdated = DateTime.UtcNow
                    });
                }

                Log.Information("[CIPS] Learned pattern for {Method}: {WrongRate:P0} error rate, adjustment: {Adj:F2}",
                    methodName, wrongRate, adjustment);
            }
        }

        /// <summary>
        /// Check if parameters match pattern conditions
        /// </summary>
        private bool MatchesConditions(Dictionary<string, object> conditions, JObject parameters)
        {
            if (conditions == null || conditions.Count == 0)
                return true;

            // For now, just return true for method-level patterns
            // More sophisticated matching can be added later
            return true;
        }

        /// <summary>
        /// Calculate suggested threshold adjustment based on feedback
        /// </summary>
        private double CalculateSuggestedAdjustment(List<FeedbackRecord> feedback)
        {
            if (feedback.Count == 0)
                return 0;

            // If AI was correct at high rate, can lower threshold slightly
            // If AI was often wrong, suggest raising threshold
            var correctRate = feedback.Count(f => f.AIWasCorrect) / (double)feedback.Count;
            var avgConfidence = feedback.Average(f => f.OriginalConfidence);

            if (correctRate > 0.9)
            {
                // Very accurate - could lower threshold
                return -0.05;
            }
            else if (correctRate < 0.5)
            {
                // Often wrong - should raise threshold
                return 0.1;
            }

            return 0;
        }

        /// <summary>
        /// Load feedback history from disk
        /// </summary>
        private void Load()
        {
            try
            {
                if (File.Exists(_historyPath))
                {
                    var json = File.ReadAllText(_historyPath);
                    var data = JsonConvert.DeserializeObject<FeedbackData>(json);
                    _feedbackHistory = data?.Records ?? new List<FeedbackRecord>();
                    _patterns = data?.Patterns ?? new List<LearnedPattern>();
                    Log.Debug("[CIPS] Loaded {Count} feedback records and {Patterns} patterns",
                        _feedbackHistory.Count, _patterns.Count);
                }
                else
                {
                    _feedbackHistory = new List<FeedbackRecord>();
                    _patterns = new List<LearnedPattern>();
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[CIPS] Error loading feedback history");
                _feedbackHistory = new List<FeedbackRecord>();
                _patterns = new List<LearnedPattern>();
            }
        }

        /// <summary>
        /// Save feedback history to disk
        /// </summary>
        private void Save()
        {
            try
            {
                var data = new FeedbackData
                {
                    Records = _feedbackHistory,
                    Patterns = _patterns,
                    LastUpdated = DateTime.UtcNow
                };
                var json = JsonConvert.SerializeObject(data, Formatting.Indented);
                File.WriteAllText(_historyPath, json);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[CIPS] Error saving feedback history");
            }
        }

        /// <summary>
        /// Container for serialization
        /// </summary>
        private class FeedbackData
        {
            public List<FeedbackRecord> Records { get; set; }
            public List<LearnedPattern> Patterns { get; set; }
            public DateTime LastUpdated { get; set; }
        }

        #region Session Learning (Enhancement #5)

        /// <summary>
        /// Start a new session with project context
        /// </summary>
        public SessionContext StartSession(string projectName = null, string projectPath = null)
        {
            lock (_lock)
            {
                CurrentSession = new SessionContext
                {
                    ProjectName = projectName,
                    ProjectPath = projectPath
                };

                Log.Information("[CIPS] Started new session {SessionId} for project '{Project}'",
                    CurrentSession.SessionId, projectName ?? "Unknown");

                return CurrentSession;
            }
        }

        /// <summary>
        /// End the current session and persist learned patterns
        /// </summary>
        public SessionOutcome EndSession(string summary = null)
        {
            if (CurrentSession == null)
                return null;

            lock (_lock)
            {
                CurrentSession.EndedAt = DateTime.UtcNow;

                var outcome = new SessionOutcome
                {
                    SessionId = CurrentSession.SessionId,
                    ProjectName = CurrentSession.ProjectName,
                    Duration = CurrentSession.EndedAt.Value - CurrentSession.StartedAt,
                    PatternsLearned = CurrentSession.LearnedPatterns.Count,
                    RulesAdded = CurrentSession.ProjectRules.Count,
                    Summary = summary ?? $"Session completed with {CurrentSession.LearnedPatterns.Count} patterns learned"
                };

                // Persist session patterns to global patterns if they're reliable
                foreach (var pattern in CurrentSession.LearnedPatterns.Where(p => p.SampleCount >= 3))
                {
                    var existingPattern = _patterns.FirstOrDefault(p =>
                        p.MethodName == pattern.MethodName &&
                        p.Description == pattern.Description);

                    if (existingPattern != null)
                    {
                        // Update existing pattern
                        existingPattern.ConfidenceAdjustment =
                            (existingPattern.ConfidenceAdjustment + pattern.ConfidenceAdjustment) / 2;
                        existingPattern.SampleCount += pattern.SampleCount;
                        existingPattern.LastUpdated = DateTime.UtcNow;
                    }
                    else
                    {
                        // Add new pattern
                        pattern.PatternId = $"sess_{Guid.NewGuid():N}";
                        _patterns.Add(pattern);
                    }
                }

                Save();

                Log.Information("[CIPS] Ended session {SessionId}. Duration: {Duration}. Patterns: {Patterns}",
                    CurrentSession.SessionId, outcome.Duration, outcome.PatternsLearned);

                CurrentSession = null;
                return outcome;
            }
        }

        /// <summary>
        /// Learn from a review decision during the current session
        /// </summary>
        public void LearnFromDecision(ReviewItem item, ReviewDecision decision)
        {
            if (CurrentSession == null || item?.Envelope == null)
                return;

            lock (_lock)
            {
                // Extract a pattern from the human decision
                var pattern = LearnedPattern.FromReviewDecision(item, decision);
                if (pattern != null)
                {
                    // Check if we already have this pattern
                    var existing = CurrentSession.LearnedPatterns.FirstOrDefault(p =>
                        p.MethodName == pattern.MethodName &&
                        ConditionsMatch(p.Conditions, pattern.Conditions));

                    if (existing != null)
                    {
                        // Reinforce existing pattern
                        existing.SampleCount++;
                        existing.ConfidenceAdjustment =
                            (existing.ConfidenceAdjustment * (existing.SampleCount - 1) + pattern.ConfidenceAdjustment) /
                            existing.SampleCount;
                        existing.LastUpdated = DateTime.UtcNow;
                    }
                    else
                    {
                        CurrentSession.LearnedPatterns.Add(pattern);
                    }

                    Log.Debug("[CIPS] Learned session pattern: {Description} (Adjustment: {Adj:+0.00;-0.00})",
                        pattern.Description, pattern.ConfidenceAdjustment);
                }

                // Record terminology if modified
                if (decision == ReviewDecision.Modify && item.ModifiedParameters != null)
                {
                    // Could learn terminology mappings here
                }
            }
        }

        /// <summary>
        /// Get session-aware confidence adjustment
        /// </summary>
        public double GetSessionConfidenceAdjustment(string methodName, JObject parameters)
        {
            if (CurrentSession == null)
                return 0;

            return CurrentSession.GetConfidenceAdjustment(methodName, parameters);
        }

        /// <summary>
        /// Add a project-specific rule to the current session
        /// </summary>
        public void AddProjectRule(string rule)
        {
            if (CurrentSession == null || string.IsNullOrWhiteSpace(rule))
                return;

            lock (_lock)
            {
                if (!CurrentSession.ProjectRules.Contains(rule))
                {
                    CurrentSession.ProjectRules.Add(rule);
                    Log.Debug("[CIPS] Added project rule: {Rule}", rule);
                }
            }
        }

        /// <summary>
        /// Add terminology mapping to current session
        /// </summary>
        public void AddTerminologyMapping(string term, string meaning)
        {
            if (CurrentSession == null)
                return;

            lock (_lock)
            {
                CurrentSession.TerminologyMap[term.ToLower()] = meaning;
                Log.Debug("[CIPS] Added terminology: '{Term}' -> '{Meaning}'", term, meaning);
            }
        }

        /// <summary>
        /// Check if two condition dictionaries match
        /// </summary>
        private bool ConditionsMatch(Dictionary<string, object> a, Dictionary<string, object> b)
        {
            if (a == null && b == null) return true;
            if (a == null || b == null) return false;
            if (a.Count != b.Count) return false;

            foreach (var kvp in a)
            {
                if (!b.TryGetValue(kvp.Key, out var bValue))
                    return false;
                if (!Equals(kvp.Value, bValue))
                    return false;
            }

            return true;
        }

        #endregion
    }

    /// <summary>
    /// Overall feedback statistics
    /// </summary>
    public class OverallFeedbackStats
    {
        public int TotalFeedback { get; set; }
        public int TotalCorrect { get; set; }
        public double OverallAccuracyRate { get; set; }
        public int UniqueMethods { get; set; }
        public List<string> TopMethods { get; set; } = new List<string>();
        public int PatternCount { get; set; }
        public DateTime? FirstFeedback { get; set; }
        public DateTime? LastFeedback { get; set; }
    }
}
