using System;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMCPBridge.Commands
{
    /// <summary>
    /// Command to show the Smart Element Info panel
    /// </summary>
    [Transaction(TransactionMode.Manual)]
    public class ShowSmartPanelCommand : IExternalCommand
    {
        private static SmartElementPanel _currentPanel;

        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var uiApp = commandData.Application;

                // If panel is already open, bring it to front
                if (_currentPanel != null && _currentPanel.IsVisible)
                {
                    _currentPanel.Activate();
                    _currentPanel.UpdatePanelFromSelection();
                    return Result.Succeeded;
                }

                // Create and show new panel
                _currentPanel = new SmartElementPanel(uiApp);
                _currentPanel.Closed += (s, e) => _currentPanel = null;
                _currentPanel.Show();

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                message = ex.Message;
                TaskDialog.Show("Smart Panel Error", $"Failed to open Smart Element Panel: {ex.Message}");
                return Result.Failed;
            }
        }

        /// <summary>
        /// Static method to refresh the panel from external code
        /// </summary>
        public static void RefreshPanel()
        {
            if (_currentPanel != null && _currentPanel.IsVisible)
            {
                _currentPanel.Dispatcher.Invoke(() => _currentPanel.UpdatePanelFromSelection());
            }
        }

        /// <summary>
        /// Static method to check if panel is open
        /// </summary>
        public static bool IsPanelOpen => _currentPanel != null && _currentPanel.IsVisible;
    }

    /// <summary>
    /// Availability class - command available when document is open
    /// </summary>
    public class SmartPanelAvailability : IExternalCommandAvailability
    {
        public bool IsCommandAvailable(UIApplication applicationData, CategorySet selectedCategories)
        {
            return applicationData?.ActiveUIDocument?.Document != null;
        }
    }
}
