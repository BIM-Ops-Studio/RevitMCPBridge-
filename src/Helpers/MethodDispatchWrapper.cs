using System;
using System.Diagnostics;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Serilog;

namespace RevitMCPBridge.Helpers
{
    /// <summary>
    /// Centralized method dispatch wrapper that adds structured logging, timing,
    /// error handling, and statistics to every MCP method call.
    ///
    /// This wraps the raw method delegates so that ALL 705+ methods automatically get:
    /// - Correlation ID tracking via CorrelatedLogger
    /// - Execution timing (recorded to MCPServer stats)
    /// - Structured error responses via ResponseBuilder
    /// - Input parameter logging at Debug level
    /// - Consistent exception-to-JSON conversion
    /// </summary>
    public static class MethodDispatchWrapper
    {
        /// <summary>
        /// Wrap a method call with full observability and error handling.
        /// Use this at both dispatch points: ProcessMessage switch and ExecuteMethod registry.
        /// </summary>
        /// <param name="methodName">The MCP method name being called</param>
        /// <param name="method">The actual method delegate</param>
        /// <param name="uiApp">Revit UIApplication context</param>
        /// <param name="parameters">JSON parameters from the caller</param>
        /// <returns>JSON response string (always valid JSON, never throws)</returns>
        public static string Execute(
            string methodName,
            Func<UIApplication, JObject, string> method,
            UIApplication uiApp,
            JObject parameters)
        {
            var sw = Stopwatch.StartNew();
            string correlationId = null;
            bool success = false;

            try
            {
                // Start correlated request scope
                using (var scope = CorrelatedLogger.BeginRequest(methodName))
                {
                    correlationId = CorrelatedLogger.CorrelationId;

                    // Log input parameters at Debug level (truncate large payloads)
                    if (parameters != null)
                    {
                        var paramStr = parameters.ToString(Formatting.None);
                        if (paramStr.Length > 2000)
                            paramStr = paramStr.Substring(0, 2000) + "...(truncated)";
                        Log.Debug("[{CorrelationId}] Parameters: {Params}", correlationId, paramStr);
                    }

                    // Validate basic preconditions
                    if (uiApp == null)
                    {
                        Log.Error("[{CorrelationId}] uiApp is null for method {Method}", correlationId, methodName);
                        return ResponseBuilder.Error("No Revit application context available", "NO_CONTEXT")
                            .WithCorrelationId(correlationId)
                            .WithExecutionTime(sw.ElapsedMilliseconds)
                            .Build();
                    }

                    // Execute the actual method
                    var result = method(uiApp, parameters ?? new JObject());

                    sw.Stop();

                    // Parse result to check success status
                    success = true;
                    try
                    {
                        var resultObj = JObject.Parse(result);
                        success = resultObj["success"]?.Value<bool>() ?? true;

                        // Inject correlation ID and timing if not already present
                        if (resultObj["correlationId"] == null)
                            resultObj["correlationId"] = correlationId;
                        if (resultObj["executionTimeMs"] == null)
                            resultObj["executionTimeMs"] = sw.ElapsedMilliseconds;

                        result = resultObj.ToString(Formatting.None);
                    }
                    catch (JsonReaderException)
                    {
                        // Result isn't valid JSON - wrap it
                        Log.Warning("[{CorrelationId}] Method {Method} returned non-JSON result",
                            correlationId, methodName);
                        result = ResponseBuilder.Success()
                            .With("rawResult", result)
                            .WithCorrelationId(correlationId)
                            .WithExecutionTime(sw.ElapsedMilliseconds)
                            .Build();
                    }

                    // Log completion
                    if (success)
                    {
                        Log.Information("[{CorrelationId}] {Method} completed in {ElapsedMs}ms",
                            correlationId, methodName, sw.ElapsedMilliseconds);
                    }
                    else
                    {
                        Log.Warning("[{CorrelationId}] {Method} returned failure in {ElapsedMs}ms",
                            correlationId, methodName, sw.ElapsedMilliseconds);
                    }

                    return result;
                }
            }
            catch (Autodesk.Revit.Exceptions.InvalidOperationException ex)
            {
                // Revit API specific exception - often means wrong thread or invalid state
                sw.Stop();
                Log.Error(ex, "[{CorrelationId}] Revit API error in {Method}: {Message}",
                    correlationId ?? "none", methodName, ex.Message);

                return ResponseBuilder.Error(
                        $"Revit API error: {ex.Message}. This often means Revit is in a modal state or the operation is not valid in the current context.",
                        "REVIT_API_ERROR")
                    .WithCorrelationId(correlationId)
                    .WithExecutionTime(sw.ElapsedMilliseconds)
                    .With("method", methodName)
                    .Build();
            }
            catch (Autodesk.Revit.Exceptions.ArgumentException ex)
            {
                // Revit argument exception - bad parameter values
                sw.Stop();
                Log.Error(ex, "[{CorrelationId}] Revit argument error in {Method}: {Message}",
                    correlationId ?? "none", methodName, ex.Message);

                return ResponseBuilder.Error(
                        $"Invalid argument: {ex.Message}",
                        "REVIT_ARGUMENT_ERROR")
                    .WithCorrelationId(correlationId)
                    .WithExecutionTime(sw.ElapsedMilliseconds)
                    .With("method", methodName)
                    .Build();
            }
            catch (Exceptions.MCPValidationException ex)
            {
                // Parameter validation failure
                sw.Stop();
                Log.Warning("[{CorrelationId}] Validation error in {Method}: {Message}",
                    correlationId ?? "none", methodName, ex.Message);

                return ResponseBuilder.FromException(ex)
                    .WithCorrelationId(correlationId)
                    .WithExecutionTime(sw.ElapsedMilliseconds)
                    .With("method", methodName)
                    .Build();
            }
            catch (Exceptions.MCPRevitException ex)
            {
                // Structured Revit operation failure
                sw.Stop();
                Log.Error(ex, "[{CorrelationId}] Revit operation error in {Method}: {Message}",
                    correlationId ?? "none", methodName, ex.Message);

                return ResponseBuilder.FromException(ex)
                    .WithCorrelationId(correlationId)
                    .WithExecutionTime(sw.ElapsedMilliseconds)
                    .With("method", methodName)
                    .Build();
            }
            catch (Exceptions.MCPTimeoutException ex)
            {
                // Timeout
                sw.Stop();
                Log.Error("[{CorrelationId}] Timeout in {Method}: {Message}",
                    correlationId ?? "none", methodName, ex.Message);

                return ResponseBuilder.FromException(ex)
                    .WithCorrelationId(correlationId)
                    .WithExecutionTime(sw.ElapsedMilliseconds)
                    .With("method", methodName)
                    .Build();
            }
            catch (Exceptions.MCPException ex)
            {
                // Any other structured MCP exception
                sw.Stop();
                Log.Error(ex, "[{CorrelationId}] MCP error in {Method}: {Message}",
                    correlationId ?? "none", methodName, ex.Message);

                return ResponseBuilder.FromException(ex)
                    .WithCorrelationId(correlationId)
                    .WithExecutionTime(sw.ElapsedMilliseconds)
                    .With("method", methodName)
                    .Build();
            }
            catch (NullReferenceException ex)
            {
                // Null reference - common in Revit API when elements are deleted or document changes
                sw.Stop();
                Log.Error(ex, "[{CorrelationId}] Null reference in {Method}. Document may have changed or element may have been deleted.",
                    correlationId ?? "none", methodName);

                return ResponseBuilder.Error(
                        $"Null reference error in {methodName}. A Revit element may have been deleted or the document state changed. Details: {ex.Message}",
                        "NULL_REFERENCE")
                    .WithCorrelationId(correlationId)
                    .WithExecutionTime(sw.ElapsedMilliseconds)
                    .With("method", methodName)
                    .With("stackTrace", ex.StackTrace)
                    .Build();
            }
            catch (Exception ex)
            {
                // Catch-all for unexpected exceptions
                sw.Stop();
                Log.Error(ex, "[{CorrelationId}] Unexpected error in {Method}: {ExType} - {Message}",
                    correlationId ?? "none", methodName, ex.GetType().Name, ex.Message);

                return ResponseBuilder.Error(
                        $"{ex.GetType().Name}: {ex.Message}",
                        "INTERNAL_ERROR")
                    .WithCorrelationId(correlationId)
                    .WithExecutionTime(sw.ElapsedMilliseconds)
                    .With("method", methodName)
                    .With("exceptionType", ex.GetType().FullName)
                    .With("stackTrace", ex.StackTrace)
                    .Build();
            }
            finally
            {
                sw.Stop();
                // Record stats regardless of outcome
                MCPServer.RecordRequestExternal(success, sw.ElapsedMilliseconds);
            }
        }

        /// <summary>
        /// Wrap a method for use in the registry.
        /// Returns a new delegate that includes the dispatch wrapper.
        /// </summary>
        public static Func<UIApplication, JObject, string> Wrap(
            string methodName,
            Func<UIApplication, JObject, string> method)
        {
            return (uiApp, parameters) => Execute(methodName, method, uiApp, parameters);
        }
    }
}
