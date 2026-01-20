using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using RevitMCPBridge.Exceptions;

namespace RevitMCPBridge.Helpers
{
    /// <summary>
    /// Standardized response builder for MCP method responses.
    /// Ensures consistent JSON structure across all methods.
    /// </summary>
    public class ResponseBuilder
    {
        private readonly Dictionary<string, object> _data;
        private string _correlationId;

        public ResponseBuilder()
        {
            _data = new Dictionary<string, object>
            {
                ["success"] = true
            };
        }

        /// <summary>
        /// Create a success response builder
        /// </summary>
        public static ResponseBuilder Success()
        {
            return new ResponseBuilder();
        }

        /// <summary>
        /// Create an error response builder
        /// </summary>
        public static ResponseBuilder Error(string message, string errorCode = "ERROR")
        {
            var builder = new ResponseBuilder();
            builder._data["success"] = false;
            builder._data["error"] = message;
            builder._data["errorCode"] = errorCode;
            return builder;
        }

        /// <summary>
        /// Create an error response from an exception
        /// </summary>
        public static ResponseBuilder FromException(Exception ex)
        {
            var builder = new ResponseBuilder();
            builder._data["success"] = false;
            builder._data["error"] = ex.Message;

            if (ex is MCPException mcpEx)
            {
                builder._data["errorCode"] = mcpEx.ErrorCode;
                if (!string.IsNullOrEmpty(mcpEx.Details))
                {
                    builder._data["details"] = mcpEx.Details;
                }
            }
            else
            {
                builder._data["errorCode"] = "INTERNAL_ERROR";
            }

#if DEBUG
            builder._data["stackTrace"] = ex.StackTrace;
#endif

            return builder;
        }

        /// <summary>
        /// Add a property to the response
        /// </summary>
        public ResponseBuilder With(string key, object value)
        {
            _data[key] = value;
            return this;
        }

        /// <summary>
        /// Add element ID to the response
        /// </summary>
        public ResponseBuilder WithElementId(int elementId, string key = "elementId")
        {
            _data[key] = elementId;
            return this;
        }

        /// <summary>
        /// Add wall-specific response data
        /// </summary>
        public ResponseBuilder WithWall(int wallId, double? length = null)
        {
            _data["wallId"] = wallId;
            if (length.HasValue)
                _data["length"] = length.Value;
            return this;
        }

        /// <summary>
        /// Add room-specific response data
        /// </summary>
        public ResponseBuilder WithRoom(int roomId, string name = null, double? area = null)
        {
            _data["roomId"] = roomId;
            if (name != null)
                _data["name"] = name;
            if (area.HasValue)
                _data["area"] = area.Value;
            return this;
        }

        /// <summary>
        /// Add view-specific response data
        /// </summary>
        public ResponseBuilder WithView(int viewId, string name = null, string viewType = null)
        {
            _data["viewId"] = viewId;
            if (name != null)
                _data["name"] = name;
            if (viewType != null)
                _data["viewType"] = viewType;
            return this;
        }

        /// <summary>
        /// Add sheet-specific response data
        /// </summary>
        public ResponseBuilder WithSheet(int sheetId, string number = null, string name = null)
        {
            _data["sheetId"] = sheetId;
            if (number != null)
                _data["sheetNumber"] = number;
            if (name != null)
                _data["sheetName"] = name;
            return this;
        }

        /// <summary>
        /// Add a list/array to the response
        /// </summary>
        public ResponseBuilder WithList<T>(string key, IEnumerable<T> items)
        {
            _data[key] = items;
            return this;
        }

        /// <summary>
        /// Add count property
        /// </summary>
        public ResponseBuilder WithCount(int count, string key = "count")
        {
            _data[key] = count;
            return this;
        }

        /// <summary>
        /// Add message property
        /// </summary>
        public ResponseBuilder WithMessage(string message)
        {
            _data["message"] = message;
            return this;
        }

        /// <summary>
        /// Add correlation ID for request tracking
        /// </summary>
        public ResponseBuilder WithCorrelationId(string correlationId)
        {
            _correlationId = correlationId;
            if (!string.IsNullOrEmpty(correlationId))
            {
                _data["correlationId"] = correlationId;
            }
            return this;
        }

        /// <summary>
        /// Add execution time
        /// </summary>
        public ResponseBuilder WithExecutionTime(long milliseconds)
        {
            _data["executionTimeMs"] = milliseconds;
            return this;
        }

        /// <summary>
        /// Build the JSON response string
        /// </summary>
        public string Build()
        {
            return JsonConvert.SerializeObject(_data, Formatting.None);
        }

        /// <summary>
        /// Build with pretty formatting (for debugging)
        /// </summary>
        public string BuildFormatted()
        {
            return JsonConvert.SerializeObject(_data, Formatting.Indented);
        }

        /// <summary>
        /// Implicit conversion to string
        /// </summary>
        public static implicit operator string(ResponseBuilder builder)
        {
            return builder.Build();
        }
    }

    /// <summary>
    /// Standard response data objects for common element types
    /// </summary>
    public static class ResponseData
    {
        public static object Wall(int id, double startX, double startY, double endX, double endY, double height, double length)
        {
            return new
            {
                wallId = id,
                startX,
                startY,
                endX,
                endY,
                height,
                length
            };
        }

        public static object Room(int id, string name, double area, int levelId)
        {
            return new
            {
                roomId = id,
                name,
                area,
                levelId
            };
        }

        public static object View(int id, string name, string viewType)
        {
            return new
            {
                viewId = id,
                name,
                viewType
            };
        }

        public static object Level(int id, string name, double elevation)
        {
            return new
            {
                levelId = id,
                name,
                elevation
            };
        }

        public static object Sheet(int id, string number, string name)
        {
            return new
            {
                sheetId = id,
                sheetNumber = number,
                sheetName = name
            };
        }

        public static object ElementType(int id, string name, string category = null)
        {
            return new
            {
                typeId = id,
                name,
                category
            };
        }
    }
}
