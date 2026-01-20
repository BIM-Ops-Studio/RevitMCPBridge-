using System;
using System.IO;
using System.Diagnostics;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Serilog;

namespace RevitMCPBridge.Commands
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class ViewLogsCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var logPath = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "Autodesk", "Revit", "Addins", "2026", "Logs");
                
                if (!Directory.Exists(logPath))
                {
                    TaskDialog.Show("MCP Bridge", "No log files found.");
                    return Result.Succeeded;
                }
                
                // Find the most recent log file
                var logFiles = Directory.GetFiles(logPath, "mcp_*.log");
                
                if (logFiles.Length == 0)
                {
                    TaskDialog.Show("MCP Bridge", "No MCP Bridge log files found.");
                    return Result.Succeeded;
                }
                
                // Sort by creation date and get the most recent
                Array.Sort(logFiles, (a, b) => File.GetCreationTime(b).CompareTo(File.GetCreationTime(a)));
                var latestLog = logFiles[0];
                
                // Open with Notepad
                var processInfo = new ProcessStartInfo
                {
                    FileName = "notepad.exe",
                    Arguments = $"\"{latestLog}\"",
                    UseShellExecute = false
                };
                Process.Start(processInfo);

                Log.Information($"Opened log file: {latestLog}");
                
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to open log file");
                message = ex.Message;
                return Result.Failed;
            }
        }
    }
}