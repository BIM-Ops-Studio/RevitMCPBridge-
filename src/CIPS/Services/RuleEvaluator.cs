using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.Services;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Evaluates executable rules from knowledge base against current project state.
    /// Loads rules from extracted-projects/executable-rules.json and matches them
    /// to detect project type and suggest appropriate actions.
    /// </summary>
    public class RuleEvaluator
    {
        private static RuleEvaluator _instance;
        private JObject _rulesData;
        private DateTime _rulesLoadedAt;
        private string _detectedProjectType;
        private string _detectedFirm;
        private SmartSheetMatcher _sheetMatcher;

        private static readonly string RulesFilePath =
            @"D:\RevitMCPBridge2026\knowledge\extracted-projects\executable-rules.json";

        public static RuleEvaluator Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = new RuleEvaluator();
                }
                return _instance;
            }
        }

        private RuleEvaluator()
        {
            _sheetMatcher = new SmartSheetMatcher();
            LoadRules();
        }

        /// <summary>
        /// Reload rules from file (call if rules file is updated)
        /// </summary>
        public void ReloadRules()
        {
            LoadRules();
        }

        private void LoadRules()
        {
            try
            {
                if (File.Exists(RulesFilePath))
                {
                    var json = File.ReadAllText(RulesFilePath);
                    _rulesData = JObject.Parse(json);
                    _rulesLoadedAt = DateTime.Now;

                    var ruleCount = _rulesData["total_rules"]?.Value<int>() ?? 0;
                    Log.Information("[RuleEvaluator] Loaded {Count} rules from {Path}",
                        ruleCount, RulesFilePath);
                }
                else
                {
                    Log.Warning("[RuleEvaluator] Rules file not found at {Path}", RulesFilePath);
                    _rulesData = new JObject();
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[RuleEvaluator] Error loading rules: {Error}", ex.Message);
                _rulesData = new JObject();
            }
        }

        /// <summary>
        /// Analyze the current project and return detected type and applicable rules
        /// </summary>
        public ProjectAnalysis AnalyzeProject(Document doc, UIApplication uiApp)
        {
            if (doc == null)
                return new ProjectAnalysis { Success = false, Error = "No document provided" };

            try
            {
                // Initialize sheet matcher for firm detection
                _sheetMatcher.Initialize(doc, uiApp);
                _detectedFirm = _sheetMatcher.DetectedFirm;

                // Detect project type from rooms, views, and sheets
                var projectTypeResult = DetectProjectType(doc);
                _detectedProjectType = projectTypeResult.ProjectType;

                // Get applicable rules for this project type
                var applicableRules = GetApplicableRules(_detectedProjectType);

                // Evaluate which rules should trigger
                var triggeredRules = EvaluateRuleTriggers(doc, applicableRules);

                // Get suggested actions from triggered rules
                var suggestedActions = GetSuggestedActions(triggeredRules, doc);

                return new ProjectAnalysis
                {
                    Success = true,
                    ProjectType = _detectedProjectType,
                    DetectedFirm = _detectedFirm,
                    FirmPattern = _sheetMatcher.DetectedPattern,
                    ProjectTypeConfidence = projectTypeResult.Confidence,
                    Indicators = projectTypeResult.Indicators,
                    ApplicableRuleCount = applicableRules.Count,
                    TriggeredRuleCount = triggeredRules.Count,
                    TriggeredRules = triggeredRules.Select(r => new RuleSummary
                    {
                        RuleId = r["rule_id"]?.ToString(),
                        Name = r["name"]?.ToString(),
                        Category = r["category"]?.ToString(),
                        Confidence = r["confidence"]?.Value<double>() ?? 0
                    }).ToList(),
                    SuggestedActions = suggestedActions
                };
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[RuleEvaluator] Error analyzing project: {Error}", ex.Message);
                return new ProjectAnalysis { Success = false, Error = ex.Message };
            }
        }

        /// <summary>
        /// Detect project type from room names, view types, and sheet patterns
        /// </summary>
        private ProjectTypeDetection DetectProjectType(Document doc)
        {
            var result = new ProjectTypeDetection
            {
                ProjectType = "unknown",
                Confidence = 0.5,
                Indicators = new List<string>()
            };

            var projectTypePatterns = _rulesData["project_type_detection"] as JObject;
            if (projectTypePatterns == null)
                return result;

            // Get all rooms
            var rooms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .Cast<Room>()
                .Where(r => r.Area > 0)
                .Select(r => r.Name?.ToUpper() ?? "")
                .ToList();

            // Get all sheets
            var sheets = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSheet))
                .Cast<ViewSheet>()
                .Select(s => s.Name?.ToUpper() ?? "")
                .ToList();

            var scores = new Dictionary<string, (double score, List<string> indicators)>();

            foreach (var typePattern in projectTypePatterns.Properties())
            {
                var typeName = typePattern.Name;
                var typeData = typePattern.Value as JObject;

                var indicators = typeData?["indicators"]?.ToObject<List<string>>() ?? new List<string>();
                var roomPatterns = typeData?["room_patterns"]?.ToObject<List<string>>() ?? new List<string>();
                var sheetPatterns = typeData?["sheet_patterns"]?.ToObject<List<string>>() ?? new List<string>();

                double score = 0;
                var matchedIndicators = new List<string>();

                // Check room patterns
                foreach (var roomPattern in roomPatterns)
                {
                    var matchCount = rooms.Count(r => r.Contains(roomPattern.ToUpper()));
                    if (matchCount > 0)
                    {
                        score += 0.3 * Math.Min(matchCount, 5) / 5.0;
                        matchedIndicators.Add($"Room pattern '{roomPattern}' found ({matchCount} matches)");
                    }
                }

                // Check sheet patterns
                foreach (var sheetPattern in sheetPatterns)
                {
                    var matchCount = sheets.Count(s => s.Contains(sheetPattern.ToUpper()));
                    if (matchCount > 0)
                    {
                        score += 0.2;
                        matchedIndicators.Add($"Sheet pattern '{sheetPattern}' found");
                    }
                }

                // Check project info indicators
                var projectInfo = doc.ProjectInformation;
                var projectName = (projectInfo.Name ?? "").ToUpper();
                var projectNumber = (projectInfo.Number ?? "").ToUpper();
                var clientName = (projectInfo.ClientName ?? "").ToUpper();
                var combinedInfo = $"{projectName} {projectNumber} {clientName}";

                foreach (var indicator in indicators)
                {
                    if (combinedInfo.Contains(indicator.ToUpper()))
                    {
                        score += 0.25;
                        matchedIndicators.Add($"Project info contains '{indicator}'");
                    }
                }

                if (matchedIndicators.Count > 0)
                {
                    scores[typeName] = (score, matchedIndicators);
                }
            }

            // Find best match
            if (scores.Count > 0)
            {
                var best = scores.OrderByDescending(kv => kv.Value.score).First();
                result.ProjectType = best.Key;
                result.Confidence = Math.Min(best.Value.score, 1.0);
                result.Indicators = best.Value.indicators;
            }

            Log.Information("[RuleEvaluator] Detected project type '{Type}' with confidence {Conf:P0}",
                result.ProjectType, result.Confidence);

            return result;
        }

        /// <summary>
        /// Get rules that apply to the detected project type
        /// </summary>
        private List<JObject> GetApplicableRules(string projectType)
        {
            var rules = _rulesData["rules"] as JArray;
            if (rules == null)
                return new List<JObject>();

            return rules
                .Cast<JObject>()
                .Where(r =>
                {
                    var appliesTo = r["applies_to"]?.ToObject<List<string>>() ?? new List<string>();
                    return appliesTo.Contains(projectType) || appliesTo.Contains("all");
                })
                .ToList();
        }

        /// <summary>
        /// Evaluate which rules should trigger based on current project state
        /// </summary>
        private List<JObject> EvaluateRuleTriggers(Document doc, List<JObject> rules)
        {
            var triggered = new List<JObject>();
            var projectState = GetProjectState(doc);

            foreach (var rule in rules)
            {
                var trigger = rule["trigger"] as JObject;
                if (trigger == null)
                {
                    triggered.Add(rule); // No trigger = always applies
                    continue;
                }

                var conditions = trigger["conditions"] as JArray;
                var logic = trigger["logic"]?.ToString() ?? "AND";

                if (conditions == null || conditions.Count == 0)
                {
                    triggered.Add(rule);
                    continue;
                }

                var conditionResults = new List<bool>();

                foreach (var condition in conditions.Cast<JObject>())
                {
                    var field = condition["field"]?.ToString();
                    var op = condition["operator"]?.ToString();
                    var value = condition["value"];

                    if (string.IsNullOrEmpty(field))
                        continue;

                    var fieldValue = projectState.GetValueOrDefault(field);
                    var matches = EvaluateCondition(fieldValue, op, value);
                    conditionResults.Add(matches);
                }

                bool triggered_rule = logic == "OR"
                    ? conditionResults.Any(c => c)
                    : conditionResults.All(c => c);

                if (triggered_rule)
                {
                    triggered.Add(rule);
                }
            }

            return triggered;
        }

        /// <summary>
        /// Get current project state values for rule evaluation
        /// </summary>
        private Dictionary<string, object> GetProjectState(Document doc)
        {
            var state = new Dictionary<string, object>();

            try
            {
                // Project type
                state["project_type"] = _detectedProjectType;

                // Level count
                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .ToList();
                state["level_count"] = levels.Count;

                // Room count
                var rooms = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Rooms)
                    .Cast<Room>()
                    .Where(r => r.Area > 0)
                    .ToList();
                state["room_count"] = rooms.Count;

                // Check for unique unit types (multi-family)
                var unitRooms = rooms.Where(r =>
                    (r.Name ?? "").ToUpper().Contains("UNIT") ||
                    (r.Name ?? "").ToUpper().StartsWith("A ") ||
                    (r.Name ?? "").ToUpper().StartsWith("B ") ||
                    (r.Name ?? "").ToUpper().StartsWith("C "));
                state["unique_unit_types"] = unitRooms.Select(r => GetUnitType(r.Name)).Distinct().Count();

                // Check building height
                if (levels.Count > 0)
                {
                    var maxElevation = levels.Max(l => l.Elevation);
                    var minElevation = levels.Min(l => l.Elevation);
                    var height = maxElevation - minElevation;
                    state["building_height"] = levels.Count - 1; // stories
                }

                // Check phases
                var phases = new FilteredElementCollector(doc)
                    .OfClass(typeof(Phase))
                    .ToList();
                state["construction_phases"] = phases.Count;

                // Check for renovation indicators
                var phaseNames = phases.Select(p => p.Name.ToUpper());
                state["project_subtype"] = phaseNames.Any(p =>
                    p.Contains("DEMO") || p.Contains("EXISTING") || p.Contains("PHASE"))
                    ? "renovation"
                    : "new";

                // Check for healthcare indicators
                var healthcareRooms = rooms.Count(r =>
                    (r.Name ?? "").ToUpper().Contains("NURSE") ||
                    (r.Name ?? "").ToUpper().Contains("PATIENT") ||
                    (r.Name ?? "").ToUpper().Contains("CLEAN") ||
                    (r.Name ?? "").ToUpper().Contains("SOILED"));
                state["has_medical_gas"] = healthcareRooms > 0;

                // Check for identical floors (for typical floor grouping)
                // Simplified check based on room counts per level
                var roomsPerLevel = rooms.GroupBy(r => r.Level?.Id.Value ?? 0)
                    .ToDictionary(g => g.Key, g => g.Count());
                var counts = roomsPerLevel.Select(kvp => kvp.Value).ToList();
                var identicalCount = counts
                    .GroupBy(v => v)
                    .Where(g => g.Count() >= 2)
                    .Sum(g => g.Count());
                state["identical_floor_count"] = identicalCount;

                // Get project phase from info
                var projectInfo = doc.ProjectInformation;
                state["project_phase"] = projectInfo.BuildingName ?? "DD"; // Default to DD if not set
            }
            catch (Exception ex)
            {
                Log.Warning("[RuleEvaluator] Error getting project state: {Error}", ex.Message);
            }

            return state;
        }

        private string GetUnitType(string roomName)
        {
            if (string.IsNullOrEmpty(roomName)) return "";

            var upper = roomName.ToUpper();
            if (upper.Contains("UNIT"))
            {
                // Extract letter after UNIT (e.g., "UNIT A" -> "A")
                var idx = upper.IndexOf("UNIT");
                var rest = upper.Substring(idx + 4).Trim();
                if (rest.Length > 0)
                    return rest.Split(' ', '-', '_')[0];
            }

            // Check for single letter prefix (A 101, B 201)
            if (upper.Length >= 2 && char.IsLetter(upper[0]) && (upper[1] == ' ' || char.IsDigit(upper[1])))
            {
                return upper[0].ToString();
            }

            return "";
        }

        /// <summary>
        /// Evaluate a single condition
        /// </summary>
        private bool EvaluateCondition(object fieldValue, string op, JToken expectedValue)
        {
            try
            {
                switch (op)
                {
                    case "==":
                        return CompareEqual(fieldValue, expectedValue);
                    case "!=":
                        return !CompareEqual(fieldValue, expectedValue);
                    case ">":
                        return CompareNumeric(fieldValue, expectedValue) > 0;
                    case ">=":
                        return CompareNumeric(fieldValue, expectedValue) >= 0;
                    case "<":
                        return CompareNumeric(fieldValue, expectedValue) < 0;
                    case "<=":
                        return CompareNumeric(fieldValue, expectedValue) <= 0;
                    case "in":
                        return CompareIn(fieldValue, expectedValue);
                    default:
                        return false;
                }
            }
            catch
            {
                return false;
            }
        }

        private bool CompareEqual(object fieldValue, JToken expected)
        {
            if (fieldValue == null) return expected.Type == JTokenType.Null;
            return fieldValue.ToString().Equals(expected.ToString(), StringComparison.OrdinalIgnoreCase);
        }

        private int CompareNumeric(object fieldValue, JToken expected)
        {
            var fieldNum = Convert.ToDouble(fieldValue ?? 0);
            var expectedNum = expected.Value<double>();
            return fieldNum.CompareTo(expectedNum);
        }

        private bool CompareIn(object fieldValue, JToken expected)
        {
            if (expected is JArray array)
            {
                var fieldStr = fieldValue?.ToString() ?? "";
                return array.Any(v => v.ToString().Equals(fieldStr, StringComparison.OrdinalIgnoreCase));
            }
            return false;
        }

        /// <summary>
        /// Get suggested actions from triggered rules
        /// </summary>
        private List<SuggestedAction> GetSuggestedActions(List<JObject> triggeredRules, Document doc)
        {
            var actions = new List<SuggestedAction>();

            foreach (var rule in triggeredRules)
            {
                var action = rule["action"] as JObject;
                if (action == null) continue;

                var actionType = action["type"]?.ToString();
                var ruleId = rule["rule_id"]?.ToString();
                var ruleName = rule["name"]?.ToString();
                var confidence = rule["confidence"]?.Value<double>() ?? 0.5;

                // Get firm-specific pattern if available
                var firmPatterns = rule["firm_patterns"] as JObject;
                var sheetPattern = firmPatterns?[_detectedFirm ?? "default"]?.ToString()
                    ?? firmPatterns?["default"]?.ToString();

                switch (actionType)
                {
                    case "create_sheets":
                        var template = action["template"] as JObject;
                        var namingPattern = template?["naming_pattern"]?.ToString();
                        var perItem = template?["per_item"]?.ToString();

                        actions.Add(new SuggestedAction
                        {
                            RuleId = ruleId,
                            RuleName = ruleName,
                            ActionType = "create_sheets",
                            Description = $"Create {ruleName} sheets",
                            SheetPattern = sheetPattern,
                            NamingPattern = namingPattern,
                            PerItem = perItem,
                            Confidence = confidence,
                            McpMethods = rule["mcp_methods"]?.ToObject<List<string>>() ?? new List<string>()
                        });
                        break;

                    case "group_floors":
                    case "organize_sections":
                    case "organize_details":
                    case "group_views":
                        actions.Add(new SuggestedAction
                        {
                            RuleId = ruleId,
                            RuleName = ruleName,
                            ActionType = actionType,
                            Description = $"{ruleName}",
                            Confidence = confidence,
                            McpMethods = rule["mcp_methods"]?.ToObject<List<string>>() ?? new List<string>()
                        });
                        break;
                }
            }

            return actions;
        }

        /// <summary>
        /// Get the sheet numbering pattern for a specific rule
        /// </summary>
        public string GetSheetPattern(string ruleId, string firmName = null)
        {
            var rules = _rulesData["rules"] as JArray;
            var rule = rules?.Cast<JObject>()
                .FirstOrDefault(r => r["rule_id"]?.ToString() == ruleId);

            if (rule == null) return null;

            var firmPatterns = rule["firm_patterns"] as JObject;
            return firmPatterns?[firmName ?? _detectedFirm ?? "default"]?.ToString()
                ?? firmPatterns?["default"]?.ToString();
        }

        /// <summary>
        /// Get all rules data for inspection
        /// </summary>
        public JObject GetRulesData() => _rulesData;

        /// <summary>
        /// Get detected project type
        /// </summary>
        public string DetectedProjectType => _detectedProjectType;

        /// <summary>
        /// Get detected firm
        /// </summary>
        public string DetectedFirm => _detectedFirm;
    }

    #region Result Models

    public class ProjectAnalysis
    {
        public bool Success { get; set; }
        public string Error { get; set; }
        public string ProjectType { get; set; }
        public string DetectedFirm { get; set; }
        public string FirmPattern { get; set; }
        public double ProjectTypeConfidence { get; set; }
        public List<string> Indicators { get; set; }
        public int ApplicableRuleCount { get; set; }
        public int TriggeredRuleCount { get; set; }
        public List<RuleSummary> TriggeredRules { get; set; }
        public List<SuggestedAction> SuggestedActions { get; set; }
    }

    public class ProjectTypeDetection
    {
        public string ProjectType { get; set; }
        public double Confidence { get; set; }
        public List<string> Indicators { get; set; }
    }

    public class RuleSummary
    {
        public string RuleId { get; set; }
        public string Name { get; set; }
        public string Category { get; set; }
        public double Confidence { get; set; }
    }

    public class SuggestedAction
    {
        public string RuleId { get; set; }
        public string RuleName { get; set; }
        public string ActionType { get; set; }
        public string Description { get; set; }
        public string SheetPattern { get; set; }
        public string NamingPattern { get; set; }
        public string PerItem { get; set; }
        public double Confidence { get; set; }
        public List<string> McpMethods { get; set; }
    }

    #endregion
}
