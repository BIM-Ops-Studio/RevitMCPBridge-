using System;
using System.Diagnostics;
using System.Threading;
using Serilog;
using Serilog.Context;

namespace RevitMCPBridge.Helpers
{
    /// <summary>
    /// Enhanced logging with correlation IDs for request tracking.
    /// Wraps Serilog with additional context management.
    /// </summary>
    public static class CorrelatedLogger
    {
        private static readonly AsyncLocal<string> _correlationId = new AsyncLocal<string>();
        private static readonly AsyncLocal<Stopwatch> _requestTimer = new AsyncLocal<Stopwatch>();

        /// <summary>
        /// Current correlation ID for the request
        /// </summary>
        public static string CorrelationId
        {
            get => _correlationId.Value ?? "no-correlation";
            private set => _correlationId.Value = value;
        }

        /// <summary>
        /// Start a new correlated request scope
        /// </summary>
        public static IDisposable BeginRequest(string method, string correlationId = null)
        {
            correlationId = correlationId ?? GenerateCorrelationId();
            CorrelationId = correlationId;

            _requestTimer.Value = Stopwatch.StartNew();

            Log.Information("[{CorrelationId}] Request started: {Method}",
                correlationId, method);

            return new RequestScope(correlationId, method);
        }

        /// <summary>
        /// Log with correlation ID automatically included
        /// </summary>
        public static void Info(string messageTemplate, params object[] args)
        {
            Log.Information($"[{{CorrelationId}}] {messageTemplate}",
                PrependCorrelationId(args));
        }

        public static void Debug(string messageTemplate, params object[] args)
        {
            Log.Debug($"[{{CorrelationId}}] {messageTemplate}",
                PrependCorrelationId(args));
        }

        public static void Warning(string messageTemplate, params object[] args)
        {
            Log.Warning($"[{{CorrelationId}}] {messageTemplate}",
                PrependCorrelationId(args));
        }

        public static void Error(string messageTemplate, params object[] args)
        {
            Log.Error($"[{{CorrelationId}}] {messageTemplate}",
                PrependCorrelationId(args));
        }

        public static void Error(Exception ex, string messageTemplate, params object[] args)
        {
            Log.Error(ex, $"[{{CorrelationId}}] {messageTemplate}",
                PrependCorrelationId(args));
        }

        /// <summary>
        /// Log method entry
        /// </summary>
        public static void MethodEntry(string methodName, object parameters = null)
        {
            if (parameters != null)
            {
                Log.Debug("[{CorrelationId}] Entering {Method} with {@Parameters}",
                    CorrelationId, methodName, parameters);
            }
            else
            {
                Log.Debug("[{CorrelationId}] Entering {Method}",
                    CorrelationId, methodName);
            }
        }

        /// <summary>
        /// Log method exit with result
        /// </summary>
        public static void MethodExit(string methodName, bool success, object result = null)
        {
            var elapsed = _requestTimer.Value?.ElapsedMilliseconds ?? 0;

            if (success)
            {
                Log.Debug("[{CorrelationId}] Exiting {Method} - Success in {ElapsedMs}ms",
                    CorrelationId, methodName, elapsed);
            }
            else
            {
                Log.Warning("[{CorrelationId}] Exiting {Method} - Failed in {ElapsedMs}ms",
                    CorrelationId, methodName, elapsed);
            }
        }

        /// <summary>
        /// Log element creation
        /// </summary>
        public static void ElementCreated(string elementType, int elementId)
        {
            Log.Information("[{CorrelationId}] Created {ElementType} with ID {ElementId}",
                CorrelationId, elementType, elementId);
        }

        /// <summary>
        /// Log element deletion
        /// </summary>
        public static void ElementDeleted(string elementType, int elementId)
        {
            Log.Information("[{CorrelationId}] Deleted {ElementType} with ID {ElementId}",
                CorrelationId, elementType, elementId);
        }

        /// <summary>
        /// Log transaction
        /// </summary>
        public static void TransactionStarted(string transactionName)
        {
            Log.Debug("[{CorrelationId}] Transaction started: {TransactionName}",
                CorrelationId, transactionName);
        }

        public static void TransactionCommitted(string transactionName)
        {
            Log.Debug("[{CorrelationId}] Transaction committed: {TransactionName}",
                CorrelationId, transactionName);
        }

        public static void TransactionRolledBack(string transactionName, string reason)
        {
            Log.Warning("[{CorrelationId}] Transaction rolled back: {TransactionName} - {Reason}",
                CorrelationId, transactionName, reason);
        }

        /// <summary>
        /// Log autonomy operation
        /// </summary>
        public static void AutonomyGoalStarted(string goalType, string taskId)
        {
            Log.Information("[{CorrelationId}] Autonomy goal started: {GoalType} (Task: {TaskId})",
                CorrelationId, goalType, taskId);
        }

        public static void AutonomyStepExecuted(string taskId, int stepNumber, string method, bool success)
        {
            if (success)
            {
                Log.Information("[{CorrelationId}] Step {StepNumber} completed: {Method}",
                    CorrelationId, stepNumber, method);
            }
            else
            {
                Log.Warning("[{CorrelationId}] Step {StepNumber} failed: {Method}",
                    CorrelationId, stepNumber, method);
            }
        }

        public static void AutonomySelfHeal(string taskId, string error, string fix)
        {
            Log.Information("[{CorrelationId}] Self-healing: {Error} -> {Fix}",
                CorrelationId, error, fix);
        }

        private static string GenerateCorrelationId()
        {
            return $"req-{DateTime.UtcNow:HHmmss}-{Guid.NewGuid().ToString("N").Substring(0, 6)}";
        }

        private static object[] PrependCorrelationId(object[] args)
        {
            var newArgs = new object[args.Length + 1];
            newArgs[0] = CorrelationId;
            Array.Copy(args, 0, newArgs, 1, args.Length);
            return newArgs;
        }

        /// <summary>
        /// Request scope for automatic cleanup
        /// </summary>
        private class RequestScope : IDisposable
        {
            private readonly string _correlationId;
            private readonly string _method;
            private readonly Stopwatch _stopwatch;

            public RequestScope(string correlationId, string method)
            {
                _correlationId = correlationId;
                _method = method;
                _stopwatch = Stopwatch.StartNew();
            }

            public void Dispose()
            {
                _stopwatch.Stop();
                Log.Information("[{CorrelationId}] Request completed: {Method} in {ElapsedMs}ms",
                    _correlationId, _method, _stopwatch.ElapsedMilliseconds);

                _correlationId.ToString(); // Clear correlation ID would go here
            }
        }
    }
}
