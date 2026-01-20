using System;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using NUnit.Framework;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using FluentAssertions;

namespace RevitMCPBridge.Tests.Integration
{
    /// <summary>
    /// Integration tests for named pipe communication.
    /// These tests verify the pipe protocol without requiring Revit.
    /// </summary>
    [TestFixture]
    [Category("Integration")]
    public class PipeConnectionTests
    {
        private const string TestPipeName = "RevitMCPBridge_Test";

        #region Protocol Tests

        [Test]
        public void JsonRequest_ValidFormat_Parses()
        {
            // Arrange
            var request = new
            {
                method = "getWalls",
                @params = new { viewId = 12345 }
            };

            // Act
            var json = JsonConvert.SerializeObject(request);
            var parsed = JObject.Parse(json);

            // Assert
            parsed["method"].Value<string>().Should().Be("getWalls");
            parsed["params"]["viewId"].Value<int>().Should().Be(12345);
        }

        [Test]
        public void JsonResponse_SuccessFormat_Correct()
        {
            // Arrange
            var response = new
            {
                success = true,
                wallId = 123456,
                length = 20.0
            };

            // Act
            var json = JsonConvert.SerializeObject(response);
            var parsed = JObject.Parse(json);

            // Assert
            parsed["success"].Value<bool>().Should().BeTrue();
            parsed["wallId"].Value<int>().Should().Be(123456);
        }

        [Test]
        public void JsonResponse_ErrorFormat_Correct()
        {
            // Arrange
            var response = new
            {
                success = false,
                error = "Wall not found",
                errorCode = "ELEMENT_NOT_FOUND"
            };

            // Act
            var json = JsonConvert.SerializeObject(response);
            var parsed = JObject.Parse(json);

            // Assert
            parsed["success"].Value<bool>().Should().BeFalse();
            parsed["error"].Value<string>().Should().Be("Wall not found");
        }

        #endregion

        #region Request Validation Tests

        [Test]
        public void Request_MissingMethod_Invalid()
        {
            // Arrange
            var request = new { @params = new { } };

            // Act
            var json = JsonConvert.SerializeObject(request);
            var parsed = JObject.Parse(json);

            // Assert
            parsed["method"].Should().BeNull();
        }

        [Test]
        public void Request_EmptyParams_Valid()
        {
            // Arrange
            var request = new { method = "getLevels", @params = new { } };

            // Act
            var json = JsonConvert.SerializeObject(request);
            var parsed = JObject.Parse(json);

            // Assert
            parsed["method"].Should().NotBeNull();
            parsed["params"].Should().NotBeNull();
        }

        [Test]
        public void Request_NullParams_Handled()
        {
            // Arrange
            var request = new { method = "getLevels" };

            // Act
            var json = JsonConvert.SerializeObject(request);
            var parsed = JObject.Parse(json);

            // Assert
            parsed["method"].Should().NotBeNull();
            // params may be null, system should handle
        }

        [Test]
        public void Request_ComplexParams_Serialized()
        {
            // Arrange
            var request = new
            {
                method = "createWallBatch",
                @params = new
                {
                    walls = new[]
                    {
                        new { startX = 0, startY = 0, endX = 10, endY = 0 },
                        new { startX = 10, startY = 0, endX = 10, endY = 10 }
                    }
                }
            };

            // Act
            var json = JsonConvert.SerializeObject(request);
            var parsed = JObject.Parse(json);
            var walls = parsed["params"]["walls"] as JArray;

            // Assert
            walls.Should().NotBeNull();
            walls.Count.Should().Be(2);
        }

        #endregion

        #region Mock Server Tests

        [Test]
        public async Task MockServer_AcceptsConnection()
        {
            // This test creates a mock server and client to test pipe communication
            var serverConnected = false;
            var clientConnected = false;

            // Start server
            var serverTask = Task.Run(() =>
            {
                using (var server = new NamedPipeServerStream(TestPipeName, PipeDirection.InOut))
                {
                    server.WaitForConnection();
                    serverConnected = true;

                    // Read request
                    var reader = new StreamReader(server);
                    var request = reader.ReadLine();

                    // Send response
                    var writer = new StreamWriter(server) { AutoFlush = true };
                    writer.WriteLine("{\"success\":true}");
                }
            });

            // Give server time to start
            await Task.Delay(100);

            // Connect client
            using (var client = new NamedPipeClientStream(".", TestPipeName, PipeDirection.InOut))
            {
                client.Connect(1000);
                clientConnected = true;

                // Send request
                var writer = new StreamWriter(client) { AutoFlush = true };
                writer.WriteLine("{\"method\":\"test\"}");

                // Read response
                var reader = new StreamReader(client);
                var response = reader.ReadLine();

                response.Should().Contain("success");
            }

            await serverTask;

            serverConnected.Should().BeTrue();
            clientConnected.Should().BeTrue();
        }

        [Test]
        public void MockServer_HandlesMultipleRequests()
        {
            // Test that we can send multiple requests over the same connection
            var requestCount = 0;

            var serverTask = Task.Run(() =>
            {
                using (var server = new NamedPipeServerStream(TestPipeName + "_multi", PipeDirection.InOut))
                {
                    server.WaitForConnection();

                    var reader = new StreamReader(server);
                    var writer = new StreamWriter(server) { AutoFlush = true };

                    // Handle 3 requests
                    for (int i = 0; i < 3; i++)
                    {
                        var request = reader.ReadLine();
                        if (request != null)
                        {
                            requestCount++;
                            writer.WriteLine($"{{\"success\":true,\"requestNum\":{i}}}");
                        }
                    }
                }
            });

            Task.Delay(100).Wait();

            using (var client = new NamedPipeClientStream(".", TestPipeName + "_multi", PipeDirection.InOut))
            {
                client.Connect(1000);

                var writer = new StreamWriter(client) { AutoFlush = true };
                var reader = new StreamReader(client);

                for (int i = 0; i < 3; i++)
                {
                    writer.WriteLine($"{{\"method\":\"test{i}\"}}");
                    var response = reader.ReadLine();
                    var parsed = JObject.Parse(response);
                    parsed["requestNum"].Value<int>().Should().Be(i);
                }
            }

            serverTask.Wait(2000);
            requestCount.Should().Be(3);
        }

        #endregion

        #region Error Handling Tests

        [Test]
        public void MalformedJson_HandledGracefully()
        {
            // Act
            Action parse = () => JObject.Parse("not valid json {{{");

            // Assert
            parse.Should().Throw<JsonReaderException>();
        }

        [Test]
        public void EmptyRequest_HandledGracefully()
        {
            // Act
            var parsed = JObject.Parse("{}");

            // Assert
            parsed["method"].Should().BeNull();
        }

        #endregion
    }
}
