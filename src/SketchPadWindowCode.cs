using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Media.Media3D;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Microsoft.Win32;
using Newtonsoft.Json;

// Suppress warnings for UI fields reserved for future functionality
#pragma warning disable CS0414, CS0169

// Type aliases to resolve ambiguity between WPF and Revit types
using Point = System.Windows.Point;
using Line = System.Windows.Shapes.Line;
using ComboBox = System.Windows.Controls.ComboBox;
using Color = System.Windows.Media.Color;
using Grid = System.Windows.Controls.Grid;
using Ellipse = System.Windows.Shapes.Ellipse;
using Rectangle = System.Windows.Shapes.Rectangle;
using TextBox = System.Windows.Controls.TextBox;
using ToggleButton = System.Windows.Controls.Primitives.ToggleButton;

namespace RevitMCPBridge
{
    /// <summary>
    /// Professional color palette for consistent UI styling
    /// </summary>
    public static class SketchPadColors
    {
        // Backgrounds
        public static Color BgPrimary = Color.FromRgb(30, 30, 30);      // #1E1E1E
        public static Color BgSecondary = Color.FromRgb(45, 45, 45);    // #2D2D2D
        public static Color BgTertiary = Color.FromRgb(60, 60, 60);     // #3C3C3C
        public static Color BgCanvas = Color.FromRgb(26, 26, 26);       // #1A1A1A
        public static Color BgInput = Color.FromRgb(50, 50, 50);        // Input fields

        // Text - IMPROVED CONTRAST
        public static Color TextPrimary = Color.FromRgb(230, 230, 230);   // #E6E6E6 - High contrast
        public static Color TextSecondary = Color.FromRgb(180, 180, 180); // #B4B4B4 - Good contrast
        public static Color TextLabel = Color.FromRgb(160, 160, 160);     // #A0A0A0 - Labels
        public static Color TextMuted = Color.FromRgb(128, 128, 128);     // #808080 - Disabled

        // Accent
        public static Color AccentBlue = Color.FromRgb(0, 122, 204);      // #007ACC - Revit blue
        public static Color AccentCyan = Color.FromRgb(0, 188, 212);      // #00BCD4
        public static Color AccentGreen = Color.FromRgb(0, 150, 100);     // Toggle on

        // Status
        public static Color Success = Color.FromRgb(76, 175, 80);         // #4CAF50
        public static Color Warning = Color.FromRgb(255, 152, 0);         // #FF9800
        public static Color Error = Color.FromRgb(244, 67, 54);           // #F44336

        // Elements
        public static Color WallColor = Color.FromRgb(220, 60, 60);       // Red walls
        public static Color DoorColor = Color.FromRgb(0, 200, 80);        // Lime doors
        public static Color WindowColor = Color.FromRgb(0, 191, 255);     // DeepSkyBlue windows
        public static Color FurnitureColor = Color.FromRgb(255, 152, 0);  // Orange furniture
        public static Color FixtureColor = Color.FromRgb(0, 191, 255);    // Cyan fixtures
        public static Color CaseworkColor = Color.FromRgb(160, 100, 50);  // Brown casework
        public static Color ElectricalColor = Color.FromRgb(255, 235, 59);// Yellow electrical
        public static Color DimensionColor = Color.FromRgb(255, 255, 0);  // Yellow dimensions
        public static Color CalibrationColor = Color.FromRgb(255, 215, 0);// Gold calibration

        // Grid
        public static Color GridMinor = Color.FromRgb(40, 40, 40);
        public static Color GridMajor = Color.FromRgb(55, 55, 55);
        public static Color GridOrigin = Color.FromRgb(80, 80, 80);

        // Borders
        public static Color Border = Color.FromRgb(70, 70, 70);
        public static Color BorderLight = Color.FromRgb(85, 85, 85);
    }

    /// <summary>
    /// SketchPad - Draw and create Revit elements in real-time (Pure C# version)
    /// As you sketch, walls appear directly in Revit!
    /// Enhanced with zoom, pan, measurements, and more tools.
    /// </summary>
    public class SketchPadWindow : Window
    {
        private UIApplication _uiApp;
        private Document _doc;
        private ExternalEvent _externalEvent;
        private CreateWallHandler _createWallHandler;

        // Canvas settings
        private double _scale = 4.0; // pixels per foot (increased for larger canvas)
        private double _gridSizeFeet = 5.0; // Adjustable grid size
        private const double MIN_SCALE = 1.0;
        private const double MAX_SCALE = 20.0;

        // Pan/zoom state
        private Point _panOffset = new Point(0, 0);
        private bool _isPanning = false;
        private Point _panStart;

        // Drawing state
        private bool _isDrawing = false;
        private Point _startPoint;
        private Line _previewLine;
        private List<Point> _roofPoints = new List<Point>();
        private bool _orthoMode = true;
        private bool _deleteMode = false;
        private double _wallHeight = 10.0;
        private bool _snapToEndpoints = true;
        private double _snapToleranceFeet = 1.0; // 1 foot snap tolerance

        // Polyline/Chain wall drawing
        private bool _chainMode = true; // When true, continue drawing walls from last endpoint
        private Point? _lastWallEndPoint = null;

        // Box selection
        private bool _isBoxSelecting = false;
        private Point _boxSelectStart;
        private Rectangle _selectionBox;
        private List<UIElement> _selectedElements = new List<UIElement>();

        // Undo stack
        private Stack<ElementId> _createdElements = new Stack<ElementId>();
        private Stack<UIElement> _canvasElements = new Stack<UIElement>();

        // Drawn walls data (for export)
        private List<DrawnWall> _drawnWalls = new List<DrawnWall>();

        // Placed doors/windows data
        private List<PlacedOpening> _placedDoors = new List<PlacedOpening>();
        private List<PlacedOpening> _placedWindows = new List<PlacedOpening>();

        // Placed elements data (for furniture, fixtures, casework, electrical)
        private List<PlacedElement> _placedFurniture = new List<PlacedElement>();
        private List<PlacedElement> _placedFixtures = new List<PlacedElement>();
        private List<PlacedElement> _placedCasework = new List<PlacedElement>();
        private List<PlacedElement> _placedElectrical = new List<PlacedElement>();

        // Current level and element types
        private ElementId _currentLevelId;
        private ElementId _currentWallTypeId;
        private ElementId _currentRoofTypeId;
        private ElementId _currentDoorTypeId;
        private ElementId _currentWindowTypeId;
        private ElementId _currentFurnitureTypeId;
        private ElementId _currentFixtureTypeId;
        private ElementId _currentCaseworkTypeId;
        private ElementId _currentElectricalTypeId;

        // External event handlers for doors/windows
        private ExternalEvent _doorExternalEvent;
        private CreateDoorHandler _createDoorHandler;
        private ExternalEvent _windowExternalEvent;
        private CreateWindowHandler _createWindowHandler;

        // External event handlers for furniture, fixtures, casework, electrical
        private ExternalEvent _elementExternalEvent;
        private CreateElementHandler _createElementHandler;

        // External event handler for deleting elements in Revit
        private ExternalEvent _deleteExternalEvent;
        private DeleteElementHandler _deleteElementHandler;

        // Background image with scaling
        private Image _backgroundImage;
        private double _imageOpacity = 0.5;
        private double _imageScale = 1.0; // Scale factor for image (e.g., 1/4" = 1'-0" -> 48)
        private string _imageScaleString = "1/4\" = 1'-0\"";
        private double _imageZoom = 1.0; // User-adjustable image zoom
        private Point _imageOffset = new Point(0, 0); // Image position offset
        private bool _isDraggingImage = false;
        private Point _imageDragStart;
        private bool _imageManipulationMode = false; // When true, mouse moves image instead of drawing

        // Image calibration mode - draw a line on image and specify real-world length
        private bool _calibrationMode = false;
        private Point? _calibrationStart = null;
        private Line _calibrationLine = null;
        private double _imagePixelsPerFoot = 1.0; // Calculated from calibration

        // UI Controls
        private Canvas GridCanvas;
        private Canvas DrawingCanvas;
        private Border CanvasBorder;
        private TextBlock ScaleText;
        private TextBlock StatusText;
        private TextBlock CoordinateText;
        private TextBlock InstructionText;
        private TextBlock MeasurementText;
        private ComboBox LevelCombo;
        private ComboBox WallTypeCombo;
        private ComboBox RoofTypeCombo;
        private ComboBox DoorTypeCombo;
        private ComboBox WindowTypeCombo;
        private ComboBox FurnitureTypeCombo;
        private ComboBox FixtureTypeCombo;
        private ComboBox CaseworkTypeCombo;
        private ComboBox ElectricalTypeCombo;
        private ComboBox ImageScaleCombo;
        private TextBox WallHeightInput;
        private TextBox GridSizeInput;
        private Slider OpacitySlider;
        private ToggleButton OrthoToggle;
        private ToggleButton DeleteToggle;
        private RadioButton WallMode;
        private RadioButton RoomMode;
        private RadioButton DoorMode;
        private RadioButton WindowMode;
        private RadioButton RoofMode;
        private RadioButton FurnitureMode;
        private RadioButton FixtureMode;
        private RadioButton CaseworkMode;
        private RadioButton ElectricalMode;
        private RadioButton DimensionMode;
        private RadioButton RoomLabelMode;
        private RadioButton SelectMode;

        // Dimension measurement state
        private List<DrawnDimension> _drawnDimensions = new List<DrawnDimension>();
        private bool _isDimensioning = false;
        private Point _dimensionStart;

        // Room label state
        private List<DrawnRoomLabel> _drawnRoomLabels = new List<DrawnRoomLabel>();

        // Selection state
        private UIElement _selectedElement = null;
        private Point _selectionOffset;
        private bool _isDragging = false;

        // Undo/Redo system
        private Stack<UndoAction> _undoStack = new Stack<UndoAction>();
        private Stack<UndoAction> _redoStack = new Stack<UndoAction>();

        // Type options panel (changes based on selected mode)
        private StackPanel TypeOptionsPanel;
        private Border WallOptionsPanel;
        private Border RoofOptionsPanel;
        private Border DoorOptionsPanel;
        private Border WindowOptionsPanel;
        private Border FurnitureOptionsPanel;
        private Border FixtureOptionsPanel;
        private Border CaseworkOptionsPanel;
        private Border ElectricalOptionsPanel;

        // 3D viewport components
        private Viewport3D _viewport3D;
        private Border _viewport3DBorder;
        private bool _show3DView = false;
        private ModelVisual3D _wallsModel;
        private PerspectiveCamera _camera3D;
        private double _cameraAngle = 45; // Degrees around Y axis
        private double _cameraPitch = 30; // Degrees pitch
        private double _cameraDistance = 100; // Distance from origin
        private Point _lastMouse3D;
        private bool _isRotating3D = false;

        public SketchPadWindow(UIApplication uiApp)
        {
            _uiApp = uiApp;
            _doc = uiApp.ActiveUIDocument.Document;

            // Window properties - LARGER SIZE
            Title = "SketchPad - Draw to Revit";
            Height = 750;
            Width = 900;
            MinHeight = 600;
            MinWidth = 700;
            WindowStartupLocation = WindowStartupLocation.Manual;
            Left = 50;
            Top = 50;
            Topmost = true;
            Background = new SolidColorBrush(Color.FromRgb(30, 30, 30));
            ResizeMode = ResizeMode.CanResizeWithGrip;

            // Build UI
            BuildUI();

            // Setup external event for creating elements
            _createWallHandler = new CreateWallHandler();
            _externalEvent = ExternalEvent.Create(_createWallHandler);

            // Setup external events for doors and windows
            _createDoorHandler = new CreateDoorHandler();
            _doorExternalEvent = ExternalEvent.Create(_createDoorHandler);
            _createWindowHandler = new CreateWindowHandler();
            _windowExternalEvent = ExternalEvent.Create(_createWindowHandler);

            // Setup external event for furniture/fixtures/casework/electrical
            _createElementHandler = new CreateElementHandler();
            _elementExternalEvent = ExternalEvent.Create(_createElementHandler);

            // Setup external event for deleting elements
            _deleteElementHandler = new DeleteElementHandler();
            _deleteExternalEvent = ExternalEvent.Create(_deleteElementHandler);

            // Load all element types from the model
            LoadLevels();
            LoadWallTypes();
            LoadRoofTypes();
            LoadDoorTypes();
            LoadWindowTypes();
            LoadFurnitureTypes();
            LoadFixtureTypes();
            LoadCaseworkTypes();
            LoadElectricalTypes();
            DrawGrid();
            UpdateScaleIndicator();
            UpdateTypeOptionsVisibility();

            this.Loaded += (s, e) => InstructionText.Visibility = System.Windows.Visibility.Collapsed;
            this.SizeChanged += (s, e) => DrawGrid();
        }

        // Data class for exported walls (public for handler access)
        public class DrawnWall
        {
            public double StartX { get; set; }
            public double StartY { get; set; }
            public double EndX { get; set; }
            public double EndY { get; set; }
            public double Height { get; set; }
            public string LevelName { get; set; }
            public string WallTypeName { get; set; }
            public int? RevitElementId { get; set; }
        }

        // Data class for placed doors/windows
        public class PlacedOpening
        {
            public double X { get; set; }
            public double Y { get; set; }
            public int WallIndex { get; set; } // Index into _drawnWalls
            public string TypeName { get; set; }
            public int? RevitElementId { get; set; }
            public int? RevitWallId { get; set; }
        }

        // Data class for placed furniture/fixtures/casework/electrical elements
        public class PlacedElement
        {
            public double X { get; set; }
            public double Y { get; set; }
            public double Rotation { get; set; } // Degrees
            public string CategoryName { get; set; } // Furniture, Fixture, Casework, Electrical
            public string FamilyName { get; set; }
            public string TypeName { get; set; }
            public int? RevitElementId { get; set; }
        }

        public class DrawnDimension
        {
            public double X1 { get; set; }
            public double Y1 { get; set; }
            public double X2 { get; set; }
            public double Y2 { get; set; }
            public double Distance { get; set; } // In feet
            public UIElement VisualElement { get; set; }
            public int? RevitElementId { get; set; }
        }

        public class DrawnRoomLabel
        {
            public double X { get; set; }
            public double Y { get; set; }
            public string RoomName { get; set; }
            public double Area { get; set; } // In square feet
            public UIElement VisualElement { get; set; }
            public int? RevitElementId { get; set; }
        }

        public class UndoAction
        {
            public string ActionType { get; set; } // "Wall", "Door", "Window", "Furniture", "Dimension", "RoomLabel"
            public UIElement CanvasElement { get; set; }
            public object DataElement { get; set; } // DrawnWall, PlacedOpening, etc.
            public ElementId RevitElementId { get; set; }
        }

        private void BuildUI()
        {
            var mainGrid = new Grid();
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // Row 0: Tool Selection
            var toolBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(45, 45, 45)),
                Padding = new Thickness(8)
            };
            Grid.SetRow(toolBorder, 0);

            var toolGrid = new Grid();
            toolGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            toolGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            toolGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            // Left: Draw Mode
            var modeStack = new StackPanel();
            modeStack.Children.Add(new Label
            {
                Content = "DRAW MODE",
                Foreground = new SolidColorBrush(SketchPadColors.TextLabel),
                FontSize = 10,
                FontWeight = FontWeights.Bold,
                Padding = new Thickness(0)
            });

            var modePanel = new WrapPanel();
            WallMode = CreateRadioButton("Wall", "DrawMode", true);
            RoomMode = CreateRadioButton("Room", "DrawMode", false);
            DoorMode = CreateRadioButton("Door", "DrawMode", false);
            WindowMode = CreateRadioButton("Window", "DrawMode", false);
            RoofMode = CreateRadioButton("Roof", "DrawMode", false);
            FurnitureMode = CreateRadioButton("Furniture", "DrawMode", false);
            FixtureMode = CreateRadioButton("Fixture", "DrawMode", false);
            CaseworkMode = CreateRadioButton("Casework", "DrawMode", false);
            ElectricalMode = CreateRadioButton("Electrical", "DrawMode", false);
            DimensionMode = CreateRadioButton("Dimension", "DrawMode", false);
            RoomLabelMode = CreateRadioButton("Label", "DrawMode", false);
            SelectMode = CreateRadioButton("Select", "DrawMode", false);

            modePanel.Children.Add(WallMode);
            modePanel.Children.Add(RoomMode);
            modePanel.Children.Add(DoorMode);
            modePanel.Children.Add(WindowMode);
            modePanel.Children.Add(RoofMode);
            modePanel.Children.Add(FurnitureMode);
            modePanel.Children.Add(FixtureMode);
            modePanel.Children.Add(CaseworkMode);
            modePanel.Children.Add(ElectricalMode);
            modePanel.Children.Add(DimensionMode);
            modePanel.Children.Add(RoomLabelMode);
            modePanel.Children.Add(SelectMode);
            modeStack.Children.Add(modePanel);
            Grid.SetColumn(modeStack, 0);
            toolGrid.Children.Add(modeStack);

            // Right: Toggle Buttons
            var toggleStack = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };

            OrthoToggle = new ToggleButton
            {
                Content = "ORTHO",
                IsChecked = true,
                Width = 60,
                Height = 28,
                Margin = new Thickness(3),
                Background = new SolidColorBrush(Color.FromRgb(0, 120, 80)),
                Foreground = Brushes.White,
                FontSize = 10,
                FontWeight = FontWeights.Bold
            };
            OrthoToggle.Checked += (s, e) => { _orthoMode = true; OrthoToggle.Background = new SolidColorBrush(Color.FromRgb(0, 120, 80)); };
            OrthoToggle.Unchecked += (s, e) => { _orthoMode = false; OrthoToggle.Background = new SolidColorBrush(Color.FromRgb(60, 60, 60)); };
            toggleStack.Children.Add(OrthoToggle);

            DeleteToggle = new ToggleButton
            {
                Content = "DELETE",
                IsChecked = false,
                Width = 60,
                Height = 28,
                Margin = new Thickness(3),
                Background = new SolidColorBrush(Color.FromRgb(60, 60, 60)),
                Foreground = Brushes.White,
                FontSize = 10,
                FontWeight = FontWeights.Bold
            };
            DeleteToggle.Checked += (s, e) => { _deleteMode = true; DeleteToggle.Background = new SolidColorBrush(Color.FromRgb(180, 50, 50)); StatusText.Text = "DELETE MODE: Click on a wall to remove it."; };
            DeleteToggle.Unchecked += (s, e) => { _deleteMode = false; DeleteToggle.Background = new SolidColorBrush(Color.FromRgb(60, 60, 60)); StatusText.Text = "Ready. Draw to create walls."; };
            toggleStack.Children.Add(DeleteToggle);

            // SNAP toggle button
            var SnapToggle = new ToggleButton
            {
                Content = "SNAP",
                IsChecked = true,
                Width = 60,
                Height = 28,
                Margin = new Thickness(3),
                Background = new SolidColorBrush(Color.FromRgb(0, 100, 150)),
                Foreground = Brushes.White,
                FontSize = 10,
                FontWeight = FontWeights.Bold
            };
            SnapToggle.Checked += (s, e) => { _snapToEndpoints = true; SnapToggle.Background = new SolidColorBrush(Color.FromRgb(0, 100, 150)); StatusText.Text = "SNAP ON: New walls will snap to existing endpoints."; };
            SnapToggle.Unchecked += (s, e) => { _snapToEndpoints = false; SnapToggle.Background = new SolidColorBrush(Color.FromRgb(60, 60, 60)); StatusText.Text = "SNAP OFF: Walls snap to grid only."; };
            toggleStack.Children.Add(SnapToggle);

            // CHAIN toggle button for polyline walls
            var ChainToggle = new ToggleButton
            {
                Content = "CHAIN",
                IsChecked = true,
                Width = 60,
                Height = 28,
                Margin = new Thickness(3),
                Background = new SolidColorBrush(Color.FromRgb(150, 100, 0)),
                Foreground = Brushes.White,
                FontSize = 10,
                FontWeight = FontWeights.Bold,
                ToolTip = "Chain mode: Continue drawing walls from last endpoint"
            };
            ChainToggle.Checked += (s, e) => { _chainMode = true; ChainToggle.Background = new SolidColorBrush(Color.FromRgb(150, 100, 0)); StatusText.Text = "CHAIN ON: Walls continue from last endpoint. Press Esc to break chain."; };
            ChainToggle.Unchecked += (s, e) => { _chainMode = false; _lastWallEndPoint = null; ChainToggle.Background = new SolidColorBrush(Color.FromRgb(60, 60, 60)); StatusText.Text = "CHAIN OFF: Each wall starts fresh."; };
            toggleStack.Children.Add(ChainToggle);

            Grid.SetColumn(toggleStack, 2);
            toolGrid.Children.Add(toggleStack);

            toolBorder.Child = toolGrid;
            mainGrid.Children.Add(toolBorder);

            // Row 1: Level and General Settings
            var optionsBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(37, 37, 37)),
                Padding = new Thickness(8)
            };
            Grid.SetRow(optionsBorder, 1);

            var optionsGrid = new Grid();
            optionsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            optionsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) });
            optionsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            optionsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            // Level combo
            var levelStack = new StackPanel { Margin = new Thickness(0, 0, 5, 0) };
            levelStack.Children.Add(new Label { Content = "LEVEL", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            LevelCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            LevelCombo.SelectionChanged += Level_Changed;
            levelStack.Children.Add(LevelCombo);
            Grid.SetColumn(levelStack, 0);
            optionsGrid.Children.Add(levelStack);

            // Type Options Panel (content changes based on mode)
            TypeOptionsPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(5, 0, 5, 0) };

            // --- Wall Options Panel ---
            WallOptionsPanel = new Border { Margin = new Thickness(0) };
            var wallOptionsStack = new StackPanel { Orientation = Orientation.Horizontal };

            var wallTypeStack = new StackPanel { Margin = new Thickness(0, 0, 10, 0), MinWidth = 200 };
            wallTypeStack.Children.Add(new Label { Content = "WALL TYPE", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            WallTypeCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            WallTypeCombo.SelectionChanged += WallType_Changed;
            wallTypeStack.Children.Add(WallTypeCombo);
            wallOptionsStack.Children.Add(wallTypeStack);

            var heightStack = new StackPanel { Margin = new Thickness(0, 0, 5, 0), Width = 70 };
            heightStack.Children.Add(new Label { Content = "HEIGHT (ft)", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            WallHeightInput = new TextBox {
                Text = "10",
                Background = new SolidColorBrush(Color.FromRgb(60, 60, 60)),
                Foreground = Brushes.White,
                Height = 26,
                TextAlignment = TextAlignment.Center,
                BorderBrush = new SolidColorBrush(Color.FromRgb(85, 85, 85))
            };
            WallHeightInput.TextChanged += (s, e) => { if (double.TryParse(WallHeightInput.Text, out double h)) _wallHeight = h; };
            heightStack.Children.Add(WallHeightInput);
            wallOptionsStack.Children.Add(heightStack);
            WallOptionsPanel.Child = wallOptionsStack;

            // --- Roof Options Panel ---
            RoofOptionsPanel = new Border { Margin = new Thickness(0), Visibility = System.Windows.Visibility.Collapsed };
            var roofOptionsStack = new StackPanel { Orientation = Orientation.Horizontal };

            var roofTypeStack = new StackPanel { Margin = new Thickness(0, 0, 10, 0), MinWidth = 200 };
            roofTypeStack.Children.Add(new Label { Content = "ROOF TYPE", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            RoofTypeCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            RoofTypeCombo.SelectionChanged += RoofType_Changed;
            roofTypeStack.Children.Add(RoofTypeCombo);
            roofOptionsStack.Children.Add(roofTypeStack);
            RoofOptionsPanel.Child = roofOptionsStack;

            // --- Door Options Panel ---
            DoorOptionsPanel = new Border { Margin = new Thickness(0), Visibility = System.Windows.Visibility.Collapsed };
            var doorOptionsStack = new StackPanel { Orientation = Orientation.Horizontal };

            var doorTypeStack = new StackPanel { Margin = new Thickness(0, 0, 10, 0), MinWidth = 250 };
            doorTypeStack.Children.Add(new Label { Content = "DOOR FAMILY/TYPE", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            DoorTypeCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            DoorTypeCombo.SelectionChanged += DoorType_Changed;
            doorTypeStack.Children.Add(DoorTypeCombo);
            doorOptionsStack.Children.Add(doorTypeStack);
            DoorOptionsPanel.Child = doorOptionsStack;

            // --- Window Options Panel ---
            WindowOptionsPanel = new Border { Margin = new Thickness(0), Visibility = System.Windows.Visibility.Collapsed };
            var windowOptionsStack = new StackPanel { Orientation = Orientation.Horizontal };

            var windowTypeStack = new StackPanel { Margin = new Thickness(0, 0, 10, 0), MinWidth = 250 };
            windowTypeStack.Children.Add(new Label { Content = "WINDOW FAMILY/TYPE", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            WindowTypeCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            WindowTypeCombo.SelectionChanged += WindowType_Changed;
            windowTypeStack.Children.Add(WindowTypeCombo);
            windowOptionsStack.Children.Add(windowTypeStack);
            WindowOptionsPanel.Child = windowOptionsStack;

            // --- Furniture Options Panel ---
            FurnitureOptionsPanel = new Border { Margin = new Thickness(0), Visibility = System.Windows.Visibility.Collapsed };
            var furnitureOptionsStack = new StackPanel { Orientation = Orientation.Horizontal };

            var furnitureTypeStack = new StackPanel { Margin = new Thickness(0, 0, 10, 0), MinWidth = 250 };
            furnitureTypeStack.Children.Add(new Label { Content = "FURNITURE FAMILY/TYPE", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            FurnitureTypeCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            FurnitureTypeCombo.SelectionChanged += FurnitureType_Changed;
            furnitureTypeStack.Children.Add(FurnitureTypeCombo);
            furnitureOptionsStack.Children.Add(furnitureTypeStack);
            FurnitureOptionsPanel.Child = furnitureOptionsStack;

            // --- Fixture Options Panel (Plumbing Fixtures) ---
            FixtureOptionsPanel = new Border { Margin = new Thickness(0), Visibility = System.Windows.Visibility.Collapsed };
            var fixtureOptionsStack = new StackPanel { Orientation = Orientation.Horizontal };

            var fixtureTypeStack = new StackPanel { Margin = new Thickness(0, 0, 10, 0), MinWidth = 250 };
            fixtureTypeStack.Children.Add(new Label { Content = "PLUMBING FIXTURE TYPE", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            FixtureTypeCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            FixtureTypeCombo.SelectionChanged += FixtureType_Changed;
            fixtureTypeStack.Children.Add(FixtureTypeCombo);
            fixtureOptionsStack.Children.Add(fixtureTypeStack);
            FixtureOptionsPanel.Child = fixtureOptionsStack;

            // --- Casework Options Panel ---
            CaseworkOptionsPanel = new Border { Margin = new Thickness(0), Visibility = System.Windows.Visibility.Collapsed };
            var caseworkOptionsStack = new StackPanel { Orientation = Orientation.Horizontal };

            var caseworkTypeStack = new StackPanel { Margin = new Thickness(0, 0, 10, 0), MinWidth = 250 };
            caseworkTypeStack.Children.Add(new Label { Content = "CASEWORK FAMILY/TYPE", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            CaseworkTypeCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            CaseworkTypeCombo.SelectionChanged += CaseworkType_Changed;
            caseworkTypeStack.Children.Add(CaseworkTypeCombo);
            caseworkOptionsStack.Children.Add(caseworkTypeStack);
            CaseworkOptionsPanel.Child = caseworkOptionsStack;

            // --- Electrical Options Panel ---
            ElectricalOptionsPanel = new Border { Margin = new Thickness(0), Visibility = System.Windows.Visibility.Collapsed };
            var electricalOptionsStack = new StackPanel { Orientation = Orientation.Horizontal };

            var electricalTypeStack = new StackPanel { Margin = new Thickness(0, 0, 10, 0), MinWidth = 250 };
            electricalTypeStack.Children.Add(new Label { Content = "ELECTRICAL DEVICE TYPE", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            ElectricalTypeCombo = new ComboBox { Background = Brushes.White, Foreground = Brushes.Black, Height = 26 };
            ElectricalTypeCombo.SelectionChanged += ElectricalType_Changed;
            electricalTypeStack.Children.Add(ElectricalTypeCombo);
            electricalOptionsStack.Children.Add(electricalTypeStack);
            ElectricalOptionsPanel.Child = electricalOptionsStack;

            // Add all panels to type options
            TypeOptionsPanel.Children.Add(WallOptionsPanel);
            TypeOptionsPanel.Children.Add(RoofOptionsPanel);
            TypeOptionsPanel.Children.Add(DoorOptionsPanel);
            TypeOptionsPanel.Children.Add(WindowOptionsPanel);
            TypeOptionsPanel.Children.Add(FurnitureOptionsPanel);
            TypeOptionsPanel.Children.Add(FixtureOptionsPanel);
            TypeOptionsPanel.Children.Add(CaseworkOptionsPanel);
            TypeOptionsPanel.Children.Add(ElectricalOptionsPanel);
            Grid.SetColumn(TypeOptionsPanel, 1);
            optionsGrid.Children.Add(TypeOptionsPanel);

            // Grid size input
            var gridStack = new StackPanel { Margin = new Thickness(5, 0, 0, 0), Width = 70 };
            gridStack.Children.Add(new Label { Content = "GRID (ft)", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, Padding = new Thickness(0) });
            GridSizeInput = new TextBox {
                Text = "5",
                Background = new SolidColorBrush(Color.FromRgb(60, 60, 60)),
                Foreground = Brushes.White,
                Height = 26,
                TextAlignment = TextAlignment.Center,
                BorderBrush = new SolidColorBrush(Color.FromRgb(85, 85, 85))
            };
            GridSizeInput.TextChanged += (s, e) => { if (double.TryParse(GridSizeInput.Text, out double g) && g > 0) { _gridSizeFeet = g; DrawGrid(); } };
            gridStack.Children.Add(GridSizeInput);
            Grid.SetColumn(gridStack, 3);
            optionsGrid.Children.Add(gridStack);

            optionsBorder.Child = optionsGrid;
            mainGrid.Children.Add(optionsBorder);

            // Row 2: Zoom/Pan Controls, Image Scale, and Opacity
            var controlsBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(40, 40, 40)),
                Padding = new Thickness(8)
            };
            Grid.SetRow(controlsBorder, 2);

            var controlsGrid = new Grid();
            controlsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            controlsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            controlsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            controlsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            // Zoom controls
            var zoomStack = new StackPanel { Orientation = Orientation.Horizontal };
            zoomStack.Children.Add(new Label { Content = "ZOOM:", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, VerticalAlignment = VerticalAlignment.Center });
            zoomStack.Children.Add(CreateButton("-", ZoomOut_Click, 30));
            zoomStack.Children.Add(CreateButton("+", ZoomIn_Click, 30));
            zoomStack.Children.Add(CreateButton("Fit", ZoomFit_Click, 40));
            zoomStack.Children.Add(CreateButton("Reset", ResetView_Click, 50));
            Grid.SetColumn(zoomStack, 0);
            controlsGrid.Children.Add(zoomStack);

            // Image scale selector
            var scaleSelectStack = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(20, 0, 0, 0) };
            scaleSelectStack.Children.Add(new Label { Content = "IMAGE SCALE:", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, VerticalAlignment = VerticalAlignment.Center });
            ImageScaleCombo = new ComboBox {
                Background = Brushes.White,
                Foreground = Brushes.Black,
                Height = 26,
                Width = 120
            };
            // Add common architectural scales
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "1\" = 1'-0\"", Tag = 12.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "1/2\" = 1'-0\"", Tag = 24.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "1/4\" = 1'-0\"", Tag = 48.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "1/8\" = 1'-0\"", Tag = 96.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "1/16\" = 1'-0\"", Tag = 192.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "3/4\" = 1'-0\"", Tag = 16.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "3/8\" = 1'-0\"", Tag = 32.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "3/16\" = 1'-0\"", Tag = 64.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "3/32\" = 1'-0\"", Tag = 128.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "1:100", Tag = 100.0 / 12.0 });
            ImageScaleCombo.Items.Add(new ComboBoxItem { Content = "1:50", Tag = 50.0 / 12.0 });
            ImageScaleCombo.SelectedIndex = 2; // Default 1/4" = 1'-0"
            ImageScaleCombo.SelectionChanged += ImageScale_Changed;
            scaleSelectStack.Children.Add(ImageScaleCombo);
            Grid.SetColumn(scaleSelectStack, 1);
            controlsGrid.Children.Add(scaleSelectStack);

            // Image opacity slider
            var opacityStack = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
            opacityStack.Children.Add(new Label { Content = "IMAGE OPACITY:", Foreground = new SolidColorBrush(SketchPadColors.TextLabel), FontSize = 10, VerticalAlignment = VerticalAlignment.Center });
            OpacitySlider = new Slider
            {
                Width = 100,
                Minimum = 0,
                Maximum = 1,
                Value = 0.5,
                VerticalAlignment = VerticalAlignment.Center
            };
            OpacitySlider.ValueChanged += (s, e) => { _imageOpacity = OpacitySlider.Value; if (_backgroundImage != null) _backgroundImage.Opacity = _imageOpacity; };
            opacityStack.Children.Add(OpacitySlider);
            Grid.SetColumn(opacityStack, 3);
            controlsGrid.Children.Add(opacityStack);

            controlsBorder.Child = controlsGrid;
            mainGrid.Children.Add(controlsBorder);

            // Row 3: Drawing Canvas
            CanvasBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(26, 26, 26)),
                Margin = new Thickness(5),
                BorderBrush = new SolidColorBrush(Color.FromRgb(51, 51, 51)),
                BorderThickness = new Thickness(1)
            };
            Grid.SetRow(CanvasBorder, 3);

            var canvasGrid = new Grid();

            GridCanvas = new Canvas { ClipToBounds = true };
            canvasGrid.Children.Add(GridCanvas);

            DrawingCanvas = new Canvas { Background = Brushes.Transparent, ClipToBounds = true };
            DrawingCanvas.MouseLeftButtonDown += Canvas_MouseLeftButtonDown;
            DrawingCanvas.MouseLeftButtonUp += Canvas_MouseLeftButtonUp;
            DrawingCanvas.MouseMove += Canvas_MouseMove;
            DrawingCanvas.MouseRightButtonDown += Canvas_MouseRightButtonDown;
            DrawingCanvas.MouseWheel += Canvas_MouseWheel;
            DrawingCanvas.PreviewMouseDown += Canvas_PreviewMouseDown;
            DrawingCanvas.PreviewMouseUp += Canvas_PreviewMouseUp;
            canvasGrid.Children.Add(DrawingCanvas);

            // Scale indicator (bottom left)
            var scaleBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(204, 45, 45, 45)),
                HorizontalAlignment = HorizontalAlignment.Left,
                VerticalAlignment = VerticalAlignment.Bottom,
                Padding = new Thickness(5),
                Margin = new Thickness(5),
                CornerRadius = new CornerRadius(3)
            };
            var scaleStack = new StackPanel { Orientation = Orientation.Horizontal };
            scaleStack.Children.Add(new Rectangle { Width = 50, Height = 3, Fill = Brushes.White, VerticalAlignment = VerticalAlignment.Center });
            ScaleText = new TextBlock { Text = "10 ft", Foreground = Brushes.White, Margin = new Thickness(5, 0, 0, 0), FontSize = 10 };
            scaleStack.Children.Add(ScaleText);
            scaleBorder.Child = scaleStack;
            canvasGrid.Children.Add(scaleBorder);

            // Coordinate display (bottom right)
            var coordBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(204, 45, 45, 45)),
                HorizontalAlignment = HorizontalAlignment.Right,
                VerticalAlignment = VerticalAlignment.Bottom,
                Padding = new Thickness(5),
                Margin = new Thickness(5),
                CornerRadius = new CornerRadius(3)
            };
            CoordinateText = new TextBlock { Text = "X: 0.0  Y: 0.0", Foreground = Brushes.Cyan, FontSize = 10, FontFamily = new FontFamily("Consolas") };
            coordBorder.Child = CoordinateText;
            canvasGrid.Children.Add(coordBorder);

            // Measurement display (top center - shows while drawing)
            var measureBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(220, 60, 60, 60)),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Top,
                Padding = new Thickness(10, 5, 10, 5),
                Margin = new Thickness(5),
                CornerRadius = new CornerRadius(3),
                Visibility = System.Windows.Visibility.Collapsed
            };
            MeasurementText = new TextBlock { Text = "0'-0\"", Foreground = Brushes.Yellow, FontSize = 14, FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Consolas") };
            measureBorder.Child = MeasurementText;
            measureBorder.Tag = "MeasurementBorder";
            canvasGrid.Children.Add(measureBorder);

            // Instructions overlay
            InstructionText = new TextBlock
            {
                Text = "Click and drag to draw walls. They appear in Revit immediately.\nMiddle-click to pan. Scroll to zoom.",
                Foreground = new SolidColorBrush(Color.FromRgb(102, 102, 102)),
                FontSize = 12,
                TextAlignment = TextAlignment.Center,
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            canvasGrid.Children.Add(InstructionText);

            CanvasBorder.Child = canvasGrid;
            mainGrid.Children.Add(CanvasBorder);

            // Row 4: Status and Actions
            var statusBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(45, 45, 45)),
                Padding = new Thickness(8)
            };
            Grid.SetRow(statusBorder, 4);

            var statusGrid = new Grid();
            statusGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            statusGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var statusStack = new StackPanel { Orientation = Orientation.Horizontal };
            StatusText = new TextBlock
            {
                Foreground = new SolidColorBrush(Color.FromRgb(170, 170, 170)),
                VerticalAlignment = VerticalAlignment.Center,
                Text = "Ready. Draw to create walls in Revit.",
                FontSize = 11
            };
            statusStack.Children.Add(StatusText);
            Grid.SetColumn(statusStack, 0);
            statusGrid.Children.Add(statusStack);

            var buttonStack = new StackPanel { Orientation = Orientation.Horizontal };
            buttonStack.Children.Add(CreateButton("Undo", Undo_Click, 50));
            buttonStack.Children.Add(CreateButton("Clear", Clear_Click, 50));
            buttonStack.Children.Add(CreateButton("Load Image", LoadImage_Click, 80));
            buttonStack.Children.Add(CreateButton("Calibrate", CalibrateImage_Click, 65));
            buttonStack.Children.Add(CreateButton("3D View", Toggle3DView_Click, 60));
            buttonStack.Children.Add(CreateButton("Export JSON", ExportJSON_Click, 80));
            Grid.SetColumn(buttonStack, 1);
            statusGrid.Children.Add(buttonStack);

            statusBorder.Child = statusGrid;
            mainGrid.Children.Add(statusBorder);

            this.Content = mainGrid;
        }

        private RadioButton CreateRadioButton(string content, string groupName, bool isChecked)
        {
            // Get keyboard shortcut for this mode
            string shortcut = GetShortcutForMode(content);
            string tooltip = GetTooltipForMode(content);

            var rb = new RadioButton
            {
                Content = shortcut != null ? $"{content} ({shortcut})" : content,
                GroupName = groupName,
                IsChecked = isChecked,
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                Padding = new Thickness(8, 5, 8, 5),
                Margin = new Thickness(2),
                ToolTip = tooltip
            };
            rb.Checked += Mode_Changed;
            return rb;
        }

        private string GetShortcutForMode(string mode)
        {
            switch (mode)
            {
                case "Wall": return "W";
                case "Room": return "R";
                case "Door": return "D";
                case "Window": return "N";
                case "Roof": return null;
                case "Furniture": return "F";
                case "Fixture": return "X";
                case "Casework": return "C";
                case "Electrical": return "E";
                case "Dimension": return "M";
                case "Label": return "L";
                case "Select": return "S";
                default: return null;
            }
        }

        private string GetTooltipForMode(string mode)
        {
            switch (mode)
            {
                case "Wall": return "Draw walls by clicking start and end points.\nChain mode: continue from last endpoint.\nPress Esc to break chain.";
                case "Room": return "Draw closed room boundaries by clicking corners.\nDouble-click or press Enter to close.";
                case "Door": return "Click on a wall to place a door.\nDoors are placed at the click location along the wall.";
                case "Window": return "Click on a wall to place a window.\nWindows are placed at the click location along the wall.";
                case "Roof": return "Click corners to define roof outline.\nDouble-click to close and create roof.";
                case "Furniture": return "Click to place furniture at location.\nElements can be rotated after placement.";
                case "Fixture": return "Click to place plumbing fixtures (toilets, sinks, tubs).\nSelect type from dropdown.";
                case "Casework": return "Click to place cabinets and casework.\nBase cabinets snap to walls.";
                case "Electrical": return "Click to place electrical devices.\nIncludes outlets, switches, and lights.";
                case "Dimension": return "Click two points to measure and annotate distance.\nDimensions show in feet-inches format.";
                case "Label": return "Click to place a room label.\nEnter room name in the dialog.";
                case "Select": return "Click to select elements.\nDrag to move, Delete to remove.";
                default: return null;
            }
        }

        private Button CreateButton(string content, RoutedEventHandler handler, double width = 50)
        {
            var btn = new Button
            {
                Content = content,
                Width = width,
                Height = 30,
                Margin = new Thickness(2),
                Background = new SolidColorBrush(SketchPadColors.BgTertiary),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.BorderLight)
            };
            btn.Click += handler;
            return btn;
        }

        #region Initialization

        private void LoadLevels()
        {
            var levels = new FilteredElementCollector(_doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            LevelCombo.Items.Clear();
            foreach (var level in levels)
            {
                var item = new ComboBoxItem
                {
                    Content = $"{level.Name} ({level.Elevation:F1}')",
                    Tag = level.Id
                };
                LevelCombo.Items.Add(item);
            }

            if (LevelCombo.Items.Count > 0)
            {
                LevelCombo.SelectedIndex = 0;
                _currentLevelId = (LevelCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }
        }

        private void LoadWallTypes()
        {
            // Load ALL wall types from the model
            var wallTypes = new FilteredElementCollector(_doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .OrderBy(w => w.Name)
                .ToList();

            WallTypeCombo.Items.Clear();
            foreach (var wt in wallTypes)
            {
                var item = new ComboBoxItem
                {
                    Content = wt.Name,
                    Tag = wt.Id,
                    ToolTip = $"Width: {wt.Width * 12:F2}\""
                };
                WallTypeCombo.Items.Add(item);
            }

            if (WallTypeCombo.Items.Count > 0)
            {
                WallTypeCombo.SelectedIndex = 0;
                _currentWallTypeId = (WallTypeCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }

            StatusText.Text = $"Loaded {wallTypes.Count} wall types from model.";
        }

        private void LoadRoofTypes()
        {
            // Load all roof types from the model
            var roofTypes = new FilteredElementCollector(_doc)
                .OfClass(typeof(RoofType))
                .Cast<RoofType>()
                .OrderBy(r => r.Name)
                .ToList();

            RoofTypeCombo.Items.Clear();
            foreach (var rt in roofTypes)
            {
                var item = new ComboBoxItem
                {
                    Content = rt.Name,
                    Tag = rt.Id
                };
                RoofTypeCombo.Items.Add(item);
            }

            if (RoofTypeCombo.Items.Count > 0)
            {
                RoofTypeCombo.SelectedIndex = 0;
                _currentRoofTypeId = (RoofTypeCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }
        }

        private void LoadDoorTypes()
        {
            // Load all door family types from the model
            var doorTypes = new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .OrderBy(d => d.Family?.Name ?? "")
                .ThenBy(d => d.Name)
                .ToList();

            DoorTypeCombo.Items.Clear();
            foreach (var dt in doorTypes)
            {
                string familyName = dt.Family?.Name ?? "Unknown";
                var item = new ComboBoxItem
                {
                    Content = $"{familyName}: {dt.Name}",
                    Tag = dt.Id,
                    ToolTip = $"Family: {familyName}\nType: {dt.Name}"
                };
                DoorTypeCombo.Items.Add(item);
            }

            if (DoorTypeCombo.Items.Count > 0)
            {
                DoorTypeCombo.SelectedIndex = 0;
                _currentDoorTypeId = (DoorTypeCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }
        }

        private void LoadWindowTypes()
        {
            // Load all window family types from the model
            var windowTypes = new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .OrderBy(w => w.Family?.Name ?? "")
                .ThenBy(w => w.Name)
                .ToList();

            WindowTypeCombo.Items.Clear();
            foreach (var wt in windowTypes)
            {
                string familyName = wt.Family?.Name ?? "Unknown";
                var item = new ComboBoxItem
                {
                    Content = $"{familyName}: {wt.Name}",
                    Tag = wt.Id,
                    ToolTip = $"Family: {familyName}\nType: {wt.Name}"
                };
                WindowTypeCombo.Items.Add(item);
            }

            if (WindowTypeCombo.Items.Count > 0)
            {
                WindowTypeCombo.SelectedIndex = 0;
                _currentWindowTypeId = (WindowTypeCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }
        }

        private void LoadFurnitureTypes()
        {
            // Load all furniture family types from the model
            var furnitureTypes = new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_Furniture)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .OrderBy(f => f.Family?.Name ?? "")
                .ThenBy(f => f.Name)
                .ToList();

            FurnitureTypeCombo.Items.Clear();
            foreach (var ft in furnitureTypes)
            {
                string familyName = ft.Family?.Name ?? "Unknown";
                var item = new ComboBoxItem
                {
                    Content = $"{familyName}: {ft.Name}",
                    Tag = ft.Id,
                    ToolTip = $"Family: {familyName}\nType: {ft.Name}"
                };
                FurnitureTypeCombo.Items.Add(item);
            }

            if (FurnitureTypeCombo.Items.Count > 0)
            {
                FurnitureTypeCombo.SelectedIndex = 0;
                _currentFurnitureTypeId = (FurnitureTypeCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }
        }

        private void LoadFixtureTypes()
        {
            // Load all plumbing fixture family types from the model
            var fixtureTypes = new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_PlumbingFixtures)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .OrderBy(f => f.Family?.Name ?? "")
                .ThenBy(f => f.Name)
                .ToList();

            FixtureTypeCombo.Items.Clear();
            foreach (var ft in fixtureTypes)
            {
                string familyName = ft.Family?.Name ?? "Unknown";
                var item = new ComboBoxItem
                {
                    Content = $"{familyName}: {ft.Name}",
                    Tag = ft.Id,
                    ToolTip = $"Family: {familyName}\nType: {ft.Name}"
                };
                FixtureTypeCombo.Items.Add(item);
            }

            if (FixtureTypeCombo.Items.Count > 0)
            {
                FixtureTypeCombo.SelectedIndex = 0;
                _currentFixtureTypeId = (FixtureTypeCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }
        }

        private void LoadCaseworkTypes()
        {
            // Load all casework family types from the model
            var caseworkTypes = new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_Casework)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .OrderBy(c => c.Family?.Name ?? "")
                .ThenBy(c => c.Name)
                .ToList();

            CaseworkTypeCombo.Items.Clear();
            foreach (var ct in caseworkTypes)
            {
                string familyName = ct.Family?.Name ?? "Unknown";
                var item = new ComboBoxItem
                {
                    Content = $"{familyName}: {ct.Name}",
                    Tag = ct.Id,
                    ToolTip = $"Family: {familyName}\nType: {ct.Name}"
                };
                CaseworkTypeCombo.Items.Add(item);
            }

            if (CaseworkTypeCombo.Items.Count > 0)
            {
                CaseworkTypeCombo.SelectedIndex = 0;
                _currentCaseworkTypeId = (CaseworkTypeCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }
        }

        private void LoadElectricalTypes()
        {
            // Load all electrical fixture/device family types from the model
            // Combine electrical fixtures, lighting fixtures, and electrical equipment
            var electricalTypes = new List<FamilySymbol>();

            // Electrical Fixtures (outlets, switches)
            electricalTypes.AddRange(new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_ElectricalFixtures)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>());

            // Lighting Fixtures
            electricalTypes.AddRange(new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_LightingFixtures)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>());

            // Electrical Equipment (panels)
            electricalTypes.AddRange(new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_ElectricalEquipment)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>());

            electricalTypes = electricalTypes
                .OrderBy(e => e.Family?.Name ?? "")
                .ThenBy(e => e.Name)
                .ToList();

            ElectricalTypeCombo.Items.Clear();
            foreach (var et in electricalTypes)
            {
                string familyName = et.Family?.Name ?? "Unknown";
                string categoryName = et.Category?.Name ?? "Electrical";
                var item = new ComboBoxItem
                {
                    Content = $"{familyName}: {et.Name}",
                    Tag = et.Id,
                    ToolTip = $"Category: {categoryName}\nFamily: {familyName}\nType: {et.Name}"
                };
                ElectricalTypeCombo.Items.Add(item);
            }

            if (ElectricalTypeCombo.Items.Count > 0)
            {
                ElectricalTypeCombo.SelectedIndex = 0;
                _currentElectricalTypeId = (ElectricalTypeCombo.Items[0] as ComboBoxItem).Tag as ElementId;
            }
        }

        private void UpdateTypeOptionsVisibility()
        {
            // Show/hide type option panels based on current mode
            WallOptionsPanel.Visibility = (WallMode.IsChecked == true) ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
            RoofOptionsPanel.Visibility = (RoofMode.IsChecked == true) ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
            DoorOptionsPanel.Visibility = (DoorMode.IsChecked == true) ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
            WindowOptionsPanel.Visibility = (WindowMode.IsChecked == true) ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
            FurnitureOptionsPanel.Visibility = (FurnitureMode.IsChecked == true) ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
            FixtureOptionsPanel.Visibility = (FixtureMode.IsChecked == true) ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
            CaseworkOptionsPanel.Visibility = (CaseworkMode.IsChecked == true) ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
            ElectricalOptionsPanel.Visibility = (ElectricalMode.IsChecked == true) ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
        }

        private void DrawGrid()
        {
            GridCanvas.Children.Clear();

            double gridPixels = _gridSizeFeet * _scale;
            double width = CanvasBorder?.ActualWidth > 0 ? CanvasBorder.ActualWidth : 800;
            double height = CanvasBorder?.ActualHeight > 0 ? CanvasBorder.ActualHeight : 500;

            // Minor grid lines
            for (double x = _panOffset.X % gridPixels; x < width; x += gridPixels)
            {
                var line = new Line
                {
                    X1 = x, Y1 = 0,
                    X2 = x, Y2 = height,
                    Stroke = new SolidColorBrush(Color.FromRgb(40, 40, 40)),
                    StrokeThickness = 0.5
                };
                GridCanvas.Children.Add(line);
            }

            for (double y = _panOffset.Y % gridPixels; y < height; y += gridPixels)
            {
                var line = new Line
                {
                    X1 = 0, Y1 = y,
                    X2 = width, Y2 = y,
                    Stroke = new SolidColorBrush(Color.FromRgb(40, 40, 40)),
                    StrokeThickness = 0.5
                };
                GridCanvas.Children.Add(line);
            }

            // Major grid lines (every 5 grid units)
            double majorGridPixels = gridPixels * 5;
            for (double x = _panOffset.X % majorGridPixels; x < width; x += majorGridPixels)
            {
                var line = new Line
                {
                    X1 = x, Y1 = 0,
                    X2 = x, Y2 = height,
                    Stroke = new SolidColorBrush(Color.FromRgb(55, 55, 55)),
                    StrokeThickness = 1
                };
                GridCanvas.Children.Add(line);
            }

            for (double y = _panOffset.Y % majorGridPixels; y < height; y += majorGridPixels)
            {
                var line = new Line
                {
                    X1 = 0, Y1 = y,
                    X2 = width, Y2 = y,
                    Stroke = new SolidColorBrush(Color.FromRgb(55, 55, 55)),
                    StrokeThickness = 1
                };
                GridCanvas.Children.Add(line);
            }

            // Origin crosshairs (if visible)
            if (_panOffset.X > 0 && _panOffset.X < width)
            {
                var originV = new Line
                {
                    X1 = _panOffset.X, Y1 = 0,
                    X2 = _panOffset.X, Y2 = height,
                    Stroke = new SolidColorBrush(Color.FromRgb(80, 80, 80)),
                    StrokeThickness = 2
                };
                GridCanvas.Children.Add(originV);
            }

            if (_panOffset.Y > 0 && _panOffset.Y < height)
            {
                var originH = new Line
                {
                    X1 = 0, Y1 = _panOffset.Y,
                    X2 = width, Y2 = _panOffset.Y,
                    Stroke = new SolidColorBrush(Color.FromRgb(80, 80, 80)),
                    StrokeThickness = 2
                };
                GridCanvas.Children.Add(originH);
            }

            // Redraw all sketch elements at new scale/pan
            RedrawAllElements();
        }

        /// <summary>
        /// Redraws all walls, doors, windows, etc. at current scale and pan offset
        /// This ensures elements stay locked to world coordinates when zooming/panning
        /// </summary>
        private void RedrawAllElements()
        {
            // Clear only the drawn elements from DrawingCanvas (not markers)
            var elementsToRemove = DrawingCanvas.Children.OfType<FrameworkElement>()
                .Where(e => e.Tag is int || // Wall lines
                            e.Tag?.ToString() == "DoorMarker" ||
                            e.Tag?.ToString() == "WindowMarker" ||
                            e.Tag?.ToString() == "FurnitureMarker" ||
                            e.Tag?.ToString() == "FixtureMarker" ||
                            e.Tag?.ToString() == "CaseworkMarker" ||
                            e.Tag?.ToString() == "ElectricalMarker" ||
                            e.Tag?.ToString() == "DimensionGroup" ||
                            e.Tag?.ToString() == "RoomLabel")
                .ToList();

            foreach (var elem in elementsToRemove)
                DrawingCanvas.Children.Remove(elem);

            // Redraw walls from stored data
            for (int i = 0; i < _drawnWalls.Count; i++)
            {
                var wall = _drawnWalls[i];
                var startCanvas = WorldToCanvas(wall.StartX, wall.StartY);
                var endCanvas = WorldToCanvas(wall.EndX, wall.EndY);

                var wallLine = new Line
                {
                    X1 = startCanvas.X, Y1 = startCanvas.Y,
                    X2 = endCanvas.X, Y2 = endCanvas.Y,
                    Stroke = Brushes.Red,
                    StrokeThickness = 3,
                    Tag = i
                };
                DrawingCanvas.Children.Add(wallLine);
            }

            // Redraw doors
            foreach (var door in _placedDoors)
            {
                var doorCanvas = WorldToCanvas(door.X, door.Y);
                // Find the wall this door is on to get orientation
                var wallIndex = door.WallIndex;
                if (wallIndex >= 0 && wallIndex < _drawnWalls.Count)
                {
                    var wall = _drawnWalls[wallIndex];
                    var wallStart = WorldToCanvas(wall.StartX, wall.StartY);
                    var wallEnd = WorldToCanvas(wall.EndX, wall.EndY);
                    DrawDoorMarkerAtWorldPos(doorCanvas, wallStart, wallEnd);
                }
            }

            // Redraw windows
            foreach (var window in _placedWindows)
            {
                var windowCanvas = WorldToCanvas(window.X, window.Y);
                var wallIndex = window.WallIndex;
                if (wallIndex >= 0 && wallIndex < _drawnWalls.Count)
                {
                    var wall = _drawnWalls[wallIndex];
                    var wallStart = WorldToCanvas(wall.StartX, wall.StartY);
                    var wallEnd = WorldToCanvas(wall.EndX, wall.EndY);
                    DrawWindowMarkerAtWorldPos(windowCanvas, wallStart, wallEnd);
                }
            }

            // Redraw furniture
            foreach (var elem in _placedFurniture)
            {
                var canvasPos = WorldToCanvas(elem.X, elem.Y);
                DrawElementMarkerAtPos(canvasPos, "Furniture", elem.Rotation);
            }

            // Redraw fixtures
            foreach (var elem in _placedFixtures)
            {
                var canvasPos = WorldToCanvas(elem.X, elem.Y);
                DrawElementMarkerAtPos(canvasPos, "Fixture", elem.Rotation);
            }

            // Redraw casework
            foreach (var elem in _placedCasework)
            {
                var canvasPos = WorldToCanvas(elem.X, elem.Y);
                DrawElementMarkerAtPos(canvasPos, "Casework", elem.Rotation);
            }

            // Redraw electrical
            foreach (var elem in _placedElectrical)
            {
                var canvasPos = WorldToCanvas(elem.X, elem.Y);
                DrawElementMarkerAtPos(canvasPos, "Electrical", elem.Rotation);
            }

            // Redraw dimensions
            foreach (var dim in _drawnDimensions)
            {
                var p1 = WorldToCanvas(dim.X1, dim.Y1);
                var p2 = WorldToCanvas(dim.X2, dim.Y2);
                dim.VisualElement = DrawDimension(p1, p2, dim.Distance);
            }

            // Redraw room labels
            foreach (var label in _drawnRoomLabels)
            {
                var pos = WorldToCanvas(label.X, label.Y);
                label.VisualElement = DrawRoomLabel(pos, label.RoomName);
            }
        }

        /// <summary>
        /// Convert world coordinates (feet) to canvas coordinates (pixels)
        /// </summary>
        private Point WorldToCanvas(double xFeet, double yFeet)
        {
            double canvasX = xFeet * _scale + _panOffset.X;
            double canvasY = DrawingCanvas.ActualHeight - (yFeet * _scale) + _panOffset.Y;
            return new Point(canvasX, canvasY);
        }

        /// <summary>
        /// Convert canvas coordinates (pixels) to world coordinates (feet)
        /// </summary>
        private Point CanvasToWorld(Point canvasPoint)
        {
            double xFeet = (canvasPoint.X - _panOffset.X) / _scale;
            double yFeet = (DrawingCanvas.ActualHeight - canvasPoint.Y + _panOffset.Y) / _scale;
            return new Point(xFeet, yFeet);
        }

        /// <summary>
        /// Draw door marker at canvas position with wall orientation
        /// </summary>
        private void DrawDoorMarkerAtWorldPos(Point pos, Point wallStart, Point wallEnd)
        {
            double dx = wallEnd.X - wallStart.X;
            double dy = wallEnd.Y - wallStart.Y;
            double len = Math.Sqrt(dx * dx + dy * dy);
            if (len == 0) return;

            // Perpendicular direction for door swing
            double perpX = -dy / len * 15;
            double perpY = dx / len * 15;

            var swingLine = new Line
            {
                X1 = pos.X,
                Y1 = pos.Y,
                X2 = pos.X + perpX,
                Y2 = pos.Y + perpY,
                Stroke = Brushes.Lime,
                StrokeThickness = 2,
                Tag = "DoorMarker"
            };
            DrawingCanvas.Children.Add(swingLine);

            var doorRect = new Rectangle
            {
                Width = 16,
                Height = 4,
                Fill = Brushes.Lime,
                Tag = "DoorMarker"
            };

            double angle = Math.Atan2(dy, dx) * 180 / Math.PI;
            doorRect.RenderTransform = new RotateTransform(angle, 8, 2);
            Canvas.SetLeft(doorRect, pos.X - 8);
            Canvas.SetTop(doorRect, pos.Y - 2);
            DrawingCanvas.Children.Add(doorRect);
        }

        /// <summary>
        /// Draw window marker at canvas position with wall orientation
        /// </summary>
        private void DrawWindowMarkerAtWorldPos(Point pos, Point wallStart, Point wallEnd)
        {
            double dx = wallEnd.X - wallStart.X;
            double dy = wallEnd.Y - wallStart.Y;

            var windowRect = new Rectangle
            {
                Width = 20,
                Height = 6,
                Stroke = Brushes.DeepSkyBlue,
                StrokeThickness = 2,
                Fill = new SolidColorBrush(Color.FromArgb(100, 0, 191, 255)),
                Tag = "WindowMarker"
            };

            double angle = Math.Atan2(dy, dx) * 180 / Math.PI;
            windowRect.RenderTransform = new RotateTransform(angle, 10, 3);
            Canvas.SetLeft(windowRect, pos.X - 10);
            Canvas.SetTop(windowRect, pos.Y - 3);
            DrawingCanvas.Children.Add(windowRect);
        }

        /// <summary>
        /// Draw element marker (furniture, fixture, casework, electrical) at position
        /// </summary>
        private void DrawElementMarkerAtPos(Point pos, string category, double rotation)
        {
            SolidColorBrush markerColor;
            string tag;

            switch (category)
            {
                case "Furniture":
                    markerColor = Brushes.Orange;
                    tag = "FurnitureMarker";
                    break;
                case "Fixture":
                    markerColor = Brushes.DeepSkyBlue;
                    tag = "FixtureMarker";
                    break;
                case "Casework":
                    markerColor = new SolidColorBrush(Color.FromRgb(139, 90, 43)); // Brown
                    tag = "CaseworkMarker";
                    break;
                case "Electrical":
                    markerColor = Brushes.Yellow;
                    tag = "ElectricalMarker";
                    break;
                default:
                    markerColor = Brushes.Gray;
                    tag = "ElementMarker";
                    break;
            }

            // Draw a rotated rectangle to represent the element
            var rect = new Rectangle
            {
                Width = 20,
                Height = 16,
                Fill = markerColor,
                Stroke = Brushes.Black,
                StrokeThickness = 1,
                Tag = tag
            };

            rect.RenderTransform = new RotateTransform(rotation, 10, 8);
            Canvas.SetLeft(rect, pos.X - 10);
            Canvas.SetTop(rect, pos.Y - 8);
            DrawingCanvas.Children.Add(rect);

            // Add a direction indicator
            var dirLine = new Line
            {
                X1 = pos.X,
                Y1 = pos.Y,
                X2 = pos.X + 12 * Math.Cos(rotation * Math.PI / 180),
                Y2 = pos.Y - 12 * Math.Sin(rotation * Math.PI / 180),
                Stroke = Brushes.Black,
                StrokeThickness = 2,
                Tag = tag
            };
            DrawingCanvas.Children.Add(dirLine);
        }

        private void UpdateScaleIndicator()
        {
            // Calculate actual feet represented by the 50px indicator bar
            double indicatorFeet = 50.0 / _scale;

            // Round to nice values for cleaner display
            if (indicatorFeet >= 100)
                indicatorFeet = Math.Round(indicatorFeet / 50) * 50;
            else if (indicatorFeet >= 10)
                indicatorFeet = Math.Round(indicatorFeet / 5) * 5;
            else if (indicatorFeet >= 1)
                indicatorFeet = Math.Round(indicatorFeet);
            else
                indicatorFeet = Math.Round(indicatorFeet * 12) / 12; // Round to inches

            ScaleText.Text = FormatFeetInches(indicatorFeet);
        }

        #endregion

        #region Zoom and Pan

        private void ZoomIn_Click(object sender, RoutedEventArgs e)
        {
            _scale = Math.Min(_scale * 1.5, MAX_SCALE);
            DrawGrid();
            UpdateScaleIndicator();
            StatusText.Text = $"Zoom: {_scale:F1}x ({_scale * 10:F0} pixels = 10 ft)";
        }

        private void ZoomOut_Click(object sender, RoutedEventArgs e)
        {
            _scale = Math.Max(_scale / 1.5, MIN_SCALE);
            DrawGrid();
            UpdateScaleIndicator();
            StatusText.Text = $"Zoom: {_scale:F1}x ({_scale * 10:F0} pixels = 10 ft)";
        }

        private void ZoomFit_Click(object sender, RoutedEventArgs e)
        {
            // Calculate bounds of all drawn elements
            if (_drawnWalls.Count == 0)
            {
                StatusText.Text = "No walls to fit.";
                return;
            }

            double minX = _drawnWalls.Min(w => Math.Min(w.StartX, w.EndX));
            double maxX = _drawnWalls.Max(w => Math.Max(w.StartX, w.EndX));
            double minY = _drawnWalls.Min(w => Math.Min(w.StartY, w.EndY));
            double maxY = _drawnWalls.Max(w => Math.Max(w.StartY, w.EndY));

            double width = maxX - minX + 20; // Add padding
            double height = maxY - minY + 20;

            double canvasWidth = CanvasBorder.ActualWidth;
            double canvasHeight = CanvasBorder.ActualHeight;

            _scale = Math.Min(canvasWidth / width, canvasHeight / height);
            _scale = Math.Max(MIN_SCALE, Math.Min(_scale, MAX_SCALE));

            _panOffset = new Point(
                -minX * _scale + 10,
                -minY * _scale + 10
            );

            DrawGrid();
            UpdateScaleIndicator();
            StatusText.Text = $"Fit to content. Zoom: {_scale:F1}x";
        }

        private void ResetView_Click(object sender, RoutedEventArgs e)
        {
            _scale = 4.0;
            _panOffset = new Point(0, 0);
            DrawGrid();
            UpdateScaleIndicator();
            StatusText.Text = "View reset.";
        }

        private void Canvas_MouseWheel(object sender, MouseWheelEventArgs e)
        {
            var pos = e.GetPosition(DrawingCanvas);

            // Handle image zoom in image manipulation mode
            if (_imageManipulationMode && _backgroundImage != null)
            {
                if (e.Delta > 0)
                    _imageZoom = Math.Min(_imageZoom * 1.1, 10.0);
                else
                    _imageZoom = Math.Max(_imageZoom / 1.1, 0.1);

                ApplyImageTransform();
                StatusText.Text = $"Image zoom: {_imageZoom:P0}";
                e.Handled = true;
                return;
            }

            double oldScale = _scale;

            if (e.Delta > 0)
                _scale = Math.Min(_scale * 1.2, MAX_SCALE);
            else
                _scale = Math.Max(_scale / 1.2, MIN_SCALE);

            // Convert cursor position to world coordinates BEFORE scale change
            // Using the old scale
            double worldX = (pos.X - _panOffset.X) / oldScale;
            double canvasHeight = DrawingCanvas.ActualHeight > 0 ? DrawingCanvas.ActualHeight : 500;
            double worldY = (canvasHeight - pos.Y + _panOffset.Y) / oldScale;

            // After scale change, calculate new pan offset to keep cursor at same world position
            // newPanX = pos.X - worldX * newScale
            // newPanY = canvasHeight - pos.Y - worldY * newScale + panOffset (rearranged)
            // Actually for Y: pos.Y = canvasHeight - worldY * scale + panOffset.Y
            // So: panOffset.Y = pos.Y - canvasHeight + worldY * scale
            _panOffset = new Point(
                pos.X - worldX * _scale,
                pos.Y - canvasHeight + worldY * _scale
            );

            DrawGrid();
            UpdateScaleIndicator();
        }

        private void Canvas_PreviewMouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Middle)
            {
                _isPanning = true;
                _panStart = e.GetPosition(DrawingCanvas);
                DrawingCanvas.CaptureMouse();
                DrawingCanvas.Cursor = Cursors.ScrollAll;
                e.Handled = true;
            }
        }

        private void Canvas_PreviewMouseUp(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Middle)
            {
                _isPanning = false;
                DrawingCanvas.ReleaseMouseCapture();
                DrawingCanvas.Cursor = Cursors.Cross;
                e.Handled = true;
            }
        }

        #endregion

        #region Drawing

        private void Canvas_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            var pos = e.GetPosition(DrawingCanvas);

            // Handle calibration mode - takes priority
            if (_calibrationMode)
            {
                HandleCalibrationClick(pos);
                return;
            }

            // Handle image manipulation mode - start dragging
            if (_imageManipulationMode && _backgroundImage != null)
            {
                _isDraggingImage = true;
                _imageDragStart = pos;
                DrawingCanvas.CaptureMouse();
                return;
            }

            // Handle delete mode
            if (_deleteMode)
            {
                DeleteElementAtPosition(pos);
                return;
            }

            // Handle door placement - click on a wall to place door
            if (DoorMode.IsChecked == true)
            {
                PlaceDoorOnWall(pos);
                return;
            }

            // Handle window placement - click on a wall to place window
            if (WindowMode.IsChecked == true)
            {
                PlaceWindowOnWall(pos);
                return;
            }

            // Handle furniture placement - click to place at location
            if (FurnitureMode.IsChecked == true)
            {
                PlaceElement(pos, "Furniture", _currentFurnitureTypeId);
                return;
            }

            // Handle fixture placement - click to place plumbing fixture
            if (FixtureMode.IsChecked == true)
            {
                PlaceElement(pos, "Fixture", _currentFixtureTypeId);
                return;
            }

            // Handle casework placement - click to place cabinet
            if (CaseworkMode.IsChecked == true)
            {
                PlaceElement(pos, "Casework", _currentCaseworkTypeId);
                return;
            }

            // Handle electrical device placement - click to place device
            if (ElectricalMode.IsChecked == true)
            {
                PlaceElement(pos, "Electrical", _currentElectricalTypeId);
                return;
            }

            // Handle dimension mode - click two points to measure
            if (DimensionMode.IsChecked == true)
            {
                HandleDimensionClick(pos);
                return;
            }

            // Handle room label mode - click to place room label
            if (RoomLabelMode.IsChecked == true)
            {
                PlaceRoomLabel(pos);
                return;
            }

            // Handle select mode - click to select an element
            if (SelectMode.IsChecked == true)
            {
                HandleSelectionClick(pos, e);
                return;
            }

            pos = SnapToGrid(pos);

            if (RoofMode.IsChecked == true)
            {
                // Roof drawing - collect points
                _roofPoints.Add(pos);
                AddRoofMarker(pos);

                if (_roofPoints.Count > 1)
                {
                    // Draw line between last two points
                    AddRoofLine(_roofPoints[_roofPoints.Count - 2], pos);
                }

                StatusText.Text = $"Roof: {_roofPoints.Count} points. Right-click to finish.";
                return;
            }

            _isDrawing = true;

            // Chain mode: Start from last wall endpoint if available
            if (_chainMode && _lastWallEndPoint.HasValue && WallMode.IsChecked == true)
            {
                _startPoint = _lastWallEndPoint.Value;
            }
            else
            {
                _startPoint = pos;
            }

            // Show measurement overlay
            ShowMeasurement(true);

            // Create preview line
            _previewLine = new Line
            {
                X1 = pos.X, Y1 = pos.Y,
                X2 = pos.X, Y2 = pos.Y,
                Stroke = Brushes.Cyan,
                StrokeThickness = 2,
                StrokeDashArray = new DoubleCollection { 4, 2 }
            };
            DrawingCanvas.Children.Add(_previewLine);

            InstructionText.Visibility = System.Windows.Visibility.Collapsed;
        }

        private void Canvas_MouseMove(object sender, MouseEventArgs e)
        {
            var pos = e.GetPosition(DrawingCanvas);

            // Handle calibration mode - update preview line
            if (_calibrationMode && _calibrationStart.HasValue && _calibrationLine != null)
            {
                _calibrationLine.X2 = pos.X;
                _calibrationLine.Y2 = pos.Y;

                // Show pixel distance while drawing
                double pixelDist = Distance(_calibrationStart.Value, pos);
                StatusText.Text = $"CALIBRATION: {pixelDist:F0} pixels - click to set end point";
                return;
            }

            // Handle image dragging in image manipulation mode
            if (_isDraggingImage && _imageManipulationMode)
            {
                HandleImageDrag(pos);
                return;
            }

            // Handle panning
            if (_isPanning)
            {
                var delta = new Point(pos.X - _panStart.X, pos.Y - _panStart.Y);
                _panOffset = new Point(_panOffset.X + delta.X, _panOffset.Y + delta.Y);
                _panStart = pos;
                DrawGrid();
                return;
            }

            // Handle box selection dragging
            if (_isBoxSelecting)
            {
                UpdateBoxSelection(pos);
                return;
            }

            // Update coordinate display
            UpdateCoordinateDisplay(pos);

            if (!_isDrawing || _previewLine == null) return;

            pos = SnapToGrid(pos);
            if (_orthoMode)
                pos = Straighten(_startPoint, pos);

            _previewLine.X2 = pos.X;
            _previewLine.Y2 = pos.Y;

            // Show length in measurement overlay and status
            double lengthFeet = Distance(_startPoint, pos) / _scale;
            UpdateMeasurement(lengthFeet);
            StatusText.Text = $"Length: {FormatFeetInches(lengthFeet)}";
        }

        private void Canvas_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            // Stop image dragging if active
            if (_isDraggingImage)
            {
                _isDraggingImage = false;
                DrawingCanvas.ReleaseMouseCapture();
                StatusText.Text = "Image position saved. Press I to exit image mode.";
                return;
            }

            // Complete box selection if active
            if (_isBoxSelecting)
            {
                var endPos = e.GetPosition(DrawingCanvas);
                CompleteBoxSelection(endPos);
                DrawingCanvas.ReleaseMouseCapture();
                return;
            }

            if (!_isDrawing) return;
            _isDrawing = false;

            // Hide measurement overlay
            ShowMeasurement(false);

            var endPoint = e.GetPosition(DrawingCanvas);
            endPoint = SnapToGrid(endPoint);
            if (_orthoMode)
                endPoint = Straighten(_startPoint, endPoint);

            // Remove preview line
            if (_previewLine != null)
            {
                DrawingCanvas.Children.Remove(_previewLine);
                _previewLine = null;
            }

            // Check minimum length
            double lengthFeet = Distance(_startPoint, endPoint) / _scale;
            if (lengthFeet < 1)
            {
                StatusText.Text = "Wall too short (min 1 ft). Try again.";
                _lastWallEndPoint = null; // Reset chain on invalid wall
                return;
            }

            // Create the wall in Revit immediately!
            CreateWallInRevit(_startPoint, endPoint);

            // Chain mode: Save endpoint for next wall
            if (_chainMode && WallMode.IsChecked == true)
            {
                _lastWallEndPoint = endPoint;
                StatusText.Text = $"Wall created ({FormatFeetInches(lengthFeet)}). Click to continue chain, Esc to break.";
            }
        }

        private void Canvas_MouseRightButtonDown(object sender, MouseButtonEventArgs e)
        {
            // Finish roof drawing
            if (RoofMode.IsChecked == true && _roofPoints.Count >= 3)
            {
                CreateRoofInRevit();
                _roofPoints.Clear();
                ClearRoofMarkers();
                StatusText.Text = "Roof created!";
                return;
            }

            // Rotate element in placement modes (furniture, fixture, casework, electrical)
            if (FurnitureMode.IsChecked == true || FixtureMode.IsChecked == true ||
                CaseworkMode.IsChecked == true || ElectricalMode.IsChecked == true)
            {
                _elementRotation = (_elementRotation + 90) % 360;
                StatusText.Text = $"Element rotation: {_elementRotation}°. Click to place.";
                return;
            }
        }

        private void UpdateCoordinateDisplay(Point pos)
        {
            // Convert screen position to Revit coordinates
            double xFeet = (pos.X - _panOffset.X) / _scale;
            double yFeet = (DrawingCanvas.ActualHeight - pos.Y + _panOffset.Y) / _scale;
            CoordinateText.Text = $"X: {xFeet:F1}  Y: {yFeet:F1}";
        }

        private void ShowMeasurement(bool show)
        {
            var measureBorder = DrawingCanvas.Parent is Grid grid
                ? grid.Children.OfType<Border>().FirstOrDefault(b => b.Tag?.ToString() == "MeasurementBorder")
                : null;

            if (measureBorder != null)
                measureBorder.Visibility = show ? System.Windows.Visibility.Visible : System.Windows.Visibility.Collapsed;
        }

        private void UpdateMeasurement(double lengthFeet)
        {
            MeasurementText.Text = FormatFeetInches(lengthFeet);
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

        private void DeleteElementAtPosition(Point pos)
        {
            // Find the closest wall line to the click position
            var wallLines = DrawingCanvas.Children.OfType<Line>()
                .Where(l => l.Tag is int)
                .ToList();

            Line closestLine = null;
            double minDist = 10; // 10 pixel tolerance

            foreach (var line in wallLines)
            {
                double dist = DistanceToLine(pos, new Point(line.X1, line.Y1), new Point(line.X2, line.Y2));
                if (dist < minDist)
                {
                    minDist = dist;
                    closestLine = line;
                }
            }

            if (closestLine != null && closestLine.Tag is int wallIndex)
            {
                // Remove from canvas
                DrawingCanvas.Children.Remove(closestLine);

                // Remove from drawn walls list
                if (wallIndex >= 0 && wallIndex < _drawnWalls.Count)
                {
                    var wall = _drawnWalls[wallIndex];
                    _drawnWalls.RemoveAt(wallIndex);

                    // Delete from Revit if it has an element ID
                    if (wall.RevitElementId.HasValue)
                    {
                        try
                        {
                            var elemId = new ElementId(wall.RevitElementId.Value);
                            using (var trans = new Transaction(_doc, "Delete SketchPad Wall"))
                            {
                                trans.Start();
                                _doc.Delete(elemId);
                                trans.Commit();
                            }
                            StatusText.Text = "Wall deleted from Revit.";
                        }
                        catch (Exception ex)
                        {
                            StatusText.Text = $"Delete failed: {ex.Message}";
                        }
                    }
                }
            }
            else
            {
                StatusText.Text = "No wall found at click location.";
            }
        }

        private double DistanceToLine(Point p, Point a, Point b)
        {
            double dx = b.X - a.X;
            double dy = b.Y - a.Y;
            double len2 = dx * dx + dy * dy;

            if (len2 == 0) return Distance(p, a);

            double t = Math.Max(0, Math.Min(1, ((p.X - a.X) * dx + (p.Y - a.Y) * dy) / len2));
            var projection = new Point(a.X + t * dx, a.Y + t * dy);
            return Distance(p, projection);
        }

        #endregion

        #region Snap and Straighten

        /// <summary>
        /// Snap to grid OR to existing wall endpoints if within tolerance
        /// </summary>
        private Point SnapToGrid(Point pos)
        {
            // First, try to snap to existing wall endpoints
            if (_snapToEndpoints && _drawnWalls.Count > 0)
            {
                Point? snapPoint = FindNearestEndpoint(pos);
                if (snapPoint.HasValue)
                {
                    return snapPoint.Value;
                }
            }

            // Fall back to grid snap
            double gridPixels = _gridSizeFeet * _scale;
            return new Point(
                Math.Round(pos.X / gridPixels) * gridPixels,
                Math.Round(pos.Y / gridPixels) * gridPixels
            );
        }

        /// <summary>
        /// Find the nearest wall endpoint within snap tolerance
        /// </summary>
        private Point? FindNearestEndpoint(Point canvasPos)
        {
            double snapTolerancePixels = _snapToleranceFeet * _scale;
            Point? nearestPoint = null;
            double minDistance = snapTolerancePixels;

            foreach (var wall in _drawnWalls)
            {
                // Check start point
                var startCanvas = WorldToCanvas(wall.StartX, wall.StartY);
                double distToStart = Distance(canvasPos, startCanvas);
                if (distToStart < minDistance)
                {
                    minDistance = distToStart;
                    nearestPoint = startCanvas;
                }

                // Check end point
                var endCanvas = WorldToCanvas(wall.EndX, wall.EndY);
                double distToEnd = Distance(canvasPos, endCanvas);
                if (distToEnd < minDistance)
                {
                    minDistance = distToEnd;
                    nearestPoint = endCanvas;
                }
            }

            return nearestPoint;
        }

        /// <summary>
        /// Get all wall endpoints for snapping - returns points in world coordinates (feet)
        /// </summary>
        private List<Point> GetAllWallEndpoints()
        {
            var endpoints = new List<Point>();
            foreach (var wall in _drawnWalls)
            {
                endpoints.Add(new Point(wall.StartX, wall.StartY));
                endpoints.Add(new Point(wall.EndX, wall.EndY));
            }
            return endpoints;
        }

        private Point Straighten(Point start, Point end)
        {
            double dx = Math.Abs(end.X - start.X);
            double dy = Math.Abs(end.Y - start.Y);

            // If nearly horizontal, make exactly horizontal
            if (dy < dx * 0.2)
                return new Point(end.X, start.Y);

            // If nearly vertical, make exactly vertical
            if (dx < dy * 0.2)
                return new Point(start.X, end.Y);

            return end;
        }

        private double Distance(Point p1, Point p2)
        {
            return Math.Sqrt(Math.Pow(p2.X - p1.X, 2) + Math.Pow(p2.Y - p1.Y, 2));
        }

        #endregion

        #region Revit Element Creation

        private void CreateWallInRevit(Point start, Point end)
        {
            // Convert canvas coordinates to Revit coordinates
            // Canvas Y increases downward, Revit Y increases upward
            double startX = (start.X - _panOffset.X) / _scale;
            double startY = (DrawingCanvas.ActualHeight - start.Y + _panOffset.Y) / _scale;
            double endX = (end.X - _panOffset.X) / _scale;
            double endY = (DrawingCanvas.ActualHeight - end.Y + _panOffset.Y) / _scale;

            // Get level and wall type names for export
            string levelName = (LevelCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Unknown";
            string wallTypeName = (WallTypeCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Unknown";

            // Add to drawn walls list
            int wallIndex = _drawnWalls.Count;
            var drawnWall = new DrawnWall
            {
                StartX = startX,
                StartY = startY,
                EndX = endX,
                EndY = endY,
                Height = _wallHeight,
                LevelName = levelName,
                WallTypeName = wallTypeName,
                RevitElementId = null // Will be set by handler
            };
            _drawnWalls.Add(drawnWall);

            // Queue the wall creation
            _createWallHandler.SetWallData(
                _doc,
                startX, startY,
                endX, endY,
                _currentLevelId,
                _currentWallTypeId,
                _wallHeight
            );
            _createWallHandler.WallIndex = wallIndex;
            _createWallHandler.DrawnWalls = _drawnWalls;

            // Trigger external event
            _externalEvent.Raise();

            // Draw the wall on canvas with wall index as tag
            var wallLine = new Line
            {
                X1 = start.X, Y1 = start.Y,
                X2 = end.X, Y2 = end.Y,
                Stroke = WallMode.IsChecked == true ? Brushes.Red : Brushes.Blue,
                StrokeThickness = 3,
                Tag = wallIndex
            };
            DrawingCanvas.Children.Add(wallLine);
            _canvasElements.Push(wallLine);

            // Update 3D view if visible
            Update3DWalls();

            double lengthFeet = Distance(start, end) / _scale;
            StatusText.Text = $"Wall created: {FormatFeetInches(lengthFeet)} (Height: {_wallHeight:F0} ft)";
        }

        private void CreateRoofInRevit()
        {
            // Convert roof points to Revit coordinates and create roof
            // This would need a more complex implementation
            StatusText.Text = "Roof outline captured. Full roof creation coming soon.";
        }

        private void PlaceDoorOnWall(Point clickPos)
        {
            // Find the closest wall to the click position
            var wallLines = DrawingCanvas.Children.OfType<Line>()
                .Where(l => l.Tag is int)
                .ToList();

            Line closestLine = null;
            int closestWallIndex = -1;
            double minDist = 15; // 15 pixel tolerance
            Point projectionPoint = clickPos;

            foreach (var line in wallLines)
            {
                Point lineStart = new Point(line.X1, line.Y1);
                Point lineEnd = new Point(line.X2, line.Y2);
                double dist = DistanceToLine(clickPos, lineStart, lineEnd);

                if (dist < minDist && line.Tag is int wallIndex)
                {
                    minDist = dist;
                    closestLine = line;
                    closestWallIndex = wallIndex;
                    projectionPoint = ProjectPointOnLine(clickPos, lineStart, lineEnd);
                }
            }

            if (closestLine == null || closestWallIndex < 0 || closestWallIndex >= _drawnWalls.Count)
            {
                StatusText.Text = "No wall found. Click on a wall to place a door.";
                return;
            }

            var wall = _drawnWalls[closestWallIndex];

            // Check if wall has a Revit element ID
            if (!wall.RevitElementId.HasValue)
            {
                StatusText.Text = "Wall not yet created in Revit. Please wait and try again.";
                return;
            }

            // Convert projection point to Revit coordinates
            double doorX = (projectionPoint.X - _panOffset.X) / _scale;
            double doorY = (DrawingCanvas.ActualHeight - projectionPoint.Y + _panOffset.Y) / _scale;

            // Get door type name
            string doorTypeName = (DoorTypeCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Unknown";

            // Add to placed doors list
            var placedDoor = new PlacedOpening
            {
                X = doorX,
                Y = doorY,
                WallIndex = closestWallIndex,
                TypeName = doorTypeName,
                RevitWallId = wall.RevitElementId
            };
            _placedDoors.Add(placedDoor);

            // Queue the door creation in Revit
            _createDoorHandler.SetDoorData(
                _doc,
                doorX, doorY,
                new ElementId(wall.RevitElementId.Value),
                _currentDoorTypeId,
                _currentLevelId
            );
            _createDoorHandler.PlacedDoors = _placedDoors;
            _createDoorHandler.DoorIndex = _placedDoors.Count - 1;

            _doorExternalEvent.Raise();

            // Draw door marker on canvas
            DrawDoorMarker(projectionPoint, closestLine);

            StatusText.Text = $"Door placed: {doorTypeName}";
        }

        private void PlaceWindowOnWall(Point clickPos)
        {
            // Find the closest wall to the click position
            var wallLines = DrawingCanvas.Children.OfType<Line>()
                .Where(l => l.Tag is int)
                .ToList();

            Line closestLine = null;
            int closestWallIndex = -1;
            double minDist = 15; // 15 pixel tolerance
            Point projectionPoint = clickPos;

            foreach (var line in wallLines)
            {
                Point lineStart = new Point(line.X1, line.Y1);
                Point lineEnd = new Point(line.X2, line.Y2);
                double dist = DistanceToLine(clickPos, lineStart, lineEnd);

                if (dist < minDist && line.Tag is int wallIndex)
                {
                    minDist = dist;
                    closestLine = line;
                    closestWallIndex = wallIndex;
                    projectionPoint = ProjectPointOnLine(clickPos, lineStart, lineEnd);
                }
            }

            if (closestLine == null || closestWallIndex < 0 || closestWallIndex >= _drawnWalls.Count)
            {
                StatusText.Text = "No wall found. Click on a wall to place a window.";
                return;
            }

            var wall = _drawnWalls[closestWallIndex];

            // Check if wall has a Revit element ID
            if (!wall.RevitElementId.HasValue)
            {
                StatusText.Text = "Wall not yet created in Revit. Please wait and try again.";
                return;
            }

            // Convert projection point to Revit coordinates
            double windowX = (projectionPoint.X - _panOffset.X) / _scale;
            double windowY = (DrawingCanvas.ActualHeight - projectionPoint.Y + _panOffset.Y) / _scale;

            // Get window type name
            string windowTypeName = (WindowTypeCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Unknown";

            // Add to placed windows list
            var placedWindow = new PlacedOpening
            {
                X = windowX,
                Y = windowY,
                WallIndex = closestWallIndex,
                TypeName = windowTypeName,
                RevitWallId = wall.RevitElementId
            };
            _placedWindows.Add(placedWindow);

            // Queue the window creation in Revit
            _createWindowHandler.SetWindowData(
                _doc,
                windowX, windowY,
                new ElementId(wall.RevitElementId.Value),
                _currentWindowTypeId,
                _currentLevelId
            );
            _createWindowHandler.PlacedWindows = _placedWindows;
            _createWindowHandler.WindowIndex = _placedWindows.Count - 1;

            _windowExternalEvent.Raise();

            // Draw window marker on canvas
            DrawWindowMarker(projectionPoint, closestLine);

            StatusText.Text = $"Window placed: {windowTypeName}";
        }

        private Point ProjectPointOnLine(Point p, Point lineStart, Point lineEnd)
        {
            double dx = lineEnd.X - lineStart.X;
            double dy = lineEnd.Y - lineStart.Y;
            double len2 = dx * dx + dy * dy;

            if (len2 == 0) return lineStart;

            double t = Math.Max(0, Math.Min(1, ((p.X - lineStart.X) * dx + (p.Y - lineStart.Y) * dy) / len2));
            return new Point(lineStart.X + t * dx, lineStart.Y + t * dy);
        }

        private double _elementRotation = 0; // Current rotation for elements (degrees)

        private void PlaceElement(Point clickPos, string category, ElementId typeId)
        {
            if (typeId == null || typeId == ElementId.InvalidElementId)
            {
                StatusText.Text = $"No {category.ToLower()} type selected.";
                return;
            }

            // Convert click position to Revit coordinates
            double elemX = (clickPos.X - _panOffset.X) / _scale;
            double elemY = (DrawingCanvas.ActualHeight - clickPos.Y + _panOffset.Y) / _scale;

            // Get the type name
            string typeName = "";
            switch (category)
            {
                case "Furniture":
                    typeName = (FurnitureTypeCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Unknown";
                    break;
                case "Fixture":
                    typeName = (FixtureTypeCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Unknown";
                    break;
                case "Casework":
                    typeName = (CaseworkTypeCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Unknown";
                    break;
                case "Electrical":
                    typeName = (ElectricalTypeCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Unknown";
                    break;
            }

            // Get the appropriate list
            List<PlacedElement> targetList = null;
            switch (category)
            {
                case "Furniture": targetList = _placedFurniture; break;
                case "Fixture": targetList = _placedFixtures; break;
                case "Casework": targetList = _placedCasework; break;
                case "Electrical": targetList = _placedElectrical; break;
            }

            // Create placed element record
            var placedElement = new PlacedElement
            {
                X = elemX,
                Y = elemY,
                Rotation = _elementRotation,
                CategoryName = category,
                FamilyName = typeName.Split(':')[0].Trim(),
                TypeName = typeName.Contains(":") ? typeName.Split(':')[1].Trim() : typeName
            };
            targetList?.Add(placedElement);

            // Queue the element creation in Revit
            _createElementHandler.SetElementData(_doc, elemX, elemY, _elementRotation, typeId, _currentLevelId, category);
            _createElementHandler.PlacedElements = targetList;
            _createElementHandler.ElementIndex = (targetList?.Count ?? 1) - 1;

            _elementExternalEvent.Raise();

            // Draw marker on canvas
            DrawElementMarker(clickPos, category);

            StatusText.Text = $"{category} placed: {typeName}";
        }

        private void DrawElementMarker(Point pos, string category)
        {
            Color markerColor;
            string tag;

            switch (category)
            {
                case "Furniture":
                    markerColor = Color.FromRgb(255, 165, 0); // Orange
                    tag = "FurnitureMarker";
                    break;
                case "Fixture":
                    markerColor = Color.FromRgb(0, 191, 255); // Deep sky blue
                    tag = "FixtureMarker";
                    break;
                case "Casework":
                    markerColor = Color.FromRgb(139, 69, 19); // Saddle brown
                    tag = "CaseworkMarker";
                    break;
                case "Electrical":
                    markerColor = Color.FromRgb(255, 255, 0); // Yellow
                    tag = "ElectricalMarker";
                    break;
                default:
                    markerColor = Colors.Gray;
                    tag = "ElementMarker";
                    break;
            }

            // Draw a rectangle marker for the element
            var rect = new Rectangle
            {
                Width = 16,
                Height = 16,
                Fill = new SolidColorBrush(Color.FromArgb(150, markerColor.R, markerColor.G, markerColor.B)),
                Stroke = new SolidColorBrush(markerColor),
                StrokeThickness = 2,
                Tag = tag
            };

            // Apply rotation if any
            if (_elementRotation != 0)
            {
                rect.RenderTransform = new RotateTransform(_elementRotation, 8, 8);
            }

            Canvas.SetLeft(rect, pos.X - 8);
            Canvas.SetTop(rect, pos.Y - 8);
            DrawingCanvas.Children.Add(rect);

            // Add category letter in center
            var label = new System.Windows.Controls.TextBlock
            {
                Text = category.Substring(0, 1), // First letter (F, C, E)
                FontSize = 10,
                FontWeight = FontWeights.Bold,
                Foreground = Brushes.White,
                Tag = tag
            };

            Canvas.SetLeft(label, pos.X - 4);
            Canvas.SetTop(label, pos.Y - 7);
            DrawingCanvas.Children.Add(label);
        }

        private void DrawDoorMarker(Point pos, Line wallLine)
        {
            // Calculate door orientation (perpendicular to wall)
            double dx = wallLine.X2 - wallLine.X1;
            double dy = wallLine.Y2 - wallLine.Y1;
            double len = Math.Sqrt(dx * dx + dy * dy);
            double perpX = -dy / len * 10; // 10 pixel offset
            double perpY = dx / len * 10;

            // Draw door arc symbol
            var doorArc = new System.Windows.Shapes.Path
            {
                Stroke = Brushes.Lime,
                StrokeThickness = 2,
                Tag = "DoorMarker"
            };

            // Create arc geometry
            var pathGeom = new PathGeometry();
            var figure = new PathFigure { StartPoint = new Point(pos.X - 8, pos.Y) };
            figure.Segments.Add(new ArcSegment(
                new Point(pos.X + 8, pos.Y),
                new System.Windows.Size(8, 8),
                0,
                false,
                SweepDirection.Clockwise,
                true
            ));
            pathGeom.Figures.Add(figure);
            doorArc.Data = pathGeom;

            DrawingCanvas.Children.Add(doorArc);

            // Draw door swing line
            var swingLine = new Line
            {
                X1 = pos.X,
                Y1 = pos.Y,
                X2 = pos.X + perpX,
                Y2 = pos.Y + perpY,
                Stroke = Brushes.Lime,
                StrokeThickness = 2,
                Tag = "DoorMarker"
            };
            DrawingCanvas.Children.Add(swingLine);

            // Draw door rectangle
            var doorRect = new Rectangle
            {
                Width = 16,
                Height = 4,
                Fill = Brushes.Lime,
                Tag = "DoorMarker"
            };

            // Rotate to align with wall
            double angle = Math.Atan2(dy, dx) * 180 / Math.PI;
            doorRect.RenderTransform = new RotateTransform(angle, 8, 2);
            Canvas.SetLeft(doorRect, pos.X - 8);
            Canvas.SetTop(doorRect, pos.Y - 2);
            DrawingCanvas.Children.Add(doorRect);
        }

        private void DrawWindowMarker(Point pos, Line wallLine)
        {
            // Calculate window orientation
            double dx = wallLine.X2 - wallLine.X1;
            double dy = wallLine.Y2 - wallLine.Y1;

            // Draw window symbol (two parallel lines)
            var windowRect = new Rectangle
            {
                Width = 20,
                Height = 6,
                Stroke = Brushes.DeepSkyBlue,
                StrokeThickness = 2,
                Fill = new SolidColorBrush(Color.FromArgb(100, 0, 191, 255)),
                Tag = "WindowMarker"
            };

            double angle = Math.Atan2(dy, dx) * 180 / Math.PI;
            windowRect.RenderTransform = new RotateTransform(angle, 10, 3);
            Canvas.SetLeft(windowRect, pos.X - 10);
            Canvas.SetTop(windowRect, pos.Y - 3);
            DrawingCanvas.Children.Add(windowRect);

            // Draw center line
            var centerLine = new Line
            {
                X1 = pos.X - 10 * Math.Cos(angle * Math.PI / 180),
                Y1 = pos.Y - 10 * Math.Sin(angle * Math.PI / 180),
                X2 = pos.X + 10 * Math.Cos(angle * Math.PI / 180),
                Y2 = pos.Y + 10 * Math.Sin(angle * Math.PI / 180),
                Stroke = Brushes.DeepSkyBlue,
                StrokeThickness = 1,
                Tag = "WindowMarker"
            };
            DrawingCanvas.Children.Add(centerLine);
        }

        private void AddRoofMarker(Point pos)
        {
            var marker = new Ellipse
            {
                Width = 8,
                Height = 8,
                Fill = Brushes.Orange,
                Tag = "RoofMarker"
            };
            Canvas.SetLeft(marker, pos.X - 4);
            Canvas.SetTop(marker, pos.Y - 4);
            DrawingCanvas.Children.Add(marker);
        }

        private void AddRoofLine(Point p1, Point p2)
        {
            var line = new Line
            {
                X1 = p1.X, Y1 = p1.Y,
                X2 = p2.X, Y2 = p2.Y,
                Stroke = Brushes.Orange,
                StrokeThickness = 2,
                Tag = "RoofLine"
            };
            DrawingCanvas.Children.Add(line);
        }

        private void ClearRoofMarkers()
        {
            var toRemove = DrawingCanvas.Children.OfType<FrameworkElement>()
                .Where(e => e.Tag?.ToString() == "RoofMarker" || e.Tag?.ToString() == "RoofLine")
                .ToList();
            foreach (var elem in toRemove)
                DrawingCanvas.Children.Remove(elem);
        }

        #endregion

        #region UI Handlers

        private void Mode_Changed(object sender, RoutedEventArgs e)
        {
            // Update type options panel visibility based on selected mode
            UpdateTypeOptionsVisibility();

            if (RoofMode.IsChecked == true)
            {
                StatusText.Text = "Roof mode: Click to add outline points. Right-click to finish.";
                _roofPoints.Clear();
            }
            else if (WallMode.IsChecked == true)
            {
                StatusText.Text = "Wall mode: Click and drag to draw walls.";
                ClearRoofMarkers();
            }
            else if (DoorMode.IsChecked == true)
            {
                StatusText.Text = "Door mode: Click on a wall to place a door.";
                ClearRoofMarkers();
            }
            else if (WindowMode.IsChecked == true)
            {
                StatusText.Text = "Window mode: Click on a wall to place a window.";
                ClearRoofMarkers();
            }
            else if (RoomMode.IsChecked == true)
            {
                StatusText.Text = "Room mode: Click inside an enclosed area to create a room.";
                ClearRoofMarkers();
            }
            else if (FurnitureMode.IsChecked == true)
            {
                StatusText.Text = "Furniture mode: Click to place furniture. Right-click to rotate.";
                ClearRoofMarkers();
            }
            else if (FixtureMode.IsChecked == true)
            {
                StatusText.Text = "Fixture mode: Click to place plumbing fixtures (toilets, sinks, tubs).";
                ClearRoofMarkers();
            }
            else if (CaseworkMode.IsChecked == true)
            {
                StatusText.Text = "Casework mode: Click to place cabinets. Right-click to rotate.";
                ClearRoofMarkers();
            }
            else if (ElectricalMode.IsChecked == true)
            {
                StatusText.Text = "Electrical mode: Click to place electrical devices (outlets, lights, panels).";
                ClearRoofMarkers();
            }
            else if (DimensionMode.IsChecked == true)
            {
                StatusText.Text = "Dimension mode: Click two points to measure distance.";
                ClearRoofMarkers();
                _isDimensioning = false;
            }
            else if (RoomLabelMode.IsChecked == true)
            {
                StatusText.Text = "Label mode: Click to place a room label. Enter room name in dialog.";
                ClearRoofMarkers();
            }
            else if (SelectMode.IsChecked == true)
            {
                StatusText.Text = "Select mode: Click an element to select it. Drag to move, Del to delete.";
                ClearRoofMarkers();
            }
            else
            {
                StatusText.Text = "Ready. Draw to create walls in Revit.";
                ClearRoofMarkers();
            }
        }

        private void Level_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (LevelCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentLevelId = id;
            }
        }

        private void WallType_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (WallTypeCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentWallTypeId = id;
                StatusText.Text = $"Wall type: {item.Content}";
            }
        }

        private void RoofType_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (RoofTypeCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentRoofTypeId = id;
                StatusText.Text = $"Roof type: {item.Content}";
            }
        }

        private void DoorType_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (DoorTypeCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentDoorTypeId = id;
                StatusText.Text = $"Door type: {item.Content}";
            }
        }

        private void WindowType_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (WindowTypeCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentWindowTypeId = id;
                StatusText.Text = $"Window type: {item.Content}";
            }
        }

        private void FurnitureType_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (FurnitureTypeCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentFurnitureTypeId = id;
                StatusText.Text = $"Furniture type: {item.Content}";
            }
        }

        private void FixtureType_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (FixtureTypeCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentFixtureTypeId = id;
                StatusText.Text = $"Fixture type: {item.Content}";
            }
        }

        private void CaseworkType_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (CaseworkTypeCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentCaseworkTypeId = id;
                StatusText.Text = $"Casework type: {item.Content}";
            }
        }

        private void ElectricalType_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (ElectricalTypeCombo.SelectedItem is ComboBoxItem item && item.Tag is ElementId id)
            {
                _currentElectricalTypeId = id;
                StatusText.Text = $"Electrical type: {item.Content}";
            }
        }

        private void ImageScale_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (ImageScaleCombo.SelectedItem is ComboBoxItem item && item.Tag is double scale)
            {
                _imageScale = scale;
                _imageScaleString = item.Content.ToString();

                // Apply scale to background image if present
                if (_backgroundImage != null)
                {
                    ApplyImageScale();
                }

                StatusText.Text = $"Image scale: {_imageScaleString}";
            }
        }

        private void ApplyImageScale()
        {
            if (_backgroundImage == null || _backgroundImage.Source == null) return;

            // Calculate the transform to apply the scale
            // At 1/4" = 1'-0" (scale factor 48), 1 inch on paper = 4 feet
            // We need to relate this to our _scale (pixels per foot)
            // The image scale determines how many real feet per inch of drawing
            // _imageScale = 48 means 1" on paper = 4' in real life
            // So if the image is 300 DPI, each pixel is 1/300 inch
            // That pixel represents (1/300) * 4 feet = 4/300 feet

            // For simplicity, we'll use a reference: at 1/4"=1'-0" with 96 DPI image:
            // 1 pixel = 1/96 inch = (1/96) * 4 feet = 0.0417 feet
            // We scale the image so that fits the canvas coordinate system

            // Calculate pixels per foot for the image based on assumed 96 DPI
            double imageDPI = 96.0;
            double inchesPerFoot = _imageScale / 12.0; // Scale factor / 12 gives paper inches per foot
            double imagePixelsPerFoot = imageDPI / inchesPerFoot;

            // Scale factor to convert image pixels to canvas pixels
            double scaleFactor = _scale / imagePixelsPerFoot;

            _backgroundImage.RenderTransform = new ScaleTransform(scaleFactor, scaleFactor, 0, 0);

            // Position at pan offset
            Canvas.SetLeft(_backgroundImage, _panOffset.X);
            Canvas.SetTop(_backgroundImage, _panOffset.Y);
        }

        /// <summary>
        /// Toggle between image manipulation mode and drawing mode
        /// </summary>
        private void ToggleImageMode()
        {
            if (_backgroundImage == null)
            {
                StatusText.Text = "No image loaded. Use Load Image button first.";
                return;
            }

            _imageManipulationMode = !_imageManipulationMode;

            if (_imageManipulationMode)
            {
                // Highlight the image with a border
                _backgroundImage.Opacity = Math.Max(_imageOpacity, 0.8);
                StatusText.Text = "IMAGE MODE: Drag to move image, scroll to resize. Press I to exit.";
                DrawingCanvas.Cursor = Cursors.SizeAll;
            }
            else
            {
                _backgroundImage.Opacity = _imageOpacity;
                StatusText.Text = "Drawing mode. Image position saved.";
                DrawingCanvas.Cursor = Cursors.Cross;
            }
        }

        /// <summary>
        /// Apply transform to background image based on current zoom and offset
        /// </summary>
        private void ApplyImageTransform()
        {
            if (_backgroundImage == null) return;

            // Apply scale transform
            _backgroundImage.RenderTransform = new ScaleTransform(_imageZoom, _imageZoom, 0, 0);

            // Apply position
            Canvas.SetLeft(_backgroundImage, _imageOffset.X);
            Canvas.SetTop(_backgroundImage, _imageOffset.Y);
        }

        /// <summary>
        /// Handle image dragging in image manipulation mode
        /// </summary>
        private void HandleImageDrag(Point currentPos)
        {
            if (!_imageManipulationMode || _backgroundImage == null) return;

            var delta = new Vector(currentPos.X - _imageDragStart.X, currentPos.Y - _imageDragStart.Y);
            _imageOffset = new Point(_imageOffset.X + delta.X, _imageOffset.Y + delta.Y);
            _imageDragStart = currentPos;

            ApplyImageTransform();
        }

        private void Undo_Click(object sender, RoutedEventArgs e)
        {
            // Remove from canvas
            if (_canvasElements.Count > 0)
            {
                var elem = _canvasElements.Pop();
                DrawingCanvas.Children.Remove(elem);
            }

            // Delete from Revit
            if (_createdElements.Count > 0)
            {
                var elemId = _createdElements.Pop();
                try
                {
                    using (var trans = new Transaction(_doc, "Undo SketchPad"))
                    {
                        trans.Start();
                        _doc.Delete(elemId);
                        trans.Commit();
                    }
                    StatusText.Text = "Undo: Element deleted.";
                }
                catch (Exception ex)
                {
                    StatusText.Text = $"Undo failed: {ex.Message}";
                }
            }
        }

        private void Clear_Click(object sender, RoutedEventArgs e)
        {
            var result = MessageBox.Show(
                "Clear all drawn elements? This will NOT delete walls already in Revit.",
                "Clear Canvas",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result == MessageBoxResult.Yes)
            {
                // Clear canvas drawings
                var toRemove = DrawingCanvas.Children.OfType<Line>().ToList();
                foreach (var line in toRemove)
                    DrawingCanvas.Children.Remove(line);

                ClearRoofMarkers();
                _canvasElements.Clear();
                StatusText.Text = "Canvas cleared.";
            }
        }

        private void LoadImage_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Filter = "Image Files|*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tif;*.tiff|All Files|*.*",
                Title = "Load Floor Plan Image (for tracing)"
            };

            if (dialog.ShowDialog() == true)
            {
                try
                {
                    // Load bitmap with explicit options to ensure it works
                    var bitmap = new BitmapImage();
                    bitmap.BeginInit();
                    bitmap.UriSource = new Uri(dialog.FileName, UriKind.Absolute);
                    bitmap.CacheOption = BitmapCacheOption.OnLoad;
                    bitmap.CreateOptions = BitmapCreateOptions.IgnoreColorProfile;
                    bitmap.EndInit();
                    bitmap.Freeze(); // Make it thread-safe

                    // Remove old background
                    if (_backgroundImage != null)
                    {
                        DrawingCanvas.Children.Remove(_backgroundImage);
                        _backgroundImage = null;
                    }

                    // Reset image position and zoom
                    _imageOffset = new Point(50, 50); // Start with some padding from edge
                    _imageZoom = 1.0;
                    _imagePixelsPerFoot = 1.0; // Reset calibration

                    // Create the image element
                    _backgroundImage = new Image
                    {
                        Source = bitmap,
                        Opacity = _imageOpacity,
                        Stretch = Stretch.Uniform,
                        Width = bitmap.PixelWidth,
                        Height = bitmap.PixelHeight
                    };

                    // Position it at the offset
                    Canvas.SetLeft(_backgroundImage, _imageOffset.X);
                    Canvas.SetTop(_backgroundImage, _imageOffset.Y);
                    Canvas.SetZIndex(_backgroundImage, -100); // Behind everything

                    // Add to canvas as first child (behind grid and drawing)
                    DrawingCanvas.Children.Insert(0, _backgroundImage);

                    // Show image info
                    StatusText.Text = $"Image loaded: {bitmap.PixelWidth}x{bitmap.PixelHeight}px. Click 'Calibrate' to set scale.";

                    // Show instructions
                    MessageBox.Show(
                        "Image loaded successfully!\n\n" +
                        "IMPORTANT: Click 'Calibrate' to scale the image!\n" +
                        "Draw a line on a known dimension (wall, room width)\n" +
                        "and enter the real-world length.\n\n" +
                        "Other controls:\n" +
                        "• Press I to toggle Image Mode (move/resize)\n" +
                        "• In Image Mode: drag to move, scroll to resize\n" +
                        "• Use the Opacity slider to adjust transparency",
                        "Image Loaded", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error loading image: {ex.Message}\n\nMake sure the file is a valid image format (PNG, JPG, BMP, GIF, TIF).",
                        "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void CalibrateImage_Click(object sender, RoutedEventArgs e)
        {
            if (_backgroundImage == null)
            {
                MessageBox.Show("Please load an image first using the 'Load Image' button.",
                    "No Image", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            // Enter calibration mode
            _calibrationMode = true;
            _calibrationStart = null;

            // Remove any existing calibration line
            if (_calibrationLine != null)
            {
                DrawingCanvas.Children.Remove(_calibrationLine);
                _calibrationLine = null;
            }

            StatusText.Text = "CALIBRATION: Click the START of a known dimension on the image...";

            MessageBox.Show(
                "Calibration Mode Active!\n\n" +
                "1. Click on the START point of a known dimension\n" +
                "   (e.g., one end of a room or wall)\n\n" +
                "2. Click on the END point of that same dimension\n\n" +
                "3. Enter the real-world length (in feet)\n\n" +
                "The image will be scaled to match your grid.\n\n" +
                "Press ESC to cancel calibration.",
                "Image Calibration", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void HandleCalibrationClick(Point pos)
        {
            if (!_calibrationStart.HasValue)
            {
                // First click - set start point
                _calibrationStart = pos;

                // Create calibration line (will follow mouse)
                _calibrationLine = new Line
                {
                    X1 = pos.X,
                    Y1 = pos.Y,
                    X2 = pos.X,
                    Y2 = pos.Y,
                    Stroke = Brushes.Magenta,
                    StrokeThickness = 3,
                    StrokeDashArray = new DoubleCollection { 4, 2 },
                    Tag = "CalibrationLine"
                };
                DrawingCanvas.Children.Add(_calibrationLine);
                Canvas.SetZIndex(_calibrationLine, 1000); // On top

                // Add start marker
                var startMarker = new Ellipse
                {
                    Width = 12,
                    Height = 12,
                    Fill = Brushes.Magenta,
                    Stroke = Brushes.White,
                    StrokeThickness = 2,
                    Tag = "CalibrationMarker"
                };
                Canvas.SetLeft(startMarker, pos.X - 6);
                Canvas.SetTop(startMarker, pos.Y - 6);
                Canvas.SetZIndex(startMarker, 1001);
                DrawingCanvas.Children.Add(startMarker);

                StatusText.Text = "CALIBRATION: Now click the END of the known dimension...";
            }
            else
            {
                // Second click - complete calibration
                var endPoint = pos;
                var startPoint = _calibrationStart.Value;

                // Calculate screen pixel distance (distance on canvas)
                double screenPixelDistance = Distance(startPoint, endPoint);

                if (screenPixelDistance < 10)
                {
                    StatusText.Text = "Distance too short. Please try again with a longer line.";
                    CancelCalibration();
                    return;
                }

                // Add end marker
                var endMarker = new Ellipse
                {
                    Width = 12,
                    Height = 12,
                    Fill = Brushes.Magenta,
                    Stroke = Brushes.White,
                    StrokeThickness = 2,
                    Tag = "CalibrationMarker"
                };
                Canvas.SetLeft(endMarker, endPoint.X - 6);
                Canvas.SetTop(endMarker, endPoint.Y - 6);
                Canvas.SetZIndex(endMarker, 1001);
                DrawingCanvas.Children.Add(endMarker);

                // Update line end position
                if (_calibrationLine != null)
                {
                    _calibrationLine.X2 = endPoint.X;
                    _calibrationLine.Y2 = endPoint.Y;
                }

                // Prompt for real-world distance
                var inputDialog = new CalibrationInputDialog(screenPixelDistance);
                inputDialog.Owner = this;

                if (inputDialog.ShowDialog() == true && inputDialog.RealWorldFeet > 0)
                {
                    double realWorldFeet = inputDialog.RealWorldFeet;

                    // The key insight:
                    // - screenPixelDistance is how many pixels the line spans on screen
                    // - realWorldFeet is how many feet that distance represents
                    // - _scale is how many screen pixels = 1 foot on the grid
                    //
                    // We want: after scaling, when you draw "realWorldFeet" on the image,
                    // it should span (realWorldFeet * _scale) screen pixels.
                    //
                    // Currently: screenPixelDistance screen pixels = realWorldFeet in real world
                    // We need: (realWorldFeet * _scale) screen pixels = realWorldFeet in real world
                    //
                    // Scale factor = (realWorldFeet * _scale) / screenPixelDistance
                    //              = (_scale * realWorldFeet) / screenPixelDistance

                    double targetScreenPixels = realWorldFeet * _scale;
                    double scaleFactor = targetScreenPixels / screenPixelDistance;

                    // Apply the scale factor relative to current zoom
                    double newZoom = _imageZoom * scaleFactor;

                    // Apply the zoom to the image
                    ApplyImageCalibration(newZoom);

                    StatusText.Text = $"Image calibrated! {realWorldFeet:F1}' = {_scale * realWorldFeet:F0}px on grid. Scale: {scaleFactor:F2}x";

                    MessageBox.Show(
                        $"Calibration Complete!\n\n" +
                        $"You measured: {screenPixelDistance:F0} screen pixels\n" +
                        $"Real-world length: {FormatFeetInches(realWorldFeet)}\n" +
                        $"Scale factor applied: {scaleFactor:F3}x\n" +
                        $"New image zoom: {newZoom:F3}x\n\n" +
                        "The image has been scaled to match the grid.\n" +
                        $"Grid scale: {_scale} pixels = 1 foot",
                        "Calibration Complete", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    StatusText.Text = "Calibration cancelled.";
                }

                // Clean up calibration UI
                CancelCalibration();
            }
        }

        private void ApplyImageCalibration(double newZoom)
        {
            if (_backgroundImage == null) return;

            var bitmap = _backgroundImage.Source as BitmapImage;
            if (bitmap == null) return;

            // Store current center position
            double currentLeft = Canvas.GetLeft(_backgroundImage);
            double currentTop = Canvas.GetTop(_backgroundImage);
            double currentWidth = _backgroundImage.Width;
            double currentHeight = _backgroundImage.Height;
            double centerX = currentLeft + currentWidth / 2;
            double centerY = currentTop + currentHeight / 2;

            // Apply new zoom
            _imageZoom = newZoom;
            double newWidth = bitmap.PixelWidth * _imageZoom;
            double newHeight = bitmap.PixelHeight * _imageZoom;

            _backgroundImage.Width = newWidth;
            _backgroundImage.Height = newHeight;

            // Reposition to keep center in same place
            Canvas.SetLeft(_backgroundImage, centerX - newWidth / 2);
            Canvas.SetTop(_backgroundImage, centerY - newHeight / 2);

            // Update offset tracking
            _imageOffset = new Point(
                Canvas.GetLeft(_backgroundImage),
                Canvas.GetTop(_backgroundImage)
            );
        }

        private void CancelCalibration()
        {
            _calibrationMode = false;
            _calibrationStart = null;

            // Remove calibration line
            if (_calibrationLine != null)
            {
                DrawingCanvas.Children.Remove(_calibrationLine);
                _calibrationLine = null;
            }

            // Remove calibration markers
            var markersToRemove = DrawingCanvas.Children.OfType<Ellipse>()
                .Where(e => e.Tag?.ToString() == "CalibrationMarker").ToList();
            foreach (var marker in markersToRemove)
            {
                DrawingCanvas.Children.Remove(marker);
            }
        }

        private void ExportJSON_Click(object sender, RoutedEventArgs e)
        {
            if (_drawnWalls.Count == 0)
            {
                MessageBox.Show("No walls to export.", "Export", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var dialog = new SaveFileDialog
            {
                Filter = "JSON Files|*.json|All Files|*.*",
                Title = "Export Drawn Walls",
                FileName = "sketchpad_walls.json"
            };

            if (dialog.ShowDialog() == true)
            {
                try
                {
                    var exportData = new
                    {
                        exportedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                        wallCount = _drawnWalls.Count,
                        scale = _scale,
                        gridSize = _gridSizeFeet,
                        walls = _drawnWalls.Select((w, i) => new
                        {
                            index = i,
                            startX = w.StartX,
                            startY = w.StartY,
                            endX = w.EndX,
                            endY = w.EndY,
                            height = w.Height,
                            levelName = w.LevelName,
                            wallTypeName = w.WallTypeName,
                            revitElementId = w.RevitElementId
                        }).ToList()
                    };

                    string json = JsonConvert.SerializeObject(exportData, Formatting.Indented);
                    File.WriteAllText(dialog.FileName, json);

                    StatusText.Text = $"Exported {_drawnWalls.Count} walls to JSON.";
                    MessageBox.Show($"Exported {_drawnWalls.Count} walls to:\n{dialog.FileName}", "Export Complete", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Export failed: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        #endregion

        #region Dimension & Measurement

        private void HandleDimensionClick(Point pos)
        {
            if (!_isDimensioning)
            {
                // First click - start dimension
                _dimensionStart = pos;
                _isDimensioning = true;

                // Add start marker
                var marker = new Ellipse
                {
                    Width = 8,
                    Height = 8,
                    Fill = Brushes.Red,
                    Tag = "DimensionMarker"
                };
                Canvas.SetLeft(marker, pos.X - 4);
                Canvas.SetTop(marker, pos.Y - 4);
                DrawingCanvas.Children.Add(marker);

                StatusText.Text = "Dimension: Click second point to complete measurement.";
            }
            else
            {
                // Second click - complete dimension
                _isDimensioning = false;

                // Calculate distance in feet (convert from canvas pixels)
                double x1Feet = (_dimensionStart.X - _panOffset.X) / _scale;
                double y1Feet = (DrawingCanvas.ActualHeight - _dimensionStart.Y + _panOffset.Y) / _scale;
                double x2Feet = (pos.X - _panOffset.X) / _scale;
                double y2Feet = (DrawingCanvas.ActualHeight - pos.Y + _panOffset.Y) / _scale;

                double distanceFeet = Math.Sqrt(Math.Pow(x2Feet - x1Feet, 2) + Math.Pow(y2Feet - y1Feet, 2));

                // Create dimension visual
                var dimGroup = DrawDimension(_dimensionStart, pos, distanceFeet);

                // Store dimension data
                var dimension = new DrawnDimension
                {
                    X1 = x1Feet,
                    Y1 = y1Feet,
                    X2 = x2Feet,
                    Y2 = y2Feet,
                    Distance = distanceFeet,
                    VisualElement = dimGroup
                };
                _drawnDimensions.Add(dimension);

                // Clear temp markers
                ClearTempDimensionMarkers();

                StatusText.Text = $"Dimension: {FormatFeetInches(distanceFeet)}";
            }
        }

        private Canvas DrawDimension(Point p1, Point p2, double distanceFeet)
        {
            var dimCanvas = new Canvas { Tag = "DimensionGroup" };

            // Main dimension line
            var line = new Line
            {
                X1 = p1.X, Y1 = p1.Y,
                X2 = p2.X, Y2 = p2.Y,
                Stroke = Brushes.Red,
                StrokeThickness = 1.5,
                Tag = "DimensionLine"
            };
            dimCanvas.Children.Add(line);

            // Extension lines (perpendicular)
            double dx = p2.X - p1.X;
            double dy = p2.Y - p1.Y;
            double len = Math.Sqrt(dx * dx + dy * dy);
            if (len > 0)
            {
                double perpX = -dy / len * 8;
                double perpY = dx / len * 8;

                // Start extension line
                var ext1 = new Line
                {
                    X1 = p1.X, Y1 = p1.Y,
                    X2 = p1.X + perpX, Y2 = p1.Y + perpY,
                    Stroke = Brushes.Red,
                    StrokeThickness = 1,
                    Tag = "DimensionLine"
                };
                dimCanvas.Children.Add(ext1);

                // End extension line
                var ext2 = new Line
                {
                    X1 = p2.X, Y1 = p2.Y,
                    X2 = p2.X + perpX, Y2 = p2.Y + perpY,
                    Stroke = Brushes.Red,
                    StrokeThickness = 1,
                    Tag = "DimensionLine"
                };
                dimCanvas.Children.Add(ext2);
            }

            // Dimension text
            var midX = (p1.X + p2.X) / 2;
            var midY = (p1.Y + p2.Y) / 2;

            var text = new TextBlock
            {
                Text = FormatFeetInches(distanceFeet),
                Foreground = Brushes.Red,
                FontSize = 12,
                FontWeight = FontWeights.Bold,
                Background = new SolidColorBrush(Color.FromArgb(200, 40, 40, 40)),
                Padding = new Thickness(3, 1, 3, 1),
                Tag = "DimensionText"
            };
            Canvas.SetLeft(text, midX + 5);
            Canvas.SetTop(text, midY - 10);
            dimCanvas.Children.Add(text);

            DrawingCanvas.Children.Add(dimCanvas);
            return dimCanvas;
        }

        private void ClearTempDimensionMarkers()
        {
            var toRemove = DrawingCanvas.Children.OfType<FrameworkElement>()
                .Where(e => e.Tag?.ToString() == "DimensionMarker")
                .ToList();
            foreach (var elem in toRemove)
                DrawingCanvas.Children.Remove(elem);
        }

        #endregion

        #region Room Labels

        private void PlaceRoomLabel(Point pos)
        {
            // Show input dialog for room name
            var dialog = new Window
            {
                Title = "Room Label",
                Width = 300,
                Height = 150,
                WindowStartupLocation = WindowStartupLocation.CenterOwner,
                Owner = this,
                Background = new SolidColorBrush(Color.FromRgb(45, 45, 48))
            };

            var stack = new StackPanel { Margin = new Thickness(15) };

            var label = new Label { Content = "Enter Room Name:", Foreground = Brushes.White };
            stack.Children.Add(label);

            var textBox = new TextBox
            {
                Margin = new Thickness(0, 5, 0, 15),
                Height = 25,
                FontSize = 14,
                Background = Brushes.White,
                Foreground = Brushes.Black
            };
            stack.Children.Add(textBox);

            var buttonPanel = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };

            var okButton = new Button
            {
                Content = "OK",
                Width = 70,
                Height = 28,
                Margin = new Thickness(5, 0, 0, 0),
                Background = new SolidColorBrush(Color.FromRgb(0, 122, 204)),
                Foreground = Brushes.White
            };

            var cancelButton = new Button
            {
                Content = "Cancel",
                Width = 70,
                Height = 28,
                Background = new SolidColorBrush(Color.FromRgb(100, 100, 100)),
                Foreground = Brushes.White
            };

            buttonPanel.Children.Add(cancelButton);
            buttonPanel.Children.Add(okButton);
            stack.Children.Add(buttonPanel);

            dialog.Content = stack;

            string roomName = null;
            okButton.Click += (s, e) => { roomName = textBox.Text; dialog.DialogResult = true; dialog.Close(); };
            cancelButton.Click += (s, e) => { dialog.DialogResult = false; dialog.Close(); };
            textBox.KeyDown += (s, e) => { if (e.Key == Key.Enter) { roomName = textBox.Text; dialog.DialogResult = true; dialog.Close(); } };

            dialog.Loaded += (s, e) => textBox.Focus();

            if (dialog.ShowDialog() == true && !string.IsNullOrWhiteSpace(roomName))
            {
                // Convert to feet coordinates
                double xFeet = (pos.X - _panOffset.X) / _scale;
                double yFeet = (DrawingCanvas.ActualHeight - pos.Y + _panOffset.Y) / _scale;

                // Create label visual
                var labelVisual = DrawRoomLabel(pos, roomName);

                // Store room label data
                var roomLabel = new DrawnRoomLabel
                {
                    X = xFeet,
                    Y = yFeet,
                    RoomName = roomName,
                    Area = 0, // Could calculate area if in enclosed space
                    VisualElement = labelVisual
                };
                _drawnRoomLabels.Add(roomLabel);

                StatusText.Text = $"Room label placed: {roomName}";
            }
        }

        private Border DrawRoomLabel(Point pos, string roomName)
        {
            var border = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(200, 60, 60, 60)),
                BorderBrush = Brushes.White,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(3),
                Padding = new Thickness(8, 4, 8, 4),
                Tag = "RoomLabel"
            };

            var text = new TextBlock
            {
                Text = roomName.ToUpper(),
                Foreground = Brushes.White,
                FontSize = 14,
                FontWeight = FontWeights.SemiBold,
                TextAlignment = TextAlignment.Center
            };

            border.Child = text;

            // Measure to center the label
            border.Measure(new Size(double.PositiveInfinity, double.PositiveInfinity));
            Canvas.SetLeft(border, pos.X - border.DesiredSize.Width / 2);
            Canvas.SetTop(border, pos.Y - border.DesiredSize.Height / 2);

            DrawingCanvas.Children.Add(border);
            return border;
        }

        #endregion

        #region Selection & Move

        private void HandleSelectionClick(Point pos, MouseButtonEventArgs e)
        {
            // Clear previous multi-selection
            ClearBoxSelection();
            DeselectElement();

            // First, try to find a wall line near the click position (proximity search)
            UIElement foundWall = FindWallNearPosition(pos, 10.0); // 10 pixel tolerance
            if (foundWall != null)
            {
                SelectElement(foundWall);
                StatusText.Text = "Wall selected. Press Delete to remove.";
                return;
            }

            // Fall back to hit test for other elements
            var hitResult = DrawingCanvas.InputHitTest(pos) as FrameworkElement;

            if (hitResult != null && hitResult != DrawingCanvas)
            {
                // Find the parent element (line, rectangle, etc)
                var element = FindParentElement(hitResult);
                if (element != null)
                {
                    SelectElement(element);
                    _selectionOffset = new Point(pos.X - Canvas.GetLeft(element), pos.Y - Canvas.GetTop(element));
                    _isDragging = true;
                    DrawingCanvas.CaptureMouse();
                    return;
                }
            }

            // No element clicked - start box selection
            StartBoxSelection(pos);
            DrawingCanvas.CaptureMouse();
        }

        /// <summary>
        /// Find a wall line element near the given canvas position
        /// </summary>
        private UIElement FindWallNearPosition(Point pos, double tolerance)
        {
            UIElement nearestWall = null;
            double minDist = tolerance;

            foreach (var child in DrawingCanvas.Children)
            {
                if (child is Line line && line.Tag is int)
                {
                    // This is a wall line (tagged with wall index)
                    var start = new Point(line.X1, line.Y1);
                    var end = new Point(line.X2, line.Y2);
                    double dist = DistanceToLine(pos, start, end);
                    if (dist < minDist)
                    {
                        minDist = dist;
                        nearestWall = line;
                    }
                }
            }

            return nearestWall;
        }

        private UIElement FindParentElement(FrameworkElement element)
        {
            // Check if the element itself is a placeable element
            var tag = element.Tag?.ToString();
            if (tag != null && (tag.Contains("Marker") || tag.Contains("Label") || tag.Contains("Dimension")))
            {
                return element;
            }

            // For lines, they are direct children
            if (element is Line)
            {
                return element;
            }

            // Check parent
            if (element.Parent is Canvas parent && parent != DrawingCanvas)
            {
                return parent;
            }

            return element;
        }

        private void SelectElement(UIElement element)
        {
            _selectedElement = element;

            // For Line elements (walls), highlight directly
            if (element is Line line)
            {
                // Store original stroke for restoration
                line.SetValue(FrameworkElement.DataContextProperty, line.Stroke);
                line.Stroke = Brushes.Cyan;
                line.StrokeThickness = 4;
                StatusText.Text = "Wall selected. Press Delete to remove.";
                return;
            }

            // Add selection highlight for other elements
            if (element is FrameworkElement fe)
            {
                // Create selection border
                var bounds = fe.TransformToAncestor(DrawingCanvas).TransformBounds(new Rect(0, 0, fe.ActualWidth, fe.ActualHeight));
                var selectionRect = new Rectangle
                {
                    Width = bounds.Width + 8,
                    Height = bounds.Height + 8,
                    Stroke = Brushes.Cyan,
                    StrokeThickness = 2,
                    StrokeDashArray = new DoubleCollection { 4, 2 },
                    Fill = new SolidColorBrush(Color.FromArgb(30, 0, 255, 255)),
                    Tag = "SelectionBox"
                };
                Canvas.SetLeft(selectionRect, bounds.Left - 4);
                Canvas.SetTop(selectionRect, bounds.Top - 4);
                DrawingCanvas.Children.Add(selectionRect);
            }

            StatusText.Text = "Selected. Drag to move, press Delete to remove.";
        }

        private void DeselectElement()
        {
            // Restore line styling if a wall was selected
            if (_selectedElement is Line line)
            {
                var originalStroke = line.GetValue(FrameworkElement.DataContextProperty) as Brush;
                if (originalStroke != null)
                    line.Stroke = originalStroke;
                else
                    line.Stroke = Brushes.White; // Default wall color
                line.StrokeThickness = 2;
            }

            _selectedElement = null;
            _isDragging = false;

            // Remove selection box for non-line elements
            var toRemove = DrawingCanvas.Children.OfType<FrameworkElement>()
                .Where(e => e.Tag?.ToString() == "SelectionBox")
                .ToList();
            foreach (var elem in toRemove)
                DrawingCanvas.Children.Remove(elem);
        }

        /// <summary>
        /// Clear multi-selection and restore all selected elements
        /// </summary>
        private void ClearBoxSelection()
        {
            foreach (var elem in _selectedElements)
            {
                if (elem is Line line)
                {
                    var originalStroke = line.GetValue(FrameworkElement.DataContextProperty) as Brush;
                    if (originalStroke != null)
                        line.Stroke = originalStroke;
                    else
                        line.Stroke = Brushes.White;
                    line.StrokeThickness = 2;
                }
            }
            _selectedElements.Clear();

            // Remove selection box rectangle
            if (_selectionBox != null)
            {
                DrawingCanvas.Children.Remove(_selectionBox);
                _selectionBox = null;
            }
            _isBoxSelecting = false;
        }

        /// <summary>
        /// Select all wall elements
        /// </summary>
        private void SelectAllElements()
        {
            ClearBoxSelection();
            DeselectElement();

            foreach (var child in DrawingCanvas.Children)
            {
                if (child is Line line && line.Tag is int)
                {
                    // Store original color
                    line.SetValue(FrameworkElement.DataContextProperty, line.Stroke);
                    line.Stroke = Brushes.Cyan;
                    line.StrokeThickness = 3;
                    _selectedElements.Add(line);
                }
            }

            StatusText.Text = $"{_selectedElements.Count} elements selected. Press Delete to remove all.";
        }

        /// <summary>
        /// Start box selection when dragging in Select mode
        /// </summary>
        private void StartBoxSelection(Point startPos)
        {
            ClearBoxSelection();
            _isBoxSelecting = true;
            _boxSelectStart = startPos;

            _selectionBox = new Rectangle
            {
                Stroke = Brushes.Cyan,
                StrokeThickness = 1,
                StrokeDashArray = new DoubleCollection { 4, 2 },
                Fill = new SolidColorBrush(Color.FromArgb(30, 0, 255, 255)),
                Tag = "BoxSelection"
            };
            Canvas.SetLeft(_selectionBox, startPos.X);
            Canvas.SetTop(_selectionBox, startPos.Y);
            DrawingCanvas.Children.Add(_selectionBox);
        }

        /// <summary>
        /// Update box selection rectangle during drag
        /// </summary>
        private void UpdateBoxSelection(Point currentPos)
        {
            if (_selectionBox == null) return;

            double x = Math.Min(_boxSelectStart.X, currentPos.X);
            double y = Math.Min(_boxSelectStart.Y, currentPos.Y);
            double width = Math.Abs(currentPos.X - _boxSelectStart.X);
            double height = Math.Abs(currentPos.Y - _boxSelectStart.Y);

            Canvas.SetLeft(_selectionBox, x);
            Canvas.SetTop(_selectionBox, y);
            _selectionBox.Width = width;
            _selectionBox.Height = height;
        }

        /// <summary>
        /// Complete box selection - select all elements within the rectangle
        /// </summary>
        private void CompleteBoxSelection(Point endPos)
        {
            if (!_isBoxSelecting) return;

            double x1 = Math.Min(_boxSelectStart.X, endPos.X);
            double y1 = Math.Min(_boxSelectStart.Y, endPos.Y);
            double x2 = Math.Max(_boxSelectStart.X, endPos.X);
            double y2 = Math.Max(_boxSelectStart.Y, endPos.Y);

            // Find all wall lines that intersect the selection box
            foreach (var child in DrawingCanvas.Children)
            {
                if (child is Line line && line.Tag is int)
                {
                    // Check if line intersects or is within the selection box
                    if (LineIntersectsRect(line.X1, line.Y1, line.X2, line.Y2, x1, y1, x2, y2))
                    {
                        line.SetValue(FrameworkElement.DataContextProperty, line.Stroke);
                        line.Stroke = Brushes.Cyan;
                        line.StrokeThickness = 3;
                        _selectedElements.Add(line);
                    }
                }
            }

            // Remove the selection box rectangle
            if (_selectionBox != null)
            {
                DrawingCanvas.Children.Remove(_selectionBox);
                _selectionBox = null;
            }

            _isBoxSelecting = false;

            if (_selectedElements.Count > 0)
                StatusText.Text = $"{_selectedElements.Count} elements selected. Press Delete to remove all.";
            else
                StatusText.Text = "No elements in selection area.";
        }

        /// <summary>
        /// Check if a line segment intersects or is within a rectangle
        /// </summary>
        private bool LineIntersectsRect(double lx1, double ly1, double lx2, double ly2, double rx1, double ry1, double rx2, double ry2)
        {
            // Check if either endpoint is inside the rectangle
            if ((lx1 >= rx1 && lx1 <= rx2 && ly1 >= ry1 && ly1 <= ry2) ||
                (lx2 >= rx1 && lx2 <= rx2 && ly2 >= ry1 && ly2 <= ry2))
                return true;

            // Check if line crosses any edge of the rectangle
            return LineSegmentsIntersect(lx1, ly1, lx2, ly2, rx1, ry1, rx2, ry1) || // Top
                   LineSegmentsIntersect(lx1, ly1, lx2, ly2, rx1, ry2, rx2, ry2) || // Bottom
                   LineSegmentsIntersect(lx1, ly1, lx2, ly2, rx1, ry1, rx1, ry2) || // Left
                   LineSegmentsIntersect(lx1, ly1, lx2, ly2, rx2, ry1, rx2, ry2);   // Right
        }

        /// <summary>
        /// Check if two line segments intersect
        /// </summary>
        private bool LineSegmentsIntersect(double ax1, double ay1, double ax2, double ay2, double bx1, double by1, double bx2, double by2)
        {
            double d = (ax2 - ax1) * (by2 - by1) - (ay2 - ay1) * (bx2 - bx1);
            if (Math.Abs(d) < 0.0001) return false;

            double t = ((bx1 - ax1) * (by2 - by1) - (by1 - ay1) * (bx2 - bx1)) / d;
            double u = -((ax2 - ax1) * (by1 - ay1) - (ay2 - ay1) * (bx1 - ax1)) / d;

            return t >= 0 && t <= 1 && u >= 0 && u <= 1;
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);

            // Escape - Cancel calibration, break chain, cancel drawing, deselect
            if (e.Key == Key.Escape)
            {
                // Cancel calibration mode if active
                if (_calibrationMode)
                {
                    CancelCalibration();
                    StatusText.Text = "Calibration cancelled. Ready.";
                    e.Handled = true;
                    return;
                }

                _lastWallEndPoint = null; // Break chain
                _isDrawing = false;
                if (_previewLine != null)
                {
                    DrawingCanvas.Children.Remove(_previewLine);
                    _previewLine = null;
                }
                DeselectElement();
                ClearBoxSelection();
                StatusText.Text = "Chain broken. Ready.";
                e.Handled = true;
                return;
            }

            // Mode shortcuts (only when no modifier keys pressed)
            if (Keyboard.Modifiers == ModifierKeys.None)
            {
                switch (e.Key)
                {
                    case Key.W: // Wall mode
                        WallMode.IsChecked = true;
                        StatusText.Text = "Wall mode. Click to draw walls.";
                        e.Handled = true;
                        break;
                    case Key.D: // Door mode
                        DoorMode.IsChecked = true;
                        StatusText.Text = "Door mode. Click on a wall to place door.";
                        e.Handled = true;
                        break;
                    case Key.N: // Window mode
                        WindowMode.IsChecked = true;
                        StatusText.Text = "Window mode. Click on a wall to place window.";
                        e.Handled = true;
                        break;
                    case Key.S: // Select mode
                        SelectMode.IsChecked = true;
                        StatusText.Text = "Select mode. Click elements to select, drag to box select.";
                        e.Handled = true;
                        break;
                    case Key.F: // Furniture mode
                        FurnitureMode.IsChecked = true;
                        StatusText.Text = "Furniture mode. Click to place.";
                        e.Handled = true;
                        break;
                    case Key.X: // Fixture mode (plumbing)
                        FixtureMode.IsChecked = true;
                        StatusText.Text = "Fixture mode. Click to place plumbing fixtures.";
                        e.Handled = true;
                        break;
                    case Key.C: // Casework mode
                        CaseworkMode.IsChecked = true;
                        StatusText.Text = "Casework mode. Click to place cabinets.";
                        e.Handled = true;
                        break;
                    case Key.E: // Electrical mode
                        ElectricalMode.IsChecked = true;
                        StatusText.Text = "Electrical mode. Click to place outlets/switches/lights.";
                        e.Handled = true;
                        break;
                    case Key.M: // Dimension/Measure mode
                        DimensionMode.IsChecked = true;
                        StatusText.Text = "Dimension mode. Click two points to measure.";
                        e.Handled = true;
                        break;
                    case Key.L: // Room label mode
                        RoomLabelMode.IsChecked = true;
                        StatusText.Text = "Room label mode. Click to place label.";
                        e.Handled = true;
                        break;
                    case Key.R: // Room boundary mode (new)
                        RoomMode.IsChecked = true;
                        StatusText.Text = "Room mode. Click corners to define room boundary.";
                        e.Handled = true;
                        break;
                    case Key.O: // Toggle Ortho
                        OrthoToggle.IsChecked = !OrthoToggle.IsChecked;
                        e.Handled = true;
                        break;
                    case Key.I: // Toggle Image manipulation mode
                        ToggleImageMode();
                        e.Handled = true;
                        break;
                    case Key.OemPlus: // Zoom image in
                    case Key.Add:
                        if (_backgroundImage != null)
                        {
                            _imageZoom *= 1.1;
                            ApplyImageTransform();
                            StatusText.Text = $"Image zoom: {_imageZoom:P0}";
                        }
                        e.Handled = true;
                        break;
                    case Key.OemMinus: // Zoom image out
                    case Key.Subtract:
                        if (_backgroundImage != null)
                        {
                            _imageZoom /= 1.1;
                            ApplyImageTransform();
                            StatusText.Text = $"Image zoom: {_imageZoom:P0}";
                        }
                        e.Handled = true;
                        break;
                }
            }

            // Handle Delete key to remove selected element
            if (e.Key == Key.Delete && _selectedElement != null)
            {
                DeleteSelectedElement();
                e.Handled = true;
            }

            // Ctrl+A - Select all
            if (e.Key == Key.A && Keyboard.Modifiers == ModifierKeys.Control)
            {
                SelectAllElements();
                e.Handled = true;
            }

            // Handle Ctrl+Z for Undo
            if (e.Key == Key.Z && Keyboard.Modifiers == ModifierKeys.Control)
            {
                Undo();
                e.Handled = true;
            }

            // Handle Ctrl+Y for Redo
            if (e.Key == Key.Y && Keyboard.Modifiers == ModifierKeys.Control)
            {
                Redo();
                e.Handled = true;
            }
        }

        private void DeleteSelectedElement()
        {
            // Handle multi-selection first (box selection)
            if (_selectedElements != null && _selectedElements.Count > 0)
            {
                FlashRedAndDeleteMultiple(_selectedElements.ToList());
                return;
            }

            // Handle single selection
            if (_selectedElement == null) return;

            // Flash red before deletion
            FlashRedAndDelete(_selectedElement);
        }

        private async void FlashRedAndDeleteMultiple(List<UIElement> elements)
        {
            // Flash all elements red
            var originalStates = new List<(UIElement element, Brush stroke, double thickness)>();

            foreach (var element in elements)
            {
                if (element is Line line)
                {
                    originalStates.Add((element, line.Stroke, line.StrokeThickness));
                    line.Stroke = Brushes.Red;
                    line.StrokeThickness = 5;
                }
                else if (element is Rectangle rect)
                {
                    originalStates.Add((element, rect.Stroke, rect.StrokeThickness));
                    rect.Stroke = Brushes.Red;
                    rect.StrokeThickness = 3;
                }
            }

            StatusText.Text = $"Deleting {elements.Count} elements...";

            // Wait 300ms so user sees the red flash
            await System.Threading.Tasks.Task.Delay(300);

            // Collect all Revit element IDs to delete in batch
            var revitIdsToDelete = new List<int>();

            // Delete all elements
            foreach (var element in elements)
            {
                // Add to undo stack
                var action = new UndoAction
                {
                    ActionType = "Delete",
                    CanvasElement = element
                };
                _undoStack.Push(action);

                // Remove from data lists based on tag
                var tag = (element as FrameworkElement)?.Tag;

                // If it's a wall (integer tag), remove from _drawnWalls
                if (tag is int wallIndex && wallIndex >= 0 && wallIndex < _drawnWalls.Count)
                {
                    var wall = _drawnWalls[wallIndex];
                    if (wall.RevitElementId.HasValue)
                        revitIdsToDelete.Add(wall.RevitElementId.Value);
                    action.DataElement = wall;
                    _drawnWalls.RemoveAt(wallIndex);
                }
                else if (tag?.ToString() == "DimensionGroup")
                {
                    var dim = _drawnDimensions.FirstOrDefault(d => d.VisualElement == element);
                    if (dim != null)
                    {
                        if (dim.RevitElementId.HasValue)
                            revitIdsToDelete.Add(dim.RevitElementId.Value);
                        action.DataElement = dim;
                        _drawnDimensions.Remove(dim);
                    }
                }
                else if (tag?.ToString() == "RoomLabel")
                {
                    var label = _drawnRoomLabels.FirstOrDefault(l => l.VisualElement == element);
                    if (label != null)
                    {
                        if (label.RevitElementId.HasValue)
                            revitIdsToDelete.Add(label.RevitElementId.Value);
                        action.DataElement = label;
                        _drawnRoomLabels.Remove(label);
                    }
                }

                // Remove from canvas
                DrawingCanvas.Children.Remove(element);
            }

            _redoStack.Clear();

            // Update wall indices after batch deletion
            UpdateWallIndices();

            // Delete from Revit in batch
            if (revitIdsToDelete.Count > 0)
            {
                DeleteFromRevitBatch(revitIdsToDelete);
            }

            // Clear selections
            _selectedElements.Clear();
            _selectedElement = null;
            _isDragging = false;
            StatusText.Text = revitIdsToDelete.Count > 0
                ? $"Deleted {elements.Count} elements from SketchPad and Revit."
                : $"Deleted {elements.Count} elements.";
        }

        private async void FlashRedAndDelete(UIElement element)
        {
            // Store original appearance and flash red
            Brush originalStroke = null;
            if (element is Line line)
            {
                originalStroke = line.Stroke;
                line.Stroke = Brushes.Red;
                line.StrokeThickness = 5;
            }
            else if (element is FrameworkElement fe)
            {
                // For other elements, try to change color
                if (fe is Rectangle rect)
                {
                    originalStroke = rect.Stroke;
                    rect.Stroke = Brushes.Red;
                    rect.StrokeThickness = 3;
                }
            }

            StatusText.Text = "Deleting...";

            // Wait 300ms so user sees the red flash
            await System.Threading.Tasks.Task.Delay(300);

            // Add to undo stack
            var action = new UndoAction
            {
                ActionType = "Delete",
                CanvasElement = element
            };
            _undoStack.Push(action);
            _redoStack.Clear();

            // Remove from data lists based on tag
            var tag = (element as FrameworkElement)?.Tag;
            int? revitElementId = null;

            // If it's a wall (integer tag), remove from _drawnWalls
            if (tag is int wallIndex && wallIndex >= 0 && wallIndex < _drawnWalls.Count)
            {
                var wall = _drawnWalls[wallIndex];
                revitElementId = wall.RevitElementId;
                action.DataElement = wall;
                _drawnWalls.RemoveAt(wallIndex);
                // Update remaining wall indices
                UpdateWallIndices();
            }
            else if (tag?.ToString() == "DimensionGroup")
            {
                var dim = _drawnDimensions.FirstOrDefault(d => d.VisualElement == element);
                if (dim != null)
                {
                    revitElementId = dim.RevitElementId;
                    action.DataElement = dim;
                    _drawnDimensions.Remove(dim);
                }
            }
            else if (tag?.ToString() == "RoomLabel")
            {
                var label = _drawnRoomLabels.FirstOrDefault(l => l.VisualElement == element);
                if (label != null)
                {
                    revitElementId = label.RevitElementId;
                    action.DataElement = label;
                    _drawnRoomLabels.Remove(label);
                }
            }

            // Remove from canvas
            DrawingCanvas.Children.Remove(element);

            // Delete from Revit if element exists there
            if (revitElementId.HasValue)
            {
                DeleteFromRevit(revitElementId.Value);
            }

            _selectedElement = null;
            _isDragging = false;
            StatusText.Text = revitElementId.HasValue ? "Element deleted from SketchPad and Revit." : "Element deleted.";

            // Update 3D view
            Update3DWalls();
        }

        /// <summary>
        /// Update wall line tags after deletion to maintain correct indices
        /// </summary>
        private void UpdateWallIndices()
        {
            int index = 0;
            foreach (var child in DrawingCanvas.Children)
            {
                if (child is Line line && line.Tag is int)
                {
                    line.Tag = index;
                    index++;
                }
            }
        }

        /// <summary>
        /// Delete a single element from Revit
        /// </summary>
        private void DeleteFromRevit(int elementId)
        {
            try
            {
                _deleteElementHandler.SetDeleteData(_doc, new List<ElementId> { new ElementId(elementId) });
                _deleteExternalEvent.Raise();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to delete from Revit: {ex.Message}");
            }
        }

        /// <summary>
        /// Delete multiple elements from Revit in a batch
        /// </summary>
        private void DeleteFromRevitBatch(List<int> elementIds)
        {
            try
            {
                var ids = elementIds.Select(id => new ElementId(id)).ToList();
                _deleteElementHandler.SetDeleteData(_doc, ids);
                _deleteExternalEvent.Raise();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to delete batch from Revit: {ex.Message}");
            }
        }

        #endregion

        #region Undo/Redo

        private void Undo()
        {
            if (_undoStack.Count == 0)
            {
                StatusText.Text = "Nothing to undo.";
                return;
            }

            var action = _undoStack.Pop();

            if (action.ActionType == "Delete")
            {
                // Restore deleted element
                DrawingCanvas.Children.Add(action.CanvasElement);
                _redoStack.Push(action);
                StatusText.Text = "Undo: Element restored.";
            }
            // Add more undo types as needed
        }

        private void Redo()
        {
            if (_redoStack.Count == 0)
            {
                StatusText.Text = "Nothing to redo.";
                return;
            }

            var action = _redoStack.Pop();

            if (action.ActionType == "Delete")
            {
                // Re-delete element
                DrawingCanvas.Children.Remove(action.CanvasElement);
                _undoStack.Push(action);
                StatusText.Text = "Redo: Element removed again.";
            }
        }

        #endregion

        #region 3D Viewport

        private void Toggle3DView_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                _show3DView = !_show3DView;

                if (_show3DView)
                {
                    Show3DViewport();
                    StatusText.Text = "3D View enabled. Drag to rotate, scroll to zoom.";
                }
                else
                {
                    Hide3DViewport();
                    StatusText.Text = "3D View disabled. Back to 2D mode.";
                }
            }
            catch (Exception ex)
            {
                _show3DView = false;
                StatusText.Text = $"3D View error: {ex.Message}";
                System.Diagnostics.Debug.WriteLine($"3D View error: {ex}");
            }
        }

        private void Show3DViewport()
        {
            if (_viewport3DBorder != null)
            {
                _viewport3DBorder.Visibility = System.Windows.Visibility.Visible;
                Update3DWalls();
                return;
            }

            // Create 3D viewport
            _viewport3D = new Viewport3D
            {
                ClipToBounds = true
            };

            // Setup camera
            _camera3D = new PerspectiveCamera
            {
                Position = new Point3D(0, -100, 50),
                LookDirection = new Vector3D(0, 100, -30),
                UpDirection = new Vector3D(0, 0, 1),
                FieldOfView = 60
            };
            _viewport3D.Camera = _camera3D;
            UpdateCameraPosition();

            // Add ambient light
            var ambientLight = new AmbientLight(Colors.Gray);
            var lightModel = new ModelVisual3D { Content = ambientLight };
            _viewport3D.Children.Add(lightModel);

            // Add directional light for shadows
            var dirLight = new DirectionalLight(Colors.White, new Vector3D(-1, -1, -1));
            var dirLightModel = new ModelVisual3D { Content = dirLight };
            _viewport3D.Children.Add(dirLightModel);

            // Add ground plane
            var groundModel = CreateGroundPlane();
            _viewport3D.Children.Add(groundModel);

            // Create walls model container
            _wallsModel = new ModelVisual3D();
            _viewport3D.Children.Add(_wallsModel);

            // Add label
            var label = new TextBlock
            {
                Text = "3D Preview",
                Foreground = Brushes.White,
                FontSize = 10,
                HorizontalAlignment = HorizontalAlignment.Left,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(5, 5, 0, 0),
                IsHitTestVisible = false // Let mouse events pass through to viewport
            };

            // Create inner grid with viewport and label
            var innerGrid = new System.Windows.Controls.Grid();
            innerGrid.Children.Add(_viewport3D);
            innerGrid.Children.Add(label);

            // Create border container for 3D viewport (overlay on right side)
            _viewport3DBorder = new Border
            {
                Width = 300,
                Height = 250,
                HorizontalAlignment = HorizontalAlignment.Right,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(0, 10, 10, 0),
                Background = new SolidColorBrush(Color.FromRgb(40, 40, 45)),
                BorderBrush = new SolidColorBrush(Color.FromRgb(100, 150, 200)),
                BorderThickness = new Thickness(2),
                CornerRadius = new CornerRadius(5),
                Child = innerGrid
            };

            // Add mouse handlers for rotation
            _viewport3DBorder.MouseLeftButtonDown += Viewport3D_MouseDown;
            _viewport3DBorder.MouseLeftButtonUp += Viewport3D_MouseUp;
            _viewport3DBorder.MouseMove += Viewport3D_MouseMove;
            _viewport3DBorder.MouseWheel += Viewport3D_MouseWheel;

            // Add to canvas grid (same parent as DrawingCanvas)
            var canvasParent = DrawingCanvas.Parent as System.Windows.Controls.Grid;
            if (canvasParent != null)
            {
                canvasParent.Children.Add(_viewport3DBorder);
            }

            Update3DWalls();
        }

        private void Hide3DViewport()
        {
            if (_viewport3DBorder != null)
            {
                _viewport3DBorder.Visibility = System.Windows.Visibility.Collapsed;
            }
        }

        private void UpdateCameraPosition()
        {
            double radAngle = _cameraAngle * Math.PI / 180.0;
            double radPitch = _cameraPitch * Math.PI / 180.0;

            double x = _cameraDistance * Math.Cos(radPitch) * Math.Sin(radAngle);
            double y = -_cameraDistance * Math.Cos(radPitch) * Math.Cos(radAngle);
            double z = _cameraDistance * Math.Sin(radPitch);

            _camera3D.Position = new Point3D(x, y, z);
            _camera3D.LookDirection = new Vector3D(-x, -y, -z);
        }

        private void Viewport3D_MouseDown(object sender, MouseButtonEventArgs e)
        {
            _isRotating3D = true;
            _lastMouse3D = e.GetPosition(_viewport3DBorder);
            _viewport3DBorder.CaptureMouse();
        }

        private void Viewport3D_MouseUp(object sender, MouseButtonEventArgs e)
        {
            _isRotating3D = false;
            _viewport3DBorder.ReleaseMouseCapture();
        }

        private void Viewport3D_MouseMove(object sender, MouseEventArgs e)
        {
            if (!_isRotating3D) return;

            var pos = e.GetPosition(_viewport3DBorder);
            double dx = pos.X - _lastMouse3D.X;
            double dy = pos.Y - _lastMouse3D.Y;

            _cameraAngle += dx * 0.5;
            _cameraPitch = Math.Max(5, Math.Min(85, _cameraPitch + dy * 0.5));

            UpdateCameraPosition();
            _lastMouse3D = pos;
        }

        private void Viewport3D_MouseWheel(object sender, MouseWheelEventArgs e)
        {
            if (e.Delta > 0)
                _cameraDistance = Math.Max(20, _cameraDistance * 0.9);
            else
                _cameraDistance = Math.Min(500, _cameraDistance * 1.1);

            UpdateCameraPosition();
            e.Handled = true;
        }

        private ModelVisual3D CreateGroundPlane()
        {
            var mesh = new MeshGeometry3D();
            double size = 100;

            // Create ground plane vertices
            mesh.Positions.Add(new Point3D(-size, -size, 0));
            mesh.Positions.Add(new Point3D(size, -size, 0));
            mesh.Positions.Add(new Point3D(size, size, 0));
            mesh.Positions.Add(new Point3D(-size, size, 0));

            mesh.TriangleIndices.Add(0);
            mesh.TriangleIndices.Add(1);
            mesh.TriangleIndices.Add(2);
            mesh.TriangleIndices.Add(0);
            mesh.TriangleIndices.Add(2);
            mesh.TriangleIndices.Add(3);

            var material = new DiffuseMaterial(new SolidColorBrush(Color.FromRgb(60, 60, 65)));
            var model = new GeometryModel3D(mesh, material);
            model.BackMaterial = material;

            return new ModelVisual3D { Content = model };
        }

        private void Update3DWalls()
        {
            try
            {
                if (_wallsModel == null || !_show3DView) return;

                var group = new Model3DGroup();

                foreach (var wall in _drawnWalls)
                {
                    if (wall != null)
                    {
                        var wallModel = CreateWall3D(wall);
                        if (wallModel != null)
                            group.Children.Add(wallModel);
                    }
                }

                _wallsModel.Content = group;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Update3DWalls error: {ex.Message}");
            }
        }

        private GeometryModel3D CreateWall3D(DrawnWall wall)
        {
            var mesh = new MeshGeometry3D();

            // Wall dimensions
            double x1 = wall.StartX;
            double y1 = wall.StartY;
            double x2 = wall.EndX;
            double y2 = wall.EndY;
            double height = wall.Height;
            double thickness = 0.5; // Wall thickness in feet

            // Calculate wall direction
            double dx = x2 - x1;
            double dy = y2 - y1;
            double length = Math.Sqrt(dx * dx + dy * dy);
            if (length < 0.1) return new GeometryModel3D();

            // Normalize direction
            dx /= length;
            dy /= length;

            // Perpendicular for thickness
            double px = -dy * thickness / 2;
            double py = dx * thickness / 2;

            // Create 8 vertices for the wall box
            // Bottom 4
            mesh.Positions.Add(new Point3D(x1 - px, y1 - py, 0));
            mesh.Positions.Add(new Point3D(x1 + px, y1 + py, 0));
            mesh.Positions.Add(new Point3D(x2 + px, y2 + py, 0));
            mesh.Positions.Add(new Point3D(x2 - px, y2 - py, 0));

            // Top 4
            mesh.Positions.Add(new Point3D(x1 - px, y1 - py, height));
            mesh.Positions.Add(new Point3D(x1 + px, y1 + py, height));
            mesh.Positions.Add(new Point3D(x2 + px, y2 + py, height));
            mesh.Positions.Add(new Point3D(x2 - px, y2 - py, height));

            // Front face (0,3,7,4)
            mesh.TriangleIndices.Add(0); mesh.TriangleIndices.Add(3); mesh.TriangleIndices.Add(7);
            mesh.TriangleIndices.Add(0); mesh.TriangleIndices.Add(7); mesh.TriangleIndices.Add(4);

            // Back face (1,2,6,5)
            mesh.TriangleIndices.Add(2); mesh.TriangleIndices.Add(1); mesh.TriangleIndices.Add(5);
            mesh.TriangleIndices.Add(2); mesh.TriangleIndices.Add(5); mesh.TriangleIndices.Add(6);

            // Left face (0,1,5,4)
            mesh.TriangleIndices.Add(1); mesh.TriangleIndices.Add(0); mesh.TriangleIndices.Add(4);
            mesh.TriangleIndices.Add(1); mesh.TriangleIndices.Add(4); mesh.TriangleIndices.Add(5);

            // Right face (2,3,7,6)
            mesh.TriangleIndices.Add(3); mesh.TriangleIndices.Add(2); mesh.TriangleIndices.Add(6);
            mesh.TriangleIndices.Add(3); mesh.TriangleIndices.Add(6); mesh.TriangleIndices.Add(7);

            // Top face (4,5,6,7)
            mesh.TriangleIndices.Add(4); mesh.TriangleIndices.Add(5); mesh.TriangleIndices.Add(6);
            mesh.TriangleIndices.Add(4); mesh.TriangleIndices.Add(6); mesh.TriangleIndices.Add(7);

            // Bottom face (0,1,2,3)
            mesh.TriangleIndices.Add(0); mesh.TriangleIndices.Add(2); mesh.TriangleIndices.Add(1);
            mesh.TriangleIndices.Add(0); mesh.TriangleIndices.Add(3); mesh.TriangleIndices.Add(2);

            var material = new DiffuseMaterial(new SolidColorBrush(Color.FromRgb(200, 180, 160)));
            var model = new GeometryModel3D(mesh, material);
            model.BackMaterial = material;

            return model;
        }

        #endregion
    }

    /// <summary>
    /// Dialog for entering calibration measurement (real-world length)
    /// </summary>
    public class CalibrationInputDialog : Window
    {
        public double RealWorldFeet { get; private set; } = 0;

        private TextBox _feetInput;
        private TextBox _inchesInput;
        private double _pixelDistance;

        public CalibrationInputDialog(double pixelDistance)
        {
            _pixelDistance = pixelDistance;

            Title = "Enter Real-World Length";
            Width = 350;
            Height = 220;
            WindowStartupLocation = WindowStartupLocation.CenterOwner;
            ResizeMode = ResizeMode.NoResize;
            Background = new SolidColorBrush(Color.FromRgb(45, 45, 48));

            var mainGrid = new Grid();
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); // Info
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); // Input
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); // Quick buttons
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); // Buttons
            mainGrid.Margin = new Thickness(15);

            // Info text
            var infoText = new TextBlock
            {
                Text = $"You drew a line of {pixelDistance:F0} pixels.\n\nEnter the real-world length this represents:",
                Foreground = Brushes.White,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 15)
            };
            Grid.SetRow(infoText, 0);
            mainGrid.Children.Add(infoText);

            // Input panel with feet and inches
            var inputPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 15) };

            _feetInput = new TextBox
            {
                Width = 60,
                Height = 30,
                FontSize = 14,
                Text = "10",
                VerticalContentAlignment = VerticalAlignment.Center,
                HorizontalContentAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 0, 5, 0)
            };
            inputPanel.Children.Add(_feetInput);
            inputPanel.Children.Add(new TextBlock { Text = "ft", Foreground = Brushes.White, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 0, 15, 0) });

            _inchesInput = new TextBox
            {
                Width = 60,
                Height = 30,
                FontSize = 14,
                Text = "0",
                VerticalContentAlignment = VerticalAlignment.Center,
                HorizontalContentAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 0, 5, 0)
            };
            inputPanel.Children.Add(_inchesInput);
            inputPanel.Children.Add(new TextBlock { Text = "in", Foreground = Brushes.White, VerticalAlignment = VerticalAlignment.Center });

            Grid.SetRow(inputPanel, 1);
            mainGrid.Children.Add(inputPanel);

            // Quick preset buttons for common lengths
            var quickPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 15) };
            quickPanel.Children.Add(CreateQuickButton("8'", 8, 0));
            quickPanel.Children.Add(CreateQuickButton("10'", 10, 0));
            quickPanel.Children.Add(CreateQuickButton("12'", 12, 0));
            quickPanel.Children.Add(CreateQuickButton("6\"", 0, 6)); // Wall thickness
            quickPanel.Children.Add(CreateQuickButton("3'", 3, 0)); // Door width

            Grid.SetRow(quickPanel, 2);
            mainGrid.Children.Add(quickPanel);

            // Buttons
            var buttonPanel = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };

            var cancelButton = new Button
            {
                Content = "Cancel",
                Width = 80,
                Height = 30,
                Margin = new Thickness(0, 0, 10, 0),
                Background = new SolidColorBrush(SketchPadColors.BgTertiary),
                Foreground = new SolidColorBrush(SketchPadColors.TextPrimary),
                BorderBrush = new SolidColorBrush(SketchPadColors.BorderLight)
            };
            cancelButton.Click += (s, e) => { DialogResult = false; Close(); };
            buttonPanel.Children.Add(cancelButton);

            var okButton = new Button
            {
                Content = "OK",
                Width = 80,
                Height = 30,
                IsDefault = true,
                Background = new SolidColorBrush(Color.FromRgb(0, 120, 215)),
                Foreground = Brushes.White,
                BorderBrush = new SolidColorBrush(Color.FromRgb(0, 100, 180))
            };
            okButton.Click += (s, e) => { TryAccept(); };
            buttonPanel.Children.Add(okButton);

            Grid.SetRow(buttonPanel, 3);
            mainGrid.Children.Add(buttonPanel);

            this.Content = mainGrid;

            // Focus the feet input when window opens
            this.Loaded += (s, e) => { _feetInput.Focus(); _feetInput.SelectAll(); };
        }

        private Button CreateQuickButton(string text, int feet, int inches)
        {
            var btn = new Button
            {
                Content = text,
                Width = 45,
                Height = 25,
                Margin = new Thickness(0, 0, 5, 0),
                Background = new SolidColorBrush(Color.FromRgb(70, 70, 75)),
                Foreground = Brushes.White,
                BorderBrush = new SolidColorBrush(Color.FromRgb(100, 100, 100)),
                FontSize = 10
            };
            btn.Click += (s, e) =>
            {
                _feetInput.Text = feet.ToString();
                _inchesInput.Text = inches.ToString();
            };
            return btn;
        }

        private void TryAccept()
        {
            if (double.TryParse(_feetInput.Text, out double feet) &&
                double.TryParse(_inchesInput.Text, out double inches))
            {
                RealWorldFeet = feet + (inches / 12.0);
                if (RealWorldFeet > 0)
                {
                    DialogResult = true;
                    Close();
                }
                else
                {
                    MessageBox.Show("Please enter a positive length.", "Invalid Input", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
            }
            else
            {
                MessageBox.Show("Please enter valid numbers.", "Invalid Input", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }
    }

    /// <summary>
    /// External event handler for creating walls in Revit
    /// This runs on Revit's main thread
    /// </summary>
    public class CreateWallHandler : IExternalEventHandler
    {
        private Document _doc;
        private double _startX, _startY, _endX, _endY;
        private ElementId _levelId, _wallTypeId;
        private double _height;
        private ElementId _lastCreatedId;

        // Reference to wall tracking
        public int WallIndex { get; set; } = -1;
        public List<SketchPadWindow.DrawnWall> DrawnWalls { get; set; }

        public ElementId LastCreatedId => _lastCreatedId;

        public void SetWallData(Document doc, double startX, double startY, double endX, double endY,
                                ElementId levelId, ElementId wallTypeId, double height)
        {
            _doc = doc;
            _startX = startX;
            _startY = startY;
            _endX = endX;
            _endY = endY;
            _levelId = levelId;
            _wallTypeId = wallTypeId;
            _height = height;
        }

        public void Execute(UIApplication app)
        {
            try
            {
                using (var trans = new Transaction(_doc, "SketchPad Wall"))
                {
                    trans.Start();

                    var startPt = new XYZ(_startX, _startY, 0);
                    var endPt = new XYZ(_endX, _endY, 0);
                    var line = Autodesk.Revit.DB.Line.CreateBound(startPt, endPt);

                    var wall = Wall.Create(_doc, line, _wallTypeId, _levelId, _height, 0, false, false);
                    _lastCreatedId = wall.Id;

                    // Update the drawn wall with the Revit element ID
                    if (WallIndex >= 0 && DrawnWalls != null && WallIndex < DrawnWalls.Count)
                    {
                        DrawnWalls[WallIndex].RevitElementId = (int)wall.Id.Value;
                    }

                    trans.Commit();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Wall creation failed: {ex.Message}");
            }
        }

        public string GetName()
        {
            return "SketchPad Create Wall";
        }
    }

    /// <summary>
    /// External event handler for placing doors in Revit walls
    /// </summary>
    public class CreateDoorHandler : IExternalEventHandler
    {
        private Document _doc;
        private double _x, _y;
        private ElementId _wallId;
        private ElementId _doorTypeId;
        private ElementId _levelId;

        public int DoorIndex { get; set; } = -1;
        public List<SketchPadWindow.PlacedOpening> PlacedDoors { get; set; }

        public void SetDoorData(Document doc, double x, double y, ElementId wallId, ElementId doorTypeId, ElementId levelId)
        {
            _doc = doc;
            _x = x;
            _y = y;
            _wallId = wallId;
            _doorTypeId = doorTypeId;
            _levelId = levelId;
        }

        public void Execute(UIApplication app)
        {
            try
            {
                using (var trans = new Transaction(_doc, "SketchPad Door"))
                {
                    trans.Start();

                    // Get the wall element
                    var wall = _doc.GetElement(_wallId) as Wall;
                    if (wall == null)
                    {
                        trans.RollBack();
                        return;
                    }

                    // Get the door family symbol
                    var doorSymbol = _doc.GetElement(_doorTypeId) as FamilySymbol;
                    if (doorSymbol == null)
                    {
                        trans.RollBack();
                        return;
                    }

                    // Activate the symbol if not already
                    if (!doorSymbol.IsActive)
                        doorSymbol.Activate();

                    // Get level
                    var level = _doc.GetElement(_levelId) as Level;

                    // Create location point
                    var location = new XYZ(_x, _y, level?.Elevation ?? 0);

                    // Create the door instance
                    var door = _doc.Create.NewFamilyInstance(location, doorSymbol, wall, level,
                        Autodesk.Revit.DB.Structure.StructuralType.NonStructural);

                    // Update the placed door with the Revit element ID
                    if (DoorIndex >= 0 && PlacedDoors != null && DoorIndex < PlacedDoors.Count)
                    {
                        PlacedDoors[DoorIndex].RevitElementId = (int)door.Id.Value;
                    }

                    trans.Commit();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Door creation failed: {ex.Message}");
            }
        }

        public string GetName()
        {
            return "SketchPad Create Door";
        }
    }

    /// <summary>
    /// External event handler for placing windows in Revit walls
    /// </summary>
    public class CreateWindowHandler : IExternalEventHandler
    {
        private Document _doc;
        private double _x, _y;
        private ElementId _wallId;
        private ElementId _windowTypeId;
        private ElementId _levelId;

        public int WindowIndex { get; set; } = -1;
        public List<SketchPadWindow.PlacedOpening> PlacedWindows { get; set; }

        public void SetWindowData(Document doc, double x, double y, ElementId wallId, ElementId windowTypeId, ElementId levelId)
        {
            _doc = doc;
            _x = x;
            _y = y;
            _wallId = wallId;
            _windowTypeId = windowTypeId;
            _levelId = levelId;
        }

        public void Execute(UIApplication app)
        {
            try
            {
                using (var trans = new Transaction(_doc, "SketchPad Window"))
                {
                    trans.Start();

                    // Get the wall element
                    var wall = _doc.GetElement(_wallId) as Wall;
                    if (wall == null)
                    {
                        trans.RollBack();
                        return;
                    }

                    // Get the window family symbol
                    var windowSymbol = _doc.GetElement(_windowTypeId) as FamilySymbol;
                    if (windowSymbol == null)
                    {
                        trans.RollBack();
                        return;
                    }

                    // Activate the symbol if not already
                    if (!windowSymbol.IsActive)
                        windowSymbol.Activate();

                    // Get level
                    var level = _doc.GetElement(_levelId) as Level;

                    // Create location point - windows need sill height offset
                    double sillHeight = 3.0; // Default 3 feet sill height
                    var location = new XYZ(_x, _y, (level?.Elevation ?? 0) + sillHeight);

                    // Create the window instance
                    var window = _doc.Create.NewFamilyInstance(location, windowSymbol, wall, level,
                        Autodesk.Revit.DB.Structure.StructuralType.NonStructural);

                    // Update the placed window with the Revit element ID
                    if (WindowIndex >= 0 && PlacedWindows != null && WindowIndex < PlacedWindows.Count)
                    {
                        PlacedWindows[WindowIndex].RevitElementId = (int)window.Id.Value;
                    }

                    trans.Commit();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Window creation failed: {ex.Message}");
            }
        }

        public string GetName()
        {
            return "SketchPad Create Window";
        }
    }

    /// <summary>
    /// External event handler for placing furniture, fixtures, casework, and electrical elements in Revit
    /// </summary>
    public class CreateElementHandler : IExternalEventHandler
    {
        private Document _doc;
        private double _x, _y;
        private double _rotation;
        private ElementId _typeId;
        private ElementId _levelId;
        private string _category;

        public int ElementIndex { get; set; } = -1;
        public List<SketchPadWindow.PlacedElement> PlacedElements { get; set; }

        public void SetElementData(Document doc, double x, double y, double rotation, ElementId typeId, ElementId levelId, string category)
        {
            _doc = doc;
            _x = x;
            _y = y;
            _rotation = rotation;
            _typeId = typeId;
            _levelId = levelId;
            _category = category;
        }

        public void Execute(UIApplication app)
        {
            try
            {
                using (var trans = new Transaction(_doc, $"SketchPad {_category}"))
                {
                    trans.Start();

                    // Get the family symbol
                    var familySymbol = _doc.GetElement(_typeId) as FamilySymbol;
                    if (familySymbol == null)
                    {
                        trans.RollBack();
                        return;
                    }

                    // Activate the symbol if not already
                    if (!familySymbol.IsActive)
                        familySymbol.Activate();

                    // Get level
                    var level = _doc.GetElement(_levelId) as Level;
                    double elevation = level?.Elevation ?? 0;

                    // Create location point at floor level
                    var location = new XYZ(_x, _y, elevation);

                    // Create the family instance
                    FamilyInstance instance = null;

                    // For face-based or work-plane-based families, we may need different placement
                    // Most furniture, casework, and plumbing fixtures are standalone
                    instance = _doc.Create.NewFamilyInstance(location, familySymbol, level,
                        Autodesk.Revit.DB.Structure.StructuralType.NonStructural);

                    if (instance != null)
                    {
                        // Apply rotation if specified
                        if (_rotation != 0)
                        {
                            var axis = Autodesk.Revit.DB.Line.CreateBound(
                                new XYZ(_x, _y, elevation),
                                new XYZ(_x, _y, elevation + 1)
                            );
                            ElementTransformUtils.RotateElement(_doc, instance.Id, axis, _rotation * Math.PI / 180);
                        }

                        // Update the placed element with the Revit element ID
                        if (ElementIndex >= 0 && PlacedElements != null && ElementIndex < PlacedElements.Count)
                        {
                            PlacedElements[ElementIndex].RevitElementId = (int)instance.Id.Value;
                        }
                    }

                    trans.Commit();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"{_category} creation failed: {ex.Message}");
            }
        }

        public string GetName()
        {
            return "SketchPad Create Element";
        }
    }

    /// <summary>
    /// External event handler for deleting elements in Revit
    /// </summary>
    public class DeleteElementHandler : IExternalEventHandler
    {
        private Document _doc;
        private List<ElementId> _elementIds = new List<ElementId>();

        public void SetDeleteData(Document doc, List<ElementId> elementIds)
        {
            _doc = doc;
            _elementIds = elementIds;
        }

        public void Execute(UIApplication app)
        {
            if (_doc == null || _elementIds == null || _elementIds.Count == 0)
                return;

            try
            {
                using (var trans = new Transaction(_doc, "SketchPad Delete"))
                {
                    trans.Start();

                    // Delete all elements
                    foreach (var id in _elementIds)
                    {
                        try
                        {
                            if (_doc.GetElement(id) != null)
                            {
                                _doc.Delete(id);
                            }
                        }
                        catch (Exception ex)
                        {
                            System.Diagnostics.Debug.WriteLine($"Failed to delete element {id}: {ex.Message}");
                        }
                    }

                    trans.Commit();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Delete transaction failed: {ex.Message}");
            }
            finally
            {
                _elementIds.Clear();
            }
        }

        public string GetName()
        {
            return "SketchPad Delete Elements";
        }
    }
}
