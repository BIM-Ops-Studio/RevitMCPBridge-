using System;
using System.IO;
using System.Windows.Forms;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Serilog;
using Newtonsoft.Json;

namespace RevitMCPBridge.Commands
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class SettingsCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var settings = MCPSettings.Load();
                var dialog = new SettingsDialog(settings);
                
                if (dialog.ShowDialog() == DialogResult.OK)
                {
                    settings.Save();
                    
                    // Restart server if it's running with new settings
                    var server = RevitMCPBridgeApp.GetServer();
                    if (server != null && server.IsRunning)
                    {
                        var result = Autodesk.Revit.UI.TaskDialog.Show("MCP Bridge", 
                            "Settings have been saved. Restart the server to apply changes?",
                            TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No);
                            
                        if (result == TaskDialogResult.Yes)
                        {
                            server.Stop();
                            server.Start();
                        }
                    }
                    else
                    {
                        Autodesk.Revit.UI.TaskDialog.Show("MCP Bridge", "Settings saved successfully.");
                    }
                }
                
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to open settings");
                message = ex.Message;
                return Result.Failed;
            }
        }
    }
    
    public class MCPSettings
    {
        public string PipeName { get; set; } = "RevitMCPBridge2026";
        public bool AutoStartServer { get; set; } = true;
        public bool EnableDebugLogging { get; set; } = false;
        public int MaxLogFileSizeMB { get; set; } = 10;
        public int MaxLogFiles { get; set; } = 7;
        
        private static string SettingsPath => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "Autodesk", "Revit", "Addins", "2026", "MCPBridgeSettings.json");
        
        public static MCPSettings Load()
        {
            try
            {
                if (File.Exists(SettingsPath))
                {
                    var json = File.ReadAllText(SettingsPath);
                    return JsonConvert.DeserializeObject<MCPSettings>(json);
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to load settings");
            }
            
            return new MCPSettings();
        }
        
        public void Save()
        {
            try
            {
                var json = JsonConvert.SerializeObject(this, Formatting.Indented);
                var dir = Path.GetDirectoryName(SettingsPath);
                if (!Directory.Exists(dir))
                    Directory.CreateDirectory(dir);
                    
                File.WriteAllText(SettingsPath, json);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to save settings");
                throw;
            }
        }
    }
    
    public class SettingsDialog : System.Windows.Forms.Form
    {
        private MCPSettings _settings;
        private System.Windows.Forms.TextBox pipeNameTextBox;
        private System.Windows.Forms.CheckBox autoStartCheckBox;
        private System.Windows.Forms.CheckBox debugLoggingCheckBox;
        private System.Windows.Forms.NumericUpDown maxLogSizeUpDown;
        private System.Windows.Forms.NumericUpDown maxLogFilesUpDown;
        
        public SettingsDialog(MCPSettings settings)
        {
            _settings = settings;
            InitializeComponent();
            LoadSettings();
        }
        
        private void InitializeComponent()
        {
            this.Text = "MCP Bridge Settings";
            this.Size = new System.Drawing.Size(400, 350);
            this.StartPosition = FormStartPosition.CenterScreen;
            
            var y = 10;
            
            // Pipe Name
            var pipeLabel = new System.Windows.Forms.Label
            {
                Text = "Pipe Name:",
                Location = new System.Drawing.Point(10, y),
                Size = new System.Drawing.Size(100, 20)
            };
            
            pipeNameTextBox = new System.Windows.Forms.TextBox
            {
                Location = new System.Drawing.Point(120, y),
                Size = new System.Drawing.Size(250, 20)
            };
            
            y += 30;
            
            // Auto Start
            autoStartCheckBox = new System.Windows.Forms.CheckBox
            {
                Text = "Auto-start server when Revit starts",
                Location = new System.Drawing.Point(10, y),
                Size = new System.Drawing.Size(350, 20)
            };
            
            y += 30;
            
            // Debug Logging
            debugLoggingCheckBox = new System.Windows.Forms.CheckBox
            {
                Text = "Enable debug logging",
                Location = new System.Drawing.Point(10, y),
                Size = new System.Drawing.Size(350, 20)
            };
            
            y += 40;
            
            // Max Log Size
            var maxSizeLabel = new System.Windows.Forms.Label
            {
                Text = "Max log file size (MB):",
                Location = new System.Drawing.Point(10, y),
                Size = new System.Drawing.Size(150, 20)
            };
            
            maxLogSizeUpDown = new System.Windows.Forms.NumericUpDown
            {
                Location = new System.Drawing.Point(170, y),
                Size = new System.Drawing.Size(100, 20),
                Minimum = 1,
                Maximum = 100,
                Value = 10
            };
            
            y += 30;
            
            // Max Log Files
            var maxFilesLabel = new System.Windows.Forms.Label
            {
                Text = "Max log files to keep:",
                Location = new System.Drawing.Point(10, y),
                Size = new System.Drawing.Size(150, 20)
            };
            
            maxLogFilesUpDown = new System.Windows.Forms.NumericUpDown
            {
                Location = new System.Drawing.Point(170, y),
                Size = new System.Drawing.Size(100, 20),
                Minimum = 1,
                Maximum = 30,
                Value = 7
            };
            
            y += 50;
            
            // Buttons
            var okButton = new System.Windows.Forms.Button
            {
                Text = "OK",
                DialogResult = DialogResult.OK,
                Location = new System.Drawing.Point(210, y),
                Size = new System.Drawing.Size(75, 23)
            };
            
            var cancelButton = new System.Windows.Forms.Button
            {
                Text = "Cancel",
                DialogResult = DialogResult.Cancel,
                Location = new System.Drawing.Point(295, y),
                Size = new System.Drawing.Size(75, 23)
            };
            
            this.Controls.AddRange(new System.Windows.Forms.Control[] {
                pipeLabel, pipeNameTextBox,
                autoStartCheckBox, debugLoggingCheckBox,
                maxSizeLabel, maxLogSizeUpDown,
                maxFilesLabel, maxLogFilesUpDown,
                okButton, cancelButton
            });
            
            this.AcceptButton = okButton;
            this.CancelButton = cancelButton;
            
            okButton.Click += (s, e) => SaveSettings();
        }
        
        private void LoadSettings()
        {
            pipeNameTextBox.Text = _settings.PipeName;
            autoStartCheckBox.Checked = _settings.AutoStartServer;
            debugLoggingCheckBox.Checked = _settings.EnableDebugLogging;
            maxLogSizeUpDown.Value = _settings.MaxLogFileSizeMB;
            maxLogFilesUpDown.Value = _settings.MaxLogFiles;
        }
        
        private void SaveSettings()
        {
            _settings.PipeName = pipeNameTextBox.Text;
            _settings.AutoStartServer = autoStartCheckBox.Checked;
            _settings.EnableDebugLogging = debugLoggingCheckBox.Checked;
            _settings.MaxLogFileSizeMB = (int)maxLogSizeUpDown.Value;
            _settings.MaxLogFiles = (int)maxLogFilesUpDown.Value;
        }
    }
}
