using System;
using NUnit.Framework;
using Newtonsoft.Json.Linq;
using FluentAssertions;

namespace RevitMCPBridge.Tests.Unit
{
    /// <summary>
    /// Unit tests for Room-related MCP methods.
    /// Tests room creation, querying, and properties.
    /// </summary>
    [TestFixture]
    public class RoomMethodsTests : TestBase
    {
        #region GetRooms Tests

        [Test]
        public void GetRooms_WithNoRooms_ReturnsEmptyList()
        {
            // Act
            var response = ExecuteMethod("getRooms");

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "rooms", 0);
        }

        [Test]
        public void GetRooms_WithExistingRooms_ReturnsAllRooms()
        {
            // Arrange
            CreateTestRoom("Office 1");
            CreateTestRoom("Office 2");
            CreateTestRoom("Conference");

            // Act
            var response = ExecuteMethod("getRooms");

            // Assert
            AssertSuccess(response);
            AssertArrayCount(response, "rooms", 3);
        }

        [Test]
        public void GetRooms_ReturnsCorrectRoomProperties()
        {
            // Arrange
            var room = MockContext.CreateRoom(1, 15.0, 20.0, "Test Office");

            // Act
            var response = ExecuteMethod("getRooms");
            var rooms = response["rooms"] as JArray;
            var firstRoom = rooms[0];

            // Assert
            firstRoom["roomId"].Value<int>().Should().Be(room.Id);
            firstRoom["name"].Value<string>().Should().Be("Test Office");
            firstRoom["levelId"].Value<int>().Should().Be(1);
        }

        #endregion

        #region CreateRoom Tests

        [Test]
        public void CreateRoom_WithValidParameters_CreatesRoom()
        {
            // Act
            var response = ExecuteMethod("createRoom", new
            {
                levelId = 1,
                x = 10.0,
                y = 10.0
            });

            // Assert
            AssertSuccess(response);
            response["roomId"].Should().NotBeNull();
            response["name"].Should().NotBeNull();

            // Verify room exists in context
            var roomId = response["roomId"].Value<int>();
            MockContext.Rooms.Should().ContainKey(roomId);
        }

        [Test]
        public void CreateRoom_InvalidLevel_ReturnsError()
        {
            // Act
            var response = ExecuteMethod("createRoom", new
            {
                levelId = 999,
                x = 10.0,
                y = 10.0
            });

            // Assert
            AssertFailure(response, "Level 999 not found");
        }

        [Test]
        public void CreateRoom_DefaultLevel_UsesLevel1()
        {
            // Act
            var response = ExecuteMethod("createRoom", new
            {
                x = 10.0,
                y = 10.0
            });

            // Assert
            AssertSuccess(response);
        }

        [Test]
        public void CreateRoom_MultipleRooms_UniqueIds()
        {
            // Act
            var response1 = ExecuteMethod("createRoom", new { levelId = 1, x = 10, y = 10 });
            var response2 = ExecuteMethod("createRoom", new { levelId = 1, x = 30, y = 10 });
            var response3 = ExecuteMethod("createRoom", new { levelId = 1, x = 50, y = 10 });

            // Assert
            var id1 = response1["roomId"].Value<int>();
            var id2 = response2["roomId"].Value<int>();
            var id3 = response3["roomId"].Value<int>();

            id1.Should().NotBe(id2);
            id2.Should().NotBe(id3);
        }

        [Test]
        public void CreateRoom_AssignsAutoName()
        {
            // Act
            var response = ExecuteMethod("createRoom", new
            {
                levelId = 1,
                x = 10.0,
                y = 10.0
            });

            // Assert
            AssertSuccess(response);
            response["name"].Value<string>().Should().StartWith("Room ");
        }

        #endregion

        #region Room at Different Levels Tests

        [Test]
        public void CreateRoom_OnLevel2_AssociatesCorrectly()
        {
            // Act
            var response = ExecuteMethod("createRoom", new
            {
                levelId = 2,
                x = 10.0,
                y = 10.0
            });

            // Assert
            AssertSuccess(response);
            var roomId = response["roomId"].Value<int>();
            MockContext.Rooms[roomId].LevelId.Should().Be(2);
        }

        [Test]
        public void CreateRoom_AllLevels_Success()
        {
            // Act & Assert - create room on each default level
            var response1 = ExecuteMethod("createRoom", new { levelId = 1, x = 10, y = 10 });
            var response2 = ExecuteMethod("createRoom", new { levelId = 2, x = 10, y = 10 });
            var response3 = ExecuteMethod("createRoom", new { levelId = 3, x = 10, y = 10 });

            AssertSuccess(response1);
            AssertSuccess(response2);
            AssertSuccess(response3);
        }

        #endregion
    }
}
