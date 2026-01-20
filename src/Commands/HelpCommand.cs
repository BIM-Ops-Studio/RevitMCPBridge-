using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Serilog;

namespace RevitMCPBridge.Commands
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class HelpCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var helpPath = GenerateHelpFile();
                Process.Start(helpPath);
                
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to show help");
                
                // Show basic help in dialog
                var dialog = new TaskDialog("MCP Bridge Help");
                dialog.MainContent = GetBasicHelp();
                dialog.ExpandedContent = "For detailed documentation, please visit the MCP Bridge documentation.";
                dialog.Show();
                
                return Result.Succeeded;
            }
        }
        
        private string GenerateHelpFile()
        {
            var helpDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "Autodesk", "Revit", "Addins", "2026", "MCPBridge");
                
            if (!Directory.Exists(helpDir))
                Directory.CreateDirectory(helpDir);
                
            var helpPath = Path.Combine(helpDir, "MCPBridge_Help.html");
            
            var html = new StringBuilder();
            html.AppendLine("<!DOCTYPE html>");
            html.AppendLine("<html>");
            html.AppendLine("<head>");
            html.AppendLine("<title>MCP Bridge Help</title>");
            html.AppendLine("<style>");
            html.AppendLine("body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }");
            html.AppendLine("h1 { color: #0066cc; }");
            html.AppendLine("h2 { color: #333; margin-top: 30px; }");
            html.AppendLine("code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }");
            html.AppendLine("pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }");
            html.AppendLine(".method { margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #0066cc; }");
            html.AppendLine("</style>");
            html.AppendLine("</head>");
            html.AppendLine("<body>");
            
            html.AppendLine("<h1>MCP Bridge for Revit 2026</h1>");
            html.AppendLine("<p>The MCP Bridge enables AI assistants like Claude to interact with Revit through the Model Context Protocol.</p>");
            
            html.AppendLine("<h2>Getting Started</h2>");
            html.AppendLine("<ol>");
            html.AppendLine("<li>Click <strong>Start Server</strong> to begin accepting MCP connections</li>");
            html.AppendLine("<li>Configure your MCP client to connect to the named pipe: <code>\\\\.\\pipe\\RevitMCPBridge2026</code></li>");
            html.AppendLine("<li>Use the available methods to query and modify your Revit model</li>");
            html.AppendLine("</ol>");
            
            html.AppendLine("<h2>Available Methods</h2>");
            
            html.AppendLine("<div class='method'>");
            html.AppendLine("<h3>ping</h3>");
            html.AppendLine("<p>Test server connectivity</p>");
            html.AppendLine("<pre>{\"method\": \"ping\"}</pre>");
            html.AppendLine("</div>");
            
            html.AppendLine("<div class='method'>");
            html.AppendLine("<h3>getProjectInfo</h3>");
            html.AppendLine("<p>Get current project information</p>");
            html.AppendLine("<pre>{\"method\": \"getProjectInfo\"}</pre>");
            html.AppendLine("</div>");
            
            html.AppendLine("<div class='method'>");
            html.AppendLine("<h3>getElements</h3>");
            html.AppendLine("<p>Query elements by category and/or view</p>");
            html.AppendLine("<pre>{");
            html.AppendLine("  \"method\": \"getElements\",");
            html.AppendLine("  \"params\": {");
            html.AppendLine("    \"category\": \"Walls\",  // optional");
            html.AppendLine("    \"viewId\": \"123456\"    // optional");
            html.AppendLine("  }");
            html.AppendLine("}</pre>");
            html.AppendLine("</div>");
            
            html.AppendLine("<div class='method'>");
            html.AppendLine("<h3>getElementProperties</h3>");
            html.AppendLine("<p>Get all properties of a specific element</p>");
            html.AppendLine("<pre>{");
            html.AppendLine("  \"method\": \"getElementProperties\",");
            html.AppendLine("  \"params\": {");
            html.AppendLine("    \"elementId\": \"123456\"");
            html.AppendLine("  }");
            html.AppendLine("}</pre>");
            html.AppendLine("</div>");
            
            html.AppendLine("<div class='method'>");
            html.AppendLine("<h3>setParameter</h3>");
            html.AppendLine("<p>Modify an element parameter</p>");
            html.AppendLine("<pre>{");
            html.AppendLine("  \"method\": \"setParameter\",");
            html.AppendLine("  \"params\": {");
            html.AppendLine("    \"elementId\": \"123456\",");
            html.AppendLine("    \"parameterName\": \"Comments\",");
            html.AppendLine("    \"value\": \"Updated by MCP\"");
            html.AppendLine("  }");
            html.AppendLine("}</pre>");
            html.AppendLine("</div>");
            
            html.AppendLine("<h2>Example Usage with Claude Desktop</h2>");
            html.AppendLine("<p>Add the following to your Claude Desktop configuration:</p>");
            html.AppendLine("<pre>{");
            html.AppendLine("  \"mcpServers\": {");
            html.AppendLine("    \"revit\": {");
            html.AppendLine("      \"command\": \"npx\",");
            html.AppendLine("      \"args\": [\"@modelcontextprotocol/server-stdio\", \"pipe://RevitMCPBridge2026\"]");
            html.AppendLine("    }");
            html.AppendLine("  }");
            html.AppendLine("}</pre>");
            
            html.AppendLine("<h2>Troubleshooting</h2>");
            html.AppendLine("<ul>");
            html.AppendLine("<li>Check server status using the <strong>Server Status</strong> button</li>");
            html.AppendLine("<li>View logs using the <strong>View Logs</strong> button</li>");
            html.AppendLine("<li>Ensure the server is running before attempting connections</li>");
            html.AppendLine("<li>Verify firewall settings allow named pipe connections</li>");
            html.AppendLine("</ul>");
            
            html.AppendLine("</body>");
            html.AppendLine("</html>");
            
            File.WriteAllText(helpPath, html.ToString());
            return helpPath;
        }
        
        private string GetBasicHelp()
        {
            return @"MCP Bridge for Revit 2026

The MCP Bridge enables AI assistants to interact with Revit through the Model Context Protocol.

Quick Start:
1. Click 'Start Server' to begin
2. Connect your MCP client to: \\.\pipe\RevitMCPBridge2026
3. Use available methods to query and modify your model

Available Methods:
- ping: Test connectivity
- getProjectInfo: Get project information
- getElements: Query elements
- getElementProperties: Get element details
- setParameter: Modify parameters
- getViews: List all views
- getCategories: List model categories

For detailed documentation, click OK to open the help file.";
        }
    }
}