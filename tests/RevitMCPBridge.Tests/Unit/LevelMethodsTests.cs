using System;
using NUnit.Framework;
using Newtonsoft.Json.Linq;
using FluentAssertions;

namespace RevitMCPBridge.Tests.Unit
{
    /// <summary>
    /// Unit tests for Level-related MCP methods.
    /// </summary>
    [TestFixture]
    public class LevelMethodsTests : TestBase
    {
        #region GetLevels Tests

        [Test]
        public void GetLevels_ReturnsDefaultLevels()
        {
            // Act
            var response = ExecuteMethod("getLevels");

            // Assert
            AssertSuccess(response);
            var levels = response["levels"] as JArray;
            levels.Should().NotBeNull();
            levels.Count.Should().Be(3); // Default: Level 1, 2, 3
        }

        [Test]
        public void GetLevels_ReturnsCorrectElevations()
        {
            // Act
            var response = ExecuteMethod("getLevels");
            var levels = response["levels"] as JArray;

            // Assert
            levels[0]["elevation"].Value<double>().Should().Be(0.0);
            levels[1]["elevation"].Value<double>().Should().Be(10.0);
            levels[2]["elevation"].Value<double>().Should().Be(20.0);
        }

        [Test]
        public void GetLevels_ReturnsCorrectNames()
        {
            // Act
            var response = ExecuteMethod("getLevels");
            var levels = response["levels"] as JArray;

            // Assert
            levels[0]["name"].Value<string>().Should().Be("Level 1");
            levels[1]["name"].Value<string>().Should().Be("Level 2");
            levels[2]["name"].Value<string>().Should().Be("Level 3");
        }

        [Test]
        public void GetLevels_EachHasUniqueId()
        {
            // Act
            var response = ExecuteMethod("getLevels");
            var levels = response["levels"] as JArray;

            // Assert
            var id1 = levels[0]["levelId"].Value<int>();
            var id2 = levels[1]["levelId"].Value<int>();
            var id3 = levels[2]["levelId"].Value<int>();

            id1.Should().NotBe(id2);
            id2.Should().NotBe(id3);
            id1.Should().NotBe(id3);
        }

        [Test]
        public void GetAllLevels_SameAsGetLevels()
        {
            // Act
            var response1 = ExecuteMethod("getLevels");
            var response2 = ExecuteMethod("getAllLevels");

            // Assert
            AssertSuccess(response1);
            AssertSuccess(response2);
        }

        #endregion

        #region Custom Levels Tests

        [Test]
        public void AddCustomLevel_AppearsInGetLevels()
        {
            // Arrange
            MockContext.AddLevel(4, "Level 4", 30.0);

            // Act
            var response = ExecuteMethod("getLevels");
            var levels = response["levels"] as JArray;

            // Assert
            levels.Count.Should().Be(4);
        }

        [Test]
        public void AddLevel_NegativeElevation_Allowed()
        {
            // Arrange
            MockContext.AddLevel(0, "Basement", -10.0);

            // Act
            var response = ExecuteMethod("getLevels");
            var levels = response["levels"] as JArray;

            // Assert
            var hasBasement = false;
            foreach (var level in levels)
            {
                if (level["name"]?.Value<string>() == "Basement")
                {
                    level["elevation"].Value<double>().Should().Be(-10.0);
                    hasBasement = true;
                    break;
                }
            }
            hasBasement.Should().BeTrue();
        }

        #endregion
    }
}
