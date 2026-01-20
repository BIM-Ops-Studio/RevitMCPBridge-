using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json;

namespace RevitMCPBridge
{
    /// <summary>
    /// Provides intelligent layout recommendations for sheets, viewports, and elements.
    /// Uses learned preferences to suggest optimal placements.
    /// </summary>
    public class LayoutIntelligence
    {
        private static LayoutIntelligence _instance;
        private static readonly object _lock = new object();

        // Standard sheet sizes (in feet)
        private static readonly Dictionary<string, (double Width, double Height)> SheetSizes = new Dictionary<string, (double, double)>
        {
            { "ARCH_D", (3.0, 2.0) },      // 36" x 24"
            { "ARCH_C", (1.5, 1.0) },      // 18" x 12"
            { "ARCH_E", (4.0, 3.0) },      // 48" x 36"
            { "ANSI_B", (1.4167, 0.9167) }, // 17" x 11"
            { "ANSI_D", (2.8333, 1.8333) }  // 34" x 22"
        };

        // Standard margins (in feet)
        private const double LeftMargin = 0.125;    // 1.5"
        private const double RightMargin = 0.0833;  // 1"
        private const double TopMargin = 0.0833;    // 1"
        private const double BottomMargin = 0.25;   // 3" (for title block)

        public static LayoutIntelligence Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new LayoutIntelligence();
                        }
                    }
                }
                return _instance;
            }
        }

        private LayoutIntelligence() { }

        #region Sheet Layout Recommendations

        /// <summary>
        /// Get recommended viewport positions for a set of views on a sheet
        /// </summary>
        public SheetLayoutRecommendation GetSheetLayout(
            ViewSheet sheet,
            List<View> viewsToPlace,
            Document doc)
        {
            var recommendation = new SheetLayoutRecommendation
            {
                SheetNumber = sheet.SheetNumber,
                SheetName = sheet.Name,
                ViewPlacements = new List<ViewportPlacement>()
            };

            // Get sheet dimensions
            var sheetSize = GetSheetSize(sheet, doc);
            double usableWidth = sheetSize.Width - LeftMargin - RightMargin;
            double usableHeight = sheetSize.Height - TopMargin - BottomMargin;

            // Analyze views to determine best layout
            var viewAnalysis = AnalyzeViews(viewsToPlace, doc);

            // Determine layout strategy based on view types
            LayoutStrategy strategy = DetermineLayoutStrategy(viewAnalysis);

            // Generate placements based on strategy
            switch (strategy)
            {
                case LayoutStrategy.SingleLarge:
                    recommendation.ViewPlacements = GenerateSingleLargeLayout(
                        viewsToPlace, sheetSize, usableWidth, usableHeight);
                    break;

                case LayoutStrategy.GridLayout:
                    recommendation.ViewPlacements = GenerateGridLayout(
                        viewsToPlace, sheetSize, usableWidth, usableHeight);
                    break;

                case LayoutStrategy.PlanWithDetails:
                    recommendation.ViewPlacements = GeneratePlanWithDetailsLayout(
                        viewsToPlace, viewAnalysis, sheetSize, usableWidth, usableHeight);
                    break;

                case LayoutStrategy.ElevationsRow:
                    recommendation.ViewPlacements = GenerateElevationsRowLayout(
                        viewsToPlace, sheetSize, usableWidth, usableHeight);
                    break;

                case LayoutStrategy.SectionsColumn:
                    recommendation.ViewPlacements = GenerateSectionsColumnLayout(
                        viewsToPlace, sheetSize, usableWidth, usableHeight);
                    break;

                default:
                    recommendation.ViewPlacements = GenerateAutoLayout(
                        viewsToPlace, sheetSize, usableWidth, usableHeight);
                    break;
            }

            // Apply learned preferences if available
            ApplyLearnedPreferences(recommendation.ViewPlacements, viewsToPlace);

            recommendation.Strategy = strategy.ToString();
            recommendation.Confidence = CalculateLayoutConfidence(recommendation.ViewPlacements);

            return recommendation;
        }

        /// <summary>
        /// Recommend scale for a view based on learned preferences and view size
        /// </summary>
        public ScaleRecommendation RecommendScale(View view, double availableWidth, double availableHeight)
        {
            // Check learned preferences first
            int? preferredScale = PreferenceLearner.Instance.GetPreferredScale(view.ViewType.ToString());

            // Standard scales to consider
            int[] standardScales = { 192, 96, 48, 24, 16, 12, 8, 4, 2, 1 };
            // 192 = 1/16" = 1'-0", 96 = 1/8", 48 = 1/4", 24 = 1/2", etc.

            // Get view's actual size at scale 1
            var cropBox = view.CropBox;
            if (cropBox == null)
            {
                return new ScaleRecommendation
                {
                    RecommendedScale = preferredScale ?? 48,
                    Reason = "Default scale (no crop box)",
                    Confidence = 0.5
                };
            }

            double viewWidth = Math.Abs(cropBox.Max.X - cropBox.Min.X);
            double viewHeight = Math.Abs(cropBox.Max.Y - cropBox.Min.Y);

            // Find largest scale that fits
            int bestScale = 192;
            foreach (int scale in standardScales)
            {
                double scaledWidth = viewWidth / scale;
                double scaledHeight = viewHeight / scale;

                if (scaledWidth <= availableWidth && scaledHeight <= availableHeight)
                {
                    bestScale = scale;
                    break;
                }
            }

            // Consider preference
            if (preferredScale.HasValue)
            {
                // Use preference if it fits
                double prefWidth = viewWidth / preferredScale.Value;
                double prefHeight = viewHeight / preferredScale.Value;

                if (prefWidth <= availableWidth && prefHeight <= availableHeight)
                {
                    return new ScaleRecommendation
                    {
                        RecommendedScale = preferredScale.Value,
                        AlternativeScale = bestScale,
                        Reason = "Based on your usual preference",
                        Confidence = 0.9
                    };
                }
            }

            return new ScaleRecommendation
            {
                RecommendedScale = bestScale,
                Reason = "Calculated to fit available space",
                Confidence = 0.7
            };
        }

        #endregion

        #region Layout Strategies

        private ViewAnalysis AnalyzeViews(List<View> views, Document doc)
        {
            var analysis = new ViewAnalysis
            {
                TotalViews = views.Count,
                ViewsByType = views.GroupBy(v => v.ViewType).ToDictionary(g => g.Key, g => g.ToList()),
                HasFloorPlan = views.Any(v => v.ViewType == ViewType.FloorPlan),
                HasElevations = views.Any(v => v.ViewType == ViewType.Elevation),
                HasSections = views.Any(v => v.ViewType == ViewType.Section),
                HasDetails = views.Any(v => v.ViewType == ViewType.Detail),
                HasSchedules = views.Any(v => v.ViewType == ViewType.Schedule)
            };

            // Calculate view sizes
            foreach (var view in views)
            {
                if (view.CropBox != null)
                {
                    double width = Math.Abs(view.CropBox.Max.X - view.CropBox.Min.X);
                    double height = Math.Abs(view.CropBox.Max.Y - view.CropBox.Min.Y);
                    analysis.ViewSizes[view.Id.Value] = (width, height);
                }
            }

            return analysis;
        }

        private LayoutStrategy DetermineLayoutStrategy(ViewAnalysis analysis)
        {
            // Single view - use single large layout
            if (analysis.TotalViews == 1)
                return LayoutStrategy.SingleLarge;

            // Floor plan with details
            if (analysis.HasFloorPlan && analysis.HasDetails && !analysis.HasElevations)
                return LayoutStrategy.PlanWithDetails;

            // All elevations
            if (analysis.HasElevations && GetViewCount(analysis.ViewsByType, ViewType.Elevation) >= 2)
                return LayoutStrategy.ElevationsRow;

            // All sections
            if (analysis.HasSections && GetViewCount(analysis.ViewsByType, ViewType.Section) >= 2)
                return LayoutStrategy.SectionsColumn;

            // Multiple views of same type - grid
            if (analysis.ViewsByType.Count == 1 && analysis.TotalViews <= 4)
                return LayoutStrategy.GridLayout;

            // Mixed views - auto layout
            return LayoutStrategy.AutoLayout;
        }

        private List<ViewportPlacement> GenerateSingleLargeLayout(
            List<View> views, (double Width, double Height) sheetSize,
            double usableWidth, double usableHeight)
        {
            var placements = new List<ViewportPlacement>();
            if (!views.Any()) return placements;

            var view = views.First();

            // Center the view in the usable area
            double centerX = LeftMargin + usableWidth / 2;
            double centerY = BottomMargin + usableHeight / 2;

            placements.Add(new ViewportPlacement
            {
                ViewId = view.Id.Value,
                ViewName = view.Name,
                ViewType = view.ViewType.ToString(),
                CenterX = centerX,
                CenterY = centerY,
                RecommendedScale = CalculateOptimalScale(view, usableWidth, usableHeight),
                Reason = "Centered single view"
            });

            return placements;
        }

        private List<ViewportPlacement> GenerateGridLayout(
            List<View> views, (double Width, double Height) sheetSize,
            double usableWidth, double usableHeight)
        {
            var placements = new List<ViewportPlacement>();
            int count = views.Count;

            // Determine grid dimensions
            int cols = (int)Math.Ceiling(Math.Sqrt(count));
            int rows = (int)Math.Ceiling((double)count / cols);

            double cellWidth = usableWidth / cols;
            double cellHeight = usableHeight / rows;

            for (int i = 0; i < views.Count; i++)
            {
                int col = i % cols;
                int row = rows - 1 - (i / cols); // Start from top

                double centerX = LeftMargin + (col + 0.5) * cellWidth;
                double centerY = BottomMargin + (row + 0.5) * cellHeight;

                placements.Add(new ViewportPlacement
                {
                    ViewId = views[i].Id.Value,
                    ViewName = views[i].Name,
                    ViewType = views[i].ViewType.ToString(),
                    CenterX = centerX,
                    CenterY = centerY,
                    RecommendedScale = CalculateOptimalScale(views[i], cellWidth * 0.9, cellHeight * 0.9),
                    Reason = $"Grid position [{row},{col}]"
                });
            }

            return placements;
        }

        private List<ViewportPlacement> GeneratePlanWithDetailsLayout(
            List<View> views, ViewAnalysis analysis,
            (double Width, double Height) sheetSize,
            double usableWidth, double usableHeight)
        {
            var placements = new List<ViewportPlacement>();

            // Floor plan takes 2/3 of width on left
            var floorPlans = views.Where(v => v.ViewType == ViewType.FloorPlan).ToList();
            var details = views.Where(v => v.ViewType == ViewType.Detail).ToList();
            var others = views.Except(floorPlans).Except(details).ToList();

            double planWidth = usableWidth * 0.65;
            double detailWidth = usableWidth * 0.35;

            // Place floor plans on left
            double planCenterX = LeftMargin + planWidth / 2;
            double planCenterY = BottomMargin + usableHeight / 2;

            foreach (var plan in floorPlans)
            {
                placements.Add(new ViewportPlacement
                {
                    ViewId = plan.Id.Value,
                    ViewName = plan.Name,
                    ViewType = plan.ViewType.ToString(),
                    CenterX = planCenterX,
                    CenterY = planCenterY,
                    RecommendedScale = CalculateOptimalScale(plan, planWidth * 0.9, usableHeight * 0.9),
                    Reason = "Main floor plan (left side)"
                });
            }

            // Stack details on right
            if (details.Any())
            {
                double detailHeight = usableHeight / details.Count;
                double detailCenterX = LeftMargin + planWidth + detailWidth / 2;

                for (int i = 0; i < details.Count; i++)
                {
                    double detailCenterY = BottomMargin + usableHeight - (i + 0.5) * detailHeight;

                    placements.Add(new ViewportPlacement
                    {
                        ViewId = details[i].Id.Value,
                        ViewName = details[i].Name,
                        ViewType = details[i].ViewType.ToString(),
                        CenterX = detailCenterX,
                        CenterY = detailCenterY,
                        RecommendedScale = CalculateOptimalScale(details[i], detailWidth * 0.9, detailHeight * 0.9),
                        Reason = $"Detail {i + 1} (right column)"
                    });
                }
            }

            return placements;
        }

        private List<ViewportPlacement> GenerateElevationsRowLayout(
            List<View> views, (double Width, double Height) sheetSize,
            double usableWidth, double usableHeight)
        {
            var placements = new List<ViewportPlacement>();
            var elevations = views.Where(v => v.ViewType == ViewType.Elevation).ToList();

            double elevWidth = usableWidth / elevations.Count;
            double centerY = BottomMargin + usableHeight / 2;

            for (int i = 0; i < elevations.Count; i++)
            {
                double centerX = LeftMargin + (i + 0.5) * elevWidth;

                placements.Add(new ViewportPlacement
                {
                    ViewId = elevations[i].Id.Value,
                    ViewName = elevations[i].Name,
                    ViewType = elevations[i].ViewType.ToString(),
                    CenterX = centerX,
                    CenterY = centerY,
                    RecommendedScale = CalculateOptimalScale(elevations[i], elevWidth * 0.9, usableHeight * 0.8),
                    Reason = $"Elevation {i + 1} (horizontal row)"
                });
            }

            return placements;
        }

        private List<ViewportPlacement> GenerateSectionsColumnLayout(
            List<View> views, (double Width, double Height) sheetSize,
            double usableWidth, double usableHeight)
        {
            var placements = new List<ViewportPlacement>();
            var sections = views.Where(v => v.ViewType == ViewType.Section).ToList();

            double sectionHeight = usableHeight / sections.Count;
            double centerX = LeftMargin + usableWidth / 2;

            for (int i = 0; i < sections.Count; i++)
            {
                double centerY = BottomMargin + usableHeight - (i + 0.5) * sectionHeight;

                placements.Add(new ViewportPlacement
                {
                    ViewId = sections[i].Id.Value,
                    ViewName = sections[i].Name,
                    ViewType = sections[i].ViewType.ToString(),
                    CenterX = centerX,
                    CenterY = centerY,
                    RecommendedScale = CalculateOptimalScale(sections[i], usableWidth * 0.9, sectionHeight * 0.85),
                    Reason = $"Section {i + 1} (vertical stack)"
                });
            }

            return placements;
        }

        private List<ViewportPlacement> GenerateAutoLayout(
            List<View> views, (double Width, double Height) sheetSize,
            double usableWidth, double usableHeight)
        {
            // Fall back to grid layout for mixed content
            return GenerateGridLayout(views, sheetSize, usableWidth, usableHeight);
        }

        #endregion

        #region Viewport Recommendations

        /// <summary>
        /// Suggest optimal viewport position based on view content
        /// </summary>
        public ViewportPlacement SuggestViewportPosition(
            View view,
            ViewSheet sheet,
            List<Viewport> existingViewports,
            Document doc)
        {
            var sheetSize = GetSheetSize(sheet, doc);
            double usableWidth = sheetSize.Width - LeftMargin - RightMargin;
            double usableHeight = sheetSize.Height - TopMargin - BottomMargin;

            // Map existing viewport positions
            var occupiedAreas = existingViewports.Select(vp =>
            {
                var center = vp.GetBoxCenter();
                var outline = vp.GetBoxOutline();
                return new
                {
                    MinX = outline.MinimumPoint.X,
                    MaxX = outline.MaximumPoint.X,
                    MinY = outline.MinimumPoint.Y,
                    MaxY = outline.MaximumPoint.Y,
                    Center = center
                };
            }).ToList();

            // Check learned preferences
            var placementPref = PreferenceLearner.Instance.GetPlacementPreference("Viewport", view.ViewType.ToString());

            // Determine best position
            double suggestedX, suggestedY;

            if (placementPref != null && placementPref.IsConsistent)
            {
                // Use learned preference
                suggestedX = placementPref.AverageNormalizedX.Value * sheetSize.Width;
                suggestedY = placementPref.AverageNormalizedY.Value * sheetSize.Height;
            }
            else
            {
                // Find open space
                suggestedX = LeftMargin + usableWidth / 2;
                suggestedY = BottomMargin + usableHeight / 2;

                // Adjust if overlapping with existing
                foreach (var area in occupiedAreas)
                {
                    if (Math.Abs(suggestedX - area.Center.X) < 0.5 &&
                        Math.Abs(suggestedY - area.Center.Y) < 0.5)
                    {
                        // Shift to find open space
                        suggestedX += 0.5;
                        if (suggestedX > sheetSize.Width - RightMargin)
                        {
                            suggestedX = LeftMargin + 0.25;
                            suggestedY -= 0.5;
                        }
                    }
                }
            }

            return new ViewportPlacement
            {
                ViewId = view.Id.Value,
                ViewName = view.Name,
                ViewType = view.ViewType.ToString(),
                CenterX = suggestedX,
                CenterY = suggestedY,
                RecommendedScale = CalculateOptimalScale(view, usableWidth * 0.8, usableHeight * 0.8),
                Reason = placementPref != null ? "Based on your placement pattern" : "Auto-calculated position"
            };
        }

        #endregion

        #region Helper Methods

        private int GetViewCount(Dictionary<ViewType, List<View>> viewsByType, ViewType viewType)
        {
            if (viewsByType.ContainsKey(viewType))
            {
                return viewsByType[viewType]?.Count ?? 0;
            }
            return 0;
        }

        private (double Width, double Height) GetSheetSize(ViewSheet sheet, Document doc)
        {
            try
            {
                var titleBlock = new FilteredElementCollector(doc, sheet.Id)
                    .OfCategory(BuiltInCategory.OST_TitleBlocks)
                    .FirstElement() as FamilyInstance;

                if (titleBlock != null)
                {
                    var widthParam = titleBlock.LookupParameter("Sheet Width");
                    var heightParam = titleBlock.LookupParameter("Sheet Height");

                    if (widthParam != null && heightParam != null)
                    {
                        return (widthParam.AsDouble(), heightParam.AsDouble());
                    }
                }
            }
            catch { }

            // Default to ARCH D
            return SheetSizes["ARCH_D"];
        }

        private int CalculateOptimalScale(View view, double availableWidth, double availableHeight)
        {
            int[] standardScales = { 192, 96, 48, 24, 16, 12, 8, 4, 2, 1 };

            if (view.CropBox == null)
                return 48; // Default 1/4" = 1'-0"

            double viewWidth = Math.Abs(view.CropBox.Max.X - view.CropBox.Min.X);
            double viewHeight = Math.Abs(view.CropBox.Max.Y - view.CropBox.Min.Y);

            foreach (int scale in standardScales)
            {
                double scaledWidth = viewWidth / scale;
                double scaledHeight = viewHeight / scale;

                if (scaledWidth <= availableWidth && scaledHeight <= availableHeight)
                {
                    return scale;
                }
            }

            return 192; // Smallest scale
        }

        private void ApplyLearnedPreferences(List<ViewportPlacement> placements, List<View> views)
        {
            foreach (var placement in placements)
            {
                var view = views.FirstOrDefault(v => v.Id.Value == placement.ViewId);
                if (view == null) continue;

                // Check for scale preference
                var preferredScale = PreferenceLearner.Instance.GetPreferredScale(view.ViewType.ToString());
                if (preferredScale.HasValue)
                {
                    // Only override if the preferred scale would fit
                    // (keep the calculated scale as it's guaranteed to fit)
                    placement.AlternativeScale = preferredScale.Value;
                    placement.PreferenceNote = $"You usually use 1/{preferredScale.Value}\" scale for {view.ViewType}";
                }
            }
        }

        private double CalculateLayoutConfidence(List<ViewportPlacement> placements)
        {
            if (!placements.Any()) return 0;

            // Higher confidence if based on learned preferences
            int preferenceBasedCount = placements.Count(p => p.Reason.Contains("pattern") || p.Reason.Contains("preference"));
            return 0.5 + (0.5 * preferenceBasedCount / placements.Count);
        }

        #endregion
    }

    #region Supporting Types

    public enum LayoutStrategy
    {
        SingleLarge,
        GridLayout,
        PlanWithDetails,
        ElevationsRow,
        SectionsColumn,
        AutoLayout
    }

    public class ViewAnalysis
    {
        public int TotalViews { get; set; }
        public Dictionary<ViewType, List<View>> ViewsByType { get; set; } = new Dictionary<ViewType, List<View>>();
        public Dictionary<long, (double Width, double Height)> ViewSizes { get; set; } = new Dictionary<long, (double, double)>();
        public bool HasFloorPlan { get; set; }
        public bool HasElevations { get; set; }
        public bool HasSections { get; set; }
        public bool HasDetails { get; set; }
        public bool HasSchedules { get; set; }
    }

    public class SheetLayoutRecommendation
    {
        public string SheetNumber { get; set; }
        public string SheetName { get; set; }
        public string Strategy { get; set; }
        public double Confidence { get; set; }
        public List<ViewportPlacement> ViewPlacements { get; set; }
    }

    public class ViewportPlacement
    {
        public long ViewId { get; set; }
        public string ViewName { get; set; }
        public string ViewType { get; set; }
        public double CenterX { get; set; }
        public double CenterY { get; set; }
        public int RecommendedScale { get; set; }
        public int? AlternativeScale { get; set; }
        public string Reason { get; set; }
        public string PreferenceNote { get; set; }
    }

    public class ScaleRecommendation
    {
        public int RecommendedScale { get; set; }
        public int? AlternativeScale { get; set; }
        public string Reason { get; set; }
        public double Confidence { get; set; }
    }

    #endregion
}
