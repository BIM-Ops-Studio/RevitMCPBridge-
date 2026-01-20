using System;
using NUnit.Framework;
using Newtonsoft.Json.Linq;
using FluentAssertions;

namespace RevitMCPBridge.Tests.Unit
{
    /// <summary>
    /// Unit tests for View-related MCP methods.
    /// Tests view querying and properties.
    /// </summary>
    [TestFixture]
    public class ViewMethodsTests : TestBase
    {
        #region GetViews Tests

        [Test]
        public void GetViews_ReturnsDefaultViews()
        {
            // Act
            var response = ExecuteMethod("getViews");

            // Assert
            AssertSuccess(response);
            var views = response["views"] as JArray;
            views.Should().NotBeNull();
            views.Count.Should().BeGreaterThan(0);
        }

        [Test]
        public void GetViews_ContainsFloorPlans()
        {
            // Act
            var response = ExecuteMethod("getViews");
            var views = response["views"] as JArray;

            // Assert
            var hasFloorPlan = false;
            foreach (var view in views)
            {
                if (view["viewType"]?.Value<string>() == "FloorPlan")
                {
                    hasFloorPlan = true;
                    break;
                }
            }
            hasFloorPlan.Should().BeTrue("Default context should have floor plan views");
        }

        [Test]
        public void GetViews_ReturnsCorrectViewProperties()
        {
            // Act
            var response = ExecuteMethod("getViews");
            var views = response["views"] as JArray;
            var firstView = views[0];

            // Assert
            firstView["viewId"].Should().NotBeNull();
            firstView["name"].Should().NotBeNull();
            firstView["viewType"].Should().NotBeNull();
        }

        [Test]
        public void GetAllViews_SameAsGetViews()
        {
            // Act
            var response1 = ExecuteMethod("getViews");
            var response2 = ExecuteMethod("getAllViews");

            // Assert
            AssertSuccess(response1);
            AssertSuccess(response2);

            var count1 = (response1["views"] as JArray).Count;
            var count2 = (response2["views"] as JArray).Count;
            count1.Should().Be(count2);
        }

        #endregion

        #region View Types Tests

        [Test]
        public void GetViews_IncludesSections()
        {
            // Act
            var response = ExecuteMethod("getViews");
            var views = response["views"] as JArray;

            // Assert
            var hasSection = false;
            foreach (var view in views)
            {
                if (view["viewType"]?.Value<string>() == "Section")
                {
                    hasSection = true;
                    break;
                }
            }
            hasSection.Should().BeTrue("Default context should have section views");
        }

        #endregion
    }
}
