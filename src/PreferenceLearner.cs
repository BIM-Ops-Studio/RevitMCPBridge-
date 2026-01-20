using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json;

namespace RevitMCPBridge
{
    /// <summary>
    /// Learns and stores user preferences from observed behavior.
    /// Tracks preferences for scales, placements, naming, and workflows.
    /// </summary>
    public class PreferenceLearner
    {
        private static PreferenceLearner _instance;
        private static readonly object _lock = new object();

        // Preference categories
        private readonly Dictionary<string, ScalePreference> _scalePreferences = new Dictionary<string, ScalePreference>();
        private readonly Dictionary<string, PlacementPreference> _placementPreferences = new Dictionary<string, PlacementPreference>();
        private readonly Dictionary<string, NamingPreference> _namingPreferences = new Dictionary<string, NamingPreference>();
        private readonly Dictionary<string, WorkflowPreference> _workflowPreferences = new Dictionary<string, WorkflowPreference>();
        private readonly List<UserPreference> _allPreferences = new List<UserPreference>();

        // Observation counters
        private readonly Dictionary<string, int> _observationCounts = new Dictionary<string, int>();

        public static PreferenceLearner Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new PreferenceLearner();
                        }
                    }
                }
                return _instance;
            }
        }

        private PreferenceLearner() { }

        #region Learning from Observations

        /// <summary>
        /// Learn from a view being created or modified
        /// </summary>
        public void LearnFromView(View view, Document doc)
        {
            if (view == null) return;

            try
            {
                // Learn scale preferences
                LearnScalePreference(view);

                // Learn view naming patterns
                LearnNamingPreference("View", view.Name, view.ViewType.ToString());

                // If it's a sheet, learn sheet patterns
                if (view is ViewSheet sheet)
                {
                    LearnSheetPattern(sheet, doc);
                }

                IncrementObservation($"View|{view.ViewType}");
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error learning from view");
            }
        }

        /// <summary>
        /// Learn from viewport placement on a sheet
        /// </summary>
        public void LearnFromViewportPlacement(Viewport viewport, ViewSheet sheet, Document doc)
        {
            if (viewport == null || sheet == null) return;

            try
            {
                var view = doc.GetElement(viewport.ViewId) as View;
                if (view == null) return;

                var boxCenter = viewport.GetBoxCenter();
                var outline = viewport.GetBoxOutline();

                // Learn placement patterns by view type
                string viewType = view.ViewType.ToString();
                string key = $"Viewport|{viewType}";

                if (!_placementPreferences.ContainsKey(key))
                {
                    _placementPreferences[key] = new PlacementPreference
                    {
                        Category = "Viewport",
                        SubCategory = viewType,
                        Positions = new List<PlacementPosition>()
                    };
                }

                // Normalize position relative to sheet (0-1 range)
                var sheetSize = GetSheetSize(sheet, doc);
                double normalizedX = boxCenter.X / sheetSize.Width;
                double normalizedY = boxCenter.Y / sheetSize.Height;

                _placementPreferences[key].Positions.Add(new PlacementPosition
                {
                    NormalizedX = normalizedX,
                    NormalizedY = normalizedY,
                    ActualX = boxCenter.X,
                    ActualY = boxCenter.Y,
                    ViewScale = view.Scale,
                    SheetNumber = sheet.SheetNumber,
                    Timestamp = DateTime.Now
                });

                // Analyze and update preference
                AnalyzePlacementPreference(key);

                IncrementObservation(key);
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error learning from viewport placement");
            }
        }

        /// <summary>
        /// Learn from element placement
        /// </summary>
        public void LearnFromElementPlacement(Element element, Document doc)
        {
            if (element == null) return;

            try
            {
                string category = element.Category?.Name ?? "Unknown";
                string key = $"Element|{category}";

                // Get element location
                var location = element.Location;
                XYZ position = null;

                if (location is LocationPoint locPoint)
                {
                    position = locPoint.Point;
                }
                else if (location is LocationCurve locCurve)
                {
                    position = locCurve.Curve.GetEndPoint(0);
                }

                if (position != null)
                {
                    if (!_placementPreferences.ContainsKey(key))
                    {
                        _placementPreferences[key] = new PlacementPreference
                        {
                            Category = "Element",
                            SubCategory = category,
                            Positions = new List<PlacementPosition>()
                        };
                    }

                    // Get level context
                    var level = doc.GetElement(element.LevelId) as Level;

                    _placementPreferences[key].Positions.Add(new PlacementPosition
                    {
                        ActualX = position.X,
                        ActualY = position.Y,
                        ActualZ = position.Z,
                        LevelName = level?.Name ?? "Unknown",
                        Timestamp = DateTime.Now
                    });
                }

                IncrementObservation(key);
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error learning from element placement");
            }
        }

        /// <summary>
        /// Learn from family/type selection
        /// </summary>
        public void LearnFromTypeSelection(string category, string familyName, string typeName)
        {
            string key = $"TypeSelection|{category}";

            var pref = GetOrCreatePreference<UserPreference>(key, () => new UserPreference
            {
                Category = "TypeSelection",
                Key = category,
                Values = new Dictionary<string, object>()
            });

            // Track frequency of type selections
            string typeKey = $"{familyName}:{typeName}";
            if (!pref.Values.ContainsKey(typeKey))
                pref.Values[typeKey] = 0;
            pref.Values[typeKey] = (int)pref.Values[typeKey] + 1;

            IncrementObservation(key);
        }

        #endregion

        #region Scale Preferences

        private void LearnScalePreference(View view)
        {
            string viewType = view.ViewType.ToString();
            string key = $"Scale|{viewType}";

            if (!_scalePreferences.ContainsKey(key))
            {
                _scalePreferences[key] = new ScalePreference
                {
                    ViewType = viewType,
                    ScaleUsage = new Dictionary<int, int>()
                };
            }

            int scale = view.Scale;
            if (!_scalePreferences[key].ScaleUsage.ContainsKey(scale))
                _scalePreferences[key].ScaleUsage[scale] = 0;
            _scalePreferences[key].ScaleUsage[scale]++;

            // Update preferred scale (most commonly used)
            _scalePreferences[key].PreferredScale = _scalePreferences[key].ScaleUsage
                .OrderByDescending(kvp => kvp.Value)
                .First().Key;
        }

        /// <summary>
        /// Get the preferred scale for a view type
        /// </summary>
        public int? GetPreferredScale(string viewType)
        {
            string key = $"Scale|{viewType}";
            if (_scalePreferences.ContainsKey(key))
            {
                return _scalePreferences[key].PreferredScale;
            }
            return null;
        }

        #endregion

        #region Naming Preferences

        private void LearnNamingPreference(string category, string name, string context)
        {
            string key = $"Naming|{category}|{context}";

            if (!_namingPreferences.ContainsKey(key))
            {
                _namingPreferences[key] = new NamingPreference
                {
                    Category = category,
                    Context = context,
                    Examples = new List<string>(),
                    DetectedPatterns = new List<string>()
                };
            }

            _namingPreferences[key].Examples.Add(name);

            // Keep only last 50 examples
            if (_namingPreferences[key].Examples.Count > 50)
            {
                _namingPreferences[key].Examples.RemoveAt(0);
            }

            // Analyze patterns periodically
            if (_namingPreferences[key].Examples.Count % 10 == 0)
            {
                AnalyzeNamingPatterns(key);
            }
        }

        private void AnalyzeNamingPatterns(string key)
        {
            var pref = _namingPreferences[key];
            pref.DetectedPatterns.Clear();

            // Detect common prefixes
            var prefixes = pref.Examples
                .Where(e => e.Length >= 2)
                .GroupBy(e => e.Substring(0, Math.Min(3, e.Length)))
                .Where(g => g.Count() >= 3)
                .Select(g => g.Key)
                .ToList();

            foreach (var prefix in prefixes)
            {
                pref.DetectedPatterns.Add($"Prefix: {prefix}");
            }

            // Detect common separators
            var separators = new[] { "-", "_", ".", " " };
            foreach (var sep in separators)
            {
                int count = pref.Examples.Count(e => e.Contains(sep));
                if (count >= pref.Examples.Count * 0.5)
                {
                    pref.DetectedPatterns.Add($"Separator: {sep}");
                }
            }

            // Detect numbering patterns
            int hasNumbers = pref.Examples.Count(e => e.Any(char.IsDigit));
            if (hasNumbers >= pref.Examples.Count * 0.7)
            {
                pref.DetectedPatterns.Add("Pattern: Includes numbers");
            }
        }

        private void LearnSheetPattern(ViewSheet sheet, Document doc)
        {
            // Learn sheet numbering pattern
            string sheetNumber = sheet.SheetNumber;
            LearnNamingPreference("SheetNumber", sheetNumber, "Sheet");

            // Learn sheet naming pattern
            LearnNamingPreference("SheetName", sheet.Name, "Sheet");

            // Analyze sheet number format (A101, A-1.1, A3.0.1, etc.)
            AnalyzeSheetNumberFormat(sheetNumber);
        }

        private void AnalyzeSheetNumberFormat(string sheetNumber)
        {
            string key = "SheetNumberFormat";

            var pref = GetOrCreatePreference<UserPreference>(key, () => new UserPreference
            {
                Category = "SheetFormat",
                Key = key,
                Values = new Dictionary<string, object>()
            });

            // Detect format type
            string format = "Unknown";
            if (System.Text.RegularExpressions.Regex.IsMatch(sheetNumber, @"^[A-Z]\d{3}$"))
                format = "A###"; // A101
            else if (System.Text.RegularExpressions.Regex.IsMatch(sheetNumber, @"^[A-Z]-\d+\.\d+$"))
                format = "A-#.#"; // A-1.1
            else if (System.Text.RegularExpressions.Regex.IsMatch(sheetNumber, @"^[A-Z]\d+\.\d+\.\d+$"))
                format = "A#.#.#"; // A3.0.1
            else if (System.Text.RegularExpressions.Regex.IsMatch(sheetNumber, @"^[A-Z]\d+\.\d+$"))
                format = "A#.#"; // A1.1

            if (!pref.Values.ContainsKey(format))
                pref.Values[format] = 0;
            pref.Values[format] = (int)pref.Values[format] + 1;
        }

        #endregion

        #region Placement Preferences

        private void AnalyzePlacementPreference(string key)
        {
            if (!_placementPreferences.ContainsKey(key))
                return;

            var pref = _placementPreferences[key];
            var positions = pref.Positions;

            if (positions.Count < 5)
                return;

            // Calculate average normalized position
            pref.AverageNormalizedX = positions.Average(p => p.NormalizedX);
            pref.AverageNormalizedY = positions.Average(p => p.NormalizedY);

            // Calculate standard deviation (consistency measure)
            double stdDevX = Math.Sqrt(positions.Average(p => Math.Pow(p.NormalizedX - pref.AverageNormalizedX.Value, 2)));
            double stdDevY = Math.Sqrt(positions.Average(p => Math.Pow(p.NormalizedY - pref.AverageNormalizedY.Value, 2)));

            // If std dev is low, user is consistent
            pref.IsConsistent = stdDevX < 0.15 && stdDevY < 0.15;

            // Determine quadrant preference
            if (pref.AverageNormalizedX < 0.5 && pref.AverageNormalizedY > 0.5)
                pref.QuadrantPreference = "TopLeft";
            else if (pref.AverageNormalizedX >= 0.5 && pref.AverageNormalizedY > 0.5)
                pref.QuadrantPreference = "TopRight";
            else if (pref.AverageNormalizedX < 0.5 && pref.AverageNormalizedY <= 0.5)
                pref.QuadrantPreference = "BottomLeft";
            else
                pref.QuadrantPreference = "BottomRight";
        }

        /// <summary>
        /// Get preferred placement position for a category
        /// </summary>
        public PlacementPreference GetPlacementPreference(string category, string subCategory)
        {
            string key = $"{category}|{subCategory}";
            if (_placementPreferences.ContainsKey(key))
            {
                return _placementPreferences[key];
            }
            return null;
        }

        #endregion

        #region Workflow Preferences

        /// <summary>
        /// Learn typical workflow sequence
        /// </summary>
        public void LearnWorkflowSequence(string workflowName, List<string> steps)
        {
            string key = $"Workflow|{workflowName}";

            if (!_workflowPreferences.ContainsKey(key))
            {
                _workflowPreferences[key] = new WorkflowPreference
                {
                    WorkflowName = workflowName,
                    StepSequences = new List<List<string>>()
                };
            }

            _workflowPreferences[key].StepSequences.Add(steps);

            // Analyze for consistent sequence
            if (_workflowPreferences[key].StepSequences.Count >= 3)
            {
                AnalyzeWorkflowSequence(key);
            }
        }

        private void AnalyzeWorkflowSequence(string key)
        {
            var pref = _workflowPreferences[key];
            var sequences = pref.StepSequences;

            // Find common starting steps
            var firstSteps = sequences
                .Where(s => s.Any())
                .Select(s => s.First())
                .GroupBy(s => s)
                .OrderByDescending(g => g.Count())
                .FirstOrDefault();

            if (firstSteps != null && firstSteps.Count() >= sequences.Count * 0.7)
            {
                pref.CommonFirstStep = firstSteps.Key;
            }

            // Find typical step count
            pref.TypicalStepCount = (int)sequences.Average(s => s.Count);
        }

        #endregion

        #region Query Methods

        /// <summary>
        /// Get all learned preferences
        /// </summary>
        public LearnedPreferences GetAllPreferences()
        {
            return new LearnedPreferences
            {
                ScalePreferences = _scalePreferences.Values.ToList(),
                PlacementPreferences = _placementPreferences.Values.ToList(),
                NamingPreferences = _namingPreferences.Values.ToList(),
                WorkflowPreferences = _workflowPreferences.Values.ToList(),
                ObservationCounts = _observationCounts,
                TotalObservations = _observationCounts.Values.Sum()
            };
        }

        /// <summary>
        /// Get preferences summary for Claude Memory storage
        /// </summary>
        public string ExportForMemory()
        {
            var export = new
            {
                exportTime = DateTime.Now,
                summary = new
                {
                    totalObservations = _observationCounts.Values.Sum(),
                    scalePreferencesCount = _scalePreferences.Count,
                    placementPreferencesCount = _placementPreferences.Count,
                    namingPatternsDetected = _namingPreferences.Values.Sum(n => n.DetectedPatterns.Count)
                },
                scalePreferences = _scalePreferences.Select(kvp => new
                {
                    viewType = kvp.Value.ViewType,
                    preferredScale = kvp.Value.PreferredScale,
                    observations = kvp.Value.ScaleUsage.Values.Sum()
                }),
                placementPreferences = _placementPreferences
                    .Where(kvp => kvp.Value.IsConsistent)
                    .Select(kvp => new
                    {
                        category = kvp.Value.Category,
                        subCategory = kvp.Value.SubCategory,
                        quadrant = kvp.Value.QuadrantPreference,
                        normalizedX = kvp.Value.AverageNormalizedX,
                        normalizedY = kvp.Value.AverageNormalizedY
                    }),
                namingPatterns = _namingPreferences.Select(kvp => new
                {
                    category = kvp.Value.Category,
                    context = kvp.Value.Context,
                    patterns = kvp.Value.DetectedPatterns
                }),
                typePreferences = _allPreferences
                    .Where(p => p.Category == "TypeSelection")
                    .Select(p => new
                    {
                        category = p.Key,
                        topTypes = p.Values
                            .OrderByDescending(v => (int)v.Value)
                            .Take(3)
                            .Select(v => v.Key)
                    })
            };

            return JsonConvert.SerializeObject(export, Formatting.Indented);
        }

        /// <summary>
        /// Import previously learned preferences from Claude Memory
        /// </summary>
        public void ImportFromMemory(string json)
        {
            if (string.IsNullOrEmpty(json))
            {
                Serilog.Log.Warning("PreferenceLearner: Empty JSON provided for import");
                return;
            }

            try
            {
                var imported = JsonConvert.DeserializeObject<ImportedPreferences>(json);
                if (imported == null)
                {
                    Serilog.Log.Warning("PreferenceLearner: Failed to deserialize preferences");
                    return;
                }

                // Import scale preferences
                if (imported.ScalePreferences != null)
                {
                    foreach (var scalePref in imported.ScalePreferences)
                    {
                        string key = $"Scale|{scalePref.ViewType}";
                        if (!_scalePreferences.ContainsKey(key))
                        {
                            _scalePreferences[key] = new ScalePreference
                            {
                                ViewType = scalePref.ViewType,
                                PreferredScale = scalePref.PreferredScale,
                                ScaleUsage = new Dictionary<int, int> { { scalePref.PreferredScale, scalePref.Observations } }
                            };
                        }
                    }
                }

                // Import placement preferences
                if (imported.PlacementPreferences != null)
                {
                    foreach (var placePref in imported.PlacementPreferences)
                    {
                        string key = $"{placePref.Category}|{placePref.SubCategory}";
                        if (!_placementPreferences.ContainsKey(key))
                        {
                            _placementPreferences[key] = new PlacementPreference
                            {
                                Category = placePref.Category,
                                SubCategory = placePref.SubCategory,
                                AverageNormalizedX = placePref.NormalizedX,
                                AverageNormalizedY = placePref.NormalizedY,
                                QuadrantPreference = placePref.Quadrant,
                                IsConsistent = true,
                                Positions = new List<PlacementPosition>()
                            };
                        }
                    }
                }

                // Import naming patterns
                if (imported.NamingPatterns != null)
                {
                    foreach (var namePref in imported.NamingPatterns)
                    {
                        string key = $"Naming|{namePref.Category}|{namePref.Context}";
                        if (!_namingPreferences.ContainsKey(key))
                        {
                            _namingPreferences[key] = new NamingPreference
                            {
                                Category = namePref.Category,
                                Context = namePref.Context,
                                DetectedPatterns = namePref.Patterns?.ToList() ?? new List<string>(),
                                Examples = new List<string>()
                            };
                        }
                    }
                }

                Serilog.Log.Information("PreferenceLearner: Successfully imported preferences from memory");
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "PreferenceLearner: Error importing from memory");
            }
        }

        /// <summary>
        /// Clear all learned preferences (for testing or reset)
        /// </summary>
        public void ClearAllPreferences()
        {
            _scalePreferences.Clear();
            _placementPreferences.Clear();
            _namingPreferences.Clear();
            _workflowPreferences.Clear();
            _allPreferences.Clear();
            _observationCounts.Clear();
            Serilog.Log.Information("PreferenceLearner: All preferences cleared");
        }

        #endregion

        #region Helper Methods

        private T GetOrCreatePreference<T>(string key, Func<T> createFunc) where T : UserPreference
        {
            var existing = _allPreferences.FirstOrDefault(p => $"{p.Category}|{p.Key}" == key);
            if (existing != null)
                return (T)existing;

            var newPref = createFunc();
            _allPreferences.Add(newPref);
            return newPref;
        }

        private void IncrementObservation(string key)
        {
            if (!_observationCounts.ContainsKey(key))
                _observationCounts[key] = 0;
            _observationCounts[key]++;
        }

        private (double Width, double Height) GetSheetSize(ViewSheet sheet, Document doc)
        {
            // Default to ARCH D (36" x 24")
            double width = 3.0;  // 36 inches in feet
            double height = 2.0; // 24 inches in feet

            try
            {
                var titleBlock = new FilteredElementCollector(doc, sheet.Id)
                    .OfCategory(BuiltInCategory.OST_TitleBlocks)
                    .FirstElement() as FamilyInstance;

                if (titleBlock != null)
                {
                    var widthParam = titleBlock.LookupParameter("Sheet Width");
                    var heightParam = titleBlock.LookupParameter("Sheet Height");

                    if (widthParam != null) width = widthParam.AsDouble();
                    if (heightParam != null) height = heightParam.AsDouble();
                }
            }
            catch { }

            return (width, height);
        }

        #endregion
    }

    #region Supporting Types

    public class UserPreference
    {
        public string Category { get; set; }
        public string Key { get; set; }
        public Dictionary<string, object> Values { get; set; } = new Dictionary<string, object>();
    }

    public class ScalePreference
    {
        public string ViewType { get; set; }
        public int PreferredScale { get; set; }
        public Dictionary<int, int> ScaleUsage { get; set; } = new Dictionary<int, int>();
    }

    public class PlacementPreference
    {
        public string Category { get; set; }
        public string SubCategory { get; set; }
        public List<PlacementPosition> Positions { get; set; } = new List<PlacementPosition>();
        public double? AverageNormalizedX { get; set; }
        public double? AverageNormalizedY { get; set; }
        public bool IsConsistent { get; set; }
        public string QuadrantPreference { get; set; }
    }

    public class PlacementPosition
    {
        public double NormalizedX { get; set; }
        public double NormalizedY { get; set; }
        public double ActualX { get; set; }
        public double ActualY { get; set; }
        public double ActualZ { get; set; }
        public int ViewScale { get; set; }
        public string SheetNumber { get; set; }
        public string LevelName { get; set; }
        public DateTime Timestamp { get; set; }
    }

    public class NamingPreference
    {
        public string Category { get; set; }
        public string Context { get; set; }
        public List<string> Examples { get; set; } = new List<string>();
        public List<string> DetectedPatterns { get; set; } = new List<string>();
    }

    public class WorkflowPreference
    {
        public string WorkflowName { get; set; }
        public List<List<string>> StepSequences { get; set; } = new List<List<string>>();
        public string CommonFirstStep { get; set; }
        public int TypicalStepCount { get; set; }
    }

    public class LearnedPreferences
    {
        public List<ScalePreference> ScalePreferences { get; set; }
        public List<PlacementPreference> PlacementPreferences { get; set; }
        public List<NamingPreference> NamingPreferences { get; set; }
        public List<WorkflowPreference> WorkflowPreferences { get; set; }
        public Dictionary<string, int> ObservationCounts { get; set; }
        public int TotalObservations { get; set; }
    }

    /// <summary>
    /// Structure for importing preferences from Claude Memory
    /// </summary>
    public class ImportedPreferences
    {
        [JsonProperty("scalePreferences")]
        public List<ImportedScalePref> ScalePreferences { get; set; }

        [JsonProperty("placementPreferences")]
        public List<ImportedPlacementPref> PlacementPreferences { get; set; }

        [JsonProperty("namingPatterns")]
        public List<ImportedNamingPref> NamingPatterns { get; set; }
    }

    public class ImportedScalePref
    {
        [JsonProperty("viewType")]
        public string ViewType { get; set; }

        [JsonProperty("preferredScale")]
        public int PreferredScale { get; set; }

        [JsonProperty("observations")]
        public int Observations { get; set; }
    }

    public class ImportedPlacementPref
    {
        [JsonProperty("category")]
        public string Category { get; set; }

        [JsonProperty("subCategory")]
        public string SubCategory { get; set; }

        [JsonProperty("quadrant")]
        public string Quadrant { get; set; }

        [JsonProperty("normalizedX")]
        public double? NormalizedX { get; set; }

        [JsonProperty("normalizedY")]
        public double? NormalizedY { get; set; }
    }

    public class ImportedNamingPref
    {
        [JsonProperty("category")]
        public string Category { get; set; }

        [JsonProperty("context")]
        public string Context { get; set; }

        [JsonProperty("patterns")]
        public List<string> Patterns { get; set; }
    }

    #endregion
}
