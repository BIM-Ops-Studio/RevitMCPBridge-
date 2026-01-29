using System;
using System.Linq;
using NUnit.Framework;
using FluentAssertions;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.Tests.Mocks;

namespace RevitMCPBridge.Tests.Unit
{
    /// <summary>
    /// Unit tests for SheetMethods - testing sheet and viewport operations
    /// </summary>
    [TestFixture]
    public class SheetMethodsTests : TestBase
    {
        #region GetAllSheets Tests

        [Test]
        public void GetAllSheets_WithNoSheets_ReturnsEmptyList()
        {
            // Act
            var response = ExecuteMethod("getAllSheets", new { });

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "sheets", 0);
        }

        [Test]
        public void GetAllSheets_WithSheets_ReturnsAllSheets()
        {
            // Arrange
            CreateTestSheet("A-101", "Floor Plan");
            CreateTestSheet("A-102", "Elevations");
            CreateTestSheet("A-103", "Sections");

            // Act
            var response = ExecuteMethod("getAllSheets", new { });

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "sheets", 3);
            AssertProperty(response, "count", 3);
        }

        [Test]
        public void GetAllSheets_ReturnsCorrectSheetProperties()
        {
            // Arrange
            var sheet = CreateTestSheet("A-201", "Details Sheet");

            // Act
            var response = ExecuteMethod("getAllSheets", new { });

            // Assert
            AssertSuccess(response);
            var sheets = response["sheets"] as JArray;
            sheets.Should().NotBeNull();

            var returnedSheet = sheets[0];
            returnedSheet["sheetId"].Value<int>().Should().Be(sheet.Id);
            returnedSheet["number"].ToString().Should().Be("A-201");
            returnedSheet["name"].ToString().Should().Be("Details Sheet");
        }

        #endregion

        #region CreateSheet Tests

        [Test]
        public void CreateSheet_WithValidParameters_CreatesSheet()
        {
            // Act
            var response = ExecuteMethod("createSheet", new
            {
                sheetNumber = "A-100",
                sheetName = "Cover Sheet"
            });

            // Assert
            AssertSuccess(response);
            response["sheetId"].Should().NotBeNull();
            response["number"].ToString().Should().Be("A-100");
            response["name"].ToString().Should().Be("Cover Sheet");
        }

        [Test]
        public void CreateSheet_WithAlternateParams_CreatesSheet()
        {
            // Act - test flexibility with 'number' and 'name' params
            var response = ExecuteMethod("createSheet", new
            {
                number = "S-101",
                name = "Structural Plan"
            });

            // Assert
            AssertSuccess(response);
            response["number"].ToString().Should().Be("S-101");
            response["name"].ToString().Should().Be("Structural Plan");
        }

        [Test]
        public void CreateSheet_DuplicateNumber_ReturnsError()
        {
            // Arrange
            CreateTestSheet("A-100", "First Sheet");

            // Act
            var response = ExecuteMethod("createSheet", new
            {
                sheetNumber = "A-100",
                sheetName = "Duplicate Sheet"
            });

            // Assert
            AssertFailure(response, "already exists");
        }

        [Test]
        public void CreateSheet_WithDefaults_UsesDefaultValues()
        {
            // Act - no parameters provided
            var response = ExecuteMethod("createSheet", new { });

            // Assert
            AssertSuccess(response);
            response["number"].ToString().Should().Be("A-100");
            response["name"].ToString().Should().Be("New Sheet");
        }

        #endregion

        #region DeleteSheet Tests

        [Test]
        public void DeleteSheet_ExistingSheet_DeletesSuccessfully()
        {
            // Arrange
            var sheet = CreateTestSheet("A-999", "Sheet to Delete");

            // Act
            var response = ExecuteMethod("deleteSheet", new { sheetId = sheet.Id });

            // Assert
            AssertSuccess(response);
            MockContext.Sheets.ContainsKey(sheet.Id).Should().BeFalse();
        }

        [Test]
        public void DeleteSheet_NonExistent_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("deleteSheet", new { sheetId = 99999 });

            // Assert
            AssertFailure(response, "Sheet not found");
        }

        #endregion

        #region PlaceViewOnSheet Tests

        [Test]
        public void PlaceViewOnSheet_ValidViewAndSheet_CreatesViewport()
        {
            // Arrange
            var sheet = CreateTestSheet("A-100", "Floor Plan Sheet");
            var viewId = 5001; // Default view from mock context

            // Act
            var response = ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheet.Id,
                viewId = viewId,
                x = 1.5,
                y = 1.0
            });

            // Assert
            AssertSuccess(response);
            response["viewportId"].Should().NotBeNull();
            response["viewName"].ToString().Should().Be("Level 1 - Floor Plan");
        }

        [Test]
        public void PlaceViewOnSheet_InvalidSheet_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = 99999,
                viewId = 5001
            });

            // Assert
            AssertFailure(response, "Sheet not found");
        }

        [Test]
        public void PlaceViewOnSheet_InvalidView_ReturnsError()
        {
            // Arrange
            var sheet = CreateTestSheet("A-100", "Test Sheet");

            // Act
            var response = ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheet.Id,
                viewId = 99999
            });

            // Assert
            AssertFailure(response, "View not found");
        }

        [Test]
        public void PlaceViewOnSheet_ViewAlreadyPlaced_ReturnsError()
        {
            // Arrange
            var sheet = CreateTestSheet("A-100", "Test Sheet");
            var viewId = 5001;

            // Place view first time
            ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheet.Id,
                viewId = viewId
            });

            // Act - try to place same view again
            var response = ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheet.Id,
                viewId = viewId
            });

            // Assert
            AssertFailure(response, "already placed");
        }

        [Test]
        public void PlaceViewOnSheet_WithCustomPosition_UsesSpecifiedCoordinates()
        {
            // Arrange
            var sheet = CreateTestSheet("A-100", "Test Sheet");

            // Act
            var response = ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheet.Id,
                viewId = 5001,
                x = 2.5,
                y = 1.75
            });

            // Assert
            AssertSuccess(response);
            var viewportId = response["viewportId"].Value<int>();
            MockContext.Viewports[viewportId].X.Should().Be(2.5);
            MockContext.Viewports[viewportId].Y.Should().Be(1.75);
        }

        #endregion

        #region GetViewportsOnSheet Tests

        [Test]
        public void GetViewportsOnSheet_EmptySheet_ReturnsEmptyList()
        {
            // Arrange
            var sheet = CreateTestSheet("A-100", "Empty Sheet");

            // Act
            var response = ExecuteMethod("getViewportsOnSheet", new { sheetId = sheet.Id });

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "viewports", 0);
        }

        [Test]
        public void GetViewportsOnSheet_WithViewports_ReturnsAll()
        {
            // Arrange
            var sheet = CreateTestSheet("A-100", "Sheet with Views");
            ExecuteMethod("placeViewOnSheet", new { sheetId = sheet.Id, viewId = 5001 });
            ExecuteMethod("placeViewOnSheet", new { sheetId = sheet.Id, viewId = 5002 });

            // Act
            var response = ExecuteMethod("getViewportsOnSheet", new { sheetId = sheet.Id });

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "viewports", 2);
        }

        [Test]
        public void GetViewportsOnSheet_InvalidSheet_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("getViewportsOnSheet", new { sheetId = 99999 });

            // Assert
            AssertFailure(response, "Sheet not found");
        }

        [Test]
        public void GetViewportsOnSheet_ReturnsCorrectViewportProperties()
        {
            // Arrange
            var sheet = CreateTestSheet("A-100", "Test Sheet");
            ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheet.Id,
                viewId = 5001,
                x = 1.5,
                y = 2.0
            });

            // Act
            var response = ExecuteMethod("getViewportsOnSheet", new { sheetId = sheet.Id });

            // Assert
            var viewports = response["viewports"] as JArray;
            viewports.Should().NotBeNull();
            viewports.Count.Should().Be(1);

            var vp = viewports[0];
            vp["viewportId"].Should().NotBeNull();
            vp["viewId"].Value<int>().Should().Be(5001);
            vp["viewName"].ToString().Should().Be("Level 1 - Floor Plan");
            vp["x"].Value<double>().Should().Be(1.5);
            vp["y"].Value<double>().Should().Be(2.0);
        }

        #endregion

        #region GetTitleblockTypes Tests

        [Test]
        public void GetTitleblockTypes_ReturnsAvailableTypes()
        {
            // Act
            var response = ExecuteMethod("getTitleblockTypes", new { });

            // Assert
            AssertSuccess(response);
            var types = response["titleblockTypes"] as JArray;
            types.Should().NotBeNull();
            types.Count.Should().BeGreaterThan(0);
        }

        [Test]
        public void GetTitleblockTypes_ContainsExpectedTypes()
        {
            // Act
            var response = ExecuteMethod("getTitleblockTypes", new { });

            // Assert
            var types = response["titleblockTypes"] as JArray;
            var hasE1 = types.Any(t => t["name"]?.ToString().Contains("30x42") == true);
            var hasD = types.Any(t => t["name"]?.ToString().Contains("22x34") == true);

            hasE1.Should().BeTrue("Expected E1 30x42 titleblock");
            hasD.Should().BeTrue("Expected D 22x34 titleblock");
        }

        #endregion

        #region Sheet Workflow Tests

        [Test]
        public void CreateSheetAndPlaceViews_CompleteWorkflow()
        {
            // This tests a typical workflow of creating a sheet and populating it with views

            // Step 1: Create a sheet
            var createResponse = ExecuteMethod("createSheet", new
            {
                sheetNumber = "A-101",
                sheetName = "Floor Plans"
            });
            AssertSuccess(createResponse);
            var sheetId = createResponse["sheetId"].Value<int>();

            // Step 2: Place views on the sheet
            var place1 = ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheetId,
                viewId = 5001, // Level 1 Floor Plan
                x = 1.0,
                y = 1.5
            });
            AssertSuccess(place1);

            var place2 = ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheetId,
                viewId = 5002, // Level 2 Floor Plan
                x = 1.5,
                y = 1.5
            });
            AssertSuccess(place2);

            // Step 3: Verify the sheet has viewports
            var viewportsResponse = ExecuteMethod("getViewportsOnSheet", new { sheetId });
            AssertSuccess(viewportsResponse);
            AssertArrayCount(viewportsResponse, "viewports", 2);

            // Step 4: Verify sheet appears in list
            var sheetsResponse = ExecuteMethod("getAllSheets", new { });
            AssertSuccess(sheetsResponse);
            var sheets = sheetsResponse["sheets"] as JArray;
            var createdSheet = sheets.FirstOrDefault(s => s["sheetId"].Value<int>() == sheetId);
            createdSheet.Should().NotBeNull();
            createdSheet["viewportCount"].Value<int>().Should().Be(2);
        }

        [Test]
        public void DeleteSheetWithViewports_RemovesAll()
        {
            // Arrange - create sheet with viewports
            var sheet = CreateTestSheet("A-100", "Test Sheet");
            var placeResponse = ExecuteMethod("placeViewOnSheet", new
            {
                sheetId = sheet.Id,
                viewId = 5001
            });
            var viewportId = placeResponse["viewportId"].Value<int>();

            // Act - delete the sheet
            var deleteResponse = ExecuteMethod("deleteSheet", new { sheetId = sheet.Id });

            // Assert
            AssertSuccess(deleteResponse);
            MockContext.Sheets.ContainsKey(sheet.Id).Should().BeFalse();
        }

        #endregion
    }
}
