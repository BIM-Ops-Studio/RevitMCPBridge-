using System;

namespace RevitMCPBridge.Exceptions
{
    /// <summary>
    /// Base exception for all MCP Bridge errors.
    /// Provides error code and structured error information.
    /// </summary>
    public class MCPException : Exception
    {
        public string ErrorCode { get; }
        public string Details { get; }

        public MCPException(string message, string errorCode = "MCP_ERROR", string details = null)
            : base(message)
        {
            ErrorCode = errorCode;
            Details = details;
        }

        public MCPException(string message, Exception innerException, string errorCode = "MCP_ERROR")
            : base(message, innerException)
        {
            ErrorCode = errorCode;
        }
    }

    /// <summary>
    /// Exception for parameter validation failures.
    /// </summary>
    public class MCPValidationException : MCPException
    {
        public string ParameterName { get; }
        public object InvalidValue { get; }

        public MCPValidationException(string parameterName, string message, object invalidValue = null)
            : base(message, "VALIDATION_ERROR", $"Parameter: {parameterName}")
        {
            ParameterName = parameterName;
            InvalidValue = invalidValue;
        }

        public static MCPValidationException Required(string parameterName)
        {
            return new MCPValidationException(parameterName, $"Parameter '{parameterName}' is required");
        }

        public static MCPValidationException InvalidType(string parameterName, string expectedType, object actualValue)
        {
            return new MCPValidationException(parameterName,
                $"Parameter '{parameterName}' must be of type {expectedType}",
                actualValue);
        }

        public static MCPValidationException OutOfRange(string parameterName, object value, object min, object max)
        {
            return new MCPValidationException(parameterName,
                $"Parameter '{parameterName}' value {value} is out of range [{min}, {max}]",
                value);
        }
    }

    /// <summary>
    /// Exception for Revit API operation failures.
    /// </summary>
    public class MCPRevitException : MCPException
    {
        public int? ElementId { get; }
        public string Operation { get; }

        public MCPRevitException(string message, string operation, int? elementId = null)
            : base(message, "REVIT_ERROR", $"Operation: {operation}")
        {
            ElementId = elementId;
            Operation = operation;
        }

        public static MCPRevitException ElementNotFound(int elementId)
        {
            return new MCPRevitException($"Element with ID {elementId} not found", "GetElement", elementId);
        }

        public static MCPRevitException TypeNotFound(string typeName, string category)
        {
            return new MCPRevitException($"{category} type '{typeName}' not found", "GetType");
        }

        public static MCPRevitException LevelNotFound(int levelId)
        {
            return new MCPRevitException($"Level with ID {levelId} not found", "GetLevel", levelId);
        }

        public static MCPRevitException TransactionFailed(string operation, string reason)
        {
            return new MCPRevitException($"Transaction failed for {operation}: {reason}", operation);
        }

        public static MCPRevitException InvalidGeometry(string description)
        {
            return new MCPRevitException($"Invalid geometry: {description}", "CreateGeometry");
        }
    }

    /// <summary>
    /// Exception for timeout conditions.
    /// </summary>
    public class MCPTimeoutException : MCPException
    {
        public int TimeoutMs { get; }
        public string Operation { get; }

        public MCPTimeoutException(string operation, int timeoutMs)
            : base($"Operation '{operation}' timed out after {timeoutMs}ms", "TIMEOUT_ERROR")
        {
            TimeoutMs = timeoutMs;
            Operation = operation;
        }
    }

    /// <summary>
    /// Exception for autonomy-related failures.
    /// </summary>
    public class MCPAutonomyException : MCPException
    {
        public string TaskId { get; }
        public string GoalType { get; }

        public MCPAutonomyException(string message, string taskId = null, string goalType = null)
            : base(message, "AUTONOMY_ERROR")
        {
            TaskId = taskId;
            GoalType = goalType;
        }

        public static MCPAutonomyException TaskNotFound(string taskId)
        {
            return new MCPAutonomyException($"Task '{taskId}' not found", taskId);
        }

        public static MCPAutonomyException UnsupportedGoal(string goalType)
        {
            return new MCPAutonomyException($"Unsupported goal type: {goalType}", goalType: goalType);
        }

        public static MCPAutonomyException GuardrailViolation(string method, string reason)
        {
            return new MCPAutonomyException($"Guardrail violation for method '{method}': {reason}");
        }

        public static MCPAutonomyException MaxRetriesExceeded(string taskId, int retries)
        {
            return new MCPAutonomyException($"Max retries ({retries}) exceeded for task '{taskId}'", taskId);
        }
    }

    /// <summary>
    /// Exception for configuration errors.
    /// </summary>
    public class MCPConfigurationException : MCPException
    {
        public string ConfigKey { get; }

        public MCPConfigurationException(string message, string configKey = null)
            : base(message, "CONFIG_ERROR")
        {
            ConfigKey = configKey;
        }
    }

    /// <summary>
    /// Exception for connection/communication errors.
    /// </summary>
    public class MCPConnectionException : MCPException
    {
        public MCPConnectionException(string message)
            : base(message, "CONNECTION_ERROR")
        {
        }

        public static MCPConnectionException PipeNotAvailable(string pipeName)
        {
            return new MCPConnectionException($"Named pipe '{pipeName}' is not available");
        }

        public static MCPConnectionException Disconnected()
        {
            return new MCPConnectionException("Connection to MCP server was lost");
        }
    }
}
