using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge
{
    /// <summary>
    /// Level 4 Intelligence: Proactive monitoring and suggestion engine.
    /// Monitors model state, detects gaps, and generates actionable suggestions.
    /// </summary>
    public class ProactiveMonitor
    {
        private static ProactiveMonitor _instance;
        private static readonly object _lock = new object();

        // State tracking
        private ModelStateSnapshot _lastSnapshot;
        private DateTime _lastSnapshotTime;
        private readonly TimeSpan _snapshotInterval = TimeSpan.FromSeconds(30);

        // Focus context for context-aware decisions (Phase 4 of Predictive Intelligence)
        private FocusContext _currentFocus = new FocusContext();
        private readonly object _focusLock = new object();

        // Suggestion tracking (avoid repeating suggestions)
        private readonly Dictionary<string, DateTime> _shownSuggestions = new Dictionary<string, DateTime>();
        private readonly TimeSpan _suggestionCooldown = TimeSpan.FromMinutes(10);

        // Gap detection thresholds
        private const int MAX_UNPLACED_VIEWS_WARNING = 5;
        private const int MAX_UNTAGGED_ROOMS_WARNING = 3;
        private const int MAX_EMPTY_SHEETS_WARNING = 2;

        public static ProactiveMonitor Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new ProactiveMonitor();
                        }
                    }
                }
                return _instance;
            }
        }

        private ProactiveMonitor() { }

        #region Focus Context (Phase 4 Predictive Intelligence)

        /// <summary>
        /// Get the current focus context (thread-safe)
        /// </summary>
        public FocusContext CurrentFocus
        {
            get
            {
                lock (_focusLock)
                {
                    return _currentFocus;
                }
            }
        }

        /// <summary>
        /// Update focus context from the current UI state
        /// </summary>
        public void UpdateFocusContext(UIApplication uiApp)
        {
            if (uiApp?.ActiveUIDocument == null)
                return;

            try
            {
                var uiDoc = uiApp.ActiveUIDocument;
                var doc = uiDoc.Document;
                var activeView = doc.ActiveView;

                lock (_focusLock)
                {
                    // Update active view info
                    if (activeView != null)
                    {
                        _currentFocus.ActiveViewId = activeView.Id.Value;
                        _currentFocus.ActiveViewType = activeView.ViewType.ToString();

                        // Check if viewing a sheet
                        if (activeView is ViewSheet sheet)
                        {
                            _currentFocus.ActiveSheetId = sheet.Id.Value;
                        }
                        else
                        {
                            _currentFocus.ActiveSheetId = null;
                        }

                        // Get level if applicable
                        if (activeView.GenLevel != null)
                        {
                            _currentFocus.ActiveLevel = activeView.GenLevel.Name;
                        }
                        else
                        {
                            _currentFocus.ActiveLevel = null;
                        }
                    }

                    // Update selected elements
                    var selection = uiDoc.Selection.GetElementIds();
                    _currentFocus.SelectedElementIds = selection.Select(id => id.Value).ToList();

                    // Get selected element types
                    _currentFocus.SelectedElementTypes = selection
                        .Select(id => doc.GetElement(id))
                        .Where(e => e != null)
                        .Select(e => e.Category?.Name ?? e.GetType().Name)
                        .Distinct()
                        .ToList();

                    _currentFocus.UpdatedAt = DateTime.UtcNow;

                    Log.Debug("[ProactiveMonitor] Focus updated: {Summary}", _currentFocus.GetSummary());
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[ProactiveMonitor] Error updating focus context");
            }
        }

        /// <summary>
        /// Record when a view is placed on a sheet (for preference tracking)
        /// </summary>
        public void RecordViewPlacement(string sheetNumber, string viewType)
        {
            lock (_focusLock)
            {
                _currentFocus.RecordViewPlacement(sheetNumber, viewType);
                Log.Debug("[ProactiveMonitor] Recorded view placement: {ViewType} on {SheetNumber}",
                    viewType, sheetNumber);
            }
        }

        /// <summary>
        /// Get the last sheet number where a view was placed
        /// </summary>
        public string GetLastPlacedSheetNumber()
        {
            lock (_focusLock)
            {
                // Only return if not stale
                if (!_currentFocus.IsStale)
                    return _currentFocus.LastPlacedSheetNumber;
                return null;
            }
        }

        /// <summary>
        /// Check if the user is currently working on sheets (for context-aware suggestions)
        /// </summary>
        public bool IsWorkingOnSheets()
        {
            lock (_focusLock)
            {
                return _currentFocus.ActiveSheetId.HasValue ||
                       !string.IsNullOrEmpty(_currentFocus.LastPlacedSheetNumber);
            }
        }

        #endregion

        #region Model State Monitoring

        /// <summary>
        /// Take a snapshot of current model state for comparison
        /// </summary>
        public ModelStateSnapshot TakeSnapshot(Document doc)
        {
            if (doc == null) return null;

            try
            {
                var snapshot = new ModelStateSnapshot
                {
                    Timestamp = DateTime.Now,
                    ProjectName = doc.Title,

                    // Count elements by category
                    WallCount = new FilteredElementCollector(doc)
                        .OfClass(typeof(Wall))
                        .GetElementCount(),

                    RoomCount = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_Rooms)
                        .WhereElementIsNotElementType()
                        .GetElementCount(),

                    DoorCount = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_Doors)
                        .WhereElementIsNotElementType()
                        .GetElementCount(),

                    WindowCount = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_Windows)
                        .WhereElementIsNotElementType()
                        .GetElementCount(),

                    // View and sheet counts
                    ViewCount = new FilteredElementCollector(doc)
                        .OfClass(typeof(View))
                        .Cast<View>()
                        .Count(v => !v.IsTemplate),

                    SheetCount = new FilteredElementCollector(doc)
                        .OfClass(typeof(ViewSheet))
                        .GetElementCount(),

                    // Detect unplaced views
                    UnplacedViews = GetUnplacedViews(doc),

                    // Detect untagged rooms
                    UntaggedRooms = GetUntaggedRooms(doc),

                    // Detect empty sheets
                    EmptySheets = GetEmptySheets(doc),

                    // Detect rooms without numbers
                    RoomsWithoutNumbers = GetRoomsWithoutNumbers(doc),

                    // Recent warnings
                    WarningCount = doc.GetWarnings()?.Count ?? 0
                };

                _lastSnapshot = snapshot;
                _lastSnapshotTime = DateTime.Now;

                return snapshot;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error taking model snapshot");
                return null;
            }
        }

        /// <summary>
        /// Compare current state to last snapshot and detect changes
        /// </summary>
        public StateChangeReport CompareToLastSnapshot(Document doc)
        {
            var currentSnapshot = TakeSnapshot(doc);
            if (currentSnapshot == null || _lastSnapshot == null)
            {
                return new StateChangeReport { HasChanges = false };
            }

            var report = new StateChangeReport
            {
                HasChanges = false,
                Changes = new List<StateChange>()
            };

            // Compare element counts
            CompareCount(report, "Walls", _lastSnapshot.WallCount, currentSnapshot.WallCount);
            CompareCount(report, "Rooms", _lastSnapshot.RoomCount, currentSnapshot.RoomCount);
            CompareCount(report, "Doors", _lastSnapshot.DoorCount, currentSnapshot.DoorCount);
            CompareCount(report, "Windows", _lastSnapshot.WindowCount, currentSnapshot.WindowCount);
            CompareCount(report, "Views", _lastSnapshot.ViewCount, currentSnapshot.ViewCount);
            CompareCount(report, "Sheets", _lastSnapshot.SheetCount, currentSnapshot.SheetCount);

            return report;
        }

        private void CompareCount(StateChangeReport report, string category, int oldCount, int newCount)
        {
            if (oldCount != newCount)
            {
                report.HasChanges = true;
                report.Changes.Add(new StateChange
                {
                    Category = category,
                    OldValue = oldCount,
                    NewValue = newCount,
                    Delta = newCount - oldCount,
                    ChangeType = newCount > oldCount ? "Added" : "Removed"
                });
            }
        }

        #endregion

        #region Gap Detection

        private List<ViewInfo> GetUnplacedViews(Document doc)
        {
            var unplaced = new List<ViewInfo>();

            try
            {
                // Get all views that can be placed on sheets
                var placeableViews = new FilteredElementCollector(doc)
                    .OfClass(typeof(View))
                    .Cast<View>()
                    .Where(v => !v.IsTemplate && CanBePlacedOnSheet(v))
                    .ToList();

                // Get all viewports to find which views are placed
                var placedViewIds = new FilteredElementCollector(doc)
                    .OfClass(typeof(Viewport))
                    .Cast<Viewport>()
                    .Select(vp => vp.ViewId)
                    .ToHashSet();

                foreach (var view in placeableViews)
                {
                    if (!placedViewIds.Contains(view.Id))
                    {
                        unplaced.Add(new ViewInfo
                        {
                            Id = view.Id.Value,
                            Name = view.Name,
                            ViewType = view.ViewType.ToString()
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error getting unplaced views");
            }

            return unplaced;
        }

        private bool CanBePlacedOnSheet(View view)
        {
            // Views that can be placed on sheets
            var placeableTypes = new[]
            {
                ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Section,
                ViewType.Elevation, ViewType.ThreeD, ViewType.Detail,
                ViewType.DraftingView, ViewType.Legend, ViewType.Schedule
            };
            return placeableTypes.Contains(view.ViewType);
        }

        private List<RoomInfo> GetUntaggedRooms(Document doc)
        {
            var untagged = new List<RoomInfo>();

            try
            {
                var rooms = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Rooms)
                    .WhereElementIsNotElementType()
                    .Cast<Room>()
                    .Where(r => r.Area > 0) // Only placed rooms
                    .ToList();

                var taggedRoomIds = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_RoomTags)
                    .WhereElementIsNotElementType()
                    .Cast<RoomTag>()
                    .Where(t => t.Room != null)
                    .Select(t => t.Room.Id)
                    .ToHashSet();

                foreach (var room in rooms)
                {
                    if (!taggedRoomIds.Contains(room.Id))
                    {
                        untagged.Add(new RoomInfo
                        {
                            Id = room.Id.Value,
                            Name = room.Name,
                            Number = room.Number,
                            Level = room.Level?.Name
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error getting untagged rooms");
            }

            return untagged;
        }

        private List<SheetInfo> GetEmptySheets(Document doc)
        {
            var empty = new List<SheetInfo>();

            try
            {
                var sheets = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSheet))
                    .Cast<ViewSheet>()
                    .ToList();

                foreach (var sheet in sheets)
                {
                    var viewports = sheet.GetAllViewports();
                    if (viewports == null || viewports.Count == 0)
                    {
                        empty.Add(new SheetInfo
                        {
                            Id = sheet.Id.Value,
                            Number = sheet.SheetNumber,
                            Name = sheet.Name
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error getting empty sheets");
            }

            return empty;
        }

        private List<RoomInfo> GetRoomsWithoutNumbers(Document doc)
        {
            var unnumbered = new List<RoomInfo>();

            try
            {
                var rooms = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Rooms)
                    .WhereElementIsNotElementType()
                    .Cast<Room>()
                    .Where(r => r.Area > 0 && string.IsNullOrWhiteSpace(r.Number))
                    .ToList();

                foreach (var room in rooms)
                {
                    unnumbered.Add(new RoomInfo
                    {
                        Id = room.Id.Value,
                        Name = room.Name,
                        Number = room.Number,
                        Level = room.Level?.Name
                    });
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error getting unnumbered rooms");
            }

            return unnumbered;
        }

        #endregion

        #region Session Lifecycle Integration

        // Methods that modify model state and should trigger monitoring
        private static readonly HashSet<string> _modifyingMethods = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "createWall", "createWalls", "deleteElements", "modifyElement",
            "placeDoor", "placeWindow", "placeFamilyInstance",
            "createRoom", "createRooms", "tagRoom", "tagRooms",
            "createSheet", "placeViewOnSheet", "createView",
            "setParameter", "setParameters", "batchSetParameters",
            "createSchedule", "addScheduleFields",
            "loadFamily", "createFloor", "createCeiling",
            "createGridLine", "createLevel", "createDimension"
        };

        private DateTime _lastOperationTime = DateTime.MinValue;
        private int _operationCount = 0;
        private const int OperationsBeforeSnapshot = 5; // Take snapshot every N operations

        /// <summary>
        /// Track an MCP operation for session monitoring.
        /// Called after each MCP method execution.
        /// </summary>
        public void TrackOperation(string methodName, bool success, Document doc)
        {
            try
            {
                _operationCount++;

                // If this was a modifying operation and it succeeded, consider taking a snapshot
                if (success && _modifyingMethods.Contains(methodName))
                {
                    _lastOperationTime = DateTime.Now;

                    // Take periodic snapshots to track model changes
                    if (_operationCount % OperationsBeforeSnapshot == 0 && doc != null)
                    {
                        TakeSnapshot(doc);
                        Log.Debug("Proactive snapshot taken after {Count} operations", _operationCount);
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Error tracking operation in ProactiveMonitor");
            }
        }

        /// <summary>
        /// Get current monitoring statistics
        /// </summary>
        public object GetMonitoringStats()
        {
            return new
            {
                operationCount = _operationCount,
                lastOperationTime = _lastOperationTime,
                snapshotCount = _lastSnapshot != null ? 1 : 0,
                suggestionCooldownsActive = _shownSuggestions.Count
            };
        }

        /// <summary>
        /// Check if proactive analysis should run (based on time since last operation)
        /// </summary>
        public bool ShouldRunProactiveAnalysis()
        {
            if (_lastSnapshot == null) return true;
            if (_operationCount > 0 && (DateTime.Now - _lastOperationTime).TotalMinutes > 5)
            {
                return true; // Run if idle for 5+ minutes after operations
            }
            return false;
        }

        #endregion

        #region Suggestion Engine

        /// <summary>
        /// Generate proactive suggestions based on current model state
        /// </summary>
        public List<MonitorSuggestion> GenerateSuggestions(Document doc)
        {
            var suggestions = new List<MonitorSuggestion>();
            var snapshot = TakeSnapshot(doc);

            if (snapshot == null) return suggestions;

            // Gap-based suggestions
            AddUnplacedViewSuggestions(suggestions, snapshot);
            AddUntaggedRoomSuggestions(suggestions, snapshot);
            AddEmptySheetSuggestions(suggestions, snapshot);
            AddRoomNumberingSuggestions(suggestions, snapshot);

            // Warning-based suggestions
            if (snapshot.WarningCount > 10)
            {
                AddSuggestionIfNew(suggestions, new MonitorSuggestion
                {
                    Id = "warnings_high",
                    Type = MonitorSuggestionType.Warning,
                    Priority = SuggestionPriority.Medium,
                    Title = "Model Has Many Warnings",
                    Description = $"Your model has {snapshot.WarningCount} warnings. Consider reviewing and resolving them.",
                    ActionMethod = "getProjectWarnings",
                    ActionParams = new JObject()
                });
            }

            // Pattern-based suggestions (from PreferenceLearner)
            AddPatternBasedSuggestions(suggestions, doc);

            // Correction-based suggestions (from CorrectionLearner)
            AddCorrectionBasedSuggestions(suggestions);

            // Filter out recently shown suggestions
            return suggestions.Where(s => !WasRecentlyShown(s.Id)).ToList();
        }

        private void AddUnplacedViewSuggestions(List<MonitorSuggestion> suggestions, ModelStateSnapshot snapshot)
        {
            if (snapshot.UnplacedViews.Count > MAX_UNPLACED_VIEWS_WARNING)
            {
                var floorPlans = snapshot.UnplacedViews.Where(v => v.ViewType == "FloorPlan").ToList();
                var sections = snapshot.UnplacedViews.Where(v => v.ViewType == "Section").ToList();

                if (floorPlans.Count > 0)
                {
                    AddSuggestionIfNew(suggestions, new MonitorSuggestion
                    {
                        Id = $"unplaced_floorplans_{floorPlans.Count}",
                        Type = MonitorSuggestionType.Action,
                        Priority = SuggestionPriority.High,
                        Title = "Unplaced Floor Plans",
                        Description = $"You have {floorPlans.Count} floor plans not placed on sheets. Would you like to create sheets for them?",
                        ActionMethod = "autoPlaceView",
                        ActionParams = new JObject
                        {
                            ["viewIds"] = JArray.FromObject(floorPlans.Select(v => v.Id)),
                            ["autoCreateSheets"] = true
                        },
                        AffectedElements = floorPlans.Select(v => v.Id).ToList()
                    });
                }

                if (sections.Count > 0)
                {
                    AddSuggestionIfNew(suggestions, new MonitorSuggestion
                    {
                        Id = $"unplaced_sections_{sections.Count}",
                        Type = MonitorSuggestionType.Action,
                        Priority = SuggestionPriority.Medium,
                        Title = "Unplaced Sections",
                        Description = $"You have {sections.Count} sections not on sheets.",
                        ActionMethod = "autoPlaceView",
                        ActionParams = new JObject
                        {
                            ["viewIds"] = JArray.FromObject(sections.Select(v => v.Id))
                        },
                        AffectedElements = sections.Select(v => v.Id).ToList()
                    });
                }
            }
        }

        private void AddUntaggedRoomSuggestions(List<MonitorSuggestion> suggestions, ModelStateSnapshot snapshot)
        {
            if (snapshot.UntaggedRooms.Count > MAX_UNTAGGED_ROOMS_WARNING)
            {
                AddSuggestionIfNew(suggestions, new MonitorSuggestion
                {
                    Id = $"untagged_rooms_{snapshot.UntaggedRooms.Count}",
                    Type = MonitorSuggestionType.Action,
                    Priority = SuggestionPriority.High,
                    Title = "Untagged Rooms",
                    Description = $"You have {snapshot.UntaggedRooms.Count} rooms without tags. Tag them now?",
                    ActionMethod = "tagAllRooms",
                    ActionParams = new JObject
                    {
                        ["roomIds"] = JArray.FromObject(snapshot.UntaggedRooms.Select(r => r.Id))
                    },
                    AffectedElements = snapshot.UntaggedRooms.Select(r => r.Id).ToList()
                });
            }
        }

        private void AddEmptySheetSuggestions(List<MonitorSuggestion> suggestions, ModelStateSnapshot snapshot)
        {
            if (snapshot.EmptySheets.Count > MAX_EMPTY_SHEETS_WARNING)
            {
                AddSuggestionIfNew(suggestions, new MonitorSuggestion
                {
                    Id = $"empty_sheets_{snapshot.EmptySheets.Count}",
                    Type = MonitorSuggestionType.Warning,
                    Priority = SuggestionPriority.Low,
                    Title = "Empty Sheets",
                    Description = $"You have {snapshot.EmptySheets.Count} empty sheets: {string.Join(", ", snapshot.EmptySheets.Take(3).Select(s => s.Number))}...",
                    ActionMethod = null, // Info only
                    AffectedElements = snapshot.EmptySheets.Select(s => s.Id).ToList()
                });
            }
        }

        private void AddRoomNumberingSuggestions(List<MonitorSuggestion> suggestions, ModelStateSnapshot snapshot)
        {
            if (snapshot.RoomsWithoutNumbers.Count > 0)
            {
                AddSuggestionIfNew(suggestions, new MonitorSuggestion
                {
                    Id = $"unnumbered_rooms_{snapshot.RoomsWithoutNumbers.Count}",
                    Type = MonitorSuggestionType.Action,
                    Priority = SuggestionPriority.High,
                    Title = "Rooms Without Numbers",
                    Description = $"{snapshot.RoomsWithoutNumbers.Count} rooms have no number assigned.",
                    ActionMethod = "autoNumberRooms",
                    ActionParams = new JObject
                    {
                        ["roomIds"] = JArray.FromObject(snapshot.RoomsWithoutNumbers.Select(r => r.Id))
                    },
                    AffectedElements = snapshot.RoomsWithoutNumbers.Select(r => r.Id).ToList()
                });
            }
        }

        private void AddPatternBasedSuggestions(List<MonitorSuggestion> suggestions, Document doc)
        {
            try
            {
                var prefs = PreferenceLearner.Instance.GetAllPreferences();
                if (prefs == null) return;

                // If user has consistent scale preferences, suggest applying them
                if (prefs.ScalePreferences?.Count > 0)
                {
                    var mostUsedScale = prefs.ScalePreferences
                        .Where(s => s.ScaleUsage != null && s.ScaleUsage.Any())
                        .OrderByDescending(s => s.ScaleUsage.Values.Sum())
                        .FirstOrDefault();

                    if (mostUsedScale != null && mostUsedScale.ScaleUsage.Values.Sum() > 5)
                    {
                        AddSuggestionIfNew(suggestions, new MonitorSuggestion
                        {
                            Id = "learned_scale_pattern",
                            Type = MonitorSuggestionType.Info,
                            Priority = SuggestionPriority.Low,
                            Title = "Learned Scale Pattern",
                            Description = $"You typically use 1:{mostUsedScale.PreferredScale} for {mostUsedScale.ViewType} views.",
                            ActionMethod = null
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error generating pattern-based suggestions");
            }
        }

        private void AddCorrectionBasedSuggestions(List<MonitorSuggestion> suggestions)
        {
            try
            {
                var correctionLearner = new CorrectionLearner();
                var stats = correctionLearner.GetStats();

                if (stats.TotalCorrections > 5 && stats.MostCommonCategory != null)
                {
                    AddSuggestionIfNew(suggestions, new MonitorSuggestion
                    {
                        Id = $"common_corrections_{stats.MostCommonCategory}",
                        Type = MonitorSuggestionType.Info,
                        Priority = SuggestionPriority.Low,
                        Title = "Common Correction Pattern",
                        Description = $"You frequently correct {stats.MostCommonCategory} operations. Consider reviewing the correction history.",
                        ActionMethod = "getMethodCorrections",
                        ActionParams = new JObject { ["category"] = stats.MostCommonCategory }
                    });
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error generating correction-based suggestions");
            }
        }

        private void AddSuggestionIfNew(List<MonitorSuggestion> suggestions, MonitorSuggestion suggestion)
        {
            if (!suggestions.Any(s => s.Id == suggestion.Id))
            {
                suggestions.Add(suggestion);
            }
        }

        private bool WasRecentlyShown(string suggestionId)
        {
            if (_shownSuggestions.TryGetValue(suggestionId, out var lastShown))
            {
                return DateTime.Now - lastShown < _suggestionCooldown;
            }
            return false;
        }

        /// <summary>
        /// Mark a suggestion as shown to avoid repeating
        /// </summary>
        public void MarkSuggestionShown(string suggestionId)
        {
            _shownSuggestions[suggestionId] = DateTime.Now;
        }

        /// <summary>
        /// Clear suggestion history (for testing or reset)
        /// </summary>
        public void ClearSuggestionHistory()
        {
            _shownSuggestions.Clear();
        }

        #endregion

        #region Auto-Correction

        /// <summary>
        /// Get corrections that can be automatically applied based on confidence
        /// </summary>
        public List<AutoCorrection> GetAutoApplicableCorrections(string method, JObject parameters)
        {
            var autoCorrections = new List<AutoCorrection>();

            try
            {
                var correctionLearner = new CorrectionLearner();
                var corrections = correctionLearner.GetMethodCorrections(method);

                foreach (var correction in corrections)
                {
                    // Only auto-apply if it's been successfully used multiple times
                    if (correction.TimesApplied >= 3)
                    {
                        autoCorrections.Add(new AutoCorrection
                        {
                            CorrectionId = correction.Id,
                            Method = method,
                            OriginalIssue = correction.WhatWentWrong,
                            SuggestedFix = correction.CorrectApproach,
                            Confidence = CalculateConfidence(correction),
                            CanAutoApply = correction.TimesApplied >= 5 // Higher threshold for auto-apply
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error getting auto-applicable corrections");
            }

            return autoCorrections;
        }

        private double CalculateConfidence(Correction correction)
        {
            // Simple confidence calculation based on usage
            // More usage = higher confidence
            double baseConfidence = 0.5;
            double usageBonus = Math.Min(0.4, correction.TimesApplied * 0.08);
            double recencyBonus = correction.LastApplied.HasValue &&
                (DateTime.Now - correction.LastApplied.Value).TotalDays < 7 ? 0.1 : 0;

            return Math.Min(1.0, baseConfidence + usageBonus + recencyBonus);
        }

        #endregion

        #region Proactive Analysis

        /// <summary>
        /// Run full proactive analysis and return comprehensive report
        /// </summary>
        public ProactiveReport RunProactiveAnalysis(Document doc)
        {
            var report = new ProactiveReport
            {
                Timestamp = DateTime.Now,
                ProjectName = doc?.Title
            };

            try
            {
                // Take snapshot
                report.Snapshot = TakeSnapshot(doc);

                // Compare to last if available
                if (_lastSnapshot != null)
                {
                    report.Changes = CompareToLastSnapshot(doc);
                }

                // Generate suggestions
                report.Suggestions = GenerateSuggestions(doc);

                // Summarize
                report.Summary = GenerateSummary(report);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error running proactive analysis");
                report.Error = ex.Message;
            }

            return report;
        }

        private string GenerateSummary(ProactiveReport report)
        {
            var parts = new List<string>();

            if (report.Snapshot != null)
            {
                parts.Add($"Model: {report.Snapshot.ViewCount} views, {report.Snapshot.SheetCount} sheets");

                if (report.Snapshot.UnplacedViews.Count > 0)
                    parts.Add($"{report.Snapshot.UnplacedViews.Count} unplaced views");

                if (report.Snapshot.UntaggedRooms.Count > 0)
                    parts.Add($"{report.Snapshot.UntaggedRooms.Count} untagged rooms");

                if (report.Snapshot.WarningCount > 0)
                    parts.Add($"{report.Snapshot.WarningCount} warnings");
            }

            if (report.Suggestions.Count > 0)
            {
                var highPriority = report.Suggestions.Count(s => s.Priority == SuggestionPriority.High);
                if (highPriority > 0)
                    parts.Add($"{highPriority} high-priority suggestions");
            }

            return string.Join(". ", parts);
        }

        #endregion
    }

    #region Data Classes

    public class ModelStateSnapshot
    {
        public DateTime Timestamp { get; set; }
        public string ProjectName { get; set; }

        // Element counts
        public int WallCount { get; set; }
        public int RoomCount { get; set; }
        public int DoorCount { get; set; }
        public int WindowCount { get; set; }
        public int ViewCount { get; set; }
        public int SheetCount { get; set; }

        // Gap detection results
        public List<ViewInfo> UnplacedViews { get; set; } = new List<ViewInfo>();
        public List<RoomInfo> UntaggedRooms { get; set; } = new List<RoomInfo>();
        public List<SheetInfo> EmptySheets { get; set; } = new List<SheetInfo>();
        public List<RoomInfo> RoomsWithoutNumbers { get; set; } = new List<RoomInfo>();

        // Warnings
        public int WarningCount { get; set; }
    }

    public class ViewInfo
    {
        public long Id { get; set; }
        public string Name { get; set; }
        public string ViewType { get; set; }
    }

    public class RoomInfo
    {
        public long Id { get; set; }
        public string Name { get; set; }
        public string Number { get; set; }
        public string Level { get; set; }
    }

    public class SheetInfo
    {
        public long Id { get; set; }
        public string Number { get; set; }
        public string Name { get; set; }
    }

    public class StateChangeReport
    {
        public bool HasChanges { get; set; }
        public List<StateChange> Changes { get; set; } = new List<StateChange>();
    }

    public class StateChange
    {
        public string Category { get; set; }
        public int OldValue { get; set; }
        public int NewValue { get; set; }
        public int Delta { get; set; }
        public string ChangeType { get; set; }
    }

    public class MonitorSuggestion
    {
        public string Id { get; set; }
        public MonitorSuggestionType Type { get; set; }
        public SuggestionPriority Priority { get; set; }
        public string Title { get; set; }
        public string Description { get; set; }
        public string ActionMethod { get; set; }
        public JObject ActionParams { get; set; }
        public List<long> AffectedElements { get; set; } = new List<long>();
    }

    public enum MonitorSuggestionType
    {
        Info,       // Just informational
        Warning,    // Something might be wrong
        Action      // Actionable suggestion with method to execute
    }

    public enum SuggestionPriority
    {
        Low,
        Medium,
        High
    }

    public class AutoCorrection
    {
        public string CorrectionId { get; set; }
        public string Method { get; set; }
        public string OriginalIssue { get; set; }
        public string SuggestedFix { get; set; }
        public double Confidence { get; set; }
        public bool CanAutoApply { get; set; }
    }

    public class ProactiveReport
    {
        public DateTime Timestamp { get; set; }
        public string ProjectName { get; set; }
        public ModelStateSnapshot Snapshot { get; set; }
        public StateChangeReport Changes { get; set; }
        public List<MonitorSuggestion> Suggestions { get; set; } = new List<MonitorSuggestion>();
        public string Summary { get; set; }
        public string Error { get; set; }
    }

    #endregion
}
