using System;
using System.Linq;
using NUnit.Framework;
using Newtonsoft.Json.Linq;
using FluentAssertions;

namespace RevitMCPBridge.Tests.Unit
{
    /// <summary>
    /// Unit tests for Wall-related MCP methods.
    /// Tests wall creation, modification, querying, and deletion.
    /// </summary>
    [TestFixture]
    public class WallMethodsTests : TestBase
    {
        #region GetWalls Tests

        [Test]
        public void GetWalls_WithNoWalls_ReturnsEmptyList()
        {
            // Act
            var response = ExecuteMethod("getWalls");

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "walls", 0);
            AssertProperty(response, "count", 0);
        }

        [Test]
        public void GetWalls_WithExistingWalls_ReturnsAllWalls()
        {
            // Arrange
            CreateTestWall(20.0);
            CreateTestWall(30.0);
            CreateTestWall(40.0);

            // Act
            var response = ExecuteMethod("getWalls");

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "walls", 3);
            AssertProperty(response, "count", 3);
        }

        [Test]
        public void GetWalls_ReturnsCorrectWallProperties()
        {
            // Arrange
            var wall = MockContext.CreateWall(0, 0, 20, 0, 1, 1001, 10.0);

            // Act
            var response = ExecuteMethod("getWalls");
            var walls = response["walls"] as JArray;
            var firstWall = walls[0];

            // Assert
            AssertSuccess(response);
            firstWall["wallId"].Value<int>().Should().Be(wall.Id);
            firstWall["startX"].Value<double>().Should().Be(0);
            firstWall["startY"].Value<double>().Should().Be(0);
            firstWall["endX"].Value<double>().Should().Be(20);
            firstWall["endY"].Value<double>().Should().Be(0);
            firstWall["height"].Value<double>().Should().Be(10.0);
            firstWall["length"].Value<double>().Should().Be(20.0);
        }

        #endregion

        #region CreateWall Tests

        [Test]
        public void CreateWall_WithValidParameters_CreatesWall()
        {
            // Act
            var response = ExecuteMethod("createWall", new
            {
                startX = 0.0,
                startY = 0.0,
                endX = 20.0,
                endY = 0.0,
                levelId = 1,
                wallTypeId = 1001,
                height = 10.0
            });

            // Assert
            AssertSuccess(response);
            response["wallId"].Should().NotBeNull();
            response["length"].Value<double>().Should().Be(20.0);

            // Verify wall exists in context
            var wallId = response["wallId"].Value<int>();
            MockContext.Walls.Should().ContainKey(wallId);
        }

        [Test]
        public void CreateWall_DiagonalWall_CalculatesCorrectLength()
        {
            // Act
            var response = ExecuteMethod("createWall", new
            {
                startX = 0.0,
                startY = 0.0,
                endX = 3.0,
                endY = 4.0,
                levelId = 1,
                wallTypeId = 1001,
                height = 10.0
            });

            // Assert
            AssertSuccess(response);
            response["length"].Value<double>().Should().Be(5.0); // 3-4-5 triangle
        }

        [Test]
        public void CreateWall_ZeroLength_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("createWall", new
            {
                startX = 10.0,
                startY = 10.0,
                endX = 10.0,
                endY = 10.0,
                levelId = 1,
                wallTypeId = 1001,
                height = 10.0
            });

            // Assert
            AssertFailure(response, "non-zero length");
        }

        [Test]
        public void CreateWall_InvalidLevel_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("createWall", new
            {
                startX = 0.0,
                startY = 0.0,
                endX = 20.0,
                endY = 0.0,
                levelId = 999, // Non-existent level
                wallTypeId = 1001,
                height = 10.0
            });

            // Assert
            AssertFailure(response, "Level 999 not found");
        }

        [Test]
        public void CreateWall_DefaultValues_UsesDefaults()
        {
            // Act - minimal parameters
            var response = ExecuteMethod("createWall", new
            {
                startX = 0.0,
                startY = 0.0,
                endX = 20.0,
                endY = 0.0
            });

            // Assert - should use default level 1, type 1001, height 10
            AssertSuccess(response);
        }

        [Test]
        public void CreateWall_MultipleWalls_CreatesUniqueIds()
        {
            // Act
            var response1 = ExecuteMethod("createWall", new { startX = 0, startY = 0, endX = 10, endY = 0, levelId = 1 });
            var response2 = ExecuteMethod("createWall", new { startX = 0, startY = 10, endX = 10, endY = 10, levelId = 1 });
            var response3 = ExecuteMethod("createWall", new { startX = 0, startY = 20, endX = 10, endY = 20, levelId = 1 });

            // Assert
            var id1 = response1["wallId"].Value<int>();
            var id2 = response2["wallId"].Value<int>();
            var id3 = response3["wallId"].Value<int>();

            id1.Should().NotBe(id2);
            id2.Should().NotBe(id3);
            id1.Should().NotBe(id3);
        }

        #endregion

        #region DeleteWall Tests

        [Test]
        public void DeleteWall_ExistingWall_DeletesSuccessfully()
        {
            // Arrange
            var wall = CreateTestWall();
            var wallId = wall.Id;

            // Verify wall exists
            AssertElementExists(wallId);

            // Act
            var response = ExecuteMethod("deleteWall", new { wallId = wallId });

            // Assert
            AssertSuccess(response);
            AssertElementNotExists(wallId);
        }

        [Test]
        public void DeleteWall_NonExistentWall_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("deleteWall", new { wallId = 999999 });

            // Assert
            AssertFailure(response, "not found");
        }

        [Test]
        public void DeleteWall_DeleteSameWallTwice_SecondFails()
        {
            // Arrange
            var wall = CreateTestWall();
            var wallId = wall.Id;

            // Act
            var response1 = ExecuteMethod("deleteWall", new { wallId = wallId });
            var response2 = ExecuteMethod("deleteWall", new { wallId = wallId });

            // Assert
            AssertSuccess(response1);
            AssertFailure(response2, "not found");
        }

        #endregion

        #region GetWallTypes Tests

        [Test]
        public void GetWallTypes_ReturnsAvailableTypes()
        {
            // Act
            var response = ExecuteMethod("getWallTypes");

            // Assert
            AssertSuccess(response);
            var types = response["wallTypes"] as JArray;
            types.Should().NotBeNull();
            types.Count.Should().BeGreaterThan(0);
        }

        [Test]
        public void GetWallTypes_ContainsExpectedTypes()
        {
            // Act
            var response = ExecuteMethod("getWallTypes");
            var types = response["wallTypes"] as JArray;

            // Assert - check for expected type names in the array
            var hasBasicWall = types.Any(t => t["name"]?.ToString() == "Basic Wall");
            var hasGeneric8 = types.Any(t => t["name"]?.ToString() == "Generic - 8\"");

            hasBasicWall.Should().BeTrue("Expected 'Basic Wall' type to exist");
            hasGeneric8.Should().BeTrue("Expected 'Generic - 8\"' type to exist");
        }

        #endregion

        #region Wall Geometry Tests

        [Test]
        public void CreateWall_VerticalWall_CorrectCoordinates()
        {
            // Act
            var response = ExecuteMethod("createWall", new
            {
                startX = 0.0,
                startY = 0.0,
                endX = 0.0,
                endY = 15.0,
                levelId = 1
            });

            // Assert
            AssertSuccess(response);
            response["length"].Value<double>().Should().Be(15.0);
        }

        [Test]
        public void CreateWall_NegativeCoordinates_Succeeds()
        {
            // Act
            var response = ExecuteMethod("createWall", new
            {
                startX = -10.0,
                startY = -10.0,
                endX = 10.0,
                endY = 10.0,
                levelId = 1
            });

            // Assert
            AssertSuccess(response);
            // Diagonal: sqrt(20^2 + 20^2) = sqrt(800) ≈ 28.28
            response["length"].Value<double>().Should().BeApproximately(28.28, 0.01);
        }

        #endregion
    }
}
