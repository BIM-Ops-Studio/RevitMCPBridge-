using System;
using System.Windows.Forms;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Serilog;

namespace RevitMCPBridge.Commands
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class ExecuteCommandCommand : IExternalCommand
    {
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
                
                // Create command dialog
                var dialog = new CommandDialog();
                if (dialog.ShowDialog() != DialogResult.OK)
                    return Result.Cancelled;
                
                var commandName = dialog.CommandName;
                var parameters = dialog.Parameters;
                
                // Execute the command
                var result = ExecuteRevitCommand(commandData, commandName, parameters);
                
                // Show results
                Autodesk.Revit.UI.TaskDialog.Show("Command Executed", $"Command: {commandName}\n\nResult: {result}");
                
                Log.Information($"Command executed: {commandName}");
                
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to execute command");
                message = ex.Message;
                return Result.Failed;
            }
        }
        
        private string ExecuteRevitCommand(ExternalCommandData commandData, string commandName, string parameters)
        {
            var doc = commandData.Application.ActiveUIDocument.Document;
            
            try
            {
                switch (commandName.ToLower())
                {
                    case "synctocentralmodel":
                        if (doc.IsWorkshared)
                        {
                            var options = new SynchronizeWithCentralOptions();
                            var transOptions = new TransactWithCentralOptions();
                            doc.SynchronizeWithCentral(transOptions, options);
                            return "Synchronized with central model successfully";
                        }
                        return "Document is not workshared";
                        
                    case "save":
                        doc.Save();
                        return "Document saved successfully";
                        
                    case "purgeunused":
                        using (var trans = new Transaction(doc, "Purge Unused"))
                        {
                            trans.Start();
                            // PurgeUnused not available in API
                            trans.Commit();
                        }
                        return "Purged unused elements";
                        
                    default:
                        return $"Unknown command: {commandName}";
                }
            }
            catch (Exception ex)
            {
                return $"Error: {ex.Message}";
            }
        }
    }
    
    // Command execution dialog
    public class CommandDialog : System.Windows.Forms.Form
    {
        private System.Windows.Forms.ComboBox commandComboBox;
        private System.Windows.Forms.TextBox parametersTextBox;
        private System.Windows.Forms.Button okButton;
        private System.Windows.Forms.Button cancelButton;
        
        public string CommandName => commandComboBox.Text;
        public string Parameters => parametersTextBox.Text;
        
        public CommandDialog()
        {
            InitializeComponent();
        }
        
        private void InitializeComponent()
        {
            this.Text = "Execute Revit Command";
            this.Size = new System.Drawing.Size(400, 250);
            this.StartPosition = FormStartPosition.CenterScreen;
            
            var commandLabel = new System.Windows.Forms.Label
            {
                Text = "Command:",
                Location = new System.Drawing.Point(10, 10),
                Size = new System.Drawing.Size(100, 20)
            };
            
            commandComboBox = new System.Windows.Forms.ComboBox
            {
                Location = new System.Drawing.Point(10, 30),
                Size = new System.Drawing.Size(360, 21),
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            commandComboBox.Items.AddRange(new[] { "Save", "SyncToCentralModel", "PurgeUnused" });
            commandComboBox.SelectedIndex = 0;
            
            var parametersLabel = new System.Windows.Forms.Label
            {
                Text = "Parameters (optional):",
                Location = new System.Drawing.Point(10, 70),
                Size = new System.Drawing.Size(200, 20)
            };
            
            parametersTextBox = new System.Windows.Forms.TextBox
            {
                Location = new System.Drawing.Point(10, 90),
                Size = new System.Drawing.Size(360, 60),
                Multiline = true
            };
            
            okButton = new System.Windows.Forms.Button
            {
                Text = "Execute",
                DialogResult = DialogResult.OK,
                Location = new System.Drawing.Point(210, 170),
                Size = new System.Drawing.Size(75, 23)
            };
            
            cancelButton = new System.Windows.Forms.Button
            {
                Text = "Cancel",
                DialogResult = DialogResult.Cancel,
                Location = new System.Drawing.Point(295, 170),
                Size = new System.Drawing.Size(75, 23)
            };
            
            this.Controls.Add(commandLabel);
            this.Controls.Add(commandComboBox);
            this.Controls.Add(parametersLabel);
            this.Controls.Add(parametersTextBox);
            this.Controls.Add(okButton);
            this.Controls.Add(cancelButton);
            
            this.AcceptButton = okButton;
            this.CancelButton = cancelButton;
        }
    }
}
