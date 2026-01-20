using System;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMCPBridge2026.AgentFramework
{
    /// <summary>
    /// Command to launch the AI Agent Chat Panel
    /// </summary>
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class LaunchAgentCommand : IExternalCommand
    {
        private static AgentChatPanel _panel;

        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var uiApp = commandData.Application;

                // If panel exists and is open, just bring it to front
                if (_panel != null && _panel.IsVisible)
                {
                    _panel.Activate();
                    return Result.Succeeded;
                }

                // Create new panel
                _panel = new AgentChatPanel(uiApp);
                _panel.Show();

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                message = ex.Message;
                return Result.Failed;
            }
        }
    }

    /// <summary>
    /// Helper class to add the Agent button to the ribbon
    /// Call AddAgentButton from your Application OnStartup
    /// </summary>
    public static class AgentRibbonSetup
    {
        public static void AddAgentButton(UIControlledApplication application, RibbonPanel panel)
        {
            try
            {
                // Get the assembly path
                string assemblyPath = typeof(LaunchAgentCommand).Assembly.Location;

                // Create push button data
                var buttonData = new PushButtonData(
                    "LaunchAgent",
                    "AI\nAssistant",
                    assemblyPath,
                    "RevitMCPBridge2026.AgentFramework.LaunchAgentCommand"
                );

                buttonData.ToolTip = "Launch the AI Assistant chat panel";
                buttonData.LongDescription = "Opens an AI-powered assistant that can help you automate Revit tasks using natural language commands.";

                // Add button to panel
                var button = panel.AddItem(buttonData) as PushButton;

                // Try to set icon (optional)
                try
                {
                    // You can add an icon later
                    // button.LargeImage = new BitmapImage(new Uri("pack://application:,,,/RevitMCPBridge2026;component/Resources/ai_icon.png"));
                }
                catch { }
            }
            catch (Exception ex)
            {
                TaskDialog.Show("Error", $"Failed to add AI Assistant button: {ex.Message}");
            }
        }
    }
}
