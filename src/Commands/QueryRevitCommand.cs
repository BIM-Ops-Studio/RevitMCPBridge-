using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.DB.Mechanical;
using Autodesk.Revit.DB.Electrical;
using Autodesk.Revit.DB.Plumbing;
using Autodesk.Revit.UI;
using Serilog;
using Newtonsoft.Json;

namespace RevitMCPBridge.Commands
{
    public static class RichTextBoxExtensions
    {
        public static void InsertLink(this RichTextBox box, string text, string hyperlink)
        {
            int start = box.TextLength;
            box.AppendText(text);
            box.Select(start, text.Length);
            box.SetSelectionLink(true);
            box.Select(box.TextLength, 0);
        }
        
        public static void SetSelectionLink(this RichTextBox box, bool link)
        {
            // Simple hack to make text look like a link
            if (link)
            {
                box.SelectionColor = System.Drawing.Color.Blue;
                box.SelectionFont = new Font(box.SelectionFont, FontStyle.Underline);
            }
        }
    }
    [Transaction(TransactionMode.ReadOnly)]
    [Regeneration(RegenerationOption.Manual)]
    public class QueryRevitCommand : IExternalCommand
    {
        internal static List<string> queryHistory = new List<string>();
        
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var server = RevitMCPBridgeApp.GetServer();
                
                if (server == null || !server.IsRunning)
                {
                    Autodesk.Revit.UI.TaskDialog.Show("MCP Bridge", "Server is not running. Please start the server first.");
                    return Result.Cancelled;
                }
                
                // Create enhanced query dialog
                var dialog = new EnhancedQueryDialog(commandData.Application.ActiveUIDocument.Document);
                if (dialog.ShowDialog() != DialogResult.OK)
                    return Result.Cancelled;
                
                var query = dialog.QueryText;
                if (!string.IsNullOrWhiteSpace(query) && !queryHistory.Contains(query))
                {
                    queryHistory.Insert(0, query);
                    if (queryHistory.Count > 20) queryHistory.RemoveAt(20);
                }
                
                // Process the query with enhanced processor
                var processor = new AdvancedQueryProcessor();
                var result = processor.ProcessQuery(commandData.Application.ActiveUIDocument.Document, query);
                
                // Show results in enhanced dialog
                var resultsDialog = new QueryResultsDialog(query, result);
                resultsDialog.ShowDialog();
                
                Log.Information($"Query executed: {query}");
                
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to execute query");
                message = ex.Message;
                return Result.Failed;
            }
        }
    }
    
    // Enhanced query dialog with larger size and more features
    public class EnhancedQueryDialog : System.Windows.Forms.Form
    {
        private System.Windows.Forms.TextBox queryTextBox;
        private RichTextBox examplesTextBox;
        private System.Windows.Forms.ComboBox historyComboBox;
        private Button executeButton;
        private Button cancelButton;
        private Button helpButton;
        private Document doc;
        
        public string QueryText => queryTextBox.Text;
        
        public EnhancedQueryDialog(Document document)
        {
            doc = document;
            InitializeComponent();
            LoadExamples();
        }
        
        private void InitializeComponent()
        {
            this.Text = "Revit Model Query - Enhanced";
            this.Size = new Size(900, 700);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.MinimumSize = new Size(800, 600);
            
            // Main layout panel
            var mainPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 4,
                Padding = new Padding(10)
            };
            mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 60F));
            mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 40F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 50F));
            
            // Title label
            var titleLabel = new Label
            {
                Text = "Enter your Revit query:",
                Font = new Font("Segoe UI", 12F, FontStyle.Bold),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft
            };
            mainPanel.Controls.Add(titleLabel, 0, 0);
            
            // History combo box
            var historyPanel = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.LeftToRight
            };
            historyPanel.Controls.Add(new Label { Text = "History:", AutoSize = true, Padding = new Padding(0, 5, 5, 0) });
            historyComboBox = new System.Windows.Forms.ComboBox
            {
                Width = 250,
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            if (QueryRevitCommand.queryHistory.Count > 0)
            {
                historyComboBox.Items.AddRange(QueryRevitCommand.queryHistory.ToArray());
            }
            historyComboBox.SelectedIndexChanged += (s, e) =>
            {
                if (historyComboBox.SelectedIndex >= 0)
                    queryTextBox.Text = historyComboBox.SelectedItem.ToString();
            };
            historyPanel.Controls.Add(historyComboBox);
            mainPanel.Controls.Add(historyPanel, 1, 0);
            
            // Query text box
            queryTextBox = new System.Windows.Forms.TextBox
            {
                Multiline = true,
                Dock = DockStyle.Fill,
                Font = new Font("Consolas", 11F),
                ScrollBars = ScrollBars.Vertical,
                WordWrap = true
            };
            mainPanel.Controls.Add(queryTextBox, 0, 1);
            
            // Examples panel
            var examplesPanel = new System.Windows.Forms.Panel
            {
                Dock = DockStyle.Fill,
                BorderStyle = BorderStyle.FixedSingle
            };
            
            var examplesLabel = new Label
            {
                Text = "Example Queries (click to use):",
                Dock = DockStyle.Top,
                Height = 25,
                Font = new Font("Segoe UI", 10F, FontStyle.Bold),
                BackColor = System.Drawing.Color.LightGray,
                TextAlign = ContentAlignment.MiddleCenter
            };
            
            examplesTextBox = new RichTextBox
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                Font = new Font("Segoe UI", 9F),
                BackColor = System.Drawing.Color.WhiteSmoke,
                BorderStyle = BorderStyle.None
            };
            examplesTextBox.LinkClicked += (s, e) =>
            {
                queryTextBox.Text = e.LinkText;
            };
            
            examplesPanel.Controls.Add(examplesTextBox);
            examplesPanel.Controls.Add(examplesLabel);
            mainPanel.Controls.Add(examplesPanel, 1, 1);
            
            // Current document info
            var infoLabel = new Label
            {
                Text = $"Current Document: {doc.Title} | Active View: {doc.ActiveView.Name}",
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft,
                ForeColor = System.Drawing.Color.DarkBlue
            };
            mainPanel.Controls.Add(infoLabel, 0, 2);
            mainPanel.SetColumnSpan(infoLabel, 2);
            
            // Buttons panel
            var buttonPanel = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.RightToLeft
            };
            
            cancelButton = new Button
            {
                Text = "Cancel",
                Size = new Size(100, 35),
                DialogResult = DialogResult.Cancel
            };
            
            executeButton = new Button
            {
                Text = "Execute Query",
                Size = new Size(120, 35),
                Font = new Font("Segoe UI", 10F, FontStyle.Bold),
                DialogResult = DialogResult.OK,
                BackColor = System.Drawing.Color.LightGreen
            };
            
            helpButton = new Button
            {
                Text = "Help",
                Size = new Size(80, 35)
            };
            helpButton.Click += (s, e) => ShowHelp();
            
            buttonPanel.Controls.Add(cancelButton);
            buttonPanel.Controls.Add(executeButton);
            buttonPanel.Controls.Add(helpButton);
            
            mainPanel.Controls.Add(buttonPanel, 0, 3);
            mainPanel.SetColumnSpan(buttonPanel, 2);
            
            this.Controls.Add(mainPanel);
            this.AcceptButton = executeButton;
            this.CancelButton = cancelButton;
            
            // Focus on query textbox
            queryTextBox.Focus();
        }
        
        private void LoadExamples()
        {
            examplesTextBox.Clear();
            
            // Count queries
            AddSection("COUNTING ELEMENTS:");
            AddExample("count all walls");
            AddExample("count doors by level");
            AddExample("count windows by type");
            AddExample("count rooms");
            AddExample("count sheets");
            AddExample("count views");
            AddExample("count families");
            AddExample("count warnings");
            
            AddSection("\nFILTERING & SEARCHING:");
            AddExample("find walls thicker than 200mm");
            AddExample("find doors on Level 1");
            AddExample("find unplaced rooms");
            AddExample("find views not on sheets");
            AddExample("find elements by id 123456");
            AddExample("find families containing 'door'");
            
            AddSection("\nANALYSIS QUERIES:");
            AddExample("analyze wall types");
            AddExample("analyze room areas");
            AddExample("analyze view usage");
            AddExample("analyze family sizes");
            AddExample("analyze parameter usage");
            
            AddSection("\nPROJECT INFORMATION:");
            AddExample("project info");
            AddExample("list all levels");
            AddExample("list all phases");
            AddExample("list worksets");
            AddExample("list linked files");
            AddExample("list view templates");
            
            AddSection("\nELEMENT DETAILS:");
            AddExample("details of selected elements");
            AddExample("parameters of walls");
            AddExample("materials in project");
            AddExample("line styles");
            AddExample("fill patterns");
            
            AddSection("\nQUALITY CHECKS:");
            AddExample("check duplicate marks");
            AddExample("check untagged elements");
            AddExample("check naming standards");
            AddExample("check model extents");
        }
        
        private void AddSection(string sectionTitle)
        {
            examplesTextBox.SelectionFont = new Font("Segoe UI", 9F, FontStyle.Bold);
            examplesTextBox.SelectionColor = System.Drawing.Color.DarkBlue;
            examplesTextBox.AppendText(sectionTitle + "\n");
        }
        
        private void AddExample(string example)
        {
            examplesTextBox.SelectionFont = new Font("Segoe UI", 9F, FontStyle.Underline);
            examplesTextBox.SelectionColor = System.Drawing.Color.Blue;
            examplesTextBox.AppendText("• " + example);
            examplesTextBox.InsertLink(" [Click to use]", example);
            examplesTextBox.AppendText("\n");
        }
        
        private void ShowHelp()
        {
            var helpText = @"REVIT QUERY LANGUAGE HELP

BASIC SYNTAX:
- Use natural language queries
- Keywords: count, find, list, analyze, check, details
- Filters: by, with, without, containing, greater than, less than

SUPPORTED QUERIES:

1. COUNTING:
   count [element type] [filters]
   Examples: count walls, count doors by level

2. FINDING/FILTERING:
   find [element type] [conditions]
   Examples: find walls thicker than 300mm

3. LISTING:
   list [category]
   Examples: list levels, list view templates

4. ANALYSIS:
   analyze [aspect]
   Examples: analyze wall types, analyze room areas

5. CHECKING:
   check [quality aspect]
   Examples: check duplicate marks, check warnings

TIPS:
- Use 'selected' to work with current selection
- Add 'detailed' for more information
- Use 'export' to save results

Press Ctrl+Space for autocomplete suggestions.";

            MessageBox.Show(helpText, "Query Help", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }
    
    // Results dialog to show query results
    public class QueryResultsDialog : System.Windows.Forms.Form
    {
        private RichTextBox resultsTextBox;
        private Button exportButton;
        private Button copyButton;
        private Button closeButton;
        private string queryText;
        private string resultsText;
        
        public QueryResultsDialog(string query, string results)
        {
            queryText = query;
            resultsText = results;
            InitializeComponent();
            DisplayResults();
        }
        
        private void InitializeComponent()
        {
            this.Text = "Query Results";
            this.Size = new Size(800, 600);
            this.StartPosition = FormStartPosition.CenterScreen;
            
            var mainPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 3,
                ColumnCount = 1,
                Padding = new Padding(10)
            };
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 50F));
            
            // Query label
            var queryLabel = new Label
            {
                Text = $"Query: {queryText}",
                Dock = DockStyle.Fill,
                Font = new Font("Segoe UI", 11F, FontStyle.Bold),
                ForeColor = System.Drawing.Color.DarkBlue
            };
            mainPanel.Controls.Add(queryLabel, 0, 0);
            
            // Results text box
            resultsTextBox = new RichTextBox
            {
                Dock = DockStyle.Fill,
                Font = new Font("Consolas", 10F),
                ReadOnly = true,
                WordWrap = true,
                BorderStyle = BorderStyle.FixedSingle
            };
            mainPanel.Controls.Add(resultsTextBox, 0, 1);
            
            // Buttons panel
            var buttonPanel = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.RightToLeft
            };
            
            closeButton = new Button
            {
                Text = "Close",
                Size = new Size(100, 35),
                DialogResult = DialogResult.OK
            };
            
            copyButton = new Button
            {
                Text = "Copy Results",
                Size = new Size(120, 35)
            };
            copyButton.Click += (s, e) =>
            {
                Clipboard.SetText(resultsText);
                MessageBox.Show("Results copied to clipboard!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
            };
            
            exportButton = new Button
            {
                Text = "Export...",
                Size = new Size(100, 35)
            };
            exportButton.Click += (s, e) => ExportResults();
            
            buttonPanel.Controls.Add(closeButton);
            buttonPanel.Controls.Add(copyButton);
            buttonPanel.Controls.Add(exportButton);
            
            mainPanel.Controls.Add(buttonPanel, 0, 2);
            
            this.Controls.Add(mainPanel);
            this.AcceptButton = closeButton;
        }
        
        private void DisplayResults()
        {
            resultsTextBox.Clear();
            
            // Add timestamp
            resultsTextBox.SelectionFont = new Font("Consolas", 9F, FontStyle.Italic);
            resultsTextBox.SelectionColor = System.Drawing.Color.Gray;
            resultsTextBox.AppendText($"Executed at: {DateTime.Now:yyyy-MM-dd HH:mm:ss}\n");
            resultsTextBox.AppendText(new string('-', 80) + "\n\n");
            
            // Add results
            resultsTextBox.SelectionFont = new Font("Consolas", 10F, FontStyle.Regular);
            resultsTextBox.SelectionColor = System.Drawing.Color.Black;
            resultsTextBox.AppendText(resultsText);
        }
        
        private void ExportResults()
        {
            var saveDialog = new SaveFileDialog
            {
                Filter = "Text Files (*.txt)|*.txt|CSV Files (*.csv)|*.csv|JSON Files (*.json)|*.json",
                FileName = $"RevitQuery_{DateTime.Now:yyyyMMdd_HHmmss}"
            };
            
            if (saveDialog.ShowDialog() == DialogResult.OK)
            {
                try
                {
                    System.IO.File.WriteAllText(saveDialog.FileName, resultsText);
                    MessageBox.Show($"Results exported to:\n{saveDialog.FileName}", "Export Successful", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Export failed:\n{ex.Message}", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }
    }
    
    // Advanced query processor
    public class AdvancedQueryProcessor
    {
        public string ProcessQuery(Document doc, string query)
        {
            try
            {
                var lowerQuery = query.ToLower().Trim();
                var result = new StringBuilder();
                
                // Count queries
                if (lowerQuery.StartsWith("count"))
                {
                    return ProcessCountQuery(doc, lowerQuery);
                }
                // Find/search queries
                else if (lowerQuery.StartsWith("find") || lowerQuery.StartsWith("search"))
                {
                    return ProcessFindQuery(doc, lowerQuery);
                }
                // List queries
                else if (lowerQuery.StartsWith("list"))
                {
                    return ProcessListQuery(doc, lowerQuery);
                }
                // Analyze queries
                else if (lowerQuery.StartsWith("analyze") || lowerQuery.StartsWith("analyse"))
                {
                    return ProcessAnalyzeQuery(doc, lowerQuery);
                }
                // Check queries
                else if (lowerQuery.StartsWith("check"))
                {
                    return ProcessCheckQuery(doc, lowerQuery);
                }
                // Project info
                else if (lowerQuery.Contains("project info"))
                {
                    return GetProjectInfo(doc);
                }
                // Details queries
                else if (lowerQuery.StartsWith("details"))
                {
                    return ProcessDetailsQuery(doc, lowerQuery);
                }
                // Selected elements
                else if (lowerQuery.Contains("selected"))
                {
                    return ProcessSelectedElements(doc);
                }
                else
                {
                    return "Query not recognized. Try starting with: count, find, list, analyze, check, details\n\n" +
                           "Examples:\n" +
                           "- count walls\n" +
                           "- find doors on Level 1\n" +
                           "- list all levels\n" +
                           "- analyze room areas\n" +
                           "- check duplicate marks";
                }
            }
            catch (Exception ex)
            {
                return $"Error processing query: {ex.Message}";
            }
        }
        
        private string ProcessCountQuery(Document doc, string query)
        {
            var result = new StringBuilder();
            
            if (query.Contains("all walls") || query.Contains("walls"))
            {
                var walls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .WhereElementIsNotElementType()
                    .ToElements();
                
                result.AppendLine($"Total Walls: {walls.Count}");
                
                if (query.Contains("by level"))
                {
                    var wallsByLevel = walls.GroupBy(w => (w as Wall).LevelId);
                    result.AppendLine("\nWalls by Level:");
                    foreach (var group in wallsByLevel)
                    {
                        var level = doc.GetElement(group.Key) as Level;
                        result.AppendLine($"  {level?.Name ?? "Unknown"}: {group.Count()}");
                    }
                }
                else if (query.Contains("by type"))
                {
                    var wallsByType = walls.GroupBy(w => w.GetTypeId());
                    result.AppendLine("\nWalls by Type:");
                    foreach (var group in wallsByType)
                    {
                        var wallType = doc.GetElement(group.Key) as WallType;
                        result.AppendLine($"  {wallType?.Name ?? "Unknown"}: {group.Count()}");
                    }
                }
            }
            else if (query.Contains("doors"))
            {
                var doors = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsNotElementType()
                    .ToElements();
                
                result.AppendLine($"Total Doors: {doors.Count}");
                
                if (query.Contains("by level"))
                {
                    var doorsByLevel = doors.OfType<FamilyInstance>()
                        .GroupBy(d => d.LevelId);
                    result.AppendLine("\nDoors by Level:");
                    foreach (var group in doorsByLevel)
                    {
                        var level = doc.GetElement(group.Key) as Level;
                        result.AppendLine($"  {level?.Name ?? "Unknown"}: {group.Count()}");
                    }
                }
            }
            else if (query.Contains("windows"))
            {
                var windows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .ToElements();
                
                result.AppendLine($"Total Windows: {windows.Count}");
            }
            else if (query.Contains("rooms"))
            {
                var rooms = new FilteredElementCollector(doc)
                    .OfClass(typeof(SpatialElement))
                    .OfCategory(BuiltInCategory.OST_Rooms)
                    .ToElements();
                
                result.AppendLine($"Total Rooms: {rooms.Count}");
                
                var placedRooms = rooms.Cast<Room>().Where(r => r.Area > 0).Count();
                var unplacedRooms = rooms.Count - placedRooms;
                result.AppendLine($"  Placed: {placedRooms}");
                result.AppendLine($"  Unplaced: {unplacedRooms}");
            }
            else if (query.Contains("sheets"))
            {
                var sheets = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSheet))
                    .ToElements();
                
                result.AppendLine($"Total Sheets: {sheets.Count}");
            }
            else if (query.Contains("views"))
            {
                var views = new FilteredElementCollector(doc)
                    .OfClass(typeof(Autodesk.Revit.DB.View))
                    .WhereElementIsNotElementType()
                    .ToElements();
                
                result.AppendLine($"Total Views: {views.Count}");
                
                var viewsByType = views.Cast<Autodesk.Revit.DB.View>().GroupBy(v => v.ViewType);
                result.AppendLine("\nViews by Type:");
                foreach (var group in viewsByType)
                {
                    result.AppendLine($"  {group.Key}: {group.Count()}");
                }
            }
            else if (query.Contains("families"))
            {
                var families = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .ToElements();
                
                result.AppendLine($"Total Families: {families.Count}");
            }
            else if (query.Contains("warnings"))
            {
                var warnings = doc.GetWarnings();
                result.AppendLine($"Total Warnings: {warnings.Count}");
                
                var warningsByType = warnings.GroupBy(w => w.GetDescriptionText());
                result.AppendLine("\nWarnings by Type:");
                foreach (var group in warningsByType.Take(10))
                {
                    result.AppendLine($"  {group.Key}: {group.Count()}");
                }
            }
            else
            {
                // Generic count all element categories
                result.AppendLine("Element Count Summary:");
                result.AppendLine($"  Walls: {new FilteredElementCollector(doc).OfClass(typeof(Wall)).WhereElementIsNotElementType().GetElementCount()}");
                result.AppendLine($"  Doors: {new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().GetElementCount()}");
                result.AppendLine($"  Windows: {new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType().GetElementCount()}");
                result.AppendLine($"  Rooms: {new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).GetElementCount()}");
                result.AppendLine($"  Floors: {new FilteredElementCollector(doc).OfClass(typeof(Floor)).WhereElementIsNotElementType().GetElementCount()}");
                result.AppendLine($"  Roofs: {new FilteredElementCollector(doc).OfClass(typeof(RoofBase)).WhereElementIsNotElementType().GetElementCount()}");
                result.AppendLine($"  Columns: {new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Columns).WhereElementIsNotElementType().GetElementCount()}");
                result.AppendLine($"  Beams: {new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFraming).WhereElementIsNotElementType().GetElementCount()}");
            }
            
            return result.ToString();
        }
        
        private string ProcessFindQuery(Document doc, string query)
        {
            var result = new StringBuilder();
            
            if (query.Contains("walls") && query.Contains("thicker than"))
            {
                // Extract thickness value
                var parts = query.Split(new[] { "than" }, StringSplitOptions.None);
                if (parts.Length > 1)
                {
                    var thicknessStr = parts[1].Trim().Replace("mm", "").Replace("m", "");
                    if (double.TryParse(thicknessStr, out double thickness))
                    {
                        // Convert to feet if needed (Revit internal units)
                        if (query.Contains("mm"))
                            thickness = thickness / 304.8; // mm to feet
                        else if (!query.Contains("'") && !query.Contains("ft"))
                            thickness = thickness / 0.3048; // m to feet
                        
                        var walls = new FilteredElementCollector(doc)
                            .OfClass(typeof(Wall))
                            .WhereElementIsNotElementType()
                            .Cast<Wall>()
                            .Where(w => w.Width > thickness)
                            .ToList();
                        
                        result.AppendLine($"Found {walls.Count} walls thicker than {thicknessStr}:");
                        foreach (var wall in walls.Take(20))
                        {
                            var wallType = doc.GetElement(wall.GetTypeId()) as WallType;
                            result.AppendLine($"  ID: {wall.Id.Value} | Type: {wallType?.Name} | Thickness: {wall.Width * 304.8:F0}mm");
                        }
                        if (walls.Count > 20)
                            result.AppendLine($"  ... and {walls.Count - 20} more");
                    }
                }
            }
            else if (query.Contains("doors") && query.Contains("level"))
            {
                // Extract level name
                var levelName = "";
                if (query.Contains("level 1") || query.Contains("level1"))
                    levelName = "1";
                else if (query.Contains("level 2") || query.Contains("level2"))
                    levelName = "2";
                // Add more level parsing as needed
                
                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .Where(l => l.Name.Contains(levelName))
                    .ToList();
                
                if (levels.Any())
                {
                    foreach (var level in levels)
                    {
                        var doors = new FilteredElementCollector(doc)
                            .OfCategory(BuiltInCategory.OST_Doors)
                            .WhereElementIsNotElementType()
                            .Cast<FamilyInstance>()
                            .Where(d => d.LevelId == level.Id)
                            .ToList();
                        
                        result.AppendLine($"Doors on {level.Name}: {doors.Count}");
                        foreach (var door in doors.Take(10))
                        {
                            var doorType = doc.GetElement(door.GetTypeId()) as FamilySymbol;
                            result.AppendLine($"  ID: {door.Id.Value} | Type: {doorType?.Name} | Mark: {door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString()}");
                        }
                        if (doors.Count > 10)
                            result.AppendLine($"  ... and {doors.Count - 10} more");
                    }
                }
                else
                {
                    result.AppendLine("No matching level found.");
                }
            }
            else if (query.Contains("unplaced rooms"))
            {
                var unplacedRooms = new FilteredElementCollector(doc)
                    .OfClass(typeof(SpatialElement))
                    .OfCategory(BuiltInCategory.OST_Rooms)
                    .Cast<Room>()
                    .Where(r => r.Area == 0)
                    .ToList();
                
                result.AppendLine($"Found {unplacedRooms.Count} unplaced rooms:");
                foreach (var room in unplacedRooms.Take(20))
                {
                    result.AppendLine($"  ID: {room.Id.Value} | Name: {room.Name} | Number: {room.Number}");
                }
                if (unplacedRooms.Count > 20)
                    result.AppendLine($"  ... and {unplacedRooms.Count - 20} more");
            }
            else if (query.Contains("views not on sheets"))
            {
                var allViews = new FilteredElementCollector(doc)
                    .OfClass(typeof(Autodesk.Revit.DB.View))
                    .WhereElementIsNotElementType()
                    .Cast<Autodesk.Revit.DB.View>()
                    .Where(v => v.CanBePrinted && !v.IsTemplate)
                    .ToList();
                
                var viewsNotOnSheets = allViews
                    .Where(v => !v.GetDependentViewIds().Any())
                    .ToList();
                
                result.AppendLine($"Found {viewsNotOnSheets.Count} views not on sheets:");
                foreach (var view in viewsNotOnSheets.Take(20))
                {
                    result.AppendLine($"  {view.ViewType}: {view.Name}");
                }
                if (viewsNotOnSheets.Count > 20)
                    result.AppendLine($"  ... and {viewsNotOnSheets.Count - 20} more");
            }
            else if (query.Contains("elements by id"))
            {
                // Extract ID
                var idMatch = System.Text.RegularExpressions.Regex.Match(query, @"\d+");
                if (idMatch.Success && int.TryParse(idMatch.Value, out int elementId))
                {
                    var element = doc.GetElement(new ElementId(elementId));
                    if (element != null)
                    {
                        result.AppendLine($"Found element with ID {elementId}:");
                        result.AppendLine($"  Category: {element.Category?.Name}");
                        result.AppendLine($"  Name: {element.Name}");
                        result.AppendLine($"  Type: {element.GetType().Name}");
                        if (element.LevelId != ElementId.InvalidElementId)
                        {
                            var level = doc.GetElement(element.LevelId) as Level;
                            result.AppendLine($"  Level: {level?.Name}");
                        }
                    }
                    else
                    {
                        result.AppendLine($"No element found with ID {elementId}");
                    }
                }
            }
            else if (query.Contains("families containing"))
            {
                var searchTerm = query.Substring(query.IndexOf("containing") + 10).Trim().Trim('\'', '"');
                var families = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .Where(f => f.Name.IndexOf(searchTerm, StringComparison.OrdinalIgnoreCase) >= 0)
                    .ToList();
                
                result.AppendLine($"Found {families.Count} families containing '{searchTerm}':");
                foreach (var family in families.Take(20))
                {
                    result.AppendLine($"  {family.FamilyCategory.Name}: {family.Name}");
                }
                if (families.Count > 20)
                    result.AppendLine($"  ... and {families.Count - 20} more");
            }
            
            return result.ToString();
        }
        
        private string ProcessListQuery(Document doc, string query)
        {
            var result = new StringBuilder();
            
            if (query.Contains("levels"))
            {
                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .ToList();
                
                result.AppendLine($"Levels in project ({levels.Count} total):");
                foreach (var level in levels)
                {
                    result.AppendLine($"  {level.Name} | Elevation: {level.Elevation * 0.3048:F2}m ({level.Elevation:F2}')");
                }
            }
            else if (query.Contains("phases"))
            {
                var phases = doc.Phases;
                result.AppendLine($"Phases in project ({phases.Size} total):");
                foreach (Phase phase in phases)
                {
                    result.AppendLine($"  {phase.Name}");
                }
            }
            else if (query.Contains("worksets"))
            {
                if (doc.IsWorkshared)
                {
                    var worksets = new FilteredWorksetCollector(doc)
                        .OfKind(WorksetKind.UserWorkset)
                        .ToWorksets();
                    
                    result.AppendLine($"Worksets in project ({worksets.Count()} total):");
                    foreach (var workset in worksets)
                    {
                        result.AppendLine($"  {workset.Name} | Open: {workset.IsOpen} | Editable: {workset.IsEditable}");
                    }
                }
                else
                {
                    result.AppendLine("Project is not workshared.");
                }
            }
            else if (query.Contains("linked") || query.Contains("links"))
            {
                var links = new FilteredElementCollector(doc)
                    .OfClass(typeof(RevitLinkInstance))
                    .ToElements();
                
                result.AppendLine($"Linked files ({links.Count} total):");
                foreach (RevitLinkInstance link in links)
                {
                    var linkDoc = link.GetLinkDocument();
                    result.AppendLine($"  {link.Name}");
                    if (linkDoc != null)
                        result.AppendLine($"    Path: {linkDoc.PathName}");
                }
            }
            else if (query.Contains("view templates"))
            {
                var templates = new FilteredElementCollector(doc)
                    .OfClass(typeof(Autodesk.Revit.DB.View))
                    .Cast<Autodesk.Revit.DB.View>()
                    .Where(v => v.IsTemplate)
                    .OrderBy(v => v.ViewType)
                    .ThenBy(v => v.Name)
                    .ToList();
                
                result.AppendLine($"View Templates ({templates.Count} total):");
                var grouped = templates.GroupBy(v => v.ViewType);
                foreach (var group in grouped)
                {
                    result.AppendLine($"\n{group.Key}:");
                    foreach (var template in group)
                    {
                        result.AppendLine($"  {template.Name}");
                    }
                }
            }
            else if (query.Contains("materials"))
            {
                var materials = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .OrderBy(m => m.Name)
                    .ToList();
                
                result.AppendLine($"Materials in project ({materials.Count} total):");
                foreach (var material in materials.Take(50))
                {
                    result.AppendLine($"  {material.Name} | Class: {material.MaterialClass}");
                }
                if (materials.Count > 50)
                    result.AppendLine($"  ... and {materials.Count - 50} more");
            }
            else if (query.Contains("line styles"))
            {
                var lineStyles = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines)
                    .SubCategories.Cast<Category>()
                    .OrderBy(c => c.Name)
                    .ToList();
                
                result.AppendLine($"Line Styles ({lineStyles.Count} total):");
                foreach (var style in lineStyles)
                {
                    result.AppendLine($"  {style.Name}");
                }
            }
            
            return result.ToString();
        }
        
        private string ProcessAnalyzeQuery(Document doc, string query)
        {
            var result = new StringBuilder();
            
            if (query.Contains("wall types"))
            {
                var walls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .WhereElementIsNotElementType()
                    .Cast<Wall>()
                    .ToList();
                
                var wallTypeUsage = walls.GroupBy(w => w.GetTypeId())
                    .Select(g => new
                    {
                        TypeId = g.Key,
                        Count = g.Count(),
                        TotalLength = g.Sum(w => w.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)?.AsDouble() ?? 0),
                        TotalArea = g.Sum(w => w.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() ?? 0)
                    })
                    .OrderByDescending(x => x.Count)
                    .ToList();
                
                result.AppendLine("Wall Type Analysis:");
                result.AppendLine($"Total wall instances: {walls.Count}");
                result.AppendLine($"Unique wall types used: {wallTypeUsage.Count}");
                result.AppendLine("\nTop Wall Types by Usage:");
                
                foreach (var usage in wallTypeUsage.Take(10))
                {
                    var wallType = doc.GetElement(usage.TypeId) as WallType;
                    result.AppendLine($"\n{wallType?.Name}:");
                    result.AppendLine($"  Count: {usage.Count}");
                    result.AppendLine($"  Total Length: {usage.TotalLength * 0.3048:F2}m");
                    result.AppendLine($"  Total Area: {usage.TotalArea * 0.092903:F2}m²");
                }
            }
            else if (query.Contains("room areas"))
            {
                var rooms = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Rooms)
                    .Cast<Room>()
                    .Where(r => r.Area > 0)
                    .ToList();
                
                if (rooms.Any())
                {
                    var totalArea = rooms.Sum(r => r.Area);
                    var avgArea = totalArea / rooms.Count;
                    var minRoom = rooms.OrderBy(r => r.Area).First();
                    var maxRoom = rooms.OrderByDescending(r => r.Area).First();
                    
                    result.AppendLine("Room Area Analysis:");
                    result.AppendLine($"Total Rooms: {rooms.Count}");
                    result.AppendLine($"Total Area: {totalArea * 0.092903:F2}m² ({totalArea:F2}ft²)");
                    result.AppendLine($"Average Area: {avgArea * 0.092903:F2}m² ({avgArea:F2}ft²)");
                    result.AppendLine($"\nSmallest Room: {minRoom.Name} - {minRoom.Area * 0.092903:F2}m²");
                    result.AppendLine($"Largest Room: {maxRoom.Name} - {maxRoom.Area * 0.092903:F2}m²");
                    
                    // Area distribution
                    result.AppendLine("\nArea Distribution:");
                    var ranges = new[] { 10, 20, 50, 100, 200 }; // m²
                    foreach (var range in ranges)
                    {
                        var count = rooms.Count(r => r.Area * 0.092903 < range);
                        result.AppendLine($"  < {range}m²: {count} rooms");
                    }
                }
            }
            else if (query.Contains("view usage"))
            {
                var views = new FilteredElementCollector(doc)
                    .OfClass(typeof(Autodesk.Revit.DB.View))
                    .WhereElementIsNotElementType()
                    .Cast<Autodesk.Revit.DB.View>()
                    .Where(v => !v.IsTemplate)
                    .ToList();
                
                var viewsOnSheets = views.Where(v => v.GetDependentViewIds().Any()).Count();
                var viewsByType = views.GroupBy(v => v.ViewType);
                
                result.AppendLine("View Usage Analysis:");
                result.AppendLine($"Total Views: {views.Count}");
                result.AppendLine($"Views on Sheets: {viewsOnSheets} ({(double)viewsOnSheets / views.Count * 100:F1}%)");
                result.AppendLine($"Views not on Sheets: {views.Count - viewsOnSheets}");
                
                result.AppendLine("\nViews by Type:");
                foreach (var group in viewsByType.OrderByDescending(g => g.Count()))
                {
                    var onSheets = group.Where(v => v.GetDependentViewIds().Any()).Count();
                    result.AppendLine($"  {group.Key}: {group.Count()} total, {onSheets} on sheets");
                }
            }
            else if (query.Contains("family sizes"))
            {
                var families = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .ToList();
                
                var familyData = families.Select(f => new
                {
                    Family = f,
                    SymbolCount = f.GetFamilySymbolIds().Count,
                    InstanceCount = new FilteredElementCollector(doc)
                        .OfClass(typeof(FamilyInstance))
                        .Cast<FamilyInstance>()
                        .Count(fi => fi.Symbol.Family.Id == f.Id)
                })
                .OrderByDescending(x => x.InstanceCount)
                .ToList();
                
                result.AppendLine("Family Size Analysis:");
                result.AppendLine($"Total Families: {families.Count}");
                result.AppendLine($"Total Family Types: {familyData.Sum(x => x.SymbolCount)}");
                result.AppendLine($"Total Family Instances: {familyData.Sum(x => x.InstanceCount)}");
                
                result.AppendLine("\nTop 10 Families by Instance Count:");
                foreach (var data in familyData.Take(10))
                {
                    result.AppendLine($"  {data.Family.Name}:");
                    result.AppendLine($"    Types: {data.SymbolCount}, Instances: {data.InstanceCount}");
                }
            }
            
            return result.ToString();
        }
        
        private string ProcessCheckQuery(Document doc, string query)
        {
            var result = new StringBuilder();
            
            if (query.Contains("duplicate marks"))
            {
                var markedElements = new FilteredElementCollector(doc)
                    .WhereElementIsNotElementType()
                    .Where(e => e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK) != null)
                    .ToList();
                
                var markGroups = markedElements
                    .GroupBy(e => e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString())
                    .Where(g => !string.IsNullOrEmpty(g.Key) && g.Count() > 1)
                    .OrderByDescending(g => g.Count())
                    .ToList();
                
                result.AppendLine($"Duplicate Mark Check:");
                result.AppendLine($"Found {markGroups.Count} duplicate marks");
                
                foreach (var group in markGroups.Take(20))
                {
                    result.AppendLine($"\nMark '{group.Key}' used {group.Count()} times:");
                    foreach (var elem in group.Take(5))
                    {
                        result.AppendLine($"  {elem.Category?.Name} - ID: {elem.Id.Value}");
                    }
                    if (group.Count() > 5)
                        result.AppendLine($"  ... and {group.Count() - 5} more");
                }
            }
            else if (query.Contains("untagged"))
            {
                // Check for untagged doors
                var doors = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsNotElementType()
                    .ToElements();
                
                var doorTags = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_DoorTags)
                    .ToElements();
                
                var taggedDoorIds = new HashSet<ElementId>();
                foreach (IndependentTag tag in doorTags)
                {
                    var taggedIds = tag.GetTaggedElementIds();
                    if (taggedIds != null && taggedIds.Count > 0)
                    {
                        var firstId = taggedIds.First();
                        if (firstId != null && firstId.HostElementId != ElementId.InvalidElementId)
                        {
                            taggedDoorIds.Add(firstId.HostElementId);
                        }
                    }
                }
                
                var untaggedDoors = doors.Where(d => !taggedDoorIds.Contains(d.Id)).ToList();
                
                result.AppendLine($"Untagged Elements Check:");
                result.AppendLine($"Untagged Doors: {untaggedDoors.Count} of {doors.Count}");
                
                // Similar checks for windows, rooms, etc.
            }
            else if (query.Contains("naming standards"))
            {
                result.AppendLine("Naming Standards Check:");
                
                // Check view naming
                var views = new FilteredElementCollector(doc)
                    .OfClass(typeof(Autodesk.Revit.DB.View))
                    .WhereElementIsNotElementType()
                    .Cast<Autodesk.Revit.DB.View>()
                    .Where(v => !v.IsTemplate)
                    .ToList();
                
                var viewsWithSpaces = views.Where(v => v.Name.Contains("  ")).ToList();
                var viewsStartingWithNumber = views.Where(v => char.IsDigit(v.Name.FirstOrDefault())).ToList();
                
                result.AppendLine($"\nViews with double spaces: {viewsWithSpaces.Count}");
                result.AppendLine($"Views starting with numbers: {viewsStartingWithNumber.Count}");
                
                // Check family naming
                var families = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .ToList();
                
                var familiesWithSpecialChars = families
                    .Where(f => f.Name.Any(c => !char.IsLetterOrDigit(c) && c != ' ' && c != '-' && c != '_'))
                    .ToList();
                
                result.AppendLine($"\nFamilies with special characters: {familiesWithSpecialChars.Count}");
            }
            else if (query.Contains("model extents"))
            {
                var allElements = new FilteredElementCollector(doc)
                    .WhereElementIsNotElementType()
                    .Where(e => e.get_BoundingBox(null) != null)
                    .ToList();
                
                if (allElements.Any())
                {
                    var minX = allElements.Min(e => e.get_BoundingBox(null).Min.X);
                    var minY = allElements.Min(e => e.get_BoundingBox(null).Min.Y);
                    var minZ = allElements.Min(e => e.get_BoundingBox(null).Min.Z);
                    var maxX = allElements.Max(e => e.get_BoundingBox(null).Max.X);
                    var maxY = allElements.Max(e => e.get_BoundingBox(null).Max.Y);
                    var maxZ = allElements.Max(e => e.get_BoundingBox(null).Max.Z);
                    
                    var width = (maxX - minX) * 0.3048;
                    var depth = (maxY - minY) * 0.3048;
                    var height = (maxZ - minZ) * 0.3048;
                    
                    result.AppendLine("Model Extents Check:");
                    result.AppendLine($"Model Dimensions:");
                    result.AppendLine($"  Width (X): {width:F2}m");
                    result.AppendLine($"  Depth (Y): {depth:F2}m");
                    result.AppendLine($"  Height (Z): {height:F2}m");
                    
                    // Check for elements far from origin
                    var distanceFromOrigin = Math.Sqrt(minX * minX + minY * minY) * 0.3048;
                    if (distanceFromOrigin > 1000) // More than 1km from origin
                    {
                        result.AppendLine($"\nWARNING: Model is {distanceFromOrigin:F0}m from origin!");
                        result.AppendLine("This may cause accuracy issues.");
                    }
                }
            }
            
            return result.ToString();
        }
        
        private string GetProjectInfo(Document doc)
        {
            var result = new StringBuilder();
            var projInfo = doc.ProjectInformation;
            
            result.AppendLine("PROJECT INFORMATION");
            result.AppendLine("==================");
            result.AppendLine($"Project Name: {projInfo.Name}");
            result.AppendLine($"Project Number: {projInfo.Number}");
            result.AppendLine($"Client Name: {projInfo.ClientName}");
            result.AppendLine($"Project Address: {projInfo.Address}");
            result.AppendLine($"Status: {projInfo.Status}");
            result.AppendLine($"Issue Date: {projInfo.IssueDate}");
            
            result.AppendLine($"\nFile Path: {doc.PathName}");
            result.AppendLine($"Workshared: {doc.IsWorkshared}");
            result.AppendLine($"File Size: {new System.IO.FileInfo(doc.PathName).Length / 1024 / 1024:F2} MB");
            
            // Units
            result.AppendLine($"\nUnits: {doc.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId().TypeId}");
            
            // Coordinates
            var projectLocation = doc.ActiveProjectLocation;
            var siteLocation = projectLocation.GetSiteLocation();
            result.AppendLine($"\nProject Location: {projectLocation.Name}");
            result.AppendLine($"Latitude: {siteLocation.Latitude * 180 / Math.PI:F6}°");
            result.AppendLine($"Longitude: {siteLocation.Longitude * 180 / Math.PI:F6}°");
            
            return result.ToString();
        }
        
        private string ProcessDetailsQuery(Document doc, string query)
        {
            var result = new StringBuilder();
            
            if (query.Contains("selected"))
            {
                return ProcessSelectedElements(doc);
            }
            else if (query.Contains("parameters"))
            {
                // Show parameter details for a category
                if (query.Contains("walls"))
                {
                    var wall = new FilteredElementCollector(doc)
                        .OfClass(typeof(Wall))
                        .WhereElementIsNotElementType()
                        .FirstElement();
                    
                    if (wall != null)
                    {
                        result.AppendLine("Wall Parameters:");
                        foreach (Parameter param in wall.Parameters)
                        {
                            if (param.HasValue)
                            {
                                var value = param.StorageType switch
                                {
                                    StorageType.Double => param.AsDouble().ToString("F2"),
                                    StorageType.Integer => param.AsInteger().ToString(),
                                    StorageType.String => param.AsString(),
                                    StorageType.ElementId => param.AsElementId().Value.ToString(),
                                    _ => "N/A"
                                };
                                result.AppendLine($"  {param.Definition.Name}: {value}");
                            }
                        }
                    }
                }
            }
            
            return result.ToString();
        }
        
        private string ProcessSelectedElements(Document doc)
        {
            var uidoc = new UIDocument(doc);
            var selection = uidoc.Selection.GetElementIds();
            var result = new StringBuilder();
            
            if (selection.Count == 0)
            {
                result.AppendLine("No elements selected.");
                result.AppendLine("\nTip: Select elements in Revit before running this query.");
            }
            else
            {
                result.AppendLine($"Selected Elements: {selection.Count}");
                result.AppendLine(new string('-', 50));
                
                foreach (var id in selection.Take(20))
                {
                    var elem = doc.GetElement(id);
                    result.AppendLine($"\nElement ID: {id.Value}");
                    result.AppendLine($"Category: {elem.Category?.Name ?? "N/A"}");
                    result.AppendLine($"Name: {elem.Name}");
                    result.AppendLine($"Type: {elem.GetType().Name}");
                    
                    // Show key parameters
                    var mark = elem.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString();
                    if (!string.IsNullOrEmpty(mark))
                        result.AppendLine($"Mark: {mark}");
                    
                    if (elem.LevelId != ElementId.InvalidElementId)
                    {
                        var level = doc.GetElement(elem.LevelId) as Level;
                        result.AppendLine($"Level: {level?.Name}");
                    }
                    
                    // Show type name
                    var typeId = elem.GetTypeId();
                    if (typeId != ElementId.InvalidElementId)
                    {
                        var type = doc.GetElement(typeId);
                        result.AppendLine($"Type Name: {type?.Name}");
                    }
                }
                
                if (selection.Count > 20)
                    result.AppendLine($"\n... and {selection.Count - 20} more elements");
            }
            
            return result.ToString();
        }
    }
}