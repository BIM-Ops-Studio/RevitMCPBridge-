using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Microsoft.Win32;

// Type aliases to resolve ambiguity between WPF and Revit types
using Point = System.Windows.Point;
using Line = System.Windows.Shapes.Line;
using ComboBox = System.Windows.Controls.ComboBox;
using TextBox = System.Windows.Controls.TextBox;
using Color = System.Windows.Media.Color;
using Grid = System.Windows.Controls.Grid;
using Ellipse = System.Windows.Shapes.Ellipse;
using Rectangle = System.Windows.Shapes.Rectangle;

namespace RevitMCPBridge
{
    /// <summary>
    /// Floor Plan Tracer - Trace walls from images directly into Revit (Pure C# version)
    /// Enhanced with live measurements, chain mode, keyboard shortcuts, and professional UI.
    /// </summary>
    public class FloorPlanTracerWindow : Window
    {
        private UIApplication _uiApp;
        private Document _doc;

        // Scale: pixels to feet
        private double _scale = 0.05; // Default: 0.05 feet per pixel
        private bool _isSettingScale = false;
        private Point? _scalePoint1 = null;

        // Drawing state
        private bool _isDrawing = false;
        private Point? _startPoint = null;
        private Line _currentLine = null;

        // Chain mode: continue walls from last endpoint
        private bool _chainMode = true;
        private Point? _lastWallEndPoint = null;

        // Traced elements
        private ObservableCollection<TracedElement> _tracedElements = new ObservableCollection<TracedElement>();
        private Stack<TracedElement> _undoStack = new Stack<TracedElement>();

        // Image origin (for coordinate conversion)
        private Point _imageOrigin = new Point(0, 0);
        private double _imageHeight = 0;
        private double _imageOpacity = 0.7;

        // Grid snap distance in pixels
        private const double SNAP_DISTANCE = 10;
        private const double STRAIGHTEN_ANGLE_TOLERANCE = 8; // degrees

        // UI Controls
        private Canvas DrawingCanvas;
        private Image FloorPlanImage;
        private TextBlock StatusText;
        private TextBlock SummaryText;
        private TextBlock MeasurementText; // Live measurement display
        private TextBox ScaleTextBox;
        private ComboBox WallTypeCombo;
        private RadioButton WallTool;
        private RadioButton SelectTool;
        private CheckBox SnapToGrid;
        private CheckBox AutoStraighten;
        private CheckBox ChainModeCheck; // Chain mode checkbox
        private Slider OpacitySlider; // Image opacity control
        private ListBox ElementList;

        public FloorPlanTracerWindow(UIApplication uiApp)
        {
            _uiApp = uiApp;
            _doc = uiApp.ActiveUIDocument.Document;

            // Window properties - professional styling using SketchPadColors
            Title = "Floor Plan Tracer - Trace to Revit";
            Width = 1100;
            Height = 750;
            MinWidth = 900;
            MinHeight = 600;
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            Background = new SolidColorBrush(SketchPadColors.BgPrimary);
            ResizeMode = ResizeMode.CanResizeWithGrip;

            BuildUI();
            LoadWallTypes();

            ElementList.ItemsSource = _tracedElements;

            // Handle keyboard shortcuts
            this.KeyDown += Window_KeyDown;
        }

        private void BuildUI()
        {
            var mainGrid = new Grid();
            mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(280) });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // Row 0: Toolbar
            var toolbar = CreateToolbar();
            Grid.SetRow(toolbar, 0);
            Grid.SetColumnSpan(toolbar, 2);
            mainGrid.Children.Add(toolbar);

            // Row 1, Col 0: Canvas area with measurement overlay
            var canvasBorder = new Border
            {
                Background = new SolidColorBrush(SketchPadColors.BgCanvas),
                Margin = new Thickness(5),
                BorderBrush = new SolidColorBrush(SketchPadColors.Border),
                BorderThickness = new Thickness(1)
            };
            Grid.SetRow(canvasBorder, 1);
            Grid.SetColumn(canvasBorder, 0);

            // Outer grid for canvas + measurement overlay
            var canvasOuterGrid = new Grid();

            var scrollViewer = new ScrollViewer
            {
                HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto
            };

            var canvasGrid = new Grid();

            FloorPlanImage = new Image
            {
                Stretch = Stretch.None,
                Opacity = _imageOpacity
            };
            canvasGrid.Children.Add(FloorPlanImage);

            DrawingCanvas = new Canvas
            {
                Background = Brushes.Transparent,
                ClipToBounds = true,
                Width = 800,
                Height = 600
            };
            DrawingCanvas.MouseLeftButtonDown += Canvas_MouseLeftButtonDown;
            DrawingCanvas.MouseLeftButtonUp += Canvas_MouseLeftButtonUp;
            DrawingCanvas.MouseMove += Canvas_MouseMove;
            DrawingCanvas.MouseWheel += Canvas_MouseWheel;
            canvasGrid.Children.Add(DrawingCanvas);

            scrollViewer.Content = canvasGrid;
            canvasOuterGrid.Children.Add(scrollViewer);

            // Live measurement overlay (top center)
            var measureBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(200, 30, 30, 30)),
                BorderBrush = new SolidColorBrush(SketchPadColors.AccentBlue),
                BorderThickness = new Thickness(2),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(10, 5, 10, 5),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(0, 10, 0, 0),
                Visibility = System.Windows.Visibility.Collapsed,
                Tag = "MeasurementBorder"
            };
            MeasurementText = new TextBlock
            {
                Foreground = new SolidColorBrush(SketchPadColors.AccentCyan),
                FontSize = 18,
                FontWeight = FontWeights.Bold,
                Text = "0'-0\""
            };
            measureBorder.Child = MeasurementText;
            canvasOuterGrid.Children.Add(measureBorder);

            canvasBorder.Child = canvasOuterGrid;
            mainGrid.Children.Add(canvasBorder);

            // Row 1, Col 1: Side panel
            var sidePanel = CreateSidePanel();
            Grid.SetRow(sidePanel, 1);
            Grid.SetColumn(sidePanel, 1);
            mainGrid.Children.Add(sidePanel);

            // Row 2: Status bar
            var statusBar = new Border
            {
                Background = new SolidColorBrush(SketchPadColors.BgSecondary),
                Padding = new Thickness(10, 5, 10, 5)
            };
            Grid.SetRow(statusBar, 2);
            Grid.SetColumnSpan(statusBar, 2);

            var statusGrid = new Grid();
            statusGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            statusGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            StatusText = new TextBlock
            {
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                Text = "Load an image to begin tracing. Press W for Wall mode, S for Select."
            };
            statusGrid.Children.Add(StatusText);

            var shortcutHelp = new TextBlock
            {
                Foreground = new SolidColorBrush(SketchPadColors.TextMuted),
                Text = "W=Wall | S=Select | Esc=Cancel | Ctrl+Z=Undo",
                HorizontalAlignment = HorizontalAlignment.Right
            };
            Grid.SetColumn(shortcutHelp, 1);
            statusGrid.Children.Add(shortcutHelp);

            statusBar.Child = statusGrid;
            mainGrid.Children.Add(statusBar);

            Content = mainGrid;
        }

        private Border CreateToolbar()
        {
            var toolbar = new Border
            {
                Background = new SolidColorBrush(SketchPadColors.BgSecondary),
                Padding = new Thickness(8)
            };

            var stack = new StackPanel { Orientation = Orientation.Horizontal };

            // File buttons
            stack.Children.Add(CreateToolbarButton("Load Image", LoadImage_Click, "Load a floor plan image (PNG, JPG, BMP)"));
            stack.Children.Add(CreateToolbarButton("Load PDF", LoadPDF_Click, "Load a PDF floor plan (requires conversion)"));
            stack.Children.Add(CreateSeparator());

            // Scale section
            stack.Children.Add(new Label
            {
                Content = "Scale:",
                Foreground = new SolidColorBrush(SketchPadColors.TextLabel),
                VerticalAlignment = VerticalAlignment.Center,
                FontWeight = FontWeights.Bold
            });
            ScaleTextBox = new TextBox
            {
                Width = 90,
                Text = "0.05 ft/px",
                Margin = new Thickness(2),
                IsReadOnly = true,
                Background = new SolidColorBrush(SketchPadColors.BgInput),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.Border)
            };
            stack.Children.Add(ScaleTextBox);
            stack.Children.Add(CreateToolbarButton("Set Scale", SetScale_Click, "Click two points on a known dimension to calibrate scale"));
            stack.Children.Add(CreateSeparator());

            // Tool selection with keyboard shortcuts
            WallTool = new RadioButton
            {
                Content = "Wall (W)",
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                IsChecked = true,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(5),
                ToolTip = "Draw walls by clicking start and end points.\nChain mode continues from last endpoint."
            };
            SelectTool = new RadioButton
            {
                Content = "Select (S)",
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(5),
                ToolTip = "Click elements to select, then Delete or modify."
            };
            stack.Children.Add(WallTool);
            stack.Children.Add(SelectTool);
            stack.Children.Add(CreateSeparator());

            // Options with tooltips
            SnapToGrid = new CheckBox
            {
                Content = "Snap",
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                IsChecked = true,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(5),
                ToolTip = "Snap to nearby wall endpoints and grid"
            };
            AutoStraighten = new CheckBox
            {
                Content = "Ortho",
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                IsChecked = true,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(5),
                ToolTip = "Auto-straighten walls to horizontal/vertical"
            };
            ChainModeCheck = new CheckBox
            {
                Content = "Chain",
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                IsChecked = true,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(5),
                ToolTip = "Continue drawing walls from last endpoint.\nPress Esc to break chain."
            };
            ChainModeCheck.Checked += (s, e) => _chainMode = true;
            ChainModeCheck.Unchecked += (s, e) => { _chainMode = false; _lastWallEndPoint = null; };
            stack.Children.Add(SnapToGrid);
            stack.Children.Add(AutoStraighten);
            stack.Children.Add(ChainModeCheck);
            stack.Children.Add(CreateSeparator());

            // Image opacity slider
            stack.Children.Add(new Label
            {
                Content = "Opacity:",
                Foreground = new SolidColorBrush(SketchPadColors.TextLabel),
                VerticalAlignment = VerticalAlignment.Center
            });
            OpacitySlider = new Slider
            {
                Width = 80,
                Minimum = 0.1,
                Maximum = 1.0,
                Value = _imageOpacity,
                VerticalAlignment = VerticalAlignment.Center,
                ToolTip = "Adjust background image transparency"
            };
            OpacitySlider.ValueChanged += (s, e) =>
            {
                _imageOpacity = OpacitySlider.Value;
                if (FloorPlanImage != null)
                    FloorPlanImage.Opacity = _imageOpacity;
            };
            stack.Children.Add(OpacitySlider);

            toolbar.Child = stack;
            return toolbar;
        }

        private UIElement CreateSeparator()
        {
            return new Border
            {
                Width = 1,
                Background = new SolidColorBrush(SketchPadColors.Border),
                Margin = new Thickness(10, 2, 10, 2)
            };
        }

        private Button CreateToolbarButton(string content, RoutedEventHandler handler, string tooltip)
        {
            var btn = new Button
            {
                Content = content,
                Height = 28,
                Padding = new Thickness(10, 2, 10, 2),
                Margin = new Thickness(2),
                Background = new SolidColorBrush(SketchPadColors.BgTertiary),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.BorderLight),
                ToolTip = tooltip
            };
            btn.Click += handler;
            return btn;
        }

        private Border CreateSidePanel()
        {
            var panel = new Border
            {
                Background = new SolidColorBrush(SketchPadColors.BgSecondary),
                Padding = new Thickness(10)
            };

            var stack = new StackPanel();

            // Wall Type
            stack.Children.Add(new Label
            {
                Content = "WALL TYPE",
                Foreground = new SolidColorBrush(SketchPadColors.TextLabel),
                FontWeight = FontWeights.Bold,
                FontSize = 10
            });
            WallTypeCombo = new ComboBox
            {
                Margin = new Thickness(0, 2, 0, 10),
                Background = new SolidColorBrush(SketchPadColors.BgInput),
                BorderBrush = new SolidColorBrush(SketchPadColors.Border)
            };
            stack.Children.Add(WallTypeCombo);

            // Summary
            stack.Children.Add(new Label
            {
                Content = "SUMMARY",
                Foreground = new SolidColorBrush(SketchPadColors.TextLabel),
                FontWeight = FontWeights.Bold,
                FontSize = 10,
                Margin = new Thickness(0, 10, 0, 0)
            });
            var summaryBorder = new Border
            {
                Background = new SolidColorBrush(SketchPadColors.BgTertiary),
                Padding = new Thickness(8),
                CornerRadius = new CornerRadius(4),
                Margin = new Thickness(0, 2, 0, 0)
            };
            SummaryText = new TextBlock
            {
                Foreground = new SolidColorBrush(SketchPadColors.TextSecondary),
                Text = "Walls: 0\nDoors: 0\nWindows: 0"
            };
            summaryBorder.Child = SummaryText;
            stack.Children.Add(summaryBorder);

            // Element list
            stack.Children.Add(new Label
            {
                Content = "TRACED ELEMENTS",
                Foreground = new SolidColorBrush(SketchPadColors.TextLabel),
                FontWeight = FontWeights.Bold,
                FontSize = 10,
                Margin = new Thickness(0, 10, 0, 0)
            });
            ElementList = new ListBox
            {
                Height = 200,
                Background = new SolidColorBrush(SketchPadColors.BgCanvas),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.Border),
                DisplayMemberPath = "DisplayName",
                Margin = new Thickness(0, 2, 0, 0)
            };
            ElementList.SelectionChanged += ElementList_SelectionChanged;
            stack.Children.Add(ElementList);

            // Action buttons
            var btnStack = new StackPanel { Margin = new Thickness(0, 10, 0, 0) };
            var btnRow1 = new StackPanel { Orientation = Orientation.Horizontal };
            btnRow1.Children.Add(CreateButton("Delete", DeleteSelected_Click, 80));
            btnRow1.Children.Add(CreateButton("Undo (Ctrl+Z)", Undo_Click, 100));
            btnStack.Children.Add(btnRow1);
            btnStack.Children.Add(CreateButton("Clear All", ClearTraced_Click, 180));
            stack.Children.Add(btnStack);

            // Revit actions
            stack.Children.Add(new Border
            {
                Height = 1,
                Background = new SolidColorBrush(SketchPadColors.Border),
                Margin = new Thickness(0, 15, 0, 15)
            });

            stack.Children.Add(new Label
            {
                Content = "REVIT ACTIONS",
                Foreground = new SolidColorBrush(SketchPadColors.TextLabel),
                FontWeight = FontWeights.Bold,
                FontSize = 10
            });
            var revitBtnStack = new StackPanel { Margin = new Thickness(0, 5, 0, 0) };
            revitBtnStack.Children.Add(CreateAccentButton("Preview", Preview_Click, 180));
            revitBtnStack.Children.Add(CreateAccentButton("Create All in Revit", CreateInRevit_Click, 180));
            stack.Children.Add(revitBtnStack);

            // Close button at bottom
            stack.Children.Add(new Border { Height = 20 }); // spacer
            stack.Children.Add(CreateButton("Close", Close_Click, 180));

            panel.Child = stack;
            return panel;
        }

        private Button CreateAccentButton(string content, RoutedEventHandler handler, double width)
        {
            var btn = new Button
            {
                Content = content,
                Width = width,
                Height = 32,
                Margin = new Thickness(2),
                Background = new SolidColorBrush(SketchPadColors.AccentBlue),
                Foreground = Brushes.White,
                BorderBrush = new SolidColorBrush(Color.FromRgb(0, 100, 180)),
                FontWeight = FontWeights.SemiBold
            };
            btn.Click += handler;
            return btn;
        }

        private Button CreateButton(string content, RoutedEventHandler handler, double width = 80)
        {
            var btn = new Button
            {
                Content = content,
                Width = width,
                Height = 28,
                Margin = new Thickness(2),
                Background = new SolidColorBrush(SketchPadColors.BgTertiary),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.BorderLight)
            };
            btn.Click += handler;
            return btn;
        }

        private void LoadWallTypes()
        {
            try
            {
                var wallTypes = new FilteredElementCollector(_doc)
                    .OfClass(typeof(WallType))
                    .Cast<WallType>()
                    .OrderBy(w => w.Name)
                    .ToList();

                WallTypeCombo.Items.Clear();
                foreach (var wt in wallTypes.Take(20))
                {
                    var item = new ComboBoxItem
                    {
                        Content = wt.Name,
                        Tag = (int)wt.Id.Value
                    };
                    WallTypeCombo.Items.Add(item);
                }

                if (WallTypeCombo.Items.Count > 0)
                    WallTypeCombo.SelectedIndex = 0;
            }
            catch (Exception ex)
            {
                StatusText.Text = $"Warning: Could not load wall types - {ex.Message}";
            }
        }

        #region File Loading

        private void LoadImage_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Filter = "Image Files|*.png;*.jpg;*.jpeg;*.bmp;*.gif|All Files|*.*",
                Title = "Select Floor Plan Image"
            };

            if (dialog.ShowDialog() == true)
            {
                LoadImageFile(dialog.FileName);
            }
        }

        private void LoadPDF_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "PDF support coming soon.\n\n" +
                "For now, please:\n" +
                "1. Open the PDF in any viewer\n" +
                "2. Take a screenshot or export as image\n" +
                "3. Load the image file",
                "PDF Support",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void LoadImageFile(string path)
        {
            try
            {
                // Ensure path is absolute and properly formatted for Uri
                string absolutePath = System.IO.Path.GetFullPath(path);

                // Use file stream to avoid URI issues with special characters
                var bitmap = new BitmapImage();
                bitmap.BeginInit();
                bitmap.CacheOption = BitmapCacheOption.OnLoad;
                bitmap.CreateOptions = BitmapCreateOptions.IgnoreColorProfile;

                // Read file directly via stream (more reliable than Uri for WSL/network paths)
                using (var stream = new System.IO.FileStream(absolutePath, System.IO.FileMode.Open, System.IO.FileAccess.Read, System.IO.FileShare.Read))
                {
                    bitmap.StreamSource = stream;
                    bitmap.EndInit();
                }
                bitmap.Freeze(); // Make thread-safe and release file handle

                FloorPlanImage.Source = bitmap;
                FloorPlanImage.Width = bitmap.PixelWidth;
                FloorPlanImage.Height = bitmap.PixelHeight;

                DrawingCanvas.Width = bitmap.PixelWidth;
                DrawingCanvas.Height = bitmap.PixelHeight;

                _imageHeight = bitmap.PixelHeight;
                _imageOrigin = new Point(0, bitmap.PixelHeight);

                StatusText.Text = $"Loaded: {System.IO.Path.GetFileName(path)} ({bitmap.PixelWidth}x{bitmap.PixelHeight}). Set scale, then trace walls.";

                ClearTracedElements();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error loading image: {ex.Message}\n\nPath: {path}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        #endregion

        #region Scale Setting

        private void SetScale_Click(object sender, RoutedEventArgs e)
        {
            _isSettingScale = true;
            _scalePoint1 = null;
            StatusText.Text = "SCALE: Click first point on a known dimension...";
            DrawingCanvas.Cursor = Cursors.Cross;
        }

        private void FinishScaleSetting(Point p1, Point p2)
        {
            double pixelDistance = Math.Sqrt(Math.Pow(p2.X - p1.X, 2) + Math.Pow(p2.Y - p1.Y, 2));

            var dialog = new ScaleInputDialog();
            if (dialog.ShowDialog() == true)
            {
                double feetDistance = dialog.DistanceInFeet;
                _scale = feetDistance / pixelDistance;

                ScaleTextBox.Text = $"{_scale:F4} ft/px";
                StatusText.Text = $"Scale set: {_scale:F4} feet per pixel. Ready to trace.";
            }

            _isSettingScale = false;
            DrawingCanvas.Cursor = Cursors.Arrow;
            RemoveScaleMarkers();
        }

        private void RemoveScaleMarkers()
        {
            var markers = DrawingCanvas.Children.OfType<Ellipse>().Where(el => el.Tag?.ToString() == "ScaleMarker").ToList();
            foreach (var m in markers)
                DrawingCanvas.Children.Remove(m);

            var lines = DrawingCanvas.Children.OfType<Line>().Where(l => l.Tag?.ToString() == "ScaleLine").ToList();
            foreach (var l in lines)
                DrawingCanvas.Children.Remove(l);
        }

        #endregion

        #region Drawing

        private void Canvas_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            var pos = e.GetPosition(DrawingCanvas);

            if (_isSettingScale)
            {
                if (_scalePoint1 == null)
                {
                    _scalePoint1 = pos;
                    AddScaleMarker(pos);
                    StatusText.Text = "SCALE: Click second point on known dimension...";
                }
                else
                {
                    AddScaleMarker(pos);
                    AddScaleLine(_scalePoint1.Value, pos);
                    double pixelDist = Distance(_scalePoint1.Value, pos);
                    StatusText.Text = $"SCALE: {pixelDist:F0} pixels selected. Enter real-world distance...";
                    FinishScaleSetting(_scalePoint1.Value, pos);
                }
                return;
            }

            if (WallTool.IsChecked == true)
            {
                if (SnapToGrid.IsChecked == true)
                    pos = SnapToNearestPoint(pos);

                // Chain mode: start from last endpoint if available
                if (_chainMode && _lastWallEndPoint.HasValue)
                {
                    _startPoint = _lastWallEndPoint.Value;
                }
                else
                {
                    _startPoint = pos;
                }
                _isDrawing = true;

                _currentLine = new Line
                {
                    X1 = _startPoint.Value.X, Y1 = _startPoint.Value.Y,
                    X2 = pos.X, Y2 = pos.Y,
                    Stroke = new SolidColorBrush(SketchPadColors.AccentCyan),
                    StrokeThickness = 2,
                    StrokeDashArray = new DoubleCollection { 4, 2 },
                    Tag = "Preview"
                };
                DrawingCanvas.Children.Add(_currentLine);

                // Show measurement overlay
                ShowMeasurement(true);
                StatusText.Text = _chainMode && _lastWallEndPoint.HasValue
                    ? "CHAIN MODE: Drawing from last endpoint. Click to place end, Esc to break chain."
                    : "Drawing wall... click to place end point.";
            }
            else if (SelectTool.IsChecked == true)
            {
                SelectElementAt(pos);
            }
        }

        private void Canvas_MouseMove(object sender, MouseEventArgs e)
        {
            var pos = e.GetPosition(DrawingCanvas);

            // Show scale line distance while setting scale
            if (_isSettingScale && _scalePoint1.HasValue)
            {
                double pixelDist = Distance(_scalePoint1.Value, pos);
                StatusText.Text = $"SCALE: {pixelDist:F0} pixels - click to set endpoint";
            }

            if (!_isDrawing || _currentLine == null) return;

            if (SnapToGrid.IsChecked == true)
                pos = SnapToNearestPoint(pos);

            if (AutoStraighten.IsChecked == true)
                pos = StraightenLine(_startPoint.Value, pos);

            _currentLine.X2 = pos.X;
            _currentLine.Y2 = pos.Y;

            // Calculate and display live measurement
            double lengthPixels = Distance(_startPoint.Value, pos);
            double lengthFeet = lengthPixels * _scale;
            MeasurementText.Text = FormatFeetInches(lengthFeet);
            StatusText.Text = $"Length: {FormatFeetInches(lengthFeet)} ({lengthPixels:F0} px)";
        }

        private void Canvas_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            if (!_isDrawing || _startPoint == null) return;

            var endPoint = e.GetPosition(DrawingCanvas);

            if (SnapToGrid.IsChecked == true)
                endPoint = SnapToNearestPoint(endPoint);

            if (AutoStraighten.IsChecked == true)
                endPoint = StraightenLine(_startPoint.Value, endPoint);

            if (_currentLine != null)
            {
                DrawingCanvas.Children.Remove(_currentLine);
                _currentLine = null;
            }

            // Hide measurement overlay
            ShowMeasurement(false);

            double lengthPixels = Distance(_startPoint.Value, endPoint);

            if (lengthPixels < 10)
            {
                _isDrawing = false;
                _startPoint = null;
                _lastWallEndPoint = null; // Reset chain on invalid wall
                StatusText.Text = "Wall too short (< 10 pixels). Try again.";
                return;
            }

            CreateTracedWall(_startPoint.Value, endPoint);

            _isDrawing = false;

            // Chain mode: save endpoint for next wall
            if (_chainMode)
            {
                _lastWallEndPoint = endPoint;
                double lengthFeet = lengthPixels * _scale;
                StatusText.Text = $"Wall created: {FormatFeetInches(lengthFeet)}. Click to continue chain, Esc to break.";
            }
            else
            {
                _lastWallEndPoint = null;
            }

            _startPoint = null;
            UpdateSummary();
        }

        private void ShowMeasurement(bool show)
        {
            // Find measurement border in canvas outer grid
            var parent = DrawingCanvas.Parent as Grid;
            if (parent?.Parent is Grid outerGrid)
            {
                var measureBorder = outerGrid.Children.OfType<Border>()
                    .FirstOrDefault(b => b.Tag?.ToString() == "MeasurementBorder");
                if (measureBorder != null)
                    measureBorder.Visibility = show ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
            }
        }

        private string FormatFeetInches(double feet)
        {
            if (feet < 0) feet = Math.Abs(feet);

            int wholeFeet = (int)feet;
            double inches = (feet - wholeFeet) * 12;

            // Round inches
            int wholeInches = (int)Math.Round(inches);
            if (wholeInches >= 12)
            {
                wholeFeet++;
                wholeInches = 0;
            }

            // Format based on value
            if (wholeFeet == 0)
                return $"{wholeInches}\"";
            else if (wholeInches == 0)
                return $"{wholeFeet}'-0\"";
            else
                return $"{wholeFeet}'-{wholeInches}\"";
        }

        private void Canvas_MouseWheel(object sender, MouseWheelEventArgs e)
        {
            var transform = DrawingCanvas.RenderTransform as ScaleTransform;
            if (transform == null)
            {
                transform = new ScaleTransform(1, 1);
                DrawingCanvas.RenderTransform = transform;
            }

            double zoom = e.Delta > 0 ? 1.1 : 0.9;
            transform.ScaleX *= zoom;
            transform.ScaleY *= zoom;
        }

        #endregion

        #region Snap and Straighten

        private Point SnapToNearestPoint(Point pos)
        {
            foreach (var elem in _tracedElements.Where(t => t.ElementType == "Wall"))
            {
                if (Distance(pos, elem.StartPoint) < SNAP_DISTANCE)
                    return elem.StartPoint;
                if (Distance(pos, elem.EndPoint) < SNAP_DISTANCE)
                    return elem.EndPoint;
            }

            double gridSize = 10;
            return new Point(
                Math.Round(pos.X / gridSize) * gridSize,
                Math.Round(pos.Y / gridSize) * gridSize
            );
        }

        private Point StraightenLine(Point start, Point end)
        {
            double dx = end.X - start.X;
            double dy = end.Y - start.Y;
            double angle = Math.Atan2(dy, dx) * 180 / Math.PI;

            if (Math.Abs(angle) < STRAIGHTEN_ANGLE_TOLERANCE ||
                Math.Abs(angle - 180) < STRAIGHTEN_ANGLE_TOLERANCE ||
                Math.Abs(angle + 180) < STRAIGHTEN_ANGLE_TOLERANCE)
            {
                return new Point(end.X, start.Y);
            }

            if (Math.Abs(angle - 90) < STRAIGHTEN_ANGLE_TOLERANCE ||
                Math.Abs(angle + 90) < STRAIGHTEN_ANGLE_TOLERANCE)
            {
                return new Point(start.X, end.Y);
            }

            return end;
        }

        private double Distance(Point p1, Point p2)
        {
            return Math.Sqrt(Math.Pow(p2.X - p1.X, 2) + Math.Pow(p2.Y - p1.Y, 2));
        }

        #endregion

        #region Traced Elements

        private void CreateTracedWall(Point start, Point end)
        {
            bool isExterior = WallTypeCombo.SelectedIndex == 0;
            var color = isExterior ? Brushes.Red : Brushes.Blue;

            int wallTypeId = 441451;
            if (WallTypeCombo.SelectedItem is ComboBoxItem item && item.Tag != null)
            {
                wallTypeId = (int)item.Tag;
            }

            var line = new Line
            {
                X1 = start.X, Y1 = start.Y,
                X2 = end.X, Y2 = end.Y,
                Stroke = color,
                StrokeThickness = isExterior ? 4 : 3,
                Tag = "TracedWall"
            };
            DrawingCanvas.Children.Add(line);

            var traced = new TracedElement
            {
                ElementType = "Wall",
                StartPoint = start,
                EndPoint = end,
                WallTypeId = wallTypeId,
                IsExterior = isExterior,
                VisualElement = line,
                Color = color,
                DisplayName = $"Wall {_tracedElements.Count(t => t.ElementType == "Wall") + 1} ({(isExterior ? "Ext" : "Int")})"
            };

            _tracedElements.Add(traced);
            _undoStack.Push(traced);

            double lengthFeet = Distance(start, end) * _scale;
            StatusText.Text = $"Wall created: {lengthFeet:F1} ft. Total: {_tracedElements.Count(t => t.ElementType == "Wall")} walls.";
        }

        private void ClearTracedElements()
        {
            var toRemove = DrawingCanvas.Children.OfType<Line>()
                .Where(l => l.Tag?.ToString() == "TracedWall").ToList();
            foreach (var l in toRemove)
                DrawingCanvas.Children.Remove(l);

            _tracedElements.Clear();
            _undoStack.Clear();
            UpdateSummary();
        }

        private void AddScaleMarker(Point pos)
        {
            var marker = new Ellipse
            {
                Width = 10, Height = 10,
                Fill = Brushes.Yellow,
                Tag = "ScaleMarker"
            };
            Canvas.SetLeft(marker, pos.X - 5);
            Canvas.SetTop(marker, pos.Y - 5);
            DrawingCanvas.Children.Add(marker);
        }

        private void AddScaleLine(Point p1, Point p2)
        {
            var line = new Line
            {
                X1 = p1.X, Y1 = p1.Y,
                X2 = p2.X, Y2 = p2.Y,
                Stroke = Brushes.Yellow,
                StrokeThickness = 2,
                StrokeDashArray = new DoubleCollection { 4, 2 },
                Tag = "ScaleLine"
            };
            DrawingCanvas.Children.Add(line);
        }

        private void SelectElementAt(Point pos)
        {
            foreach (var elem in _tracedElements)
            {
                double dist = DistanceToLine(pos, elem.StartPoint, elem.EndPoint);
                if (dist < 10)
                {
                    ElementList.SelectedItem = elem;
                    HighlightElement(elem);
                    return;
                }
            }

            ElementList.SelectedItem = null;
        }

        private double DistanceToLine(Point p, Point lineStart, Point lineEnd)
        {
            double A = p.X - lineStart.X;
            double B = p.Y - lineStart.Y;
            double C = lineEnd.X - lineStart.X;
            double D = lineEnd.Y - lineStart.Y;

            double dot = A * C + B * D;
            double lenSq = C * C + D * D;
            double param = lenSq != 0 ? dot / lenSq : -1;

            double xx, yy;
            if (param < 0) { xx = lineStart.X; yy = lineStart.Y; }
            else if (param > 1) { xx = lineEnd.X; yy = lineEnd.Y; }
            else { xx = lineStart.X + param * C; yy = lineStart.Y + param * D; }

            return Distance(p, new Point(xx, yy));
        }

        private void HighlightElement(TracedElement elem)
        {
            foreach (var e in _tracedElements)
            {
                if (e.VisualElement is Line line)
                {
                    line.Stroke = e.Color;
                    line.StrokeThickness = e.IsExterior ? 4 : 3;
                }
            }

            if (elem?.VisualElement is Line selectedLine)
            {
                selectedLine.Stroke = Brushes.Lime;
                selectedLine.StrokeThickness = 5;
            }
        }

        #endregion

        #region Revit Integration

        private void Preview_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                $"Preview Summary:\n\n" +
                $"Walls: {_tracedElements.Count(t => t.ElementType == "Wall")}\n" +
                $"Doors: {_tracedElements.Count(t => t.ElementType == "Door")}\n" +
                $"Windows: {_tracedElements.Count(t => t.ElementType == "Window")}\n\n" +
                $"Scale: {_scale:F4} ft/pixel\n\n" +
                $"Click 'Create All in Revit' to generate these elements.",
                "Preview",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void CreateInRevit_Click(object sender, RoutedEventArgs e)
        {
            var walls = _tracedElements.Where(t => t.ElementType == "Wall").ToList();

            if (walls.Count == 0)
            {
                MessageBox.Show("No walls to create. Trace some walls first.", "No Walls", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var result = MessageBox.Show(
                $"Create {walls.Count} walls in Revit?\n\n" +
                $"This will create actual Revit wall elements.",
                "Confirm",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes) return;

            try
            {
                int created = 0;

                using (var trans = new Transaction(_doc, "Create Traced Walls"))
                {
                    trans.Start();

                    var level = new FilteredElementCollector(_doc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .OrderBy(l => l.Elevation)
                        .FirstOrDefault();

                    if (level == null)
                    {
                        MessageBox.Show("No levels found in the model.", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                        trans.RollBack();
                        return;
                    }

                    foreach (var wall in walls)
                    {
                        try
                        {
                            var startRevit = PixelToRevit(wall.StartPoint);
                            var endRevit = PixelToRevit(wall.EndPoint);

                            var line = Autodesk.Revit.DB.Line.CreateBound(
                                new XYZ(startRevit.X, startRevit.Y, 0),
                                new XYZ(endRevit.X, endRevit.Y, 0)
                            );

                            var wallType = _doc.GetElement(new ElementId(wall.WallTypeId)) as WallType;
                            if (wallType == null)
                            {
                                wallType = new FilteredElementCollector(_doc)
                                    .OfClass(typeof(WallType))
                                    .Cast<WallType>()
                                    .FirstOrDefault();
                            }

                            var newWall = Wall.Create(_doc, line, wallType.Id, level.Id, 10.0, 0, false, false);
                            if (newWall != null)
                                created++;
                        }
                        catch (Exception ex)
                        {
                            System.Diagnostics.Debug.WriteLine($"Failed to create wall: {ex.Message}");
                        }
                    }

                    trans.Commit();
                }

                StatusText.Text = $"Created {created} walls in Revit!";
                MessageBox.Show($"Successfully created {created} walls in Revit!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error creating walls: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private Point PixelToRevit(Point pixel)
        {
            double x = pixel.X * _scale;
            double y = (_imageHeight - pixel.Y) * _scale;
            return new Point(x, y);
        }

        #endregion

        #region UI Handlers

        private void ElementList_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var selected = ElementList.SelectedItem as TracedElement;
            HighlightElement(selected);
        }

        private void DeleteSelected_Click(object sender, RoutedEventArgs e)
        {
            var selected = ElementList.SelectedItem as TracedElement;
            if (selected == null) return;

            if (selected.VisualElement is Line line)
            {
                DrawingCanvas.Children.Remove(line);
            }

            _tracedElements.Remove(selected);
            UpdateSummary();
        }

        private void Undo_Click(object sender, RoutedEventArgs e)
        {
            if (_undoStack.Count == 0) return;

            var elem = _undoStack.Pop();
            if (elem.VisualElement is Line line)
            {
                DrawingCanvas.Children.Remove(line);
            }

            _tracedElements.Remove(elem);
            UpdateSummary();
        }

        private void ClearTraced_Click(object sender, RoutedEventArgs e)
        {
            if (_tracedElements.Count == 0) return;

            var result = MessageBox.Show(
                $"Clear all {_tracedElements.Count} traced elements?",
                "Confirm Clear",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result == MessageBoxResult.Yes)
            {
                ClearTracedElements();
                StatusText.Text = "All traced elements cleared.";
            }
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }

        private void UpdateSummary()
        {
            int walls = _tracedElements.Count(t => t.ElementType == "Wall");
            int doors = _tracedElements.Count(t => t.ElementType == "Door");
            int windows = _tracedElements.Count(t => t.ElementType == "Window");

            SummaryText.Text = $"Walls: {walls}\nDoors: {doors}\nWindows: {windows}";
        }

        #endregion

        #region Keyboard Shortcuts

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            // Escape - Cancel operations, break chain
            if (e.Key == Key.Escape)
            {
                // Cancel scale setting
                if (_isSettingScale)
                {
                    _isSettingScale = false;
                    _scalePoint1 = null;
                    RemoveScaleMarkers();
                    DrawingCanvas.Cursor = Cursors.Arrow;
                    StatusText.Text = "Scale setting cancelled.";
                    e.Handled = true;
                    return;
                }

                // Cancel drawing
                if (_isDrawing)
                {
                    if (_currentLine != null)
                    {
                        DrawingCanvas.Children.Remove(_currentLine);
                        _currentLine = null;
                    }
                    _isDrawing = false;
                    _startPoint = null;
                    ShowMeasurement(false);
                }

                // Break chain mode
                _lastWallEndPoint = null;
                StatusText.Text = "Chain broken. Click to start new wall.";
                e.Handled = true;
                return;
            }

            // Mode shortcuts (only when no modifier keys pressed)
            if (Keyboard.Modifiers == ModifierKeys.None)
            {
                switch (e.Key)
                {
                    case Key.W: // Wall mode
                        WallTool.IsChecked = true;
                        StatusText.Text = "Wall mode. Click to draw walls.";
                        e.Handled = true;
                        break;
                    case Key.S: // Select mode
                        SelectTool.IsChecked = true;
                        StatusText.Text = "Select mode. Click elements to select.";
                        e.Handled = true;
                        break;
                }
            }

            // Delete key - remove selected element
            if (e.Key == Key.Delete && ElementList.SelectedItem != null)
            {
                DeleteSelected_Click(this, null);
                e.Handled = true;
            }

            // Ctrl+Z - Undo
            if (e.Key == Key.Z && Keyboard.Modifiers == ModifierKeys.Control)
            {
                Undo_Click(this, null);
                e.Handled = true;
            }
        }

        #endregion
    }

    /// <summary>
    /// Represents a traced element (wall, door, or window)
    /// </summary>
    public class TracedElement : INotifyPropertyChanged
    {
        public string ElementType { get; set; }
        public Point StartPoint { get; set; }
        public Point EndPoint { get; set; }
        public int WallTypeId { get; set; }
        public bool IsExterior { get; set; }
        public UIElement VisualElement { get; set; }
        public Brush Color { get; set; }
        public string DisplayName { get; set; }

#pragma warning disable CS0067 // Event is declared but never used (required by interface)
        public event PropertyChangedEventHandler PropertyChanged;
#pragma warning restore CS0067
    }

    /// <summary>
    /// Dialog for entering scale distance - Professional styling
    /// </summary>
    public class ScaleInputDialog : Window
    {
        private TextBox _feetBox;
        private TextBox _inchesBox;

        public double DistanceInFeet { get; private set; }

        public ScaleInputDialog()
        {
            Title = "Scale Calibration - Enter Known Distance";
            Width = 350;
            Height = 180;
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            Background = new SolidColorBrush(SketchPadColors.BgPrimary);
            ResizeMode = ResizeMode.NoResize;

            var grid = new Grid { Margin = new Thickness(15) };
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            var label = new TextBlock
            {
                Text = "Enter the real-world distance for the line you drew:",
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 5)
            };
            Grid.SetRow(label, 0);

            var hint = new TextBlock
            {
                Text = "Tip: Use a known dimension from the floor plan (e.g., door width = 3'-0\")",
                Foreground = new SolidColorBrush(SketchPadColors.TextMuted),
                FontSize = 11,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 10)
            };
            Grid.SetRow(hint, 1);

            var inputPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 5, 0, 15) };
            _feetBox = new TextBox
            {
                Width = 60,
                Text = "10",
                Background = new SolidColorBrush(SketchPadColors.BgInput),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.Border),
                FontSize = 14,
                Padding = new Thickness(5, 3, 5, 3)
            };
            inputPanel.Children.Add(_feetBox);
            inputPanel.Children.Add(new Label
            {
                Content = "ft",
                Foreground = new SolidColorBrush(SketchPadColors.TextSecondary),
                VerticalAlignment = VerticalAlignment.Center
            });
            _inchesBox = new TextBox
            {
                Width = 60,
                Text = "0",
                Background = new SolidColorBrush(SketchPadColors.BgInput),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.Border),
                FontSize = 14,
                Padding = new Thickness(5, 3, 5, 3),
                Margin = new Thickness(10, 0, 0, 0)
            };
            inputPanel.Children.Add(_inchesBox);
            inputPanel.Children.Add(new Label
            {
                Content = "in",
                Foreground = new SolidColorBrush(SketchPadColors.TextSecondary),
                VerticalAlignment = VerticalAlignment.Center
            });
            Grid.SetRow(inputPanel, 2);

            var buttonPanel = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
            var okButton = new Button
            {
                Content = "Set Scale",
                Width = 90,
                Height = 30,
                Margin = new Thickness(0, 0, 8, 0),
                Background = new SolidColorBrush(SketchPadColors.AccentBlue),
                Foreground = Brushes.White,
                FontWeight = FontWeights.SemiBold
            };
            okButton.Click += (s, e) =>
            {
                double feet = 0, inches = 0;
                double.TryParse(_feetBox.Text, out feet);
                double.TryParse(_inchesBox.Text, out inches);
                DistanceInFeet = feet + (inches / 12.0);
                DialogResult = true;
            };
            var cancelButton = new Button
            {
                Content = "Cancel",
                Width = 75,
                Height = 30,
                Background = new SolidColorBrush(SketchPadColors.BgTertiary),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.BorderLight)
            };
            cancelButton.Click += (s, e) => DialogResult = false;
            buttonPanel.Children.Add(okButton);
            buttonPanel.Children.Add(cancelButton);
            Grid.SetRow(buttonPanel, 2);

            grid.Children.Add(label);
            grid.Children.Add(inputPanel);
            grid.Children.Add(buttonPanel);

            Content = grid;
        }
    }
}
