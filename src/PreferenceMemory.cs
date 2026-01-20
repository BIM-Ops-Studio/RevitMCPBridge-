using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge
{
    /// <summary>
    /// Learns and remembers user preferences from interactions.
    /// Applies these preferences to improve future responses.
    /// </summary>
    public class PreferenceMemory
    {
        private readonly string _preferencesFile;
        private UserPreferences _preferences;

        public PreferenceMemory()
        {
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var bimOpsDir = Path.Combine(appData, "BIMOpsStudio");
            Directory.CreateDirectory(bimOpsDir);
            _preferencesFile = Path.Combine(bimOpsDir, "preferences.json");

            LoadPreferences();
        }

        #region Preference Learning

        /// <summary>
        /// Learn from a successful interaction (thumbs up)
        /// </summary>
        public void LearnFromSuccess(string userRequest, string method, JObject parameters)
        {
            // Learn naming patterns
            LearnNamingPattern(method, parameters);

            // Learn parameter preferences
            LearnParameterPreferences(method, parameters);

            // Learn workflow patterns
            LearnWorkflowPattern(userRequest, method);

            SavePreferences();
        }

        /// <summary>
        /// Learn naming conventions from successful operations
        /// </summary>
        private void LearnNamingPattern(string method, JObject parameters)
        {
            // Sheet naming
            if (method.IndexOf("Sheet", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var sheetNumber = parameters["sheetNumber"]?.ToString();
                var sheetName = parameters["sheetName"]?.ToString();

                if (!string.IsNullOrEmpty(sheetNumber))
                {
                    // Detect pattern: A-1.1, A1.1, A101, etc.
                    var pattern = DetectNumberingPattern(sheetNumber);
                    if (!string.IsNullOrEmpty(pattern))
                    {
                        _preferences.SheetNumberingPattern = pattern;
                    }
                }
            }

            // View naming
            if (method.IndexOf("View", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var viewName = parameters["viewName"]?.ToString() ??
                              parameters["name"]?.ToString();
                if (!string.IsNullOrEmpty(viewName))
                {
                    _preferences.LastViewNameFormat = viewName;
                }
            }
        }

        /// <summary>
        /// Learn preferred parameter values
        /// </summary>
        private void LearnParameterPreferences(string method, JObject parameters)
        {
            // Wall preferences
            if (method.IndexOf("Wall", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var wallType = parameters["wallTypeName"]?.ToString() ??
                              parameters["typeName"]?.ToString();
                var height = parameters["height"]?.ToObject<double>();

                if (!string.IsNullOrEmpty(wallType))
                {
                    UpdateFrequency(_preferences.PreferredWallTypes, wallType);
                }
                if (height.HasValue && height > 0)
                {
                    _preferences.DefaultWallHeight = height.Value;
                }
            }

            // Door preferences
            if (method.IndexOf("Door", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var doorType = parameters["doorTypeName"]?.ToString() ??
                              parameters["typeName"]?.ToString();
                if (!string.IsNullOrEmpty(doorType))
                {
                    UpdateFrequency(_preferences.PreferredDoorTypes, doorType);
                }
            }

            // Window preferences
            if (method.IndexOf("Window", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var windowType = parameters["windowTypeName"]?.ToString() ??
                                parameters["typeName"]?.ToString();
                if (!string.IsNullOrEmpty(windowType))
                {
                    UpdateFrequency(_preferences.PreferredWindowTypes, windowType);
                }
            }

            // Text preferences
            if (method.IndexOf("Text", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var textType = parameters["textTypeId"]?.ToString() ??
                              parameters["textTypeName"]?.ToString();
                if (!string.IsNullOrEmpty(textType))
                {
                    _preferences.PreferredTextType = textType;
                }
            }
        }

        /// <summary>
        /// Learn workflow patterns (what commands often follow each other)
        /// </summary>
        private void LearnWorkflowPattern(string userRequest, string method)
        {
            if (!string.IsNullOrEmpty(_preferences.LastMethod))
            {
                var pattern = $"{_preferences.LastMethod} -> {method}";
                UpdateFrequency(_preferences.WorkflowPatterns, pattern);
            }
            _preferences.LastMethod = method;
            _preferences.LastRequest = userRequest;
        }

        #endregion

        #region Preference Application

        /// <summary>
        /// Get the most frequently used wall type
        /// </summary>
        public string GetPreferredWallType()
        {
            return GetMostFrequent(_preferences.PreferredWallTypes);
        }

        /// <summary>
        /// Get the most frequently used door type
        /// </summary>
        public string GetPreferredDoorType()
        {
            return GetMostFrequent(_preferences.PreferredDoorTypes);
        }

        /// <summary>
        /// Get the most frequently used window type
        /// </summary>
        public string GetPreferredWindowType()
        {
            return GetMostFrequent(_preferences.PreferredWindowTypes);
        }

        /// <summary>
        /// Get preferred wall height
        /// </summary>
        public double? GetPreferredWallHeight()
        {
            return _preferences.DefaultWallHeight > 0 ? _preferences.DefaultWallHeight : (double?)null;
        }

        /// <summary>
        /// Get sheet numbering pattern
        /// </summary>
        public string GetSheetNumberingPattern()
        {
            return _preferences.SheetNumberingPattern;
        }

        /// <summary>
        /// Set preferred titleblock (called when detecting from project)
        /// </summary>
        public void SetPreferredTitleblock(long titleblockId, string titleblockName)
        {
            _preferences.PreferredTitleblockId = titleblockId;
            _preferences.PreferredTitleblockName = titleblockName;
            SavePreferences();
        }

        /// <summary>
        /// Get preferred titleblock ID (0 if not set)
        /// </summary>
        public long GetPreferredTitleblockId()
        {
            return _preferences.PreferredTitleblockId;
        }

        /// <summary>
        /// Get preferred titleblock name
        /// </summary>
        public string GetPreferredTitleblockName()
        {
            return _preferences.PreferredTitleblockName;
        }

        /// <summary>
        /// Get preferences formatted as knowledge for local model
        /// </summary>
        public string GetPreferencesAsKnowledge()
        {
            var knowledge = "USER PREFERENCES:\n";

            if (!string.IsNullOrEmpty(_preferences.SheetNumberingPattern))
                knowledge += $"- Sheet numbering pattern: {_preferences.SheetNumberingPattern}\n";

            var wallType = GetPreferredWallType();
            if (!string.IsNullOrEmpty(wallType))
                knowledge += $"- Preferred wall type: {wallType}\n";

            var doorType = GetPreferredDoorType();
            if (!string.IsNullOrEmpty(doorType))
                knowledge += $"- Preferred door type: {doorType}\n";

            var windowType = GetPreferredWindowType();
            if (!string.IsNullOrEmpty(windowType))
                knowledge += $"- Preferred window type: {windowType}\n";

            if (_preferences.DefaultWallHeight > 0)
                knowledge += $"- Default wall height: {_preferences.DefaultWallHeight} ft\n";

            if (!string.IsNullOrEmpty(_preferences.PreferredTextType))
                knowledge += $"- Preferred text type: {_preferences.PreferredTextType}\n";

            // Add workflow suggestions
            var commonWorkflows = _preferences.WorkflowPatterns
                .OrderByDescending(kv => kv.Value)
                .Take(3)
                .ToList();

            if (commonWorkflows.Any())
            {
                knowledge += "\nCOMMON WORKFLOWS:\n";
                foreach (var wf in commonWorkflows)
                {
                    knowledge += $"- {wf.Key} (used {wf.Value} times)\n";
                }
            }

            return knowledge;
        }

        /// <summary>
        /// Suggest next likely method based on workflow patterns
        /// </summary>
        public List<string> SuggestNextMethods(string currentMethod)
        {
            var suggestions = _preferences.WorkflowPatterns
                .Where(kv => kv.Key.StartsWith($"{currentMethod} -> "))
                .OrderByDescending(kv => kv.Value)
                .Take(3)
                .Select(kv => kv.Key.Split(new[] { " -> " }, StringSplitOptions.None).Last())
                .ToList();

            return suggestions;
        }

        /// <summary>
        /// Apply preferences to parameters (fill in defaults)
        /// </summary>
        public JObject ApplyPreferences(string method, JObject parameters)
        {
            var result = parameters != null ? (JObject)parameters.DeepClone() : new JObject();

            // Apply wall preferences
            if (method.IndexOf("Wall", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                if (result["height"] == null && _preferences.DefaultWallHeight > 0)
                {
                    result["height"] = _preferences.DefaultWallHeight;
                }
                if (result["wallTypeName"] == null && result["typeName"] == null)
                {
                    var preferredWall = GetPreferredWallType();
                    if (!string.IsNullOrEmpty(preferredWall))
                    {
                        result["wallTypeName"] = preferredWall;
                    }
                }
            }

            // Apply door preferences
            if (method.IndexOf("Door", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                if (result["doorTypeName"] == null && result["typeName"] == null)
                {
                    var preferredDoor = GetPreferredDoorType();
                    if (!string.IsNullOrEmpty(preferredDoor))
                    {
                        result["doorTypeName"] = preferredDoor;
                    }
                }
            }

            // Apply window preferences
            if (method.IndexOf("Window", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                if (result["windowTypeName"] == null && result["typeName"] == null)
                {
                    var preferredWindow = GetPreferredWindowType();
                    if (!string.IsNullOrEmpty(preferredWindow))
                    {
                        result["windowTypeName"] = preferredWindow;
                    }
                }
            }

            return result;
        }

        #endregion

        #region Helper Methods

        private void UpdateFrequency(Dictionary<string, int> dict, string key)
        {
            if (dict.ContainsKey(key))
                dict[key]++;
            else
                dict[key] = 1;
        }

        private string GetMostFrequent(Dictionary<string, int> dict)
        {
            if (dict == null || !dict.Any()) return null;
            return dict.OrderByDescending(kv => kv.Value).First().Key;
        }

        private string DetectNumberingPattern(string number)
        {
            // A-1.1 pattern
            if (System.Text.RegularExpressions.Regex.IsMatch(number, @"^[A-Z]-\d+\.\d+$"))
                return "A-#.#";

            // A1.1 pattern
            if (System.Text.RegularExpressions.Regex.IsMatch(number, @"^[A-Z]\d+\.\d+$"))
                return "A#.#";

            // A101 pattern
            if (System.Text.RegularExpressions.Regex.IsMatch(number, @"^[A-Z]\d{3}$"))
                return "A###";

            // A-101 pattern
            if (System.Text.RegularExpressions.Regex.IsMatch(number, @"^[A-Z]-\d{3}$"))
                return "A-###";

            return null;
        }

        private void LoadPreferences()
        {
            _preferences = new UserPreferences();

            if (File.Exists(_preferencesFile))
            {
                try
                {
                    var json = File.ReadAllText(_preferencesFile);
                    _preferences = JsonConvert.DeserializeObject<UserPreferences>(json) ?? new UserPreferences();
                }
                catch
                {
                    _preferences = new UserPreferences();
                }
            }
        }

        private void SavePreferences()
        {
            try
            {
                var json = JsonConvert.SerializeObject(_preferences, Formatting.Indented);
                File.WriteAllText(_preferencesFile, json);
            }
            catch
            {
                // Silently fail on write errors
            }
        }

        #endregion
    }

    /// <summary>
    /// User preferences data structure
    /// </summary>
    public class UserPreferences
    {
        // Naming patterns
        public string SheetNumberingPattern { get; set; }
        public string LastViewNameFormat { get; set; }

        // Preferred types (with frequency counts)
        public Dictionary<string, int> PreferredWallTypes { get; set; } = new Dictionary<string, int>();
        public Dictionary<string, int> PreferredDoorTypes { get; set; } = new Dictionary<string, int>();
        public Dictionary<string, int> PreferredWindowTypes { get; set; } = new Dictionary<string, int>();

        // Default values
        public double DefaultWallHeight { get; set; }
        public string PreferredTextType { get; set; }

        // Titleblock preference (ID and name for verification)
        public long PreferredTitleblockId { get; set; }
        public string PreferredTitleblockName { get; set; }

        // Workflow tracking
        public Dictionary<string, int> WorkflowPatterns { get; set; } = new Dictionary<string, int>();
        public string LastMethod { get; set; }
        public string LastRequest { get; set; }

        // UI preferences
        public bool PreferLocalModel { get; set; } = true;
        public bool ShowVerification { get; set; } = true;
    }
}
