using System;
using NUnit.Framework;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.Tests.Mocks;

namespace RevitMCPBridge.Tests
{
    /// <summary>
    /// Base class for all RevitMCPBridge tests.
    /// Provides common setup, utilities, and mock context.
    /// </summary>
    public abstract class TestBase
    {
        protected MockRevitContext MockContext { get; private set; }

        [SetUp]
        public virtual void Setup()
        {
            MockContext = new MockRevitContext();
        }

        [TearDown]
        public virtual void TearDown()
        {
            MockContext = null;
        }

        #region Assertion Helpers

        /// <summary>
        /// Execute a mock MCP method and return the parsed response
        /// </summary>
        protected JObject ExecuteMethod(string method, object parameters = null)
        {
            var paramsJson = parameters != null
                ? JObject.FromObject(parameters)
                : new JObject();

            var response = MockContext.ExecuteMethod(method, paramsJson);
            return JObject.Parse(response);
        }

        /// <summary>
        /// Assert that a response indicates success
        /// </summary>
        protected void AssertSuccess(JObject response, string message = null)
        {
            Assert.That(response["success"]?.Value<bool>(), Is.True,
                message ?? $"Expected success but got error: {response["error"]}");
        }

        /// <summary>
        /// Assert that a response indicates failure
        /// </summary>
        protected void AssertFailure(JObject response, string expectedError = null)
        {
            Assert.That(response["success"]?.Value<bool>(), Is.False,
                "Expected failure but got success");

            if (expectedError != null)
            {
                Assert.That(response["error"]?.ToString(), Does.Contain(expectedError));
            }
        }

        /// <summary>
        /// Assert that a response contains a specific property with expected value
        /// </summary>
        protected void AssertProperty<T>(JObject response, string property, T expectedValue)
        {
            var actualValue = response[property]?.Value<T>();
            Assert.That(actualValue, Is.EqualTo(expectedValue),
                $"Property '{property}' expected {expectedValue} but was {actualValue}");
        }

        /// <summary>
        /// Assert that a response contains an array with expected count
        /// </summary>
        protected void AssertArrayCount(JObject response, string property, int expectedCount)
        {
            var array = response[property] as JArray;
            Assert.That(array, Is.Not.Null, $"Property '{property}' is not an array");
            Assert.That(array.Count, Is.EqualTo(expectedCount),
                $"Array '{property}' expected {expectedCount} items but had {array.Count}");
        }

        /// <summary>
        /// Assert that an element exists in the mock context
        /// </summary>
        protected void AssertElementExists(int elementId)
        {
            Assert.That(MockContext.Elements.ContainsKey(elementId), Is.True,
                $"Element {elementId} should exist but doesn't");
        }

        /// <summary>
        /// Assert that an element does not exist in the mock context
        /// </summary>
        protected void AssertElementNotExists(int elementId)
        {
            Assert.That(MockContext.Elements.ContainsKey(elementId), Is.False,
                $"Element {elementId} should not exist but does");
        }

        #endregion

        #region Test Data Helpers

        /// <summary>
        /// Create a standard wall for testing
        /// </summary>
        protected MockWall CreateTestWall(double length = 20.0)
        {
            return MockContext.CreateWall(0, 0, length, 0, 1, 1001, 10.0);
        }

        /// <summary>
        /// Create a standard room for testing
        /// </summary>
        protected MockRoom CreateTestRoom(string name = "Test Room")
        {
            return MockContext.CreateRoom(1, 10, 10, name);
        }

        /// <summary>
        /// Create a standard sheet for testing
        /// </summary>
        protected MockSheet CreateTestSheet(string number = "A-101", string name = "Test Sheet")
        {
            return MockContext.CreateSheet(number, name, null);
        }

        #endregion
    }
}
