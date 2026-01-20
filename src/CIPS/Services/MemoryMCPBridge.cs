using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Bridge to the claude-memory MCP server for cross-session persistence.
    /// Stores corrections, learned patterns, and retrieves historical accuracy data.
    /// Phase 3 of Predictive Intelligence Enhancement.
    /// </summary>
    public class MemoryMCPBridge
    {
        private const string PipeName = "claude-memory-pipe";
        private const int TimeoutMs = 5000;
        private const string ProjectName = "RevitMCPBridge2026";

        // Cache for historical accuracy (avoid repeated lookups)
        private readonly ConcurrentDictionary<string, MethodAccuracy> _accuracyCache =
            new ConcurrentDictionary<string, MethodAccuracy>();

        private DateTime _lastCacheRefresh = DateTime.MinValue;
        private readonly TimeSpan _cacheExpiry = TimeSpan.FromMinutes(15);

        private bool _isAvailable;
        private DateTime _lastAvailabilityCheck = DateTime.MinValue;

        private static MemoryMCPBridge _instance;
        private static readonly object _lock = new object();

        public static MemoryMCPBridge Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new MemoryMCPBridge();
                        }
                    }
                }
                return _instance;
            }
        }

        private MemoryMCPBridge()
        {
            // Try initial connection check
            CheckAvailability();
        }

        /// <summary>
        /// Check if the memory MCP server is available
        /// </summary>
        public bool IsAvailable
        {
            get
            {
                // Re-check every 30 seconds
                if ((DateTime.Now - _lastAvailabilityCheck).TotalSeconds > 30)
                {
                    CheckAvailability();
                }
                return _isAvailable;
            }
        }

        private void CheckAvailability()
        {
            _lastAvailabilityCheck = DateTime.Now;
            try
            {
                // Check if the pipe exists by trying to connect briefly
                using (var client = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut))
                {
                    client.Connect(500);
                    _isAvailable = true;
                    Log.Debug("[MemoryMCPBridge] Memory MCP server is available");
                }
            }
            catch
            {
                _isAvailable = false;
                Log.Debug("[MemoryMCPBridge] Memory MCP server is not available");
            }
        }

        /// <summary>
        /// Store a correction when AI is wrong
        /// </summary>
        public async Task StoreCorrectionAsync(string whatClaudeSaid, string whatWasWrong,
            string correctApproach, string category)
        {
            if (!IsAvailable)
            {
                Log.Debug("[MemoryMCPBridge] Skipping correction storage - MCP not available");
                return;
            }

            try
            {
                var request = new JObject
                {
                    ["method"] = "memory_store_correction",
                    ["params"] = new JObject
                    {
                        ["what_claude_said"] = whatClaudeSaid,
                        ["what_was_wrong"] = whatWasWrong,
                        ["correct_approach"] = correctApproach,
                        ["project"] = ProjectName,
                        ["category"] = category ?? "revit-cips"
                    }
                };

                await SendRequestAsync(request);
                Log.Information("[MemoryMCPBridge] Stored correction for: {Category}", category);
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[MemoryMCPBridge] Failed to store correction: {Error}", ex.Message);
            }
        }

        /// <summary>
        /// Store a learned pattern for cross-session persistence
        /// </summary>
        public async Task StorePatternAsync(LearnedPattern pattern)
        {
            if (!IsAvailable || pattern == null)
                return;

            try
            {
                var content = $"CIPS Learned Pattern: {pattern.Description}\n" +
                              $"Method: {pattern.MethodName}\n" +
                              $"Adjustment: {pattern.ConfidenceAdjustment:+0.00;-0.00}\n" +
                              $"Samples: {pattern.SampleCount}\n" +
                              $"Conditions: {JsonConvert.SerializeObject(pattern.Conditions)}";

                var request = new JObject
                {
                    ["method"] = "memory_store",
                    ["params"] = new JObject
                    {
                        ["content"] = content,
                        ["project"] = ProjectName,
                        ["tags"] = new JArray { "cips", "pattern", pattern.MethodName },
                        ["importance"] = pattern.SampleCount >= 5 ? 7 : 5,
                        ["memory_type"] = "decision",
                        ["summary"] = $"Pattern for {pattern.MethodName}: {pattern.ConfidenceAdjustment:+0.00;-0.00}",
                        ["namespace"] = "project:RevitMCPBridge2026",
                        ["verified"] = pattern.SampleCount >= 5
                    }
                };

                await SendRequestAsync(request);
                Log.Debug("[MemoryMCPBridge] Stored pattern: {Description}", pattern.Description);
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[MemoryMCPBridge] Failed to store pattern: {Error}", ex.Message);
            }
        }

        /// <summary>
        /// Query historical accuracy for confidence calculation
        /// </summary>
        public async Task<MethodAccuracy> GetHistoricalAccuracyAsync(string methodName)
        {
            // Check cache first
            if (_accuracyCache.TryGetValue(methodName, out var cached))
            {
                if ((DateTime.Now - _lastCacheRefresh) < _cacheExpiry)
                    return cached;
            }

            if (!IsAvailable)
                return null;

            try
            {
                var request = new JObject
                {
                    ["method"] = "memory_recall",
                    ["params"] = new JObject
                    {
                        ["query"] = $"CIPS correction {methodName}",
                        ["project"] = ProjectName,
                        ["memory_type"] = "error",
                        ["limit"] = 20
                    }
                };

                var response = await SendRequestAsync(request);
                if (response == null)
                    return null;

                var memories = response["memories"] as JArray;
                if (memories == null || memories.Count == 0)
                {
                    // No correction history = assume good accuracy
                    var defaultAccuracy = new MethodAccuracy
                    {
                        MethodName = methodName,
                        TotalCalls = 0,
                        CorrectCalls = 0,
                        AccuracyRate = 0.8, // Default assumption
                        LastUpdated = DateTime.UtcNow
                    };
                    _accuracyCache[methodName] = defaultAccuracy;
                    return defaultAccuracy;
                }

                // Count corrections as errors
                var correctionCount = memories.Count;
                var assumedCalls = Math.Max(correctionCount * 3, 10); // Assume 3:1 success:error ratio minimum

                var accuracy = new MethodAccuracy
                {
                    MethodName = methodName,
                    TotalCalls = assumedCalls,
                    CorrectCalls = assumedCalls - correctionCount,
                    AccuracyRate = 1.0 - ((double)correctionCount / assumedCalls),
                    LastUpdated = DateTime.UtcNow
                };

                _accuracyCache[methodName] = accuracy;
                _lastCacheRefresh = DateTime.Now;

                return accuracy;
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[MemoryMCPBridge] Failed to get historical accuracy: {Error}", ex.Message);
                return null;
            }
        }

        /// <summary>
        /// Get historical accuracy synchronously (for use in confidence calculation)
        /// </summary>
        public MethodAccuracy GetHistoricalAccuracy(string methodName)
        {
            // Check cache first
            if (_accuracyCache.TryGetValue(methodName, out var cached))
            {
                if ((DateTime.Now - _lastCacheRefresh) < _cacheExpiry)
                    return cached;
            }

            // Run async method synchronously (not ideal but needed for integration)
            try
            {
                return GetHistoricalAccuracyAsync(methodName).GetAwaiter().GetResult();
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// Summarize a CIPS session at end
        /// </summary>
        public async Task SummarizeSessionAsync(SessionOutcome outcome)
        {
            if (!IsAvailable || outcome == null)
                return;

            try
            {
                var request = new JObject
                {
                    ["method"] = "memory_summarize_session",
                    ["params"] = new JObject
                    {
                        ["project"] = ProjectName,
                        ["summary"] = outcome.Summary,
                        ["key_outcomes"] = new JArray
                        {
                            $"Operations: {outcome.TotalOperations} ({outcome.SuccessfulOperations} successful)",
                            $"Patterns learned: {outcome.PatternsLearned}",
                            $"Rules added: {outcome.RulesAdded}"
                        },
                        ["decisions_made"] = outcome.ThresholdSuggestions.Count > 0
                            ? new JArray(outcome.ThresholdSuggestions.ConvertAll(t =>
                                $"Consider adjusting {t.MethodName} threshold: {t.CurrentThreshold:F2} -> {t.SuggestedThreshold:F2}"))
                            : new JArray(),
                        ["next_steps"] = new JArray
                        {
                            "Review any flagged corrections",
                            "Test methods with low accuracy scores"
                        }
                    }
                };

                await SendRequestAsync(request);
                Log.Information("[MemoryMCPBridge] Session summary stored");
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[MemoryMCPBridge] Failed to summarize session: {Error}", ex.Message);
            }
        }

        /// <summary>
        /// Get recent corrections for a method to inform confidence
        /// </summary>
        public async Task<List<CorrectionSummary>> GetRecentCorrectionsAsync(string methodName, int limit = 5)
        {
            if (!IsAvailable)
                return new List<CorrectionSummary>();

            try
            {
                var request = new JObject
                {
                    ["method"] = "memory_get_corrections",
                    ["params"] = new JObject
                    {
                        ["project"] = ProjectName,
                        ["category"] = "revit-cips",
                        ["limit"] = limit
                    }
                };

                var response = await SendRequestAsync(request);
                if (response == null)
                    return new List<CorrectionSummary>();

                var corrections = new List<CorrectionSummary>();
                var memories = response["corrections"] as JArray;
                if (memories != null)
                {
                    foreach (var memory in memories)
                    {
                        corrections.Add(new CorrectionSummary
                        {
                            WhatWasWrong = memory["what_was_wrong"]?.ToString(),
                            CorrectApproach = memory["correct_approach"]?.ToString(),
                            CreatedAt = memory["created_at"]?.ToObject<DateTime?>() ?? DateTime.MinValue
                        });
                    }
                }

                return corrections;
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "[MemoryMCPBridge] Failed to get corrections: {Error}", ex.Message);
                return new List<CorrectionSummary>();
            }
        }

        /// <summary>
        /// Send a request to the memory MCP server via named pipe
        /// </summary>
        private async Task<JObject> SendRequestAsync(JObject request)
        {
            try
            {
                using (var client = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut))
                using (var cts = new CancellationTokenSource(TimeoutMs))
                {
                    await client.ConnectAsync(TimeoutMs, cts.Token);

                    var requestJson = JsonConvert.SerializeObject(request);
                    var requestBytes = Encoding.UTF8.GetBytes(requestJson);

                    // Write request
                    await client.WriteAsync(requestBytes, 0, requestBytes.Length, cts.Token);
                    await client.FlushAsync(cts.Token);

                    // Read response
                    var buffer = new byte[65536];
                    var bytesRead = await client.ReadAsync(buffer, 0, buffer.Length, cts.Token);

                    if (bytesRead > 0)
                    {
                        var responseJson = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                        return JObject.Parse(responseJson);
                    }
                }
            }
            catch (TimeoutException)
            {
                Log.Debug("[MemoryMCPBridge] Request timed out");
            }
            catch (Exception ex)
            {
                Log.Debug("[MemoryMCPBridge] Request failed: {Error}", ex.Message);
            }

            return null;
        }

        /// <summary>
        /// Clear the accuracy cache (e.g., after storing new corrections)
        /// </summary>
        public void ClearCache()
        {
            _accuracyCache.Clear();
            _lastCacheRefresh = DateTime.MinValue;
        }

        /// <summary>
        /// Preload accuracy data for common methods
        /// </summary>
        public async Task PreloadCommonMethodsAsync()
        {
            var commonMethods = new[]
            {
                "createWall", "placeDoor", "placeWindow", "createRoom",
                "placeViewOnSheet", "createSheet", "setParameter"
            };

            foreach (var method in commonMethods)
            {
                await GetHistoricalAccuracyAsync(method);
            }
        }
    }

    /// <summary>
    /// Historical accuracy data for a method
    /// </summary>
    public class MethodAccuracy
    {
        public string MethodName { get; set; }
        public int TotalCalls { get; set; }
        public int CorrectCalls { get; set; }
        public double AccuracyRate { get; set; }
        public DateTime LastUpdated { get; set; }
    }

    /// <summary>
    /// Summary of a correction from memory
    /// </summary>
    public class CorrectionSummary
    {
        public string WhatWasWrong { get; set; }
        public string CorrectApproach { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}
