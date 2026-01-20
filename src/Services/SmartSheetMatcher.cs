using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using Serilog;

namespace RevitMCPBridge.Services
{
    /// <summary>
    /// Smart sheet matcher that uses pattern detection and learned preferences
    /// to find the best sheet for a view or schedule.
    /// Phase 2 of Predictive Intelligence Enhancement.
    /// </summary>
    public class SmartSheetMatcher
    {
        private string _detectedPattern;
        private string _detectedFirm;
        private JObject _patternRules;
        private string _patternSource; // "extracted" or "legacy"
        private readonly Dictionary<ViewType, string> _lastPlacedSheets = new Dictionary<ViewType, string>();
        private DateTime _lastInitialized;
        private Document _lastDoc;

        /// <summary>
        /// Known firm patterns from extracted project analysis
        /// </summary>
        private static readonly HashSet<string> KnownFirmPatterns = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "SOP", "ARKY", "BD", "Fantal"
        };

        /// <summary>
        /// Initialize the matcher for a specific document
        /// </summary>
        public void Initialize(Document doc, UIApplication uiApp)
        {
            if (doc == null) return;

            // Skip re-initialization if same document and recent
            if (_lastDoc == doc && (DateTime.Now - _lastInitialized).TotalMinutes < 5)
                return;

            try
            {
                // Detect sheet pattern from project info or title block
                var firmName = GetFirmNameFromProject(doc);

                if (!string.IsNullOrEmpty(firmName))
                {
                    _detectedFirm = firmName;

                    var detectParams = new JObject { ["firmName"] = firmName };
                    var detectResult = JObject.Parse(SheetPatternMethods.DetectSheetPattern(uiApp, detectParams));

                    if (detectResult["success"]?.ToObject<bool>() == true)
                    {
                        _detectedPattern = detectResult["pattern"]?.ToString();
                        _patternSource = detectResult["source"]?.ToString() ?? "legacy";

                        // Get the rules for this pattern
                        var rulesParams = new JObject { ["patternId"] = _detectedPattern };
                        var rulesResult = JObject.Parse(SheetPatternMethods.GetPatternRules(uiApp, rulesParams));

                        if (rulesResult["success"]?.ToObject<bool>() == true)
                        {
                            _patternRules = rulesResult["rules"] as JObject;
                        }

                        Log.Information("[SmartSheetMatcher] Detected pattern {Pattern} for firm '{Firm}' (source: {Source})",
                            _detectedPattern, firmName, _patternSource);
                    }
                }

                _lastDoc = doc;
                _lastInitialized = DateTime.Now;
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[SmartSheetMatcher] Error initializing: {Error}", ex.Message);
                _detectedPattern = "C"; // Default to professional standard
                _patternSource = "default";
            }
        }

        /// <summary>
        /// Get the detected firm name
        /// </summary>
        public string DetectedFirm => _detectedFirm;

        /// <summary>
        /// Get the detected pattern ID
        /// </summary>
        public string DetectedPattern => _detectedPattern;

        /// <summary>
        /// Check if using extracted (new) patterns vs legacy patterns
        /// </summary>
        public bool IsUsingExtractedPatterns => _patternSource == "extracted";

        /// <summary>
        /// Find the best sheet for a view based on detected pattern and view type
        /// </summary>
        public ViewSheet FindSheetForView(Document doc, View view)
        {
            if (doc == null || view == null) return null;

            var sheets = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSheet))
                .Cast<ViewSheet>()
                .Where(s => !s.IsPlaceholder)
                .OrderBy(s => s.SheetNumber)
                .ToList();

            if (sheets.Count == 0) return null;

            // First, check if user recently placed a similar view type on a sheet
            if (_lastPlacedSheets.TryGetValue(view.ViewType, out var lastSheetNumber))
            {
                var lastSheet = sheets.FirstOrDefault(s => s.SheetNumber == lastSheetNumber);
                if (lastSheet != null && HasAvailableSpace(doc, lastSheet, view))
                {
                    Log.Debug("[SmartSheetMatcher] Using last-used sheet {SheetNumber} for {ViewType}",
                        lastSheetNumber, view.ViewType);
                    return lastSheet;
                }
            }

            // Use pattern-based matching
            if (_patternRules != null)
            {
                var patternSheet = FindSheetByPattern(sheets, view);
                if (patternSheet != null)
                {
                    Log.Debug("[SmartSheetMatcher] Pattern {Pattern} matched sheet {SheetNumber} for {ViewType}",
                        _detectedPattern, patternSheet.SheetNumber, view.ViewType);
                    return patternSheet;
                }
            }

            // Fall back to traditional matching
            return FindSheetByViewType(sheets, view);
        }

        /// <summary>
        /// Find the best sheet for a schedule
        /// </summary>
        public ViewSheet FindSheetForSchedule(Document doc, ViewSchedule schedule)
        {
            if (doc == null || schedule == null) return null;

            var sheets = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSheet))
                .Cast<ViewSheet>()
                .Where(s => !s.IsPlaceholder)
                .OrderBy(s => s.SheetNumber)
                .ToList();

            if (sheets.Count == 0) return null;

            var scheduleName = schedule.Name.ToLower();

            // Pattern-based matching for schedules using extracted firm patterns
            if (_patternRules != null && _detectedPattern != null)
            {
                switch (_detectedPattern)
                {
                    // New extracted firm patterns
                    case "SOP":
                        // SOP uses A1.1.x for general, schedules typically on cover or dedicated sheets
                        var sopSheet = sheets.FirstOrDefault(s =>
                            s.SheetNumber.Contains("0.5") ||
                            s.Name.ToLower().Contains("schedule") ||
                            s.Name.ToLower().Contains("door") && scheduleName.Contains("door"));
                        if (sopSheet != null) return sopSheet;
                        break;

                    case "ARKY":
                        // ARKY uses A-x.x format
                        var arkySheet = sheets.FirstOrDefault(s =>
                            s.SheetNumber.Contains("-0.5") ||
                            s.Name.ToLower().Contains("schedule"));
                        if (arkySheet != null) return arkySheet;
                        break;

                    case "BD":
                        // BD uses A6xx for doors (A601)
                        var bdSheet = sheets.FirstOrDefault(s =>
                            (s.SheetNumber.StartsWith("A6") && scheduleName.Contains("door")) ||
                            s.Name.ToLower().Contains("schedule"));
                        if (bdSheet != null) return bdSheet;
                        break;

                    case "Fantal":
                        // Fantal uses simple decimal (A0.x for admin)
                        var fantalSheet = sheets.FirstOrDefault(s =>
                            s.SheetNumber.Contains("0.") ||
                            s.Name.ToLower().Contains("schedule"));
                        if (fantalSheet != null) return fantalSheet;
                        break;

                    // Legacy patterns
                    case "A":
                        // Pattern A: Look for A0.5 or dedicated schedule sheets
                        var patternASheet = sheets.FirstOrDefault(s =>
                            s.SheetNumber.Contains("0.5") ||
                            s.SheetNumber.Contains("-0.5") ||
                            s.Name.ToLower().Contains("schedule"));
                        if (patternASheet != null) return patternASheet;
                        break;

                    case "C":
                    case "C-Zero":
                    case "C-Institutional":
                        // Pattern C: Look for A601, A602 or 5xx series
                        var patternCSheet = sheets.FirstOrDefault(s =>
                            (s.SheetNumber.StartsWith("A6") && s.SheetNumber.Length == 4) ||
                            s.SheetNumber.StartsWith("A5") ||
                            s.Name.ToLower().Contains("schedule"));
                        if (patternCSheet != null) return patternCSheet;
                        break;

                    case "D":
                        // Pattern D: Look for A 0.x style
                        var patternDSheet = sheets.FirstOrDefault(s =>
                            s.SheetNumber.Contains(" 0.") ||
                            s.Name.ToLower().Contains("schedule"));
                        if (patternDSheet != null) return patternDSheet;
                        break;
                }
            }

            // Type-specific matching
            if (scheduleName.Contains("door"))
            {
                var doorSheet = sheets.FirstOrDefault(s =>
                    s.SheetNumber.Contains("2.3") ||
                    s.SheetNumber.StartsWith("A6") ||
                    s.Name.ToLower().Contains("door") ||
                    s.Name.ToLower().Contains("schedule"));
                if (doorSheet != null) return doorSheet;
            }

            if (scheduleName.Contains("window"))
            {
                var windowSheet = sheets.FirstOrDefault(s =>
                    s.SheetNumber.Contains("2.3") ||
                    s.Name.ToLower().Contains("window") ||
                    s.Name.ToLower().Contains("schedule"));
                if (windowSheet != null) return windowSheet;
            }

            if (scheduleName.Contains("room") || scheduleName.Contains("finish"))
            {
                var finishSheet = sheets.FirstOrDefault(s =>
                    s.Name.ToLower().Contains("finish") ||
                    s.Name.ToLower().Contains("schedule"));
                if (finishSheet != null) return finishSheet;
            }

            // Default to any schedule sheet
            return sheets.FirstOrDefault(s =>
                s.SheetNumber.StartsWith("A5") ||
                s.SheetNumber.StartsWith("A6") ||
                s.SheetNumber.Contains(".5") ||
                s.Name.ToLower().Contains("schedule"));
        }

        /// <summary>
        /// Suggest a sheet number for a new sheet based on detected pattern and rule.
        /// This is used when creating new sheets per the executable rules.
        /// </summary>
        public string SuggestSheetNumber(string ruleId, Dictionary<string, string> variables)
        {
            if (string.IsNullOrEmpty(_detectedPattern) || _patternRules == null)
                return null;

            var rules = _patternRules["rules"] as JObject;
            if (rules == null)
                return null;

            var ruleTemplate = rules[ruleId]?.ToString();
            if (string.IsNullOrEmpty(ruleTemplate))
                return null;

            // Replace variables in template
            var result = ruleTemplate;
            foreach (var kvp in variables)
            {
                result = result.Replace("{" + kvp.Key + "}", kvp.Value);
            }

            return result;
        }

        /// <summary>
        /// Get the sheet category prefix for a view type based on detected pattern.
        /// Returns the sheet number prefix (e.g., "A1", "A-2", "A10") for the view type.
        /// </summary>
        public string GetSheetCategoryPrefix(ViewType viewType)
        {
            if (_patternRules == null)
                return GetDefaultSheetPrefix(viewType);

            var sheetCategories = _patternRules["sheetCategories"] as JObject;
            if (sheetCategories == null)
                return GetDefaultSheetPrefix(viewType);

            string categoryKey = viewType switch
            {
                ViewType.FloorPlan => "floorPlans",
                ViewType.CeilingPlan => "rcpPlans",
                ViewType.Elevation => "elevations",
                ViewType.Section => "sections",
                ViewType.Detail => "details",
                ViewType.DraftingView => "details",
                _ => null
            };

            if (categoryKey != null)
            {
                var categoryValue = sheetCategories[categoryKey]?.ToString();
                if (!string.IsNullOrEmpty(categoryValue))
                {
                    return ExtractSheetPrefix(categoryValue);
                }
            }

            return GetDefaultSheetPrefix(viewType);
        }

        private string GetDefaultSheetPrefix(ViewType viewType)
        {
            return viewType switch
            {
                ViewType.FloorPlan => "A1",
                ViewType.CeilingPlan => "A3",
                ViewType.Elevation => "A4",
                ViewType.Section => "A5",
                ViewType.Detail => "A5",
                ViewType.DraftingView => "A5",
                _ => "A"
            };
        }

        /// <summary>
        /// Record a manual placement for learning
        /// </summary>
        public void RecordPlacement(ViewType viewType, string sheetNumber)
        {
            _lastPlacedSheets[viewType] = sheetNumber;
            Log.Debug("[SmartSheetMatcher] Recorded placement: {ViewType} -> {SheetNumber}",
                viewType, sheetNumber);
        }

        /// <summary>
        /// Get firm name from project info or title block.
        /// PRIORITY: Titleblock family name > Project info parameters > Instance/Type parameters
        /// Based on lesson learned: Firm name is in titleblock family name, NOT folder structure.
        /// Pattern: TITLEBLOCK_{FIRM}_{SIZE}_{VARIANT} or {SIZE} Border- {FIRM}
        /// </summary>
        private string GetFirmNameFromProject(Document doc)
        {
            try
            {
                // PRIORITY 1: Extract from titleblock family NAME (most reliable)
                var firmFromTitleblock = GetFirmFromTitleblockFamilyName(doc);
                if (!string.IsNullOrEmpty(firmFromTitleblock))
                {
                    Log.Debug("[SmartSheetMatcher] Firm detected from titleblock family: {Firm}", firmFromTitleblock);
                    return firmFromTitleblock;
                }

                // PRIORITY 2: Try project info
                var projectInfo = doc.ProjectInformation;

                // Check Author parameter
                var author = projectInfo.Author;
                if (!string.IsNullOrWhiteSpace(author))
                    return author;

                // Check ClientName parameter
                var clientName = projectInfo.ClientName;
                if (!string.IsNullOrWhiteSpace(clientName))
                    return clientName;

                // Check OrganizationName parameter
                var orgName = projectInfo.OrganizationName;
                if (!string.IsNullOrWhiteSpace(orgName))
                    return orgName;

                // PRIORITY 3: Try titleblock instance/type parameters
                var titleBlock = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_TitleBlocks)
                    .WhereElementIsNotElementType()
                    .FirstOrDefault() as FamilyInstance;

                if (titleBlock != null)
                {
                    // Try common parameter names
                    foreach (var paramName in new[] { "Firm Name", "Company Name", "Architect", "Designer" })
                    {
                        var param = titleBlock.LookupParameter(paramName);
                        if (param != null && param.HasValue)
                        {
                            var value = param.AsString();
                            if (!string.IsNullOrWhiteSpace(value))
                                return value;
                        }
                    }

                    // Also try type parameters
                    var familySymbol = titleBlock.Symbol;
                    foreach (var paramName in new[] { "Firm Name", "Company Name" })
                    {
                        var param = familySymbol.LookupParameter(paramName);
                        if (param != null && param.HasValue)
                        {
                            var value = param.AsString();
                            if (!string.IsNullOrWhiteSpace(value))
                                return value;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Debug("[SmartSheetMatcher] Error getting firm name: {Error}", ex.Message);
            }

            return null;
        }

        /// <summary>
        /// Extract firm name from titleblock FAMILY NAME.
        /// Pattern 1: TITLEBLOCK_{FIRM}_{SIZE}_{VARIANT} (e.g., TITLEBLOCK_SOP_36x24_2018 -> "SOP")
        /// Pattern 2: {SIZE} Border- {FIRM} (e.g., "24 x 36 Border- BD" -> "BD")
        /// This is more reliable than project info parameters.
        /// </summary>
        private string GetFirmFromTitleblockFamilyName(Document doc)
        {
            try
            {
                // Get all titleblock family types
                var titleblockTypes = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_TitleBlocks)
                    .WhereElementIsElementType()
                    .Cast<FamilySymbol>()
                    .ToList();

                var firmCandidates = new Dictionary<string, int>();
                var excludedTerms = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
                {
                    "SCHEMATIC", "SKETCH", "STANDARD", "PRESENTATION", "CLEAN",
                    "TITLEBLOCK", "BORDER", "COVER", "24", "36", "30", "42"
                };

                foreach (var type in titleblockTypes)
                {
                    var familyName = type.FamilyName ?? "";
                    var typeName = type.Name ?? "";

                    // Pattern 1: TITLEBLOCK_{FIRM}_{SIZE}
                    if (familyName.ToUpper().StartsWith("TITLEBLOCK_"))
                    {
                        var parts = familyName.Split('_');
                        if (parts.Length >= 2)
                        {
                            var candidate = parts[1];
                            if (!excludedTerms.Contains(candidate) && candidate.Length >= 2)
                            {
                                firmCandidates[candidate] = firmCandidates.GetValueOrDefault(candidate, 0) + 1;
                            }
                        }
                    }

                    // Pattern 2: "{SIZE} Border- {FIRM}" (BD pattern)
                    if (familyName.Contains("Border-") || typeName.Contains("Border-"))
                    {
                        var name = familyName.Contains("Border-") ? familyName : typeName;
                        var idx = name.IndexOf("Border-");
                        if (idx >= 0)
                        {
                            var afterBorder = name.Substring(idx + 7).Trim();
                            // Extract first word/token
                            var candidate = afterBorder.Split(' ', '_')[0];
                            if (!excludedTerms.Contains(candidate) && candidate.Length >= 2)
                            {
                                firmCandidates[candidate] = firmCandidates.GetValueOrDefault(candidate, 0) + 1;
                            }
                        }
                    }

                    // Pattern 3: "{SIZE} Cover- {FIRM}"
                    if (familyName.Contains("Cover-") || typeName.Contains("Cover-"))
                    {
                        var name = familyName.Contains("Cover-") ? familyName : typeName;
                        var idx = name.IndexOf("Cover-");
                        if (idx >= 0)
                        {
                            var afterCover = name.Substring(idx + 6).Trim();
                            var candidate = afterCover.Split(' ', '_')[0];
                            if (!excludedTerms.Contains(candidate) && candidate.Length >= 2)
                            {
                                firmCandidates[candidate] = firmCandidates.GetValueOrDefault(candidate, 0) + 1;
                            }
                        }
                    }
                }

                // Return most common firm candidate
                if (firmCandidates.Count > 0)
                {
                    var mostCommon = firmCandidates.OrderByDescending(kv => kv.Value).First().Key;
                    Log.Information("[SmartSheetMatcher] Detected firm '{Firm}' from {Count} titleblock families",
                        mostCommon, firmCandidates[mostCommon]);
                    return mostCommon;
                }
            }
            catch (Exception ex)
            {
                Log.Debug("[SmartSheetMatcher] Error parsing titleblock families: {Error}", ex.Message);
            }

            return null;
        }

        /// <summary>
        /// Find sheet by detected pattern rules
        /// </summary>
        private ViewSheet FindSheetByPattern(List<ViewSheet> sheets, View view)
        {
            if (_patternRules == null || _detectedPattern == null)
                return null;

            var sheetCategories = _patternRules["sheetCategories"] as JObject;
            if (sheetCategories == null)
                return null;

            string categoryKey = view.ViewType switch
            {
                ViewType.FloorPlan => "floorPlan",
                ViewType.CeilingPlan => "rcpPlans",
                ViewType.Elevation => "elevations",
                ViewType.Section => "sections",
                ViewType.Detail => "details",
                ViewType.DraftingView => "details",
                ViewType.ThreeD => "floorPlan", // 3D views often go with plans
                _ => null
            };

            if (categoryKey == null)
                return null;

            // Try multiple variations of the category key
            var variations = new[] { categoryKey, categoryKey + "s", categoryKey.TrimEnd('s') };

            foreach (var key in variations)
            {
                var categoryValue = sheetCategories[key]?.ToString();
                if (string.IsNullOrEmpty(categoryValue))
                    continue;

                // Parse the category value (e.g., "A-1.x", "A105-A107", "A5.x")
                var targetPrefix = ExtractSheetPrefix(categoryValue);
                if (string.IsNullOrEmpty(targetPrefix))
                    continue;

                // Find matching sheet with available space
                var matchingSheet = sheets
                    .Where(s => SheetMatchesPrefix(s.SheetNumber, targetPrefix))
                    .FirstOrDefault(s => HasAvailableSpace(_lastDoc, s, view));

                if (matchingSheet != null)
                    return matchingSheet;

                // If no sheet with space, return first matching sheet
                matchingSheet = sheets.FirstOrDefault(s => SheetMatchesPrefix(s.SheetNumber, targetPrefix));
                if (matchingSheet != null)
                    return matchingSheet;
            }

            return null;
        }

        /// <summary>
        /// Extract the sheet prefix from a category value like "A-1.x" or "A105-A107"
        /// </summary>
        private string ExtractSheetPrefix(string categoryValue)
        {
            if (string.IsNullOrEmpty(categoryValue))
                return null;

            // Handle range format "A105-A107" -> "A10"
            if (categoryValue.Contains("-") && char.IsDigit(categoryValue[categoryValue.IndexOf('-') - 1]))
            {
                var prefix = categoryValue.Split('-')[0];
                // Return prefix without last digit (e.g., "A105" -> "A10")
                return prefix.Length > 2 ? prefix.Substring(0, prefix.Length - 1) : prefix;
            }

            // Handle pattern format "A-1.x" or "A5.x" -> "A-1" or "A5"
            if (categoryValue.Contains(".x"))
            {
                return categoryValue.Replace(".x", "");
            }

            // Handle simple prefix "A2.1, A2.2" -> "A2"
            var commaIndex = categoryValue.IndexOf(',');
            if (commaIndex > 0)
            {
                var firstValue = categoryValue.Substring(0, commaIndex).Trim();
                var dotIndex = firstValue.LastIndexOf('.');
                return dotIndex > 0 ? firstValue.Substring(0, dotIndex) : firstValue;
            }

            // Return as-is if no special format
            return categoryValue.Length > 3 ? categoryValue.Substring(0, 3) : categoryValue;
        }

        /// <summary>
        /// Check if sheet number matches a prefix
        /// </summary>
        private bool SheetMatchesPrefix(string sheetNumber, string prefix)
        {
            if (string.IsNullOrEmpty(sheetNumber) || string.IsNullOrEmpty(prefix))
                return false;

            // Handle hyphen/no-hyphen variations
            var normalizedSheet = sheetNumber.Replace("-", "").Replace(" ", "");
            var normalizedPrefix = prefix.Replace("-", "").Replace(" ", "");

            return normalizedSheet.StartsWith(normalizedPrefix, StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>
        /// Fall back to traditional view type matching
        /// </summary>
        private ViewSheet FindSheetByViewType(List<ViewSheet> sheets, View view)
        {
            return view.ViewType switch
            {
                ViewType.FloorPlan => sheets.FirstOrDefault(s =>
                    s.SheetNumber.StartsWith("A1") ||
                    s.SheetNumber.StartsWith("A2.1") ||
                    s.SheetNumber.StartsWith("A2.2") ||
                    s.Name.ToLower().Contains("plan")),

                ViewType.CeilingPlan => sheets.FirstOrDefault(s =>
                    s.SheetNumber.StartsWith("A3") ||
                    s.Name.ToLower().Contains("ceiling") ||
                    s.Name.ToLower().Contains("rcp")),

                ViewType.Elevation => sheets.FirstOrDefault(s =>
                    s.SheetNumber.StartsWith("A5") ||
                    s.SheetNumber.StartsWith("A4") ||
                    s.Name.ToLower().Contains("elevation")),

                ViewType.Section => sheets.FirstOrDefault(s =>
                    s.SheetNumber.StartsWith("A7") ||
                    s.SheetNumber.StartsWith("A6") ||
                    s.Name.ToLower().Contains("section")),

                _ => sheets.FirstOrDefault(s => s.GetAllViewports().Count < 6)
            };
        }

        /// <summary>
        /// Check if a sheet has available space for another view
        /// </summary>
        private bool HasAvailableSpace(Document doc, ViewSheet sheet, View view)
        {
            if (doc == null || sheet == null)
                return true; // Assume available if can't check

            try
            {
                var viewports = sheet.GetAllViewports();

                // Simple heuristic: limit views per sheet
                if (viewports.Count >= 8)
                    return false;

                // For floor plans and elevations, usually 1-2 per sheet
                if (view.ViewType == ViewType.FloorPlan || view.ViewType == ViewType.Elevation)
                {
                    var sameTypeCount = viewports
                        .Select(vpId => doc.GetElement(vpId) as Viewport)
                        .Count(vp => vp != null &&
                            doc.GetElement(vp.ViewId) is View v &&
                            v.ViewType == view.ViewType);

                    if (sameTypeCount >= 2)
                        return false;
                }

                return true;
            }
            catch
            {
                return true;
            }
        }
    }
}
