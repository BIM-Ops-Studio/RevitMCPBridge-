using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Events;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge
{
    /// <summary>
    /// Smart Element Info Panel - Dockable WPF panel that shows comprehensive element information
    /// with clickable links to related views, schedules, and manufacturer resources.
    /// Built entirely in code for Revit compatibility.
    /// </summary>
    public class SmartElementPanel : Window
    {
        #region UI Elements

        private TextBlock _headerText;
        private TextBlock _categoryText;
        private StackPanel _specsPanel;
        private StackPanel _linkedViewsPanel;
        private ListBox _linkedViewsList;
        private Button _openViewButton;
        private StackPanel _schedulePanel;
        private Button _scheduleButton;
        private StackPanel _resourcesPanel;
        private TextBlock _statusText;
        private ScrollViewer _mainScrollViewer;

        #endregion

        #region Fields

        private UIApplication _uiApp;
        private Element _currentElement;
        private ElementType _currentElementType;
        private Document _currentDocument;
        private bool _isUpdating;
        private bool _isClosing;

        // Colors (using fully qualified name to avoid ambiguity with Autodesk.Revit.DB.Color)
        private static readonly SolidColorBrush DarkBackground = new SolidColorBrush(System.Windows.Media.Color.FromRgb(30, 30, 30));
        private static readonly SolidColorBrush PanelBackground = new SolidColorBrush(System.Windows.Media.Color.FromRgb(45, 45, 45));
        private static readonly SolidColorBrush AccentColor = new SolidColorBrush(System.Windows.Media.Color.FromRgb(0, 122, 204));
        private static readonly SolidColorBrush TextColor = new SolidColorBrush(System.Windows.Media.Color.FromRgb(220, 220, 220));
        private static readonly SolidColorBrush LabelColor = new SolidColorBrush(System.Windows.Media.Color.FromRgb(140, 140, 140));
        private static readonly SolidColorBrush LinkColor = new SolidColorBrush(System.Windows.Media.Color.FromRgb(86, 156, 214));

        #endregion

        #region Constructor

        public SmartElementPanel(UIApplication uiApp)
        {
            _uiApp = uiApp;
            _currentDocument = uiApp?.ActiveUIDocument?.Document;

            // Window setup
            Title = "Smart Element Info";
            Width = 350;
            Height = 600;
            MinWidth = 280;
            MinHeight = 400;
            WindowStartupLocation = WindowStartupLocation.Manual;
            Left = SystemParameters.PrimaryScreenWidth - 370;
            Top = 100;
            Background = DarkBackground;
            WindowStyle = WindowStyle.ToolWindow;
            Topmost = true;

            // Build UI
            BuildUI();

            // Subscribe to selection changed event
            if (_uiApp?.ActiveUIDocument != null)
            {
                _uiApp.Application.DocumentChanged += OnDocumentChanged;
            }

            // Initial update
            UpdatePanelFromSelection();

            // Handle closing - prevent crash by properly cleaning up
            Closing += (s, e) =>
            {
                _isClosing = true;
                try
                {
                    if (_uiApp?.Application != null)
                    {
                        _uiApp.Application.DocumentChanged -= OnDocumentChanged;
                    }
                }
                catch
                {
                    // Ignore errors during cleanup
                }
            };

            Closed += (s, e) =>
            {
                _uiApp = null;
                _currentDocument = null;
                _currentElement = null;
                _currentElementType = null;
            };
        }

        #endregion

        #region UI Building

        private void BuildUI()
        {
            var mainGrid = new System.Windows.Controls.Grid();
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); // Header
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) }); // Content
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); // Status

            // Header
            var header = CreateHeader();
            System.Windows.Controls.Grid.SetRow(header, 0);
            ((System.Windows.Controls.Panel)mainGrid).Children.Add(header);

            // Scrollable content area
            _mainScrollViewer = new ScrollViewer
            {
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Margin = new Thickness(0)
            };
            var contentPanel = CreateContentPanel();
            _mainScrollViewer.Content = contentPanel;
            System.Windows.Controls.Grid.SetRow(_mainScrollViewer, 1);
            ((System.Windows.Controls.Panel)mainGrid).Children.Add(_mainScrollViewer);

            // Status bar
            var statusBar = CreateStatusBar();
            System.Windows.Controls.Grid.SetRow(statusBar, 2);
            ((System.Windows.Controls.Panel)mainGrid).Children.Add(statusBar);

            Content = mainGrid;
        }

        private Border CreateHeader()
        {
            var headerPanel = new StackPanel
            {
                Background = PanelBackground,
                Margin = new Thickness(0, 0, 0, 1)
            };

            // Title
            _headerText = new TextBlock
            {
                Text = "No Element Selected",
                FontSize = 16,
                FontWeight = FontWeights.SemiBold,
                Foreground = TextColor,
                Margin = new Thickness(12, 12, 12, 4),
                TextWrapping = TextWrapping.Wrap
            };
            headerPanel.Children.Add(_headerText);

            // Category
            _categoryText = new TextBlock
            {
                Text = "Select an element to see details",
                FontSize = 12,
                Foreground = LabelColor,
                Margin = new Thickness(12, 0, 12, 12)
            };
            headerPanel.Children.Add(_categoryText);

            // Refresh button
            var refreshButton = new Button
            {
                Content = "Refresh",
                Width = 70,
                Height = 24,
                Margin = new Thickness(12, 0, 12, 12),
                HorizontalAlignment = HorizontalAlignment.Right,
                Background = AccentColor,
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0)
            };
            refreshButton.Click += (s, e) => UpdatePanelFromSelection();
            headerPanel.Children.Add(refreshButton);

            return new Border
            {
                Child = headerPanel,
                BorderBrush = new SolidColorBrush(System.Windows.Media.Color.FromRgb(60, 60, 60)),
                BorderThickness = new Thickness(0, 0, 0, 1)
            };
        }

        private StackPanel CreateContentPanel()
        {
            var contentPanel = new StackPanel
            {
                Margin = new Thickness(0)
            };

            // Specifications section
            contentPanel.Children.Add(CreateSectionHeader("SPECIFICATIONS"));
            _specsPanel = new StackPanel
            {
                Background = PanelBackground,
                Margin = new Thickness(0, 0, 0, 8)
            };
            contentPanel.Children.Add(_specsPanel);

            // Linked Views section
            contentPanel.Children.Add(CreateSectionHeader("LINKED VIEWS"));
            _linkedViewsPanel = new StackPanel
            {
                Background = PanelBackground,
                Margin = new Thickness(0, 0, 0, 8)
            };

            _linkedViewsList = new ListBox
            {
                Background = new SolidColorBrush(System.Windows.Media.Color.FromRgb(35, 35, 35)),
                BorderThickness = new Thickness(0),
                MaxHeight = 150,
                Margin = new Thickness(8),
                Foreground = TextColor
            };
            // Style for ListBox items to ensure visibility
            var itemStyle = new Style(typeof(ListBoxItem));
            itemStyle.Setters.Add(new Setter(ListBoxItem.BackgroundProperty, Brushes.Transparent));
            itemStyle.Setters.Add(new Setter(ListBoxItem.ForegroundProperty, TextColor));
            itemStyle.Setters.Add(new Setter(ListBoxItem.PaddingProperty, new Thickness(8, 4, 8, 4)));
            // Selection highlight
            var selectedTrigger = new Trigger { Property = ListBoxItem.IsSelectedProperty, Value = true };
            selectedTrigger.Setters.Add(new Setter(ListBoxItem.BackgroundProperty, AccentColor));
            selectedTrigger.Setters.Add(new Setter(ListBoxItem.ForegroundProperty, Brushes.White));
            itemStyle.Triggers.Add(selectedTrigger);
            // Mouse over highlight
            var hoverTrigger = new Trigger { Property = ListBoxItem.IsMouseOverProperty, Value = true };
            hoverTrigger.Setters.Add(new Setter(ListBoxItem.BackgroundProperty, new SolidColorBrush(System.Windows.Media.Color.FromRgb(55, 55, 55))));
            itemStyle.Triggers.Add(hoverTrigger);
            _linkedViewsList.ItemContainerStyle = itemStyle;
            _linkedViewsList.SelectionChanged += OnLinkedViewSelected;
            _linkedViewsPanel.Children.Add(_linkedViewsList);

            _openViewButton = new Button
            {
                Content = "Open Selected View",
                Height = 28,
                Margin = new Thickness(8, 0, 8, 8),
                Background = AccentColor,
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0),
                IsEnabled = false
            };
            _openViewButton.Click += OnOpenViewClicked;
            _linkedViewsPanel.Children.Add(_openViewButton);

            contentPanel.Children.Add(_linkedViewsPanel);

            // Schedule section
            contentPanel.Children.Add(CreateSectionHeader("SCHEDULES"));
            _schedulePanel = new StackPanel
            {
                Background = PanelBackground,
                Margin = new Thickness(0, 0, 0, 8)
            };

            _scheduleButton = new Button
            {
                Content = "No Schedule Linked",
                Height = 28,
                Margin = new Thickness(8),
                Background = new SolidColorBrush(System.Windows.Media.Color.FromRgb(60, 60, 60)),
                Foreground = LabelColor, // Light gray text on dark button
                BorderThickness = new Thickness(0),
                IsEnabled = false
            };
            _scheduleButton.Click += OnScheduleClicked;
            _schedulePanel.Children.Add(_scheduleButton);

            contentPanel.Children.Add(_schedulePanel);

            // Resources section
            contentPanel.Children.Add(CreateSectionHeader("RESOURCES"));
            _resourcesPanel = new StackPanel
            {
                Background = PanelBackground,
                Margin = new Thickness(0, 0, 0, 8)
            };
            contentPanel.Children.Add(_resourcesPanel);

            return contentPanel;
        }

        private TextBlock CreateSectionHeader(string text)
        {
            return new TextBlock
            {
                Text = text,
                FontSize = 11,
                FontWeight = FontWeights.SemiBold,
                Foreground = LabelColor,
                Margin = new Thickness(12, 12, 12, 4)
            };
        }

        private Border CreateStatusBar()
        {
            _statusText = new TextBlock
            {
                Text = "Ready",
                FontSize = 11,
                Foreground = LabelColor,
                Margin = new Thickness(12, 8, 12, 8)
            };

            return new Border
            {
                Child = _statusText,
                Background = PanelBackground,
                BorderBrush = new SolidColorBrush(System.Windows.Media.Color.FromRgb(60, 60, 60)),
                BorderThickness = new Thickness(0, 1, 0, 0)
            };
        }

        #endregion

        #region Update Methods

        public void UpdatePanelFromSelection()
        {
            if (_isUpdating) return;
            _isUpdating = true;

            try
            {
                var uidoc = _uiApp?.ActiveUIDocument;
                if (uidoc == null)
                {
                    ShowNoSelection();
                    return;
                }

                _currentDocument = uidoc.Document;
                var selection = uidoc.Selection.GetElementIds();

                if (selection.Count == 0)
                {
                    ShowNoSelection();
                    return;
                }

                var elementId = selection.First();
                _currentElement = _currentDocument.GetElement(elementId);

                if (_currentElement == null)
                {
                    ShowNoSelection();
                    return;
                }

                // Get element type
                var typeId = _currentElement.GetTypeId();
                if (typeId != ElementId.InvalidElementId)
                {
                    _currentElementType = _currentDocument.GetElement(typeId) as ElementType;
                }
                else
                {
                    _currentElementType = null;
                }

                UpdateUIWithElementInfo();
                _statusText.Text = $"Element ID: {_currentElement.Id.Value}";
            }
            catch (Exception ex)
            {
                _statusText.Text = $"Error: {ex.Message}";
            }
            finally
            {
                _isUpdating = false;
            }
        }

        private void ShowNoSelection()
        {
            _headerText.Text = "No Element Selected";
            _categoryText.Text = "Select an element to see details";
            _specsPanel.Children.Clear();
            _linkedViewsList.Items.Clear();
            _openViewButton.IsEnabled = false;
            _scheduleButton.Content = "No Schedule Linked";
            _scheduleButton.IsEnabled = false;
            _resourcesPanel.Children.Clear();
            _currentElement = null;
            _currentElementType = null;
            _statusText.Text = "Ready";
        }

        private void UpdateUIWithElementInfo()
        {
            if (_currentElement == null) return;

            // Update header
            _headerText.Text = _currentElementType?.Name ?? _currentElement.Name ?? "Unknown";
            _categoryText.Text = $"{_currentElement.Category?.Name ?? "Unknown"}" +
                (_currentElementType != null ? $" | {_currentElementType.FamilyName}" : "");

            // Update specifications
            UpdateSpecifications();

            // Update linked views
            UpdateLinkedViews();

            // Update schedule
            UpdateSchedule();

            // Update resources
            UpdateResources();
        }

        private void UpdateSpecifications()
        {
            _specsPanel.Children.Clear();

            if (_currentElementType == null)
            {
                AddSpecRow("No type information", "");
                return;
            }

            // ===== BASIC INFO =====
            AddSpecSectionHeader("BASIC INFO");
            AddSpecRow("Type Name", _currentElementType.Name);
            AddSpecRow("Family", _currentElementType.FamilyName);
            AddSpecRow("Type ID", _currentElementType.Id.Value.ToString());

            // Category-specific info
            var category = _currentElement?.Category?.Name ?? _currentElementType.Category?.Name;
            if (!string.IsNullOrEmpty(category))
            {
                AddSpecRow("Category", category);
            }

            // ===== DIMENSIONS =====
            AddSpecSectionHeader("DIMENSIONS");

            // Wall width
            var widthParam = _currentElementType.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM);
            if (widthParam != null && widthParam.HasValue)
            {
                var widthFeet = widthParam.AsDouble();
                var widthInches = widthFeet * 12;
                AddSpecRow("Width", $"{widthInches:F2}\"");
            }

            // Door/Window dimensions
            var heightParam = _currentElementType.get_Parameter(BuiltInParameter.DOOR_HEIGHT)
                           ?? _currentElementType.get_Parameter(BuiltInParameter.WINDOW_HEIGHT)
                           ?? _currentElementType.get_Parameter(BuiltInParameter.FAMILY_HEIGHT_PARAM);
            if (heightParam != null && heightParam.HasValue)
            {
                AddSpecRow("Height", FormatLength(heightParam.AsDouble()));
            }

            var doorWidthParam = _currentElementType.get_Parameter(BuiltInParameter.DOOR_WIDTH)
                              ?? _currentElementType.get_Parameter(BuiltInParameter.WINDOW_WIDTH)
                              ?? _currentElementType.get_Parameter(BuiltInParameter.FAMILY_WIDTH_PARAM);
            if (doorWidthParam != null && doorWidthParam.HasValue)
            {
                AddSpecRow("Width", FormatLength(doorWidthParam.AsDouble()));
            }

            // ===== CODE & RATINGS =====
            AddSpecSectionHeader("CODE & RATINGS");

            // Smart Template parameters for ratings
            var ratingParams = new[]
            {
                ("ST_FireRating", "Fire Rating"),
                ("ST_ULCode", "UL Code"),
                ("ST_STCRating", "STC Rating"),
                ("ST_NOANumber", "NOA Number"),
                ("ST_ADACompliant", "ADA Compliant")
            };

            foreach (var (paramName, displayName) in ratingParams)
            {
                var param = _currentElementType.LookupParameter(paramName);
                if (param != null && param.HasValue)
                {
                    var value = GetParameterDisplayValue(param);
                    if (!string.IsNullOrEmpty(value))
                    {
                        AddSpecRow(displayName, value);
                    }
                }
            }

            // Built-in Fire Rating
            var builtInFireRating = _currentElementType.get_Parameter(BuiltInParameter.FIRE_RATING);
            if (builtInFireRating != null && builtInFireRating.HasValue && !string.IsNullOrEmpty(builtInFireRating.AsString()))
            {
                AddSpecRow("Fire Rating (Built-in)", builtInFireRating.AsString());
            }

            // ===== CONSTRUCTION =====
            AddSpecSectionHeader("CONSTRUCTION");

            // Assembly Code (use lookup by name since BuiltInParameter names vary by Revit version)
            var assemblyCode = _currentElementType.LookupParameter("Assembly Code");
            if (assemblyCode != null && assemblyCode.HasValue && !string.IsNullOrEmpty(assemblyCode.AsString()))
            {
                AddSpecRow("Assembly Code", assemblyCode.AsString());
            }

            // Assembly Description
            var assemblyDesc = _currentElementType.LookupParameter("Assembly Description");
            if (assemblyDesc != null && assemblyDesc.HasValue && !string.IsNullOrEmpty(assemblyDesc.AsString()))
            {
                AddSpecRow("Assembly", assemblyDesc.AsString());
            }

            // Function (for walls)
            var functionParam = _currentElementType.get_Parameter(BuiltInParameter.FUNCTION_PARAM);
            if (functionParam != null && functionParam.HasValue)
            {
                var functionValue = functionParam.AsInteger();
                var functionName = functionValue switch
                {
                    0 => "Interior",
                    1 => "Exterior",
                    2 => "Foundation",
                    3 => "Retaining",
                    4 => "Soffit",
                    5 => "Core-shaft",
                    _ => functionValue.ToString()
                };
                AddSpecRow("Function", functionName);
            }

            // Wall layers/structure (for compound walls)
            if (_currentElementType is WallType wallType)
            {
                try
                {
                    var structure = wallType.GetCompoundStructure();
                    if (structure != null)
                    {
                        var layerCount = structure.LayerCount;
                        AddSpecRow("Layers", layerCount.ToString());

                        // List each layer
                        for (int i = 0; i < Math.Min(layerCount, 5); i++)
                        {
                            var layer = structure.GetLayers()[i];
                            var materialId = layer.MaterialId;
                            var material = materialId != ElementId.InvalidElementId
                                ? _currentDocument.GetElement(materialId) as Material
                                : null;
                            var materialName = material?.Name ?? "No Material";
                            var thickness = layer.Width * 12; // Convert to inches
                            AddSpecRow($"  Layer {i + 1}", $"{thickness:F2}\" - {materialName}");
                        }
                    }
                }
                catch { /* Ignore errors getting structure */ }
            }

            // ===== MATERIALS & FINISHES =====
            AddSpecSectionHeader("MATERIALS & FINISHES");

            // Structural Material
            var structMaterial = _currentElementType.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM);
            if (structMaterial != null && structMaterial.HasValue)
            {
                var matId = structMaterial.AsElementId();
                if (matId != ElementId.InvalidElementId)
                {
                    var mat = _currentDocument.GetElement(matId) as Material;
                    if (mat != null)
                    {
                        AddSpecRow("Structural Material", mat.Name);
                    }
                }
            }

            // Finish options from Smart Template
            var finishOptions = _currentElementType.LookupParameter("ST_FinishOptions");
            if (finishOptions != null && finishOptions.HasValue && !string.IsNullOrEmpty(finishOptions.AsString()))
            {
                AddSpecRow("Finish Options", finishOptions.AsString());
            }

            // ===== MANUFACTURER =====
            AddSpecSectionHeader("MANUFACTURER");

            var mfgParams = new[]
            {
                ("ST_ManufacturerName", "Manufacturer"),
                ("ST_ProductModel", "Model"),
                ("ST_HardwareGroup", "Hardware Group"),
                ("ST_GlazingType", "Glazing Type"),
                ("ST_MountingType", "Mounting Type")
            };

            foreach (var (paramName, displayName) in mfgParams)
            {
                var param = _currentElementType.LookupParameter(paramName);
                if (param != null && param.HasValue)
                {
                    var value = GetParameterDisplayValue(param);
                    if (!string.IsNullOrEmpty(value))
                    {
                        AddSpecRow(displayName, value);
                    }
                }
            }

            // ===== DESCRIPTION & NOTES =====
            var descParam = _currentElementType.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION);
            if (descParam != null && descParam.HasValue && !string.IsNullOrEmpty(descParam.AsString()))
            {
                AddSpecSectionHeader("DESCRIPTION");
                AddSpecRow("", descParam.AsString());
            }

            var notesParam = _currentElementType.LookupParameter("ST_Notes");
            if (notesParam != null && notesParam.HasValue && !string.IsNullOrEmpty(notesParam.AsString()))
            {
                AddSpecSectionHeader("NOTES");
                AddSpecRow("", notesParam.AsString());
            }

            // Type Mark
            var typeMarkParam = _currentElementType.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK);
            if (typeMarkParam != null && typeMarkParam.HasValue && !string.IsNullOrEmpty(typeMarkParam.AsString()))
            {
                AddSpecRow("Type Mark", typeMarkParam.AsString());
            }
        }

        private void AddSpecSectionHeader(string text)
        {
            var header = new TextBlock
            {
                Text = text,
                FontSize = 10,
                FontWeight = FontWeights.Bold,
                Foreground = AccentColor,
                Margin = new Thickness(12, 10, 12, 2)
            };
            _specsPanel.Children.Add(header);
        }

        private string FormatLength(double feet)
        {
            var totalInches = feet * 12;
            var wholeInches = (int)totalInches;
            var fraction = totalInches - wholeInches;

            if (Math.Abs(fraction) < 0.01)
                return $"{wholeInches}\"";

            // Convert to fractional inches
            var numerator = (int)Math.Round(fraction * 16);
            var denominator = 16;

            // Simplify fraction
            while (numerator % 2 == 0 && denominator > 1)
            {
                numerator /= 2;
                denominator /= 2;
            }

            if (numerator == 0)
                return $"{wholeInches}\"";

            return $"{wholeInches}-{numerator}/{denominator}\"";
        }

        private void AddSpecRow(string label, string value)
        {
            var grid = new System.Windows.Controls.Grid { Margin = new Thickness(12, 4, 12, 4) };
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(110) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            var labelText = new TextBlock
            {
                Text = label + ":",
                Foreground = LabelColor,
                FontSize = 12
            };
            System.Windows.Controls.Grid.SetColumn(labelText, 0);
            ((System.Windows.Controls.Panel)grid).Children.Add(labelText);

            var valueText = new TextBlock
            {
                Text = value,
                Foreground = TextColor,
                FontSize = 12,
                TextWrapping = TextWrapping.Wrap
            };
            System.Windows.Controls.Grid.SetColumn(valueText, 1);
            ((System.Windows.Controls.Panel)grid).Children.Add(valueText);

            _specsPanel.Children.Add(grid);
        }

        private void UpdateLinkedViews()
        {
            _linkedViewsList.Items.Clear();
            _openViewButton.IsEnabled = false;

            if (_currentElementType == null) return;

            var detailViewsParam = _currentElementType.LookupParameter("ST_DetailViewNames");
            if (detailViewsParam == null || !detailViewsParam.HasValue)
            {
                _linkedViewsList.Items.Add(new ListBoxItem
                {
                    Content = "No linked views",
                    Foreground = LabelColor,
                    IsEnabled = false
                });
                return;
            }

            var viewNames = detailViewsParam.AsString()
                .Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(n => n.Trim())
                .ToList();

            if (viewNames.Count == 0)
            {
                _linkedViewsList.Items.Add(new ListBoxItem
                {
                    Content = "No linked views",
                    Foreground = LabelColor,
                    IsEnabled = false
                });
                return;
            }

            // Find views in document
            var allViews = new FilteredElementCollector(_currentDocument)
                .OfClass(typeof(View))
                .Cast<View>()
                .Where(v => !v.IsTemplate)
                .ToList();

            foreach (var viewName in viewNames)
            {
                var matchingView = allViews.FirstOrDefault(v =>
                    v.Name.Equals(viewName, StringComparison.OrdinalIgnoreCase));

                var item = new ListBoxItem
                {
                    Content = matchingView != null ? viewName : $"{viewName} (not found)",
                    Tag = matchingView?.Id,
                    Foreground = matchingView != null ? LinkColor : LabelColor,
                    IsEnabled = matchingView != null
                };
                _linkedViewsList.Items.Add(item);
            }
        }

        private void UpdateSchedule()
        {
            if (_currentElementType == null)
            {
                _scheduleButton.Content = "No Schedule Linked";
                _scheduleButton.IsEnabled = false;
                _scheduleButton.Tag = null;
                return;
            }

            var scheduleParam = _currentElementType.LookupParameter("ST_ScheduleName");
            if (scheduleParam == null || !scheduleParam.HasValue)
            {
                _scheduleButton.Content = "No Schedule Linked";
                _scheduleButton.IsEnabled = false;
                _scheduleButton.Tag = null;
                return;
            }

            var scheduleName = scheduleParam.AsString();

            // Find schedule
            var schedule = new FilteredElementCollector(_currentDocument)
                .OfClass(typeof(ViewSchedule))
                .Cast<ViewSchedule>()
                .FirstOrDefault(vs => vs.Name.Equals(scheduleName, StringComparison.OrdinalIgnoreCase));

            if (schedule != null)
            {
                _scheduleButton.Content = $"Open: {scheduleName}";
                _scheduleButton.Tag = schedule.Id;
                _scheduleButton.IsEnabled = true;
                _scheduleButton.Background = AccentColor;
                _scheduleButton.Foreground = Brushes.White; // White text on blue button
            }
            else
            {
                _scheduleButton.Content = $"{scheduleName} (not found)";
                _scheduleButton.IsEnabled = false;
                _scheduleButton.Tag = null;
                _scheduleButton.Background = new SolidColorBrush(System.Windows.Media.Color.FromRgb(60, 60, 60));
                _scheduleButton.Foreground = LabelColor; // Light gray text on dark button
            }
        }

        private void UpdateResources()
        {
            _resourcesPanel.Children.Clear();

            if (_currentElementType == null)
            {
                AddResourceLink("No resources available", null);
                return;
            }

            var resources = new[]
            {
                ("ST_ManufacturerURL", "Manufacturer Website"),
                ("ST_SubmittalLink", "Submittal Document"),
                ("ST_InstallGuideLink", "Installation Guide")
            };

            bool hasAnyResource = false;
            foreach (var (paramName, displayName) in resources)
            {
                var param = _currentElementType.LookupParameter(paramName);
                if (param != null && param.HasValue && !string.IsNullOrEmpty(param.AsString()))
                {
                    AddResourceLink(displayName, param.AsString());
                    hasAnyResource = true;
                }
            }

            if (!hasAnyResource)
            {
                AddResourceLink("No resources available", null);
            }
        }

        private void AddResourceLink(string text, string url)
        {
            var textBlock = new TextBlock
            {
                Margin = new Thickness(12, 6, 12, 6)
            };

            if (!string.IsNullOrEmpty(url))
            {
                var hyperlink = new Hyperlink
                {
                    NavigateUri = new Uri(url, UriKind.Absolute),
                    Foreground = LinkColor
                };
                hyperlink.Inlines.Add(text);
                hyperlink.RequestNavigate += (s, e) =>
                {
                    try
                    {
                        Process.Start(new ProcessStartInfo(e.Uri.AbsoluteUri) { UseShellExecute = true });
                        e.Handled = true;
                    }
                    catch (Exception ex)
                    {
                        _statusText.Text = $"Error opening URL: {ex.Message}";
                    }
                };
                textBlock.Inlines.Add(hyperlink);
            }
            else
            {
                textBlock.Text = text;
                textBlock.Foreground = LabelColor;
            }

            _resourcesPanel.Children.Add(textBlock);
        }

        #endregion

        #region Event Handlers

        private void OnDocumentChanged(object sender, DocumentChangedEventArgs e)
        {
            // Don't update if we're closing - prevents crash
            if (_isClosing) return;

            try
            {
                // Update panel when document changes (if selection might have changed)
                Dispatcher.InvokeAsync(() =>
                {
                    if (!_isClosing)
                    {
                        UpdatePanelFromSelection();
                    }
                });
            }
            catch
            {
                // Ignore errors if window is closing
            }
        }

        private void OnLinkedViewSelected(object sender, System.Windows.Controls.SelectionChangedEventArgs e)
        {
            var selectedItem = _linkedViewsList.SelectedItem as ListBoxItem;
            _openViewButton.IsEnabled = selectedItem?.Tag != null;
        }

        private void OnOpenViewClicked(object sender, RoutedEventArgs e)
        {
            var selectedItem = _linkedViewsList.SelectedItem as ListBoxItem;
            if (selectedItem?.Tag is ElementId viewId)
            {
                try
                {
                    var view = _currentDocument.GetElement(viewId) as View;
                    if (view != null)
                    {
                        _uiApp.ActiveUIDocument.ActiveView = view;
                        _statusText.Text = $"Opened view: {view.Name}";
                    }
                }
                catch (Exception ex)
                {
                    _statusText.Text = $"Error: {ex.Message}";
                }
            }
        }

        private void OnScheduleClicked(object sender, RoutedEventArgs e)
        {
            if (_scheduleButton.Tag is ElementId scheduleId)
            {
                try
                {
                    var schedule = _currentDocument.GetElement(scheduleId) as ViewSchedule;
                    if (schedule != null)
                    {
                        _uiApp.ActiveUIDocument.ActiveView = schedule;
                        _statusText.Text = $"Opened schedule: {schedule.Name}";
                    }
                }
                catch (Exception ex)
                {
                    _statusText.Text = $"Error: {ex.Message}";
                }
            }
        }

        #endregion

        #region Helpers

        private string GetParameterDisplayValue(Parameter param)
        {
            if (!param.HasValue) return null;

            switch (param.StorageType)
            {
                case StorageType.String:
                    return param.AsString();
                case StorageType.Integer:
                    if (param.Definition.GetDataType() == SpecTypeId.Boolean.YesNo)
                    {
                        return param.AsInteger() == 1 ? "Yes" : "No";
                    }
                    return param.AsInteger().ToString();
                case StorageType.Double:
                    return param.AsDouble().ToString("F2");
                case StorageType.ElementId:
                    var elemId = param.AsElementId();
                    if (elemId != ElementId.InvalidElementId && _currentDocument != null)
                    {
                        var elem = _currentDocument.GetElement(elemId);
                        return elem?.Name ?? elemId.Value.ToString();
                    }
                    return elemId?.Value.ToString();
                default:
                    return null;
            }
        }

        #endregion
    }
}
