using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// Context for a CIPS session, including learned patterns specific to this project.
    /// This is Enhancement #5: Session Learning
    /// </summary>
    public class SessionContext
    {
        [JsonProperty("sessionId")]
        public string SessionId { get; set; } = Guid.NewGuid().ToString();

        [JsonProperty("projectName")]
        public string ProjectName { get; set; }

        [JsonProperty("projectPath")]
        public string ProjectPath { get; set; }

        [JsonProperty("startedAt")]
        public DateTime StartedAt { get; set; } = DateTime.UtcNow;

        [JsonProperty("lastActivityAt")]
        public DateTime LastActivityAt { get; set; } = DateTime.UtcNow;

        [JsonProperty("endedAt")]
        public DateTime? EndedAt { get; set; }

        [JsonProperty("learnedPatterns")]
        public List<LearnedPattern> LearnedPatterns { get; set; } = new List<LearnedPattern>();

        [JsonProperty("projectRules")]
        public List<string> ProjectRules { get; set; } = new List<string>();

        [JsonProperty("terminologyMap")]
        public Dictionary<string, string> TerminologyMap { get; set; } = new Dictionary<string, string>();

        [JsonProperty("operationCount")]
        public int OperationCount { get; set; }

        [JsonProperty("successCount")]
        public int SuccessCount { get; set; }

        [JsonProperty("reviewCount")]
        public int ReviewCount { get; set; }

        /// <summary>
        /// Current focus context - what user is actively working on.
        /// Updated by ProactiveMonitor to enable context-aware decisions.
        /// Phase 4 of Predictive Intelligence Enhancement.
        /// </summary>
        [JsonProperty("currentFocus")]
        public FocusContext CurrentFocus { get; set; } = new FocusContext();

        /// <summary>
        /// Get confidence adjustment based on learned patterns
        /// </summary>
        public double GetConfidenceAdjustment(string methodName, JObject parameters)
        {
            double adjustment = 0;

            foreach (var pattern in LearnedPatterns.Where(p =>
                p.AppliesTo == "all" ||
                p.AppliesTo.Equals(methodName, StringComparison.OrdinalIgnoreCase)))
            {
                if (pattern.Matches(parameters))
                {
                    adjustment += pattern.ConfidenceAdjustment;
                }
            }

            return adjustment;
        }

        /// <summary>
        /// Add a learned pattern to this session
        /// </summary>
        public void AddPattern(LearnedPattern pattern)
        {
            pattern.PatternId = $"sp_{LearnedPatterns.Count + 1}_{DateTime.UtcNow.Ticks}";
            LearnedPatterns.Add(pattern);
            LastActivityAt = DateTime.UtcNow;
        }

        /// <summary>
        /// Add a project-specific rule
        /// </summary>
        public void AddProjectRule(string rule)
        {
            if (!ProjectRules.Contains(rule))
            {
                ProjectRules.Add(rule);
                LastActivityAt = DateTime.UtcNow;
            }
        }

        /// <summary>
        /// Map a term (abbreviation to full name)
        /// </summary>
        public void AddTerminology(string abbreviation, string fullName)
        {
            TerminologyMap[abbreviation.ToUpper()] = fullName;
            LastActivityAt = DateTime.UtcNow;
        }

        /// <summary>
        /// Expand terminology in a string
        /// </summary>
        public string ExpandTerminology(string input)
        {
            if (string.IsNullOrEmpty(input) || TerminologyMap.Count == 0)
                return input;

            foreach (var kvp in TerminologyMap)
            {
                input = input.Replace(kvp.Key, kvp.Value);
            }

            return input;
        }

        /// <summary>
        /// Record an operation
        /// </summary>
        public void RecordOperation(bool success, bool wentToReview)
        {
            OperationCount++;
            if (success) SuccessCount++;
            if (wentToReview) ReviewCount++;
            LastActivityAt = DateTime.UtcNow;
        }

        /// <summary>
        /// Get success rate
        /// </summary>
        public double SuccessRate => OperationCount > 0 ? (double)SuccessCount / OperationCount : 0;

        /// <summary>
        /// Get session duration
        /// </summary>
        public TimeSpan Duration => DateTime.UtcNow - StartedAt;

        /// <summary>
        /// Get summary of session
        /// </summary>
        public string GetSummary()
        {
            return $"Session {SessionId.Substring(0, 8)}: " +
                   $"{OperationCount} operations ({SuccessRate:P0} success), " +
                   $"{LearnedPatterns.Count} patterns learned, " +
                   $"{ProjectRules.Count} rules, " +
                   $"running {Duration.TotalMinutes:F0} minutes";
        }
    }

    // Note: LearnedPattern class is defined in FeedbackRecord.cs
    // and is shared between feedback learning and session learning.

    /// <summary>
    /// Outcome summary for a completed session
    /// </summary>
    public class SessionOutcome
    {
        [JsonProperty("sessionId")]
        public string SessionId { get; set; }

        [JsonProperty("projectName")]
        public string ProjectName { get; set; }

        [JsonProperty("startedAt")]
        public DateTime StartedAt { get; set; }

        [JsonProperty("completedAt")]
        public DateTime CompletedAt { get; set; }

        [JsonProperty("duration")]
        public TimeSpan Duration { get; set; }

        [JsonProperty("totalOperations")]
        public int TotalOperations { get; set; }

        [JsonProperty("successfulOperations")]
        public int SuccessfulOperations { get; set; }

        [JsonProperty("reviewedOperations")]
        public int ReviewedOperations { get; set; }

        [JsonProperty("patternsLearned")]
        public int PatternsLearned { get; set; }

        [JsonProperty("rulesAdded")]
        public int RulesAdded { get; set; }

        [JsonProperty("summary")]
        public string Summary { get; set; }

        [JsonProperty("averageConfidence")]
        public double AverageConfidence { get; set; }

        [JsonProperty("averageConfidenceImprovement")]
        public double AverageConfidenceImprovement { get; set; }

        [JsonProperty("thresholdSuggestions")]
        public List<ThresholdSuggestion> ThresholdSuggestions { get; set; } = new List<ThresholdSuggestion>();
    }

    /// <summary>
    /// Suggestion for threshold adjustment based on session data
    /// </summary>
    public class ThresholdSuggestion
    {
        [JsonProperty("methodName")]
        public string MethodName { get; set; }

        [JsonProperty("currentThreshold")]
        public double CurrentThreshold { get; set; }

        [JsonProperty("suggestedThreshold")]
        public double SuggestedThreshold { get; set; }

        [JsonProperty("reason")]
        public string Reason { get; set; }

        [JsonProperty("sampleCount")]
        public int SampleCount { get; set; }
    }

    /// <summary>
    /// Tracks the user's current working context for intelligent decision-making.
    /// Phase 4 of Predictive Intelligence Enhancement.
    /// </summary>
    public class FocusContext
    {
        /// <summary>
        /// ID of the currently active view
        /// </summary>
        [JsonProperty("activeViewId")]
        public long ActiveViewId { get; set; }

        /// <summary>
        /// Type of the currently active view (FloorPlan, Section, etc.)
        /// </summary>
        [JsonProperty("activeViewType")]
        public string ActiveViewType { get; set; }

        /// <summary>
        /// ID of the currently active sheet (if viewing a sheet)
        /// </summary>
        [JsonProperty("activeSheetId")]
        public long? ActiveSheetId { get; set; }

        /// <summary>
        /// Sheet number of the last sheet where user placed a view
        /// Used to prefer that sheet for related views
        /// </summary>
        [JsonProperty("lastPlacedSheetNumber")]
        public string LastPlacedSheetNumber { get; set; }

        /// <summary>
        /// IDs of currently selected elements
        /// </summary>
        [JsonProperty("selectedElementIds")]
        public List<long> SelectedElementIds { get; set; } = new List<long>();

        /// <summary>
        /// Types of currently selected elements
        /// </summary>
        [JsonProperty("selectedElementTypes")]
        public List<string> SelectedElementTypes { get; set; } = new List<string>();

        /// <summary>
        /// Level name of the currently active view (if applicable)
        /// </summary>
        [JsonProperty("activeLevel")]
        public string ActiveLevel { get; set; }

        /// <summary>
        /// The last view type placed by the user (for sequence prediction)
        /// </summary>
        [JsonProperty("lastPlacedViewType")]
        public string LastPlacedViewType { get; set; }

        /// <summary>
        /// When this focus context was last updated
        /// </summary>
        [JsonProperty("updatedAt")]
        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// Update the last placed sheet tracking
        /// </summary>
        public void RecordViewPlacement(string sheetNumber, string viewType)
        {
            LastPlacedSheetNumber = sheetNumber;
            LastPlacedViewType = viewType;
            UpdatedAt = DateTime.UtcNow;
        }

        /// <summary>
        /// Check if context is stale (older than 5 minutes)
        /// </summary>
        public bool IsStale => (DateTime.UtcNow - UpdatedAt).TotalMinutes > 5;

        /// <summary>
        /// Get a summary of the current focus
        /// </summary>
        public string GetSummary()
        {
            var parts = new List<string>();

            if (!string.IsNullOrEmpty(ActiveViewType))
                parts.Add($"View: {ActiveViewType}");

            if (!string.IsNullOrEmpty(ActiveLevel))
                parts.Add($"Level: {ActiveLevel}");

            if (SelectedElementIds.Count > 0)
                parts.Add($"Selected: {SelectedElementIds.Count} elements");

            if (!string.IsNullOrEmpty(LastPlacedSheetNumber))
                parts.Add($"Last sheet: {LastPlacedSheetNumber}");

            return parts.Count > 0 ? string.Join(", ", parts) : "No focus";
        }
    }
}
