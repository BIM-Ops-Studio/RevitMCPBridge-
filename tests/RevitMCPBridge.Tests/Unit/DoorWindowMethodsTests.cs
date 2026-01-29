using System;
using NUnit.Framework;
using FluentAssertions;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.Tests.Mocks;

namespace RevitMCPBridge.Tests.Unit
{
    /// <summary>
    /// Unit tests for DoorWindowMethods - testing door and window operations
    /// </summary>
    [TestFixture]
    public class DoorWindowMethodsTests : TestBase
    {
        #region PlaceDoor Tests

        [Test]
        public void PlaceDoor_WithValidWall_ReturnsSuccess()
        {
            // Arrange
            var wall = CreateTestWall();

            // Act
            var response = ExecuteMethod("placeDoor", new
            {
                wallId = wall.Id,
                doorTypeId = 2001
            });

            // Assert
            AssertSuccess(response);
            response["doorId"].Should().NotBeNull();
            response["typeName"].ToString().Should().Be("Single-Flush");
        }

        [Test]
        public void PlaceDoor_WithAlternateTypeIdParam_ReturnsSuccess()
        {
            // Arrange - test flexibility with 'typeId' instead of 'doorTypeId'
            var wall = CreateTestWall();

            // Act
            var response = ExecuteMethod("placeDoor", new
            {
                wallId = wall.Id,
                typeId = 2002 // Double-Flush
            });

            // Assert
            AssertSuccess(response);
            response["typeName"].ToString().Should().Be("Double-Flush");
        }

        [Test]
        public void PlaceDoor_WithInvalidWall_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("placeDoor", new
            {
                wallId = 99999, // Non-existent wall
                doorTypeId = 2001
            });

            // Assert
            AssertFailure(response, "Wall not found");
        }

        [Test]
        public void PlaceDoor_WithInvalidDoorType_ReturnsError()
        {
            // Arrange
            var wall = CreateTestWall();

            // Act
            var response = ExecuteMethod("placeDoor", new
            {
                wallId = wall.Id,
                doorTypeId = 99999 // Non-existent type
            });

            // Assert
            AssertFailure(response, "No valid door type found");
        }

        [Test]
        public void PlaceDoor_WithCustomLocation_PlacesAtSpecifiedPosition()
        {
            // Arrange
            var wall = CreateTestWall();
            var customLocation = new double[] { 5.0, 0.0, 0.0 };

            // Act
            var response = ExecuteMethod("placeDoor", new
            {
                wallId = wall.Id,
                doorTypeId = 2001,
                location = customLocation
            });

            // Assert
            AssertSuccess(response);
            var doorId = response["doorId"].Value<int>();
            MockContext.Doors[doorId].X.Should().Be(5.0);
            MockContext.Doors[doorId].Y.Should().Be(0.0);
        }

        [Test]
        public void PlaceDoor_WithoutLocation_PlacesAtWallMidpoint()
        {
            // Arrange - wall from (0,0) to (20,0), midpoint is (10,0)
            var wall = CreateTestWall(20.0);

            // Act
            var response = ExecuteMethod("placeDoor", new
            {
                wallId = wall.Id,
                doorTypeId = 2001
            });

            // Assert
            AssertSuccess(response);
            var doorId = response["doorId"].Value<int>();
            MockContext.Doors[doorId].X.Should().Be(10.0);
        }

        #endregion

        #region PlaceWindow Tests

        [Test]
        public void PlaceWindow_WithValidWall_ReturnsSuccess()
        {
            // Arrange
            var wall = CreateTestWall();

            // Act
            var response = ExecuteMethod("placeWindow", new
            {
                wallId = wall.Id,
                windowTypeId = 3001
            });

            // Assert
            AssertSuccess(response);
            response["windowId"].Should().NotBeNull();
            response["typeName"].ToString().Should().Be("Fixed");
        }

        [Test]
        public void PlaceWindow_WithSillHeight_UsesSpecifiedHeight()
        {
            // Arrange
            var wall = CreateTestWall();
            var sillHeight = 4.5;

            // Act
            var response = ExecuteMethod("placeWindow", new
            {
                wallId = wall.Id,
                windowTypeId = 3001,
                sillHeight = sillHeight
            });

            // Assert
            AssertSuccess(response);
            response["sillHeight"].Value<double>().Should().Be(4.5);
        }

        [Test]
        public void PlaceWindow_WithDefaultSillHeight_UsesThreeFeet()
        {
            // Arrange
            var wall = CreateTestWall();

            // Act
            var response = ExecuteMethod("placeWindow", new
            {
                wallId = wall.Id,
                windowTypeId = 3001
            });

            // Assert
            AssertSuccess(response);
            response["sillHeight"].Value<double>().Should().Be(3.0);
        }

        [Test]
        public void PlaceWindow_WithInvalidWall_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("placeWindow", new
            {
                wallId = 99999,
                windowTypeId = 3001
            });

            // Assert
            AssertFailure(response, "Wall not found");
        }

        [Test]
        public void PlaceWindow_WithInvalidWindowType_ReturnsError()
        {
            // Arrange
            var wall = CreateTestWall();

            // Act
            var response = ExecuteMethod("placeWindow", new
            {
                wallId = wall.Id,
                windowTypeId = 99999
            });

            // Assert
            AssertFailure(response, "No valid window type found");
        }

        #endregion

        #region GetDoors Tests

        [Test]
        public void GetDoors_WithNoDoors_ReturnsEmptyList()
        {
            // Act
            var response = ExecuteMethod("getDoors", new { });

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "doors", 0);
        }

        [Test]
        public void GetDoors_WithMultipleDoors_ReturnsAllDoors()
        {
            // Arrange
            var wall = CreateTestWall();
            MockContext.CreateDoor(wall.Id, 5.0, 0.0, 2001);
            MockContext.CreateDoor(wall.Id, 10.0, 0.0, 2002);
            MockContext.CreateDoor(wall.Id, 15.0, 0.0, 2001);

            // Act
            var response = ExecuteMethod("getDoors", new { });

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "doors", 3);
            AssertProperty(response, "count", 3);
        }

        [Test]
        public void GetDoors_ReturnsCorrectDoorProperties()
        {
            // Arrange
            var wall = CreateTestWall();
            var door = MockContext.CreateDoor(wall.Id, 7.5, 0.0, 2001);

            // Act
            var response = ExecuteMethod("getDoors", new { });

            // Assert
            AssertSuccess(response);
            var doors = response["doors"] as JArray;
            doors.Should().NotBeNull();
            doors.Count.Should().Be(1);

            var returnedDoor = doors[0];
            returnedDoor["doorId"].Value<int>().Should().Be(door.Id);
            returnedDoor["wallId"].Value<int>().Should().Be(wall.Id);
            returnedDoor["x"].Value<double>().Should().Be(7.5);
            returnedDoor["typeId"].Value<int>().Should().Be(2001);
        }

        #endregion

        #region GetWindows Tests

        [Test]
        public void GetWindows_WithNoWindows_ReturnsEmptyList()
        {
            // Act
            var response = ExecuteMethod("getWindows", new { });

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "windows", 0);
        }

        [Test]
        public void GetWindows_WithMultipleWindows_ReturnsAllWindows()
        {
            // Arrange
            var wall = CreateTestWall();
            MockContext.CreateWindow(wall.Id, 3.0, 0.0, 3001);
            MockContext.CreateWindow(wall.Id, 8.0, 0.0, 3002);

            // Act
            var response = ExecuteMethod("getWindows", new { });

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "windows", 2);
        }

        [Test]
        public void GetWindows_ReturnsCorrectWindowProperties()
        {
            // Arrange
            var wall = CreateTestWall();
            var window = MockContext.CreateWindow(wall.Id, 6.0, 0.0, 3002, 4.0);

            // Act
            var response = ExecuteMethod("getWindows", new { });

            // Assert
            AssertSuccess(response);
            var windows = response["windows"] as JArray;
            windows.Should().NotBeNull();

            var returnedWindow = windows[0];
            returnedWindow["windowId"].Value<int>().Should().Be(window.Id);
            returnedWindow["sillHeight"].Value<double>().Should().Be(4.0);
            returnedWindow["typeId"].Value<int>().Should().Be(3002);
        }

        #endregion

        #region GetDoorTypes Tests

        [Test]
        public void GetDoorTypes_ReturnsAllDoorTypes()
        {
            // Act
            var response = ExecuteMethod("getDoorTypes", new { });

            // Assert
            AssertSuccess(response);
            var doorTypes = response["doorTypes"] as JArray;
            doorTypes.Should().NotBeNull();
            doorTypes.Count.Should().Be(2); // Single-Flush and Double-Flush
        }

        [Test]
        public void GetDoorTypes_ReturnsCorrectTypeProperties()
        {
            // Act
            var response = ExecuteMethod("getDoorTypes", new { });

            // Assert
            var doorTypes = response["doorTypes"] as JArray;
            var hasExpectedTypes = false;

            foreach (var type in doorTypes)
            {
                var name = type["name"].ToString();
                if (name == "Single-Flush" || name == "Double-Flush")
                {
                    hasExpectedTypes = true;
                    type["typeId"].Should().NotBeNull();
                }
            }

            hasExpectedTypes.Should().BeTrue();
        }

        #endregion

        #region GetWindowTypes Tests

        [Test]
        public void GetWindowTypes_ReturnsAllWindowTypes()
        {
            // Act
            var response = ExecuteMethod("getWindowTypes", new { });

            // Assert
            AssertSuccess(response);
            var windowTypes = response["windowTypes"] as JArray;
            windowTypes.Should().NotBeNull();
            windowTypes.Count.Should().Be(2); // Fixed and Casement
        }

        #endregion

        #region Delete Operations Tests

        [Test]
        public void DeleteElement_WithValidDoor_RemovesDoor()
        {
            // Arrange
            var wall = CreateTestWall();
            var door = MockContext.CreateDoor(wall.Id, 5.0, 0.0, 2001);

            // Act
            var response = ExecuteMethod("deleteElement", new
            {
                elementId = door.Id
            });

            // Assert
            AssertSuccess(response);
            MockContext.Doors.ContainsKey(door.Id).Should().BeFalse();
            MockContext.Elements.ContainsKey(door.Id).Should().BeFalse();
        }

        [Test]
        public void DeleteElement_WithValidWindow_RemovesWindow()
        {
            // Arrange
            var wall = CreateTestWall();
            var window = MockContext.CreateWindow(wall.Id, 5.0, 0.0, 3001);

            // Act
            var response = ExecuteMethod("deleteElement", new
            {
                elementId = window.Id
            });

            // Assert
            AssertSuccess(response);
            MockContext.Windows.ContainsKey(window.Id).Should().BeFalse();
            MockContext.Elements.ContainsKey(window.Id).Should().BeFalse();
        }

        #endregion

        #region Edge Cases

        [Test]
        public void PlaceDoor_WithWrongCategoryType_ReturnsError()
        {
            // Arrange - try to use a window type ID as door type
            var wall = CreateTestWall();

            // Act
            var response = ExecuteMethod("placeDoor", new
            {
                wallId = wall.Id,
                doorTypeId = 3001 // This is a window type, not door
            });

            // Assert
            AssertFailure(response, "No valid door type found");
        }

        [Test]
        public void PlaceWindow_WithWrongCategoryType_ReturnsError()
        {
            // Arrange - try to use a door type ID as window type
            var wall = CreateTestWall();

            // Act
            var response = ExecuteMethod("placeWindow", new
            {
                wallId = wall.Id,
                windowTypeId = 2001 // This is a door type, not window
            });

            // Assert
            AssertFailure(response, "No valid window type found");
        }

        [Test]
        public void PlaceMultipleDoorsOnSameWall_AllSucceed()
        {
            // Arrange
            var wall = CreateTestWall(30.0);

            // Act
            var response1 = ExecuteMethod("placeDoor", new { wallId = wall.Id, location = new double[] { 5.0, 0.0, 0.0 } });
            var response2 = ExecuteMethod("placeDoor", new { wallId = wall.Id, location = new double[] { 15.0, 0.0, 0.0 } });
            var response3 = ExecuteMethod("placeDoor", new { wallId = wall.Id, location = new double[] { 25.0, 0.0, 0.0 } });

            // Assert
            AssertSuccess(response1);
            AssertSuccess(response2);
            AssertSuccess(response3);
            MockContext.Doors.Count.Should().Be(3);
        }

        #endregion
    }
}
