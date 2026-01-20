using System;
using System.Text;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Serilog;

namespace RevitMCPBridge.Commands
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class ServerStatusCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var server = RevitMCPBridgeApp.GetServer();
                var status = new StringBuilder();
                
                status.AppendLine("MCP Bridge Server Status");
                status.AppendLine("========================");
                status.AppendLine();
                
                if (server == null)
                {
                    status.AppendLine("Status: Not Initialized");
                    status.AppendLine("The MCP server has not been created yet.");
                }
                else
                {
                    status.AppendLine($"Status: {(server.IsRunning ? "Running" : "Stopped")}");
                    status.AppendLine($"Pipe Name: {server.PipeName}");
                    
                    if (server.IsRunning)
                    {
                        status.AppendLine();
                        status.AppendLine("Connection Information:");
                        status.AppendLine($"- Named Pipe: \\\\.\\pipe\\{server.PipeName}");
                        status.AppendLine("- Protocol: Model Context Protocol (MCP)");
                        status.AppendLine("- Transport: Named Pipes (Windows)");
                        status.AppendLine();
                        status.AppendLine("Available Methods:");
                        status.AppendLine("- ping: Test server connectivity");
                        status.AppendLine("- getProjectInfo: Get current project information");
                        status.AppendLine("- getElements: Query elements by category/view");
                        status.AppendLine("- getElementProperties: Get element parameters");
                        status.AppendLine("- getViews: List all views in project");
                        status.AppendLine("- getCategories: List all model categories");
                        status.AppendLine("- getParameters: Get element parameters");
                        status.AppendLine("- setParameter: Modify element parameters");
                        status.AppendLine("- executeCommand: Execute Revit commands");
                    }
                    else
                    {
                        status.AppendLine();
                        status.AppendLine("Click 'Start Server' to begin accepting MCP connections.");
                    }
                }
                
                status.AppendLine();
                status.AppendLine("Log Location:");
                var logPath = System.IO.Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "Autodesk", "Revit", "Addins", "2026", "Logs");
                status.AppendLine(logPath);
                
                var dialog = new TaskDialog("MCP Bridge Status");
                dialog.MainContent = status.ToString();
                dialog.MainIcon = TaskDialogIcon.TaskDialogIconInformation;
                dialog.Show();
                
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to get server status");
                message = ex.Message;
                return Result.Failed;
            }
        }
    }
}