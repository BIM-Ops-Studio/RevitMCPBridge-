using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Interface for verification hooks that check placed elements.
    /// This is Enhancement #6: Verification Loops
    /// </summary>
    public interface IVerificationHook
    {
        string HookName { get; }
        VerificationCheck Verify(ConfidenceEnvelope envelope, JObject executionResult);
    }

    /// <summary>
    /// Runs post-execution verifications to ensure placed elements match intent
    /// </summary>
    public class PostExecutionVerifier
    {
        private readonly UIApplication _uiApp;
        private readonly List<IVerificationHook> _hooks = new List<IVerificationHook>();

        public PostExecutionVerifier(UIApplication uiApp)
        {
            _uiApp = uiApp;

            // Register built-in hooks
            RegisterHook(new ElementExistsVerifier());
            RegisterHook(new ResultSuccessVerifier());
        }

        /// <summary>
        /// Register a verification hook
        /// </summary>
        public void RegisterHook(IVerificationHook hook)
        {
            _hooks.Add(hook);
            Log.Debug("[CIPS] Registered verification hook: {Hook}", hook.HookName);
        }

        /// <summary>
        /// Run all verification hooks on an executed operation
        /// </summary>
        public VerificationReport RunVerifications(ConfidenceEnvelope envelope)
        {
            var report = new VerificationReport
            {
                OperationId = envelope.OperationId
            };

            if (envelope.Result == null)
            {
                report.AddCheck(VerificationCheck.Fail(
                    "ResultExists",
                    "Non-null result",
                    "null",
                    "No execution result available to verify"));
                return report;
            }

            foreach (var hook in _hooks)
            {
                try
                {
                    var sw = Stopwatch.StartNew();
                    var check = hook.Verify(envelope, envelope.Result);
                    sw.Stop();

                    check.ExecutionTimeMs = sw.ElapsedMilliseconds;
                    report.AddCheck(check);

                    Log.Debug("[CIPS] Verification {Hook}: {Passed} ({Time}ms)",
                        hook.HookName, check.Passed ? "PASSED" : "FAILED", check.ExecutionTimeMs);
                }
                catch (Exception ex)
                {
                    Log.Warning(ex, "[CIPS] Verification hook {Hook} threw exception", hook.HookName);
                    report.AddCheck(new VerificationCheck
                    {
                        CheckName = hook.HookName,
                        Passed = false,
                        Message = $"Verification error: {ex.Message}"
                    });
                }
            }

            return report;
        }

        /// <summary>
        /// Get list of registered hooks
        /// </summary>
        public List<string> GetRegisteredHooks()
        {
            return _hooks.Select(h => h.HookName).ToList();
        }
    }

    /// <summary>
    /// Verifies that the execution result indicates success
    /// </summary>
    public class ResultSuccessVerifier : IVerificationHook
    {
        public string HookName => "ResultSuccess";

        public VerificationCheck Verify(ConfidenceEnvelope envelope, JObject result)
        {
            var success = result["success"]?.Value<bool>() ?? false;

            if (success)
            {
                return VerificationCheck.Pass(HookName, "Operation returned success=true");
            }

            var error = result["error"]?.ToString() ?? "Unknown error";
            return VerificationCheck.Fail(HookName, "success=true", "success=false", $"Operation failed: {error}");
        }
    }

    /// <summary>
    /// Verifies that an element was actually created (has a valid ID)
    /// </summary>
    public class ElementExistsVerifier : IVerificationHook
    {
        public string HookName => "ElementExists";

        public VerificationCheck Verify(ConfidenceEnvelope envelope, JObject result)
        {
            // Check various ways the element ID might be returned
            var elementId = result["elementId"]?.Value<int>()
                ?? result["element"]?["id"]?.Value<int>()
                ?? result["id"]?.Value<int>();

            if (elementId.HasValue && elementId.Value > 0)
            {
                return VerificationCheck.Pass(HookName, $"Element created with ID {elementId.Value}");
            }

            // Check for array of elements
            var elements = result["elements"] as JArray;
            if (elements != null && elements.Count > 0)
            {
                return VerificationCheck.Pass(HookName, $"{elements.Count} elements created");
            }

            // Some operations don't create elements (queries, deletions, etc.)
            var methodName = envelope.MethodName?.ToLower() ?? "";
            if (methodName.Contains("get") || methodName.Contains("list") ||
                methodName.Contains("delete") || methodName.Contains("query"))
            {
                return VerificationCheck.Pass(HookName, "Operation type does not create elements");
            }

            return VerificationCheck.Fail(HookName,
                "Valid element ID",
                "No element ID found",
                "Could not verify element creation - no element ID in result");
        }
    }

    /// <summary>
    /// Verifies wall placement matches intended parameters
    /// </summary>
    public class WallPlacementVerifier : IVerificationHook
    {
        private readonly UIApplication _uiApp;
        private const double PositionTolerance = 0.5; // feet

        public string HookName => "WallPlacement";

        public WallPlacementVerifier(UIApplication uiApp)
        {
            _uiApp = uiApp;
        }

        public VerificationCheck Verify(ConfidenceEnvelope envelope, JObject result)
        {
            if (!envelope.MethodName.ToLower().Contains("wall"))
            {
                return VerificationCheck.Pass(HookName, "Not a wall operation");
            }

            var elementId = result["elementId"]?.Value<int>();
            if (!elementId.HasValue)
            {
                return VerificationCheck.Fail(HookName, "Wall element", "null", "No wall element ID in result");
            }

            try
            {
                var doc = _uiApp.ActiveUIDocument?.Document;
                if (doc == null)
                {
                    return VerificationCheck.Fail(HookName, "Active document", "null", "No active document");
                }

                var wall = doc.GetElement(new ElementId(elementId.Value)) as Wall;
                if (wall == null)
                {
                    return VerificationCheck.Fail(HookName, "Wall element", "null", $"Element {elementId.Value} is not a wall");
                }

                // Get intended endpoints from parameters
                var startPoint = envelope.Parameters["startPoint"] as JObject;
                var endPoint = envelope.Parameters["endPoint"] as JObject;

                if (startPoint == null || endPoint == null)
                {
                    return VerificationCheck.Pass(HookName, "No position parameters to verify");
                }

                // Get actual wall location
                var locationCurve = wall.Location as LocationCurve;
                if (locationCurve == null)
                {
                    return VerificationCheck.Fail(HookName, "Wall curve", "null", "Wall has no location curve");
                }

                var line = locationCurve.Curve as Line;
                if (line == null)
                {
                    return VerificationCheck.Pass(HookName, "Non-linear wall - position verification skipped");
                }

                var actualStart = line.GetEndPoint(0);
                var actualEnd = line.GetEndPoint(1);

                // Calculate deviations
                double intendedX1 = startPoint["x"]?.Value<double>() ?? 0;
                double intendedY1 = startPoint["y"]?.Value<double>() ?? 0;
                double intendedX2 = endPoint["x"]?.Value<double>() ?? 0;
                double intendedY2 = endPoint["y"]?.Value<double>() ?? 0;

                double startDeviation = Math.Sqrt(
                    Math.Pow(actualStart.X - intendedX1, 2) +
                    Math.Pow(actualStart.Y - intendedY1, 2));

                double endDeviation = Math.Sqrt(
                    Math.Pow(actualEnd.X - intendedX2, 2) +
                    Math.Pow(actualEnd.Y - intendedY2, 2));

                double maxDeviation = Math.Max(startDeviation, endDeviation);

                return VerificationCheck.WithTolerance(
                    HookName,
                    0, // Expected deviation
                    maxDeviation,
                    PositionTolerance);
            }
            catch (Exception ex)
            {
                return VerificationCheck.Fail(HookName, "Verification", $"Error: {ex.Message}", $"Verification failed: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Verifies that doors/windows are properly hosted in walls
    /// </summary>
    public class HostedElementVerifier : IVerificationHook
    {
        private readonly UIApplication _uiApp;

        public string HookName => "HostedElement";

        public HostedElementVerifier(UIApplication uiApp)
        {
            _uiApp = uiApp;
        }

        public VerificationCheck Verify(ConfidenceEnvelope envelope, JObject result)
        {
            var methodLower = envelope.MethodName?.ToLower() ?? "";
            if (!methodLower.Contains("door") && !methodLower.Contains("window"))
            {
                return VerificationCheck.Pass(HookName, "Not a hosted element operation");
            }

            var elementId = result["elementId"]?.Value<int>();
            if (!elementId.HasValue)
            {
                return VerificationCheck.Fail(HookName, "Element ID", "null", "No element ID in result");
            }

            try
            {
                var doc = _uiApp.ActiveUIDocument?.Document;
                if (doc == null)
                {
                    return VerificationCheck.Fail(HookName, "Active document", "null", "No active document");
                }

                var element = doc.GetElement(new ElementId(elementId.Value)) as FamilyInstance;
                if (element == null)
                {
                    return VerificationCheck.Fail(HookName, "FamilyInstance", "null", $"Element {elementId.Value} is not a family instance");
                }

                var host = element.Host;
                if (host == null)
                {
                    return VerificationCheck.Fail(HookName, "Host wall", "null", "Element has no host wall");
                }

                if (!(host is Wall))
                {
                    return VerificationCheck.Fail(HookName, "Wall host", host.GetType().Name, "Element is not hosted in a wall");
                }

                return VerificationCheck.Pass(HookName, $"Element properly hosted in wall {host.Id.Value}");
            }
            catch (Exception ex)
            {
                return VerificationCheck.Fail(HookName, "Verification", $"Error: {ex.Message}", $"Verification failed: {ex.Message}");
            }
        }
    }
}
