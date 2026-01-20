using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge
{
    /// <summary>
    /// Construction Document Checklist verification methods
    /// Automates CD set completeness checking via MCP
    /// </summary>
    public static class CDChecklistMethods
    {
        #region Main Checklist Method

        /// <summary>
        /// Run comprehensive CD checklist verification on the current model
        /// Returns pass/fail status for each check category
        /// </summary>
        public static string RunCDChecklist(UIApplication uiApp, JObject parameters)
        {
            try
            {
                var doc = uiApp.ActiveUIDocument.Document;
                var includeDetails = parameters["includeDetails"]?.ToObject<bool>() ?? true;
                var categories = parameters["categories"]?.ToObject<string[]>()
                    ?? new[] { "all" };

                var results = new Dictionary<string, object>();
                var summary = new ChecklistSummary();

                // Run all checks
                if (categories.Contains("all") || categories.Contains("sheets"))
                {
                    var sheetResult = CheckSheets(doc);
                    results["sheets"] = sheetResult;
                    UpdateSummary(summary, sheetResult);
                }

                if (categories.Contains("all") || categories.Contains("rooms"))
                {
                    var roomResult = CheckRooms(doc);
                    results["rooms"] = roomResult;
                    UpdateSummary(summary, roomResult);
                }

                if (categories.Contains("all") || categories.Contains("doors"))
                {
                    var doorResult = CheckDoors(doc);
                    results["doors"] = doorResult;
                    UpdateSummary(summary, doorResult);
                }

                if (categories.Contains("all") || categories.Contains("windows"))
                {
                    var windowResult = CheckWindows(doc);
                    results["windows"] = windowResult;
                    UpdateSummary(summary, windowResult);
                }

                if (categories.Contains("all") || categories.Contains("views"))
                {
                    var viewResult = CheckViews(doc);
                    results["views"] = viewResult;
                    UpdateSummary(summary, viewResult);
                }

                if (categories.Contains("all") || categories.Contains("schedules"))
                {
                    var scheduleResult = CheckSchedules(doc);
                    results["schedules"] = scheduleResult;
                    UpdateSummary(summary, scheduleResult);
                }

                if (categories.Contains("all") || categories.Contains("projectInfo"))
                {
                    var projectResult = CheckProjectInfo(doc);
                    results["projectInfo"] = projectResult;
                    UpdateSummary(summary, projectResult);
                }

                if (categories.Contains("all") || categories.Contains("levels"))
                {
                    var levelResult = CheckLevels(doc);
                    results["levels"] = levelResult;
                    UpdateSummary(summary, levelResult);
                }

                // Calculate overall pass rate
                summary.PassRate = summary.TotalChecks > 0
                    ? Math.Round((double)summary.Passed / summary.TotalChecks * 100, 1)
                    : 0;

                return JsonConvert.SerializeObject(new
                {
                    success = true,
                    projectName = doc.Title,
                    timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                    summary = new
                    {
                        passed = summary.Passed,
                        warnings = summary.Warnings,
                        failures = summary.Failures,
                        totalChecks = summary.TotalChecks,
                        passRate = summary.PassRate
                    },
                    results = includeDetails ? results : null,
                    recommendations = GenerateRecommendations(results)
                });
            }
            catch (Exception ex)
            {
                return JsonConvert.SerializeObject(new
                {
                    success = false,
                    error = ex.Message,
                    stackTrace = ex.StackTrace
                });
            }
        }

        #endregion

        #region Individual Check Methods

        /// <summary>
        /// Check sheet organization and completeness
        /// </summary>
        private static CheckResult CheckSheets(Document doc)
        {
            var result = new CheckResult { Category = "Sheets" };
            var issues = new List<string>();
            var details = new List<object>();

            // Get all sheets
            var sheets = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSheet))
                .Cast<ViewSheet>()
                .Where(s => !s.IsPlaceholder)
                .ToList();

            result.Count = sheets.Count;

            // Check for minimum sheets
            if (sheets.Count == 0)
            {
                issues.Add("No sheets found in model");
                result.Status = "FAIL";
            }
            else
            {
                // Group sheets by discipline
                var sheetsByDiscipline = sheets
                    .GroupBy(s => GetDiscipline(s.SheetNumber))
                    .ToDictionary(g => g.Key, g => g.ToList());

                details.Add(new {
                    totalSheets = sheets.Count,
                    byDiscipline = sheetsByDiscipline.ToDictionary(
                        kvp => kvp.Key,
                        kvp => kvp.Value.Count)
                });

                // Check for required architectural sheets
                var archSheets = sheets.Where(s => s.SheetNumber.StartsWith("A")).ToList();
                if (archSheets.Count == 0)
                {
                    issues.Add("No architectural sheets (A-series) found");
                }

                // Check for cover sheet
                var hasCover = sheets.Any(s =>
                    s.SheetNumber.Contains("0.0") ||
                    s.SheetNumber.Contains("-000") ||
                    s.SheetNumber.EndsWith("00") ||
                    s.Name.ToLower().Contains("cover"));
                if (!hasCover)
                {
                    issues.Add("No cover sheet detected");
                }

                // Check for orphan sheets (no viewports)
                var emptySheets = sheets.Where(s =>
                    new FilteredElementCollector(doc, s.Id)
                        .OfClass(typeof(Viewport))
                        .GetElementCount() == 0 &&
                    !s.Name.ToLower().Contains("cover") &&
                    !s.Name.ToLower().Contains("index") &&
                    !s.Name.ToLower().Contains("schedule")).ToList();

                if (emptySheets.Any())
                {
                    issues.Add($"{emptySheets.Count} sheet(s) have no viewports placed");
                    details.Add(new {
                        emptySheets = emptySheets.Select(s => new {
                            number = s.SheetNumber,
                            name = s.Name
                        })
                    });
                }

                result.Status = issues.Count == 0 ? "PASS" :
                               issues.Count <= 2 ? "WARNING" : "FAIL";
            }

            result.Issues = issues;
            result.Details = details;
            return result;
        }

        /// <summary>
        /// Check room naming and numbering
        /// </summary>
        private static CheckResult CheckRooms(Document doc)
        {
            var result = new CheckResult { Category = "Rooms" };
            var issues = new List<string>();
            var details = new List<object>();

            // Get all rooms
            var rooms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
                .Cast<Room>()
                .Where(r => r.Location != null && r.Area > 0)
                .ToList();

            result.Count = rooms.Count;

            if (rooms.Count == 0)
            {
                issues.Add("No placed rooms found in model");
                result.Status = "FAIL";
            }
            else
            {
                // Check for unnamed rooms
                var unnamedRooms = rooms.Where(r =>
                    string.IsNullOrWhiteSpace(r.Name) ||
                    r.Name == "Room").ToList();
                if (unnamedRooms.Any())
                {
                    issues.Add($"{unnamedRooms.Count} room(s) are unnamed");
                }

                // Check for unnumbered rooms
                var unnumberedRooms = rooms.Where(r =>
                    string.IsNullOrWhiteSpace(r.Number)).ToList();
                if (unnumberedRooms.Any())
                {
                    issues.Add($"{unnumberedRooms.Count} room(s) have no number");
                }

                // Check for duplicate room numbers
                var duplicateNumbers = rooms
                    .Where(r => !string.IsNullOrWhiteSpace(r.Number))
                    .GroupBy(r => r.Number)
                    .Where(g => g.Count() > 1)
                    .Select(g => g.Key)
                    .ToList();
                if (duplicateNumbers.Any())
                {
                    issues.Add($"Duplicate room numbers: {string.Join(", ", duplicateNumbers)}");
                }

                // Check for rooms without finishes (common finish parameters)
                var roomsWithoutFinish = rooms.Where(r =>
                {
                    var floorFinish = r.LookupParameter("Floor Finish")?.AsString();
                    var wallFinish = r.LookupParameter("Wall Finish")?.AsString();
                    return string.IsNullOrWhiteSpace(floorFinish) &&
                           string.IsNullOrWhiteSpace(wallFinish);
                }).ToList();

                if (roomsWithoutFinish.Count > rooms.Count / 2)
                {
                    issues.Add($"{roomsWithoutFinish.Count} room(s) have no finish data");
                }

                details.Add(new
                {
                    totalRooms = rooms.Count,
                    named = rooms.Count - unnamedRooms.Count,
                    numbered = rooms.Count - unnumberedRooms.Count,
                    withFinishes = rooms.Count - roomsWithoutFinish.Count
                });

                result.Status = issues.Count == 0 ? "PASS" :
                               issues.Count <= 2 ? "WARNING" : "FAIL";
            }

            result.Issues = issues;
            result.Details = details;
            return result;
        }

        /// <summary>
        /// Check door marks and schedule readiness
        /// </summary>
        private static CheckResult CheckDoors(Document doc)
        {
            var result = new CheckResult { Category = "Doors" };
            var issues = new List<string>();
            var details = new List<object>();

            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            result.Count = doors.Count;

            if (doors.Count == 0)
            {
                issues.Add("No doors found in model");
                result.Status = "WARNING";
            }
            else
            {
                // Check for unmarked doors
                var unmarkedDoors = doors.Where(d =>
                {
                    var mark = d.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString();
                    return string.IsNullOrWhiteSpace(mark);
                }).ToList();

                if (unmarkedDoors.Any())
                {
                    issues.Add($"{unmarkedDoors.Count} door(s) have no mark");
                }

                // Check for duplicate marks
                var duplicateMarks = doors
                    .Select(d => d.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString())
                    .Where(m => !string.IsNullOrWhiteSpace(m))
                    .GroupBy(m => m)
                    .Where(g => g.Count() > 1)
                    .Select(g => g.Key)
                    .ToList();

                if (duplicateMarks.Any())
                {
                    issues.Add($"Duplicate door marks: {string.Join(", ", duplicateMarks.Take(5))}" +
                        (duplicateMarks.Count > 5 ? $" (+{duplicateMarks.Count - 5} more)" : ""));
                }

                details.Add(new
                {
                    totalDoors = doors.Count,
                    marked = doors.Count - unmarkedDoors.Count,
                    unmarked = unmarkedDoors.Count,
                    duplicateMarks = duplicateMarks.Count
                });

                result.Status = unmarkedDoors.Count == 0 && duplicateMarks.Count == 0 ? "PASS" :
                               unmarkedDoors.Count <= 3 ? "WARNING" : "FAIL";
            }

            result.Issues = issues;
            result.Details = details;
            return result;
        }

        /// <summary>
        /// Check window marks and schedule readiness
        /// </summary>
        private static CheckResult CheckWindows(Document doc)
        {
            var result = new CheckResult { Category = "Windows" };
            var issues = new List<string>();
            var details = new List<object>();

            var windows = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            result.Count = windows.Count;

            if (windows.Count == 0)
            {
                // Windows might not exist in all building types
                result.Status = "PASS";
                details.Add(new { note = "No windows in model (may be intentional)" });
            }
            else
            {
                // Check for unmarked windows
                var unmarkedWindows = windows.Where(w =>
                {
                    var mark = w.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString();
                    return string.IsNullOrWhiteSpace(mark);
                }).ToList();

                if (unmarkedWindows.Any())
                {
                    issues.Add($"{unmarkedWindows.Count} window(s) have no mark");
                }

                details.Add(new
                {
                    totalWindows = windows.Count,
                    marked = windows.Count - unmarkedWindows.Count,
                    unmarked = unmarkedWindows.Count
                });

                result.Status = unmarkedWindows.Count == 0 ? "PASS" :
                               unmarkedWindows.Count <= 3 ? "WARNING" : "FAIL";
            }

            result.Issues = issues;
            result.Details = details;
            return result;
        }

        /// <summary>
        /// Check view organization and placement
        /// </summary>
        private static CheckResult CheckViews(Document doc)
        {
            var result = new CheckResult { Category = "Views" };
            var issues = new List<string>();
            var details = new List<object>();

            // Get all views (excluding templates and schedules)
            var views = new FilteredElementCollector(doc)
                .OfClass(typeof(View))
                .Cast<View>()
                .Where(v => !v.IsTemplate &&
                           v.ViewType != ViewType.Schedule &&
                           v.ViewType != ViewType.DrawingSheet)
                .ToList();

            result.Count = views.Count;

            // Get all viewports
            var viewports = new FilteredElementCollector(doc)
                .OfClass(typeof(Viewport))
                .Cast<Viewport>()
                .ToList();

            var viewsOnSheets = viewports.Select(vp => vp.ViewId).Distinct().ToList();

            // Check for floor plans
            var floorPlans = views.Where(v => v.ViewType == ViewType.FloorPlan).ToList();
            var floorPlansOnSheets = floorPlans.Where(v => viewsOnSheets.Contains(v.Id)).ToList();

            if (floorPlans.Count == 0)
            {
                issues.Add("No floor plans found");
            }
            else if (floorPlansOnSheets.Count < floorPlans.Count)
            {
                issues.Add($"{floorPlans.Count - floorPlansOnSheets.Count} floor plan(s) not on sheets");
            }

            // Check for elevations
            var elevations = views.Where(v => v.ViewType == ViewType.Elevation).ToList();
            var elevationsOnSheets = elevations.Where(v => viewsOnSheets.Contains(v.Id)).ToList();

            if (elevations.Count < 4)
            {
                issues.Add($"Only {elevations.Count} elevation(s) (need 4 for complete set)");
            }

            // Check for sections
            var sections = views.Where(v => v.ViewType == ViewType.Section).ToList();
            if (sections.Count == 0)
            {
                issues.Add("No building sections found");
            }

            // Orphan views (not on any sheet)
            var orphanViews = views.Where(v =>
                !viewsOnSheets.Contains(v.Id) &&
                v.ViewType != ViewType.ThreeD &&
                v.ViewType != ViewType.Legend &&
                !v.Name.StartsWith("_") &&
                !v.Name.Contains("Working")).Count();

            if (orphanViews > 10)
            {
                issues.Add($"{orphanViews} view(s) not placed on sheets");
            }

            details.Add(new
            {
                totalViews = views.Count,
                floorPlans = floorPlans.Count,
                elevations = elevations.Count,
                sections = sections.Count,
                onSheets = viewsOnSheets.Count,
                orphanViews = orphanViews
            });

            result.Status = issues.Count == 0 ? "PASS" :
                           issues.Count <= 2 ? "WARNING" : "FAIL";

            result.Issues = issues;
            result.Details = details;
            return result;
        }

        /// <summary>
        /// Check required schedules exist
        /// </summary>
        private static CheckResult CheckSchedules(Document doc)
        {
            var result = new CheckResult { Category = "Schedules" };
            var issues = new List<string>();
            var details = new List<object>();

            var schedules = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSchedule))
                .Cast<ViewSchedule>()
                .Where(s => !s.IsTitleblockRevisionSchedule && !s.IsTemplate)
                .ToList();

            result.Count = schedules.Count;

            // Check for essential schedules
            var hasDoorSchedule = schedules.Any(s =>
                s.Name.ToLower().Contains("door"));
            var hasWindowSchedule = schedules.Any(s =>
                s.Name.ToLower().Contains("window"));
            var hasRoomSchedule = schedules.Any(s =>
                s.Name.ToLower().Contains("room") ||
                s.Name.ToLower().Contains("finish"));
            var hasSheetIndex = schedules.Any(s =>
                s.Name.ToLower().Contains("sheet") ||
                s.Name.ToLower().Contains("index") ||
                s.Name.ToLower().Contains("drawing list"));

            if (!hasDoorSchedule)
                issues.Add("No door schedule found");
            if (!hasWindowSchedule)
                issues.Add("No window schedule found");
            if (!hasRoomSchedule)
                issues.Add("No room/finish schedule found");
            if (!hasSheetIndex)
                issues.Add("No sheet index/drawing list found");

            // Check schedules are on sheets
            var viewports = new FilteredElementCollector(doc)
                .OfClass(typeof(Viewport))
                .Cast<Viewport>()
                .ToList();
            var viewsOnSheets = viewports.Select(vp => vp.ViewId).Distinct().ToList();

            var schedulesOnSheets = schedules.Where(s => viewsOnSheets.Contains(s.Id)).Count();

            details.Add(new
            {
                totalSchedules = schedules.Count,
                onSheets = schedulesOnSheets,
                hasDoorSchedule,
                hasWindowSchedule,
                hasRoomSchedule,
                hasSheetIndex
            });

            result.Status = issues.Count == 0 ? "PASS" :
                           issues.Count <= 2 ? "WARNING" : "FAIL";

            result.Issues = issues;
            result.Details = details;
            return result;
        }

        /// <summary>
        /// Check project information completeness
        /// </summary>
        private static CheckResult CheckProjectInfo(Document doc)
        {
            var result = new CheckResult { Category = "Project Info" };
            var issues = new List<string>();
            var details = new List<object>();

            var projectInfo = doc.ProjectInformation;
            result.Count = 1;

            // Check required fields
            if (string.IsNullOrWhiteSpace(projectInfo.Name) || projectInfo.Name == "Project Name")
                issues.Add("Project name not set");

            if (string.IsNullOrWhiteSpace(projectInfo.Number) || projectInfo.Number == "Project Number")
                issues.Add("Project number not set");

            if (string.IsNullOrWhiteSpace(projectInfo.Address))
                issues.Add("Project address not set");

            if (string.IsNullOrWhiteSpace(projectInfo.ClientName))
                issues.Add("Client name not set");

            // Check for issue date
            var issueDate = projectInfo.IssueDate;
            if (string.IsNullOrWhiteSpace(issueDate))
                issues.Add("Issue date not set");

            details.Add(new
            {
                name = projectInfo.Name,
                number = projectInfo.Number,
                address = projectInfo.Address,
                client = projectInfo.ClientName,
                issueDate = issueDate,
                status = projectInfo.Status
            });

            result.Status = issues.Count == 0 ? "PASS" :
                           issues.Count <= 2 ? "WARNING" : "FAIL";

            result.Issues = issues;
            result.Details = details;
            return result;
        }

        /// <summary>
        /// Check levels match floor plans
        /// </summary>
        private static CheckResult CheckLevels(Document doc)
        {
            var result = new CheckResult { Category = "Levels" };
            var issues = new List<string>();
            var details = new List<object>();

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .Where(l => !l.Name.ToLower().Contains("ref"))
                .OrderBy(l => l.Elevation)
                .ToList();

            result.Count = levels.Count;

            // Get floor plans
            var floorPlans = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => v.ViewType == ViewType.FloorPlan && !v.IsTemplate)
                .ToList();

            // Check each level has a floor plan
            foreach (var level in levels)
            {
                var hasFloorPlan = floorPlans.Any(fp =>
                    fp.GenLevel?.Id == level.Id);
                if (!hasFloorPlan)
                {
                    // Skip levels that are typically not plans
                    if (!level.Name.ToLower().Contains("t.o.") &&
                        !level.Name.ToLower().Contains("parapet") &&
                        !level.Name.ToLower().Contains("bearing"))
                    {
                        issues.Add($"Level '{level.Name}' has no floor plan");
                    }
                }
            }

            details.Add(new
            {
                totalLevels = levels.Count,
                floorPlans = floorPlans.Count,
                levels = levels.Select(l => new
                {
                    name = l.Name,
                    elevation = Math.Round(l.Elevation, 2)
                })
            });

            result.Status = issues.Count == 0 ? "PASS" :
                           issues.Count <= 1 ? "WARNING" : "FAIL";

            result.Issues = issues;
            result.Details = details;
            return result;
        }

        #endregion

        #region Helper Methods

        private static string GetDiscipline(string sheetNumber)
        {
            if (string.IsNullOrEmpty(sheetNumber)) return "Unknown";

            var firstChar = sheetNumber.ToUpper()[0];
            switch (firstChar)
            {
                case 'G': return "General";
                case 'C': return "Civil";
                case 'L': return "Landscape";
                case 'A': return "Architectural";
                case 'S': return "Structural";
                case 'M': return "Mechanical";
                case 'P': return "Plumbing";
                case 'E': return "Electrical";
                case 'F': return "Fire Protection";
                case 'I': return "Interiors";
                default: return "Other";
            }
        }

        private static void UpdateSummary(ChecklistSummary summary, CheckResult result)
        {
            summary.TotalChecks++;
            switch (result.Status)
            {
                case "PASS": summary.Passed++; break;
                case "WARNING": summary.Warnings++; break;
                case "FAIL": summary.Failures++; break;
            }
        }

        private static List<string> GenerateRecommendations(Dictionary<string, object> results)
        {
            var recommendations = new List<string>();

            foreach (var kvp in results)
            {
                if (kvp.Value is CheckResult cr && cr.Issues?.Count > 0)
                {
                    switch (cr.Category)
                    {
                        case "Rooms":
                            if (cr.Issues.Any(i => i.Contains("unnamed")))
                                recommendations.Add("Run Room naming tool to assign room names");
                            if (cr.Issues.Any(i => i.Contains("no number")))
                                recommendations.Add("Number rooms using Auto-Number feature");
                            break;
                        case "Doors":
                            if (cr.Issues.Any(i => i.Contains("no mark")))
                                recommendations.Add("Tag doors and assign marks before creating schedule");
                            break;
                        case "Windows":
                            if (cr.Issues.Any(i => i.Contains("no mark")))
                                recommendations.Add("Tag windows and assign marks before creating schedule");
                            break;
                        case "Schedules":
                            if (cr.Issues.Any(i => i.Contains("door schedule")))
                                recommendations.Add("Create Door Schedule from View > Schedules");
                            if (cr.Issues.Any(i => i.Contains("window schedule")))
                                recommendations.Add("Create Window Schedule from View > Schedules");
                            break;
                        case "Views":
                            if (cr.Issues.Any(i => i.Contains("not on sheets")))
                                recommendations.Add("Place working views on sheets or prefix with '_' to exclude");
                            break;
                    }
                }
            }

            if (recommendations.Count == 0)
                recommendations.Add("All checks passed - model is ready for documentation");

            return recommendations;
        }

        #endregion

        #region Data Classes

        private class ChecklistSummary
        {
            public int Passed { get; set; }
            public int Warnings { get; set; }
            public int Failures { get; set; }
            public int TotalChecks { get; set; }
            public double PassRate { get; set; }
        }

        private class CheckResult
        {
            public string Category { get; set; }
            public string Status { get; set; } = "PASS";
            public int Count { get; set; }
            public List<string> Issues { get; set; } = new List<string>();
            public List<object> Details { get; set; } = new List<object>();
        }

        #endregion
    }
}
