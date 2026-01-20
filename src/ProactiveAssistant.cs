using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json;

namespace RevitMCPBridge
{
    /// <summary>
    /// The brain of the intelligence system. Combines workflow analysis, preference learning,
    /// and layout intelligence to provide proactive, context-aware assistance.
    /// </summary>
    public class ProactiveAssistant
    {
        private static ProactiveAssistant _instance;
        private static readonly object _lock = new object();

        // Context tracking
        private AssistantContext _currentContext;
        private readonly List<Suggestion> _pendingSuggestions = new List<Suggestion>();
        private readonly List<AssistantAction> _suggestedActions = new List<AssistantAction>();
        private DateTime _lastContextUpdate = DateTime.MinValue;

        // Learning state
        private int _suggestionsAccepted = 0;
        private int _suggestionsRejected = 0;
        private readonly Dictionary<string, int> _suggestionTypeAcceptance = new Dictionary<string, int>();

        public static ProactiveAssistant Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new ProactiveAssistant();
                        }
                    }
                }
                return _instance;
            }
        }

        private ProactiveAssistant()
        {
            _currentContext = new AssistantContext();
        }

        #region Context Updates

        /// <summary>
        /// Update the assistant's understanding of current context
        /// </summary>
        public void UpdateContext(UIApplication uiApp)
        {
            if (uiApp?.ActiveUIDocument?.Document == null)
                return;

            try
            {
                var doc = uiApp.ActiveUIDocument.Document;
                var activeView = uiApp.ActiveUIDocument.ActiveView;
                var selection = uiApp.ActiveUIDocument.Selection.GetElementIds();

                _currentContext = new AssistantContext
                {
                    Timestamp = DateTime.Now,
                    DocumentName = doc.Title,
                    DocumentPath = doc.PathName,
                    ActiveViewId = activeView?.Id.Value ?? -1,
                    ActiveViewName = activeView?.Name ?? "None",
                    ActiveViewType = activeView?.ViewType.ToString() ?? "Unknown",
                    IsOnSheet = activeView is ViewSheet,
                    SheetNumber = (activeView as ViewSheet)?.SheetNumber ?? "",
                    SelectedElementCount = selection.Count,
                    SelectedCategories = GetSelectedCategories(selection, doc),
                    RecentActions = WorkflowAnalyzer.Instance.GetStatistics(),
                    WorkflowStatistics = WorkflowAnalyzer.Instance.GetStatistics()
                };

                // Analyze context and generate suggestions
                AnalyzeContextAndSuggest(doc);

                _lastContextUpdate = DateTime.Now;
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error updating ProactiveAssistant context");
            }
        }

        /// <summary>
        /// Process a change event and potentially generate suggestions
        /// </summary>
        public void ProcessChange(ChangeRecord change, Document doc)
        {
            // Feed to workflow analyzer for pattern learning
            WorkflowAnalyzer.Instance.RecordFromChangeRecord(change, doc);

            // Feed to preference learner
            if (change.Details != null && change.Details.ContainsKey("elements"))
            {
                var elements = change.Details["elements"] as List<Dictionary<string, object>>;
                if (elements != null)
                {
                    foreach (var elemInfo in elements)
                    {
                        if (elemInfo.ContainsKey("id"))
                        {
                            var element = doc.GetElement(new ElementId(Convert.ToInt64(elemInfo["id"])));
                            if (element != null)
                            {
                                PreferenceLearner.Instance.LearnFromElementPlacement(element, doc);
                            }
                        }
                    }
                }
            }

            // Generate contextual suggestions based on the change
            GenerateChangeBasedSuggestions(change, doc);
        }

        #endregion

        #region Suggestion Generation

        private void AnalyzeContextAndSuggest(Document doc)
        {
            _pendingSuggestions.Clear();

            // 1. Check if user might need help based on current state
            CheckForQualityOpportunities(doc);

            // 2. Check for workflow recommendations
            CheckForWorkflowSuggestions(doc);

            // 3. Check for pattern-based suggestions
            CheckForPatternBasedSuggestions();

            // 4. Check for layout suggestions if on a sheet
            if (_currentContext.IsOnSheet)
            {
                CheckForLayoutSuggestions(doc);
            }

            // Sort by relevance
            _pendingSuggestions.Sort((a, b) => b.Relevance.CompareTo(a.Relevance));
        }

        private void GenerateChangeBasedSuggestions(ChangeRecord change, Document doc)
        {
            // After adding walls, suggest doors/windows
            if (change.ChangeType == ChangeType.ElementsAdded)
            {
                string category = ExtractCategory(change);

                if (category == "Walls" && change.ElementCount >= 3)
                {
                    AddSuggestion(new Suggestion
                    {
                        Type = SuggestionType.NextStep,
                        Title = "Add Openings",
                        Description = "You've added several walls. Would you like to place doors and windows?",
                        Relevance = 0.7,
                        SuggestedAction = new AssistantAction
                        {
                            ActionType = "PlaceDoors",
                            Parameters = new Dictionary<string, object>()
                        }
                    });
                }

                if (category == "Rooms" && change.ElementCount >= 1)
                {
                    AddSuggestion(new Suggestion
                    {
                        Type = SuggestionType.NextStep,
                        Title = "Tag Rooms",
                        Description = "New rooms have been created. Would you like to add room tags?",
                        Relevance = 0.6,
                        SuggestedAction = new AssistantAction
                        {
                            ActionType = "TagAllRooms",
                            Parameters = new Dictionary<string, object>()
                        }
                    });
                }
            }

            // After many modifications, suggest saving
            if (change.ChangeType == ChangeType.ElementsModified)
            {
                var stats = WorkflowAnalyzer.Instance.GetStatistics();
                if (stats.TotalActionsRecorded > 0 && stats.TotalActionsRecorded % 50 == 0)
                {
                    AddSuggestion(new Suggestion
                    {
                        Type = SuggestionType.QualityCheck,
                        Title = "Consider Saving",
                        Description = $"You've made {stats.TotalActionsRecorded} changes this session. Consider saving your work.",
                        Relevance = 0.5,
                        SuggestedAction = new AssistantAction
                        {
                            ActionType = "SaveDocument",
                            Parameters = new Dictionary<string, object>()
                        }
                    });
                }
            }
        }

        private void CheckForQualityOpportunities(Document doc)
        {
            // Check for untagged elements
            var rooms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
                .ToElements();

            var roomTags = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_RoomTags)
                .WhereElementIsNotElementType()
                .ToElements();

            int untaggedRooms = rooms.Count - roomTags.Count;
            if (untaggedRooms > 0)
            {
                AddSuggestion(new Suggestion
                {
                    Type = SuggestionType.QualityCheck,
                    Title = "Untagged Rooms",
                    Description = $"Found {untaggedRooms} rooms without tags. Would you like to tag them?",
                    Relevance = 0.6,
                    SuggestedAction = new AssistantAction
                    {
                        ActionType = "TagAllRooms",
                        Parameters = new Dictionary<string, object> { { "count", untaggedRooms } }
                    }
                });
            }

            // Check for missing door tags
            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .ToElements();

            var doorTags = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_DoorTags)
                .WhereElementIsNotElementType()
                .ToElements();

            int untaggedDoors = doors.Count - doorTags.Count;
            if (untaggedDoors > 5)
            {
                AddSuggestion(new Suggestion
                {
                    Type = SuggestionType.QualityCheck,
                    Title = "Untagged Doors",
                    Description = $"Found {untaggedDoors} doors without tags.",
                    Relevance = 0.5,
                    SuggestedAction = new AssistantAction
                    {
                        ActionType = "TagAllDoors",
                        Parameters = new Dictionary<string, object> { { "count", untaggedDoors } }
                    }
                });
            }
        }

        private void CheckForWorkflowSuggestions(Document doc)
        {
            // Get workflow recommendations from analyzer
            var recommendations = WorkflowAnalyzer.Instance.GetRecommendations(doc);

            foreach (var rec in recommendations)
            {
                AddSuggestion(new Suggestion
                {
                    Type = MapRecommendationType(rec.Type),
                    Title = rec.Title,
                    Description = rec.Description,
                    Relevance = rec.Confidence,
                    SuggestedAction = new AssistantAction
                    {
                        ActionType = rec.SuggestedAction,
                        Parameters = new Dictionary<string, object>()
                    }
                });
            }
        }

        private void CheckForPatternBasedSuggestions()
        {
            // Get patterns from analyzer
            var patterns = WorkflowAnalyzer.Instance.GetPatterns(5);

            // If user is in the middle of a known pattern, suggest completion
            foreach (var pattern in patterns.Take(3))
            {
                if (pattern.Occurrences >= 5)
                {
                    AddSuggestion(new Suggestion
                    {
                        Type = SuggestionType.PatternCompletion,
                        Title = "Recognized Pattern",
                        Description = $"You often: {pattern.Description}",
                        Relevance = 0.4 + (pattern.Occurrences * 0.05),
                        Source = "WorkflowAnalyzer"
                    });
                }
            }
        }

        private void CheckForLayoutSuggestions(Document doc)
        {
            if (string.IsNullOrEmpty(_currentContext.SheetNumber))
                return;

            // Get current sheet
            var sheets = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSheet))
                .Cast<ViewSheet>()
                .Where(s => s.SheetNumber == _currentContext.SheetNumber)
                .ToList();

            if (!sheets.Any())
                return;

            var sheet = sheets.First();
            var viewportIds = sheet.GetAllViewports();

            // If sheet has few viewports, suggest adding more
            if (viewportIds.Count == 0)
            {
                AddSuggestion(new Suggestion
                {
                    Type = SuggestionType.LayoutOptimization,
                    Title = "Empty Sheet",
                    Description = "This sheet has no views. Would you like help placing views?",
                    Relevance = 0.8,
                    SuggestedAction = new AssistantAction
                    {
                        ActionType = "SuggestViewsForSheet",
                        Parameters = new Dictionary<string, object> { { "sheetNumber", sheet.SheetNumber } }
                    }
                });
            }
            else if (viewportIds.Count == 1)
            {
                AddSuggestion(new Suggestion
                {
                    Type = SuggestionType.LayoutOptimization,
                    Title = "Single View Sheet",
                    Description = "This sheet has only one view. Consider adding related views or details.",
                    Relevance = 0.4
                });
            }
        }

        private void AddSuggestion(Suggestion suggestion)
        {
            // Check if similar suggestion already exists
            if (_pendingSuggestions.Any(s => s.Title == suggestion.Title))
                return;

            // Adjust relevance based on past acceptance
            if (_suggestionTypeAcceptance.ContainsKey(suggestion.Type.ToString()))
            {
                int acceptanceCount = _suggestionTypeAcceptance[suggestion.Type.ToString()];
                suggestion.Relevance *= (1 + acceptanceCount * 0.1);
            }

            _pendingSuggestions.Add(suggestion);
        }

        #endregion

        #region Public Query Methods

        /// <summary>
        /// Get current suggestions based on context
        /// </summary>
        public List<Suggestion> GetSuggestions(int maxCount = 5)
        {
            return _pendingSuggestions
                .OrderByDescending(s => s.Relevance)
                .Take(maxCount)
                .ToList();
        }

        /// <summary>
        /// Get proactive assistance summary
        /// </summary>
        public AssistanceSummary GetAssistanceSummary(Document doc)
        {
            return new AssistanceSummary
            {
                CurrentContext = _currentContext,
                TopSuggestions = GetSuggestions(3),
                WorkflowStatistics = WorkflowAnalyzer.Instance.GetStatistics(),
                LearnedPreferences = PreferenceLearner.Instance.GetAllPreferences(),
                SuggestionsAccepted = _suggestionsAccepted,
                SuggestionsRejected = _suggestionsRejected,
                LearningProgress = CalculateLearningProgress()
            };
        }

        /// <summary>
        /// Get what the assistant has learned about the user
        /// </summary>
        public string GetLearningReport()
        {
            var report = new
            {
                generatedAt = DateTime.Now,
                learningProgress = CalculateLearningProgress(),
                workflowPatterns = WorkflowAnalyzer.Instance.GetPatterns(10),
                preferences = PreferenceLearner.Instance.ExportForMemory(),
                actionFrequencies = WorkflowAnalyzer.Instance.GetActionFrequencies(20),
                suggestionEffectiveness = new
                {
                    accepted = _suggestionsAccepted,
                    rejected = _suggestionsRejected,
                    acceptanceRate = _suggestionsAccepted + _suggestionsRejected > 0
                        ? (double)_suggestionsAccepted / (_suggestionsAccepted + _suggestionsRejected)
                        : 0
                }
            };

            return JsonConvert.SerializeObject(report, Formatting.Indented);
        }

        /// <summary>
        /// Ask the assistant for help with a specific task
        /// </summary>
        public TaskAssistance GetTaskAssistance(string taskDescription, Document doc)
        {
            var assistance = new TaskAssistance
            {
                TaskDescription = taskDescription,
                Timestamp = DateTime.Now,
                Steps = new List<AssistanceStep>(),
                Recommendations = new List<string>()
            };

            // Analyze task description
            string taskLower = taskDescription.ToLower();

            if (taskLower.Contains("sheet") || taskLower.Contains("layout"))
            {
                assistance.Steps.Add(new AssistanceStep
                {
                    StepNumber = 1,
                    Description = "I'll analyze your sheet layout preferences",
                    Action = "getSheetLayoutRecommendation"
                });

                // Check for learned preferences
                var preferences = PreferenceLearner.Instance.GetAllPreferences();
                if (preferences.PlacementPreferences.Any(p => p.Category == "Viewport"))
                {
                    assistance.Recommendations.Add("Based on your history, you prefer viewports in the " +
                        preferences.PlacementPreferences.First(p => p.Category == "Viewport").QuadrantPreference);
                }
            }

            if (taskLower.Contains("floor plan") || taskLower.Contains("plan"))
            {
                var preferredScale = PreferenceLearner.Instance.GetPreferredScale("FloorPlan");
                if (preferredScale.HasValue)
                {
                    assistance.Recommendations.Add($"You typically use 1/{preferredScale}\" scale for floor plans");
                }
            }

            if (taskLower.Contains("tag") || taskLower.Contains("annotation"))
            {
                assistance.Steps.Add(new AssistanceStep
                {
                    StepNumber = 1,
                    Description = "I'll check for untagged elements",
                    Action = "checkUntaggedElements"
                });
                assistance.Steps.Add(new AssistanceStep
                {
                    StepNumber = 2,
                    Description = "Tag all elements of the selected categories",
                    Action = "tagElements"
                });
            }

            // Add workflow-based recommendations
            var workflowRecs = WorkflowAnalyzer.Instance.GetRecommendations(doc);
            foreach (var rec in workflowRecs.Where(r => r.Confidence > 0.5))
            {
                assistance.Recommendations.Add($"{rec.Title}: {rec.Description}");
            }

            return assistance;
        }

        #endregion

        #region Feedback Handling

        /// <summary>
        /// Record user acceptance of a suggestion
        /// </summary>
        public void AcceptSuggestion(string suggestionTitle)
        {
            var suggestion = _pendingSuggestions.FirstOrDefault(s => s.Title == suggestionTitle);
            if (suggestion != null)
            {
                _suggestionsAccepted++;

                string typeKey = suggestion.Type.ToString();
                if (!_suggestionTypeAcceptance.ContainsKey(typeKey))
                    _suggestionTypeAcceptance[typeKey] = 0;
                _suggestionTypeAcceptance[typeKey]++;

                _pendingSuggestions.Remove(suggestion);

                Serilog.Log.Information($"Suggestion accepted: {suggestionTitle}");
            }
        }

        /// <summary>
        /// Record user rejection of a suggestion
        /// </summary>
        public void RejectSuggestion(string suggestionTitle)
        {
            var suggestion = _pendingSuggestions.FirstOrDefault(s => s.Title == suggestionTitle);
            if (suggestion != null)
            {
                _suggestionsRejected++;

                string typeKey = suggestion.Type.ToString();
                if (_suggestionTypeAcceptance.ContainsKey(typeKey))
                    _suggestionTypeAcceptance[typeKey] = Math.Max(0, _suggestionTypeAcceptance[typeKey] - 1);

                _pendingSuggestions.Remove(suggestion);

                Serilog.Log.Information($"Suggestion rejected: {suggestionTitle}");
            }
        }

        #endregion

        #region Helper Methods

        private List<string> GetSelectedCategories(ICollection<ElementId> selection, Document doc)
        {
            var categories = new HashSet<string>();
            foreach (var id in selection)
            {
                var element = doc.GetElement(id);
                if (element?.Category != null)
                {
                    categories.Add(element.Category.Name);
                }
            }
            return categories.ToList();
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

        private SuggestionType MapRecommendationType(RecommendationType type)
        {
            switch (type)
            {
                case RecommendationType.NextStep: return SuggestionType.NextStep;
                case RecommendationType.ViewSwitch: return SuggestionType.ViewSwitch;
                case RecommendationType.PatternCompletion: return SuggestionType.PatternCompletion;
                case RecommendationType.QualityCheck: return SuggestionType.QualityCheck;
                case RecommendationType.Optimization: return SuggestionType.LayoutOptimization;
                default: return SuggestionType.General;
            }
        }

        private LearningProgress CalculateLearningProgress()
        {
            var stats = WorkflowAnalyzer.Instance.GetStatistics();
            var prefs = PreferenceLearner.Instance.GetAllPreferences();

            int totalObservations = prefs.TotalObservations;
            int patternsFound = stats.PatternsDetected;
            int preferencesLearned = prefs.ScalePreferences.Count +
                                     prefs.PlacementPreferences.Count(p => p.IsConsistent) +
                                     prefs.NamingPreferences.Count(n => n.DetectedPatterns.Any());

            // Calculate progress (0-100%)
            double progress = Math.Min(100, (totalObservations / 100.0 * 30) +
                                            (patternsFound * 10) +
                                            (preferencesLearned * 5));

            return new LearningProgress
            {
                TotalObservations = totalObservations,
                PatternsDiscovered = patternsFound,
                PreferencesLearned = preferencesLearned,
                ProgressPercentage = progress,
                Status = progress < 20 ? "Learning" :
                         progress < 50 ? "Understanding" :
                         progress < 80 ? "Knowledgeable" : "Expert"
            };
        }

        #endregion
    }

    #region Supporting Types

    public class AssistantContext
    {
        public DateTime Timestamp { get; set; }
        public string DocumentName { get; set; }
        public string DocumentPath { get; set; }
        public long ActiveViewId { get; set; }
        public string ActiveViewName { get; set; }
        public string ActiveViewType { get; set; }
        public bool IsOnSheet { get; set; }
        public string SheetNumber { get; set; }
        public int SelectedElementCount { get; set; }
        public List<string> SelectedCategories { get; set; } = new List<string>();
        public WorkflowStatistics RecentActions { get; set; }
        public WorkflowStatistics WorkflowStatistics { get; set; }
    }

    public enum SuggestionType
    {
        NextStep,
        QualityCheck,
        LayoutOptimization,
        PatternCompletion,
        ViewSwitch,
        General
    }

    public class Suggestion
    {
        public SuggestionType Type { get; set; }
        public string Title { get; set; }
        public string Description { get; set; }
        public double Relevance { get; set; }
        public AssistantAction SuggestedAction { get; set; }
        public string Source { get; set; }
    }

    public class AssistantAction
    {
        public string ActionType { get; set; }
        public Dictionary<string, object> Parameters { get; set; }
    }

    public class AssistanceSummary
    {
        public AssistantContext CurrentContext { get; set; }
        public List<Suggestion> TopSuggestions { get; set; }
        public WorkflowStatistics WorkflowStatistics { get; set; }
        public LearnedPreferences LearnedPreferences { get; set; }
        public int SuggestionsAccepted { get; set; }
        public int SuggestionsRejected { get; set; }
        public LearningProgress LearningProgress { get; set; }
    }

    public class LearningProgress
    {
        public int TotalObservations { get; set; }
        public int PatternsDiscovered { get; set; }
        public int PreferencesLearned { get; set; }
        public double ProgressPercentage { get; set; }
        public string Status { get; set; }
    }

    public class TaskAssistance
    {
        public string TaskDescription { get; set; }
        public DateTime Timestamp { get; set; }
        public List<AssistanceStep> Steps { get; set; }
        public List<string> Recommendations { get; set; }
    }

    public class AssistanceStep
    {
        public int StepNumber { get; set; }
        public string Description { get; set; }
        public string Action { get; set; }
    }

    #endregion
}
