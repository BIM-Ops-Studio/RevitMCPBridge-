using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// Result of a single verification check after element placement.
    /// This is part of Enhancement #6: Verification Loops
    /// </summary>
    public class VerificationCheck
    {
        [JsonProperty("checkName")]
        public string CheckName { get; set; }

        [JsonProperty("passed")]
        public bool Passed { get; set; }

        [JsonProperty("expected")]
        public string Expected { get; set; }

        [JsonProperty("actual")]
        public string Actual { get; set; }

        [JsonProperty("tolerance")]
        public double? Tolerance { get; set; }

        [JsonProperty("deviation")]
        public double? Deviation { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }

        [JsonProperty("executedAt")]
        public DateTime ExecutedAt { get; set; } = DateTime.UtcNow;

        [JsonProperty("executionTimeMs")]
        public double ExecutionTimeMs { get; set; }

        /// <summary>
        /// Create a passing check
        /// </summary>
        public static VerificationCheck Pass(string checkName, string message = null)
        {
            return new VerificationCheck
            {
                CheckName = checkName,
                Passed = true,
                Message = message ?? "Check passed"
            };
        }

        /// <summary>
        /// Create a failing check
        /// </summary>
        public static VerificationCheck Fail(string checkName, string expected, string actual, string message)
        {
            return new VerificationCheck
            {
                CheckName = checkName,
                Passed = false,
                Expected = expected,
                Actual = actual,
                Message = message
            };
        }

        /// <summary>
        /// Create a check with tolerance comparison
        /// </summary>
        public static VerificationCheck WithTolerance(string checkName, double expected, double actual, double tolerance)
        {
            double deviation = Math.Abs(expected - actual);
            bool passed = deviation <= tolerance;

            return new VerificationCheck
            {
                CheckName = checkName,
                Passed = passed,
                Expected = expected.ToString("F3"),
                Actual = actual.ToString("F3"),
                Tolerance = tolerance,
                Deviation = deviation,
                Message = passed
                    ? $"Within tolerance (deviation: {deviation:F3})"
                    : $"Outside tolerance (deviation: {deviation:F3}, max: {tolerance:F3})"
            };
        }
    }

    /// <summary>
    /// Complete verification report for an operation
    /// </summary>
    public class VerificationReport
    {
        [JsonProperty("operationId")]
        public string OperationId { get; set; }

        [JsonProperty("checks")]
        public List<VerificationCheck> Checks { get; set; } = new List<VerificationCheck>();

        [JsonProperty("passed")]
        public bool AllPassed => Checks.All(c => c.Passed);

        [JsonProperty("passedCount")]
        public int PassedCount => Checks.Count(c => c.Passed);

        [JsonProperty("failedCount")]
        public int FailedCount => Checks.Count(c => !c.Passed);

        [JsonProperty("totalChecks")]
        public int TotalChecks => Checks.Count;

        [JsonProperty("failures")]
        public List<string> Failures => Checks.Where(c => !c.Passed).Select(c => c.Message).ToList();

        [JsonProperty("generatedAt")]
        public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

        [JsonProperty("totalExecutionTimeMs")]
        public double TotalExecutionTimeMs => Checks.Sum(c => c.ExecutionTimeMs);

        /// <summary>
        /// Get summary of the verification
        /// </summary>
        public string GetSummary()
        {
            if (Checks.Count == 0)
                return "No verifications performed";

            if (AllPassed)
                return $"All {TotalChecks} verification checks passed";

            return $"FAILED: {FailedCount} of {TotalChecks} checks failed - {string.Join("; ", Failures)}";
        }

        /// <summary>
        /// Add a check to the report
        /// </summary>
        public void AddCheck(VerificationCheck check)
        {
            Checks.Add(check);
        }

        /// <summary>
        /// Create an empty passing report
        /// </summary>
        public static VerificationReport Empty(string operationId)
        {
            return new VerificationReport
            {
                OperationId = operationId,
                Checks = new List<VerificationCheck>()
            };
        }
    }

    /// <summary>
    /// Auto-correction suggestion when verification fails
    /// </summary>
    public class AutoCorrectionSuggestion
    {
        [JsonProperty("suggestionId")]
        public string SuggestionId { get; set; }

        [JsonProperty("checkName")]
        public string CheckName { get; set; }

        [JsonProperty("description")]
        public string Description { get; set; }

        [JsonProperty("correctionType")]
        public CorrectionType Type { get; set; }

        [JsonProperty("parameters")]
        public Dictionary<string, object> Parameters { get; set; } = new Dictionary<string, object>();

        [JsonProperty("confidence")]
        public double Confidence { get; set; }

        [JsonProperty("isRecommended")]
        public bool IsRecommended { get; set; }
    }

    /// <summary>
    /// Types of auto-corrections available
    /// </summary>
    public enum CorrectionType
    {
        /// <summary>Adjust the position of an element</summary>
        AdjustPosition,

        /// <summary>Extend an element to meet another</summary>
        Extend,

        /// <summary>Shorten an element</summary>
        Shorten,

        /// <summary>Change element type</summary>
        ChangeType,

        /// <summary>Re-host to different element</summary>
        Rehost,

        /// <summary>Join with another element</summary>
        Join,

        /// <summary>Delete and recreate</summary>
        Recreate,

        /// <summary>Manual intervention required</summary>
        ManualRequired
    }
}
