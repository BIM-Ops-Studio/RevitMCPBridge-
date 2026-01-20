using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json;

namespace RevitMCPBridge
{
    /// <summary>
    /// Analyzes user workflow patterns from change sequences.
    /// Detects repeated action patterns and learns user behavior.
    /// </summary>
    public class WorkflowAnalyzer
    {
        private static WorkflowAnalyzer _instance;
        private static readonly object _lock = new object();

        // Workflow sequences (ordered list of actions)
        private readonly List<WorkflowAction> _actionHistory = new List<WorkflowAction>();
        private readonly int _maxHistorySize = 5000;

        // Detected patterns
        private readonly List<WorkflowPattern> _detectedPatterns = new List<WorkflowPattern>();
        private readonly Dictionary<string, int> _actionFrequency = new Dictionary<string, int>();
        private readonly Dictionary<string, List<string>> _actionFollowers = new Dictionary<string, List<string>>();

        // Session tracking
        private string _currentTask = "";
        private DateTime _sessionStart = DateTime.Now;
        private readonly List<TaskSession> _taskSessions = new List<TaskSession>();

        public static WorkflowAnalyzer Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new WorkflowAnalyzer();
                        }
                    }
                }
                return _instance;
            }
        }

        private WorkflowAnalyzer() { }

        #region Action Recording

        /// <summary>
        /// Record a workflow action from ChangeTracker events
        /// </summary>
        public void RecordAction(WorkflowAction action)
        {
            lock (_actionHistory)
            {
                _actionHistory.Add(action);

                // Update frequency tracking
                string actionKey = GetActionKey(action);
                if (!_actionFrequency.ContainsKey(actionKey))
                    _actionFrequency[actionKey] = 0;
                _actionFrequency[actionKey]++;

                // Track what actions follow other actions
                if (_actionHistory.Count > 1)
                {
                    var previousAction = _actionHistory[_actionHistory.Count - 2];
                    string prevKey = GetActionKey(previousAction);

                    if (!_actionFollowers.ContainsKey(prevKey))
                        _actionFollowers[prevKey] = new List<string>();
                    _actionFollowers[prevKey].Add(actionKey);
                }

                // Trim if too large
                while (_actionHistory.Count > _maxHistorySize)
                {
                    _actionHistory.RemoveAt(0);
                }

                // Analyze for patterns periodically
                if (_actionHistory.Count % 50 == 0)
                {
                    AnalyzePatterns();
                }
            }

            Serilog.Log.Debug($"WorkflowAnalyzer recorded: {action.ActionType} - {action.Category}");
        }

        /// <summary>
        /// Record action from ChangeRecord
        /// </summary>
        public void RecordFromChangeRecord(ChangeRecord change, Document doc)
        {
            var action = new WorkflowAction
            {
                Timestamp = change.Timestamp,
                ActionType = MapChangeTypeToActionType(change.ChangeType),
                Category = ExtractCategory(change),
                ElementCount = change.ElementCount,
                ViewContext = GetCurrentViewContext(doc),
                TransactionName = change.TransactionName,
                Details = change.Details
            };

            RecordAction(action);
        }

        #endregion

        #region Pattern Analysis

        /// <summary>
        /// Analyze action history for patterns
        /// </summary>
        public void AnalyzePatterns()
        {
            lock (_actionHistory)
            {
                // Find repeated sequences
                FindRepeatedSequences(3);  // Look for 3-action sequences
                FindRepeatedSequences(5);  // Look for 5-action sequences

                // Analyze category-specific patterns
                AnalyzeCategoryPatterns();

                // Analyze view-based patterns
                AnalyzeViewPatterns();
            }
        }

        private void FindRepeatedSequences(int sequenceLength)
        {
            if (_actionHistory.Count < sequenceLength * 2)
                return;

            var sequences = new Dictionary<string, int>();

            for (int i = 0; i <= _actionHistory.Count - sequenceLength; i++)
            {
                var sequence = _actionHistory.Skip(i).Take(sequenceLength).ToList();
                string seqKey = GetSequenceKey(sequence);

                if (!sequences.ContainsKey(seqKey))
                    sequences[seqKey] = 0;
                sequences[seqKey]++;
            }

            // Patterns that occur 3+ times are significant
            foreach (var kvp in sequences.Where(s => s.Value >= 3))
            {
                var existingPattern = _detectedPatterns.FirstOrDefault(p => p.SequenceKey == kvp.Key);
                if (existingPattern != null)
                {
                    existingPattern.Occurrences = kvp.Value;
                    existingPattern.LastSeen = DateTime.Now;
                }
                else
                {
                    _detectedPatterns.Add(new WorkflowPattern
                    {
                        SequenceKey = kvp.Key,
                        SequenceLength = sequenceLength,
                        Occurrences = kvp.Value,
                        FirstSeen = DateTime.Now,
                        LastSeen = DateTime.Now,
                        Description = DescribeSequence(kvp.Key)
                    });
                }
            }
        }

        private void AnalyzeCategoryPatterns()
        {
            // Group actions by category and find common sequences within each
            var categoryGroups = _actionHistory
                .Where(a => !string.IsNullOrEmpty(a.Category))
                .GroupBy(a => a.Category);

            foreach (var group in categoryGroups)
            {
                var categoryActions = group.ToList();
                if (categoryActions.Count >= 5)
                {
                    // Track common action types for this category
                    var actionTypes = categoryActions
                        .GroupBy(a => a.ActionType)
                        .OrderByDescending(g => g.Count())
                        .Take(3)
                        .Select(g => new { Type = g.Key, Count = g.Count() })
                        .ToList();

                    // This data helps understand: "For Walls, user mostly Adds then Modifies"
                }
            }
        }

        private void AnalyzeViewPatterns()
        {
            // Track which views user works in most
            var viewContexts = _actionHistory
                .Where(a => a.ViewContext != null)
                .GroupBy(a => a.ViewContext.ViewType)
                .OrderByDescending(g => g.Count())
                .ToList();

            // Track typical workflow: Floor Plan -> Elevation -> Section
            var viewSequences = new List<string>();
            string lastViewType = null;

            foreach (var action in _actionHistory.Where(a => a.ViewContext != null))
            {
                if (action.ViewContext.ViewType != lastViewType && lastViewType != null)
                {
                    viewSequences.Add($"{lastViewType}->{action.ViewContext.ViewType}");
                }
                lastViewType = action.ViewContext.ViewType;
            }

            // Find common view transitions
            var commonTransitions = viewSequences
                .GroupBy(s => s)
                .Where(g => g.Count() >= 3)
                .OrderByDescending(g => g.Count())
                .ToList();
        }

        #endregion

        #region Predictions

        /// <summary>
        /// Predict what the user will likely do next based on current context
        /// </summary>
        public List<PredictedAction> PredictNextActions(WorkflowAction currentAction, int maxPredictions = 5)
        {
            var predictions = new List<PredictedAction>();
            string currentKey = GetActionKey(currentAction);

            // Check what usually follows this action
            if (_actionFollowers.ContainsKey(currentKey))
            {
                var followers = _actionFollowers[currentKey]
                    .GroupBy(f => f)
                    .OrderByDescending(g => g.Count())
                    .Take(maxPredictions);

                foreach (var follower in followers)
                {
                    int totalFollows = _actionFollowers[currentKey].Count;
                    double probability = (double)follower.Count() / totalFollows;

                    predictions.Add(new PredictedAction
                    {
                        ActionKey = follower.Key,
                        Probability = probability,
                        BasedOn = $"Follows {currentKey} {follower.Count()}/{totalFollows} times"
                    });
                }
            }

            // Also consider patterns
            foreach (var pattern in _detectedPatterns.OrderByDescending(p => p.Occurrences))
            {
                if (pattern.SequenceKey.StartsWith(currentKey))
                {
                    var nextInPattern = pattern.SequenceKey.Split('|').Skip(1).FirstOrDefault();
                    if (!string.IsNullOrEmpty(nextInPattern) &&
                        !predictions.Any(p => p.ActionKey == nextInPattern))
                    {
                        predictions.Add(new PredictedAction
                        {
                            ActionKey = nextInPattern,
                            Probability = 0.5 * (pattern.Occurrences / 10.0),
                            BasedOn = $"Part of pattern seen {pattern.Occurrences} times"
                        });
                    }
                }
            }

            return predictions.OrderByDescending(p => p.Probability).Take(maxPredictions).ToList();
        }

        /// <summary>
        /// Get workflow recommendations based on current state
        /// </summary>
        public List<WorkflowRecommendation> GetRecommendations(Document doc)
        {
            var recommendations = new List<WorkflowRecommendation>();

            // Get current context
            var recentActions = _actionHistory.Skip(Math.Max(0, _actionHistory.Count - 10)).ToList();
            if (!recentActions.Any())
                return recommendations;

            var lastAction = recentActions.Last();

            // Recommendation: Based on category workflow
            if (lastAction.Category == "Walls" && lastAction.ActionType == ActionType.Add)
            {
                // User just added walls - often followed by doors/windows
                if (GetActionProbability("Add|Doors") > 0.3)
                {
                    recommendations.Add(new WorkflowRecommendation
                    {
                        Type = RecommendationType.NextStep,
                        Title = "Add Doors/Windows",
                        Description = "You typically add doors and windows after placing walls",
                        Confidence = GetActionProbability("Add|Doors"),
                        SuggestedAction = "placeDoor"
                    });
                }
            }

            // Recommendation: Based on view patterns
            var currentView = GetCurrentViewContext(doc);
            if (currentView?.ViewType == "FloorPlan")
            {
                var plansWorkedOn = recentActions.Count(a => a.ViewContext?.ViewType == "FloorPlan");
                if (plansWorkedOn >= 5)
                {
                    recommendations.Add(new WorkflowRecommendation
                    {
                        Type = RecommendationType.ViewSwitch,
                        Title = "Check Elevations",
                        Description = "You've made several changes to floor plans - consider reviewing elevations",
                        Confidence = 0.6,
                        SuggestedAction = "switchToElevation"
                    });
                }
            }

            // Recommendation: Based on detected patterns
            foreach (var pattern in _detectedPatterns.Where(p => p.Occurrences >= 5))
            {
                var patternActions = pattern.SequenceKey.Split('|');
                var recentKeys = recentActions.Select(a => GetActionKey(a)).ToList();

                // Check if we're in the middle of a known pattern
                for (int i = 0; i < patternActions.Length - 1; i++)
                {
                    if (recentKeys.Count > i && recentKeys[recentKeys.Count - 1 - i] == patternActions[patternActions.Length - 2 - i])
                    {
                        var nextExpected = patternActions.Last();
                        recommendations.Add(new WorkflowRecommendation
                        {
                            Type = RecommendationType.PatternCompletion,
                            Title = $"Complete Pattern: {nextExpected}",
                            Description = $"You usually follow this with: {DescribeActionKey(nextExpected)}",
                            Confidence = 0.7,
                            SuggestedAction = nextExpected
                        });
                        break;
                    }
                }
            }

            return recommendations.OrderByDescending(r => r.Confidence).Take(5).ToList();
        }

        #endregion

        #region Task Session Tracking

        /// <summary>
        /// Start tracking a named task (e.g., "Setting up floor plan sheet")
        /// </summary>
        public void StartTask(string taskName)
        {
            if (!string.IsNullOrEmpty(_currentTask))
            {
                EndTask();
            }

            _currentTask = taskName;
            _sessionStart = DateTime.Now;

            Serilog.Log.Information($"WorkflowAnalyzer: Started task '{taskName}'");
        }

        /// <summary>
        /// End the current task and save the workflow
        /// </summary>
        public TaskSession EndTask()
        {
            if (string.IsNullOrEmpty(_currentTask))
                return null;

            var session = new TaskSession
            {
                TaskName = _currentTask,
                StartTime = _sessionStart,
                EndTime = DateTime.Now,
                Actions = _actionHistory
                    .Where(a => a.Timestamp >= _sessionStart)
                    .ToList()
            };

            _taskSessions.Add(session);

            Serilog.Log.Information($"WorkflowAnalyzer: Ended task '{_currentTask}' with {session.Actions.Count} actions");

            _currentTask = "";
            return session;
        }

        /// <summary>
        /// Get actions for a specific task type (for learning)
        /// </summary>
        public List<TaskSession> GetTaskSessions(string taskNameContains)
        {
            return _taskSessions
                .Where(s => s.TaskName.ToLower().Contains(taskNameContains.ToLower()))
                .ToList();
        }

        #endregion

        #region Query Methods

        /// <summary>
        /// Get most frequent actions
        /// </summary>
        public Dictionary<string, int> GetActionFrequencies(int top = 20)
        {
            return _actionFrequency
                .OrderByDescending(kvp => kvp.Value)
                .Take(top)
                .ToDictionary(kvp => kvp.Key, kvp => kvp.Value);
        }

        /// <summary>
        /// Get detected patterns
        /// </summary>
        public List<WorkflowPattern> GetPatterns(int minOccurrences = 3)
        {
            return _detectedPatterns
                .Where(p => p.Occurrences >= minOccurrences)
                .OrderByDescending(p => p.Occurrences)
                .ToList();
        }

        /// <summary>
        /// Get workflow statistics
        /// </summary>
        public WorkflowStatistics GetStatistics()
        {
            return new WorkflowStatistics
            {
                TotalActionsRecorded = _actionHistory.Count,
                UniqueActionTypes = _actionFrequency.Count,
                PatternsDetected = _detectedPatterns.Count,
                TaskSessionsRecorded = _taskSessions.Count,
                MostCommonAction = _actionFrequency.OrderByDescending(kvp => kvp.Value).FirstOrDefault().Key ?? "None",
                SessionDuration = DateTime.Now - _sessionStart,
                CurrentTask = _currentTask
            };
        }

        /// <summary>
        /// Export learned patterns for external storage (Claude Memory)
        /// </summary>
        public string ExportLearnedPatterns()
        {
            var export = new
            {
                exportTime = DateTime.Now,
                statistics = GetStatistics(),
                topActions = GetActionFrequencies(30),
                patterns = GetPatterns(3),
                taskSessions = _taskSessions.Select(s => new
                {
                    s.TaskName,
                    s.StartTime,
                    s.EndTime,
                    actionCount = s.Actions.Count,
                    actionSummary = s.Actions
                        .GroupBy(a => GetActionKey(a))
                        .Select(g => new { action = g.Key, count = g.Count() })
                        .OrderByDescending(x => x.count)
                        .Take(10)
                }).ToList()
            };

            return JsonConvert.SerializeObject(export, Formatting.Indented);
        }

        #endregion

        #region Helper Methods

        private string GetActionKey(WorkflowAction action)
        {
            return $"{action.ActionType}|{action.Category ?? "Unknown"}";
        }

        private string GetSequenceKey(List<WorkflowAction> sequence)
        {
            return string.Join("|", sequence.Select(a => GetActionKey(a)));
        }

        private ActionType MapChangeTypeToActionType(ChangeType changeType)
        {
            switch (changeType)
            {
                case ChangeType.ElementsAdded: return ActionType.Add;
                case ChangeType.ElementsDeleted: return ActionType.Delete;
                case ChangeType.ElementsModified: return ActionType.Modify;
                case ChangeType.ViewChanged: return ActionType.ViewChange;
                case ChangeType.SelectionChanged: return ActionType.Select;
                case ChangeType.DocumentSaved: return ActionType.Save;
                default: return ActionType.Other;
            }
        }

        private string ExtractCategory(ChangeRecord change)
        {
            if (change.Details != null && change.Details.ContainsKey("elements"))
            {
                var elements = change.Details["elements"] as List<Dictionary<string, object>>;
                if (elements != null && elements.Any())
                {
                    return elements.First()["category"]?.ToString() ?? "Unknown";
                }
            }
            return "Unknown";
        }

        private ViewContext GetCurrentViewContext(Document doc)
        {
            if (doc == null) return null;

            try
            {
                var uiDoc = new UIDocument(doc);
                var view = uiDoc.ActiveView;

                return new ViewContext
                {
                    ViewId = view?.Id.Value ?? -1,
                    ViewName = view?.Name ?? "Unknown",
                    ViewType = view?.ViewType.ToString() ?? "Unknown",
                    IsSheet = view is ViewSheet,
                    SheetNumber = (view as ViewSheet)?.SheetNumber ?? ""
                };
            }
            catch
            {
                return null;
            }
        }

        private double GetActionProbability(string actionKey)
        {
            if (!_actionFrequency.ContainsKey(actionKey))
                return 0;

            int total = _actionFrequency.Values.Sum();
            return (double)_actionFrequency[actionKey] / total;
        }

        private string DescribeSequence(string sequenceKey)
        {
            var parts = sequenceKey.Split('|');
            var descriptions = new List<string>();

            for (int i = 0; i < parts.Length; i += 2)
            {
                if (i + 1 < parts.Length)
                {
                    descriptions.Add($"{parts[i]} {parts[i + 1]}");
                }
            }

            return string.Join(" -> ", descriptions);
        }

        private string DescribeActionKey(string actionKey)
        {
            var parts = actionKey.Split('|');
            if (parts.Length >= 2)
            {
                return $"{parts[0]} {parts[1]}";
            }
            return actionKey;
        }

        #endregion
    }

    #region Supporting Types

    public enum ActionType
    {
        Add,
        Delete,
        Modify,
        Select,
        ViewChange,
        Save,
        Copy,
        Move,
        Rotate,
        Mirror,
        Array,
        Group,
        Other
    }

    public class WorkflowAction
    {
        public DateTime Timestamp { get; set; }
        public ActionType ActionType { get; set; }
        public string Category { get; set; }
        public int ElementCount { get; set; }
        public ViewContext ViewContext { get; set; }
        public string TransactionName { get; set; }
        public Dictionary<string, object> Details { get; set; }
    }

    public class ViewContext
    {
        public long ViewId { get; set; }
        public string ViewName { get; set; }
        public string ViewType { get; set; }
        public bool IsSheet { get; set; }
        public string SheetNumber { get; set; }
    }

    public class WorkflowPattern
    {
        public string SequenceKey { get; set; }
        public int SequenceLength { get; set; }
        public int Occurrences { get; set; }
        public DateTime FirstSeen { get; set; }
        public DateTime LastSeen { get; set; }
        public string Description { get; set; }
    }

    public class PredictedAction
    {
        public string ActionKey { get; set; }
        public double Probability { get; set; }
        public string BasedOn { get; set; }
    }

    public class WorkflowRecommendation
    {
        public RecommendationType Type { get; set; }
        public string Title { get; set; }
        public string Description { get; set; }
        public double Confidence { get; set; }
        public string SuggestedAction { get; set; }
    }

    public enum RecommendationType
    {
        NextStep,
        ViewSwitch,
        PatternCompletion,
        QualityCheck,
        Optimization
    }

    public class TaskSession
    {
        public string TaskName { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public List<WorkflowAction> Actions { get; set; } = new List<WorkflowAction>();
    }

    public class WorkflowStatistics
    {
        public int TotalActionsRecorded { get; set; }
        public int UniqueActionTypes { get; set; }
        public int PatternsDetected { get; set; }
        public int TaskSessionsRecorded { get; set; }
        public string MostCommonAction { get; set; }
        public TimeSpan SessionDuration { get; set; }
        public string CurrentTask { get; set; }
    }

    #endregion
}
