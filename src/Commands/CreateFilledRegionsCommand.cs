using System;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge.Commands
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class CreateFilledRegionsCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var uiApp = commandData.Application;
                var doc = uiApp.ActiveUIDocument.Document;
                var activeView = doc.ActiveView;

                // Check if in a floor plan view
                if (activeView.ViewType != ViewType.FloorPlan)
                {
                    TaskDialog.Show("Invalid View",
                        "Please switch to a floor plan view before running this command.");
                    return Result.Cancelled;
                }

                // Confirm action with user
                var result = TaskDialog.Show("Create Filled Regions for All Offices",
                    "This will create filled regions for ALL offices in the current view.\n\n" +
                    "Features:\n" +
                    "• EXTERIOR walls: Boundary at exterior face\n" +
                    "• HALLWAY walls: Boundary at hallway face\n" +
                    "• DEMISING walls: Boundary at center\n" +
                    "• Transparent filled regions\n" +
                    "• Calculates effective usable area\n\n" +
                    "Continue?",
                    TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No);

                if (result != TaskDialogResult.Yes)
                {
                    return Result.Cancelled;
                }

                // Create parameters for the MCP method
                var parameters = new JObject
                {
                    ["fillPatternName"] = "Solid fill",
                    ["transparency"] = 50,
                    ["roomNameFilter"] = "OFFICE"
                };

                // Call the automated method
                var jsonResult = AutomatedFilledRegion.CreateFilledRegionsForAllOffices(uiApp, parameters);
                var responseData = JsonConvert.DeserializeObject<dynamic>(jsonResult);

                if (responseData.success == true)
                {
                    var successCount = (int)responseData.successCount;
                    var failCount = (int)responseData.failCount;
                    var totalRooms = (int)responseData.totalRooms;

                    var resultMessage = $"✅ SUCCESS!\n\n" +
                                      $"Created filled regions for {successCount} out of {totalRooms} offices.\n";

                    if (failCount > 0)
                    {
                        resultMessage += $"\n⚠️ Failed: {failCount} rooms\n" +
                                       $"Check log for details.";
                    }

                    resultMessage += $"\n\nView: {responseData.viewName}";

                    TaskDialog.Show("Filled Regions Created", resultMessage);
                    return Result.Succeeded;
                }
                else
                {
                    TaskDialog.Show("Error",
                        $"Failed to create filled regions:\n{responseData.error}");
                    return Result.Failed;
                }
            }
            catch (Exception ex)
            {
                message = ex.Message;
                TaskDialog.Show("Error", $"Command failed:\n{ex.Message}");
                return Result.Failed;
            }
        }
    }
}
