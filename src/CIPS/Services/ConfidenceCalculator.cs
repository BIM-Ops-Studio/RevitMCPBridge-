using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Calculates confidence scores for operations.
    /// Uses existing infrastructure (PreFlightCheck, CorrectionLearner) without modifying them.
    /// Enhanced with Architectural Validation and Explainable Reasoning (Enhancements #1, #3)
    /// Phase 5 Enhancement: Memory MCP integration for cross-session historical accuracy
    /// </summary>
    public class ConfidenceCalculator
    {
        private readonly UIApplication _uiApp;
        private readonly FeedbackLearner _feedbackLearner;
        private readonly ArchitecturalValidator _architecturalValidator;

        // Phase 5: Cache for memory-based accuracy (avoid repeated lookups per session)
        private readonly Dictionary<string, double> _memoryAccuracyCache = new Dictionary<string, double>();
        private DateTime _memoryCacheTime = DateTime.MinValue;
        private readonly TimeSpan _memoryCacheExpiry = TimeSpan.FromMinutes(15);

        /// <summary>
        /// Methods that create or modify elements (higher scrutiny)
        /// </summary>
        private static readonly HashSet<string> _modifyingMethods = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "createWall", "createWallByPoints", "createWallsFromPolyline", "batchCreateWalls",
            "createRoom", "createSheet", "placeDoor", "placeWindow", "placeFamilyInstance",
            "placeViewOnSheet", "deleteElement", "deleteElements", "modifyWall", "setParameter"
        };

        /// <summary>
        /// Methods that delete elements (highest scrutiny)
        /// </summary>
        private static readonly HashSet<string> _deletingMethods = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "deleteElement", "deleteElements", "deleteWall", "deleteRoom", "deleteSheet", "deleteView"
        };

        /// <summary>
        /// Required parameters for common methods
        /// </summary>
        private static readonly Dictionary<string, string[]> _requiredParameters = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase)
        {
            { "createWallByPoints", new[] { "startPoint", "endPoint", "levelId" } },
            { "placeDoor", new[] { "wallId", "location" } },
            { "placeWindow", new[] { "wallId", "location" } },
            { "createRoom", new[] { "levelId", "location" } },
            { "createSheet", new[] { "titleBlockId", "sheetNumber" } },
            { "placeViewOnSheet", new[] { "sheetId", "viewId", "location" } },
            { "deleteElement", new[] { "elementId" } },
            { "setParameter", new[] { "elementId", "parameterName", "value" } }
        };

        public ConfidenceCalculator(UIApplication uiApp, FeedbackLearner feedbackLearner = null, ArchitecturalValidator architecturalValidator = null)
        {
            _uiApp = uiApp;
            _feedbackLearner = feedbackLearner;
            _architecturalValidator = architecturalValidator ?? new ArchitecturalValidator();
        }

        /// <summary>
        /// Calculate confidence for an operation.
        /// Enhanced with reasoning chain for explainability (Enhancement #1)
        /// </summary>
        public ConfidenceEnvelope Calculate(string methodName, JObject parameters)
        {
            var envelope = ConfidenceEnvelope.Create(methodName, parameters);
            var factors = new List<ConfidenceFactor>();

            // Initialize reasoning chain for explainability
            var reasoning = new ReasoningChain();

            try
            {
                // Factor 1: Parameter Completeness (0.18)
                var paramFactor = CalculateParameterCompleteness(methodName, parameters);
                factors.Add(paramFactor);
                reasoning.AddStep(
                    paramFactor.FactorName,
                    paramFactor.Score,
                    GetObservationForFactor(paramFactor),
                    paramFactor.Reason);

                // Factor 2: Type/Element Validation (0.14)
                var typeFactor = CalculateTypeValidation(methodName, parameters);
                factors.Add(typeFactor);
                reasoning.AddStep(
                    typeFactor.FactorName,
                    typeFactor.Score,
                    GetObservationForFactor(typeFactor),
                    typeFactor.Reason);

                // Factor 3: Correction History (0.22)
                var correctionFactor = CalculateCorrectionHistory(methodName, parameters);
                factors.Add(correctionFactor);
                reasoning.AddStep(
                    correctionFactor.FactorName,
                    correctionFactor.Score,
                    GetObservationForFactor(correctionFactor),
                    correctionFactor.Reason);

                // Factor 4: PreFlight Check (0.22)
                var preflightFactor = CalculatePreFlightCheck(methodName, parameters);
                factors.Add(preflightFactor);
                reasoning.AddStep(
                    preflightFactor.FactorName,
                    preflightFactor.Score,
                    GetObservationForFactor(preflightFactor),
                    preflightFactor.Reason);

                // Factor 5: Pattern Match from Feedback (0.14)
                var patternFactor = CalculatePatternMatch(methodName, parameters);
                factors.Add(patternFactor);
                reasoning.AddStep(
                    patternFactor.FactorName,
                    patternFactor.Score,
                    GetObservationForFactor(patternFactor),
                    patternFactor.Reason);

                // Factor 6: Architectural Validation (0.10) - Enhancement #3
                var archFactor = _architecturalValidator.Validate(methodName, parameters);
                factors.Add(archFactor);
                reasoning.AddStep(
                    archFactor.FactorName,
                    archFactor.Score,
                    GetObservationForFactor(archFactor),
                    archFactor.Reason);

                // Calculate overall confidence
                envelope.Factors = factors;
                envelope.OverallConfidence = factors.Sum(f => f.WeightedScore);

                // Finalize reasoning chain
                reasoning.Finalize();
                envelope.Reasoning = reasoning;

                // Apply any learned adjustments
                if (_feedbackLearner != null)
                {
                    var adjustment = _feedbackLearner.GetConfidenceAdjustment(methodName, parameters);
                    envelope.OverallConfidence = Math.Max(0, Math.Min(1, envelope.OverallConfidence + adjustment));

                    if (Math.Abs(adjustment) > 0.01)
                    {
                        reasoning.AddStep(
                            "SessionLearning",
                            1.0,
                            $"Applied learned adjustment of {adjustment:+0.00;-0.00;0}",
                            "Based on session patterns and corrections");
                    }
                }

                // Find alternatives if confidence is not high
                if (envelope.OverallConfidence < CIPSConfiguration.Instance.Thresholds.High)
                {
                    envelope.Alternatives = FindAlternatives(methodName, parameters);
                }

                Log.Debug("[CIPS] Calculated confidence {Confidence:F2} for {Method} with {StepCount} reasoning steps",
                    envelope.OverallConfidence, methodName, reasoning.Steps.Count);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[CIPS] Error calculating confidence for {Method}", methodName);
                envelope.OverallConfidence = 0.5; // Default to medium if calculation fails
                envelope.Factors.Add(ConfidenceFactor.Partial(
                    "CalculationError", 1.0, 0.5, $"Error during calculation: {ex.Message}"));

                reasoning.AddStep("Error", 0.5, "Calculation error occurred", ex.Message);
                envelope.Reasoning = reasoning;
            }

            return envelope;
        }

        /// <summary>
        /// Generate an observation string for a confidence factor
        /// </summary>
        private string GetObservationForFactor(ConfidenceFactor factor)
        {
            if (factor.Score >= 0.9)
                return $"{factor.FactorName} indicates high confidence";
            if (factor.Score >= 0.7)
                return $"{factor.FactorName} shows acceptable confidence";
            if (factor.Score >= 0.5)
                return $"{factor.FactorName} indicates moderate uncertainty";
            return $"{factor.FactorName} shows significant concerns";
        }

        /// <summary>
        /// Calculate parameter completeness factor
        /// </summary>
        private ConfidenceFactor CalculateParameterCompleteness(string methodName, JObject parameters)
        {
            const double weight = ConfidenceWeights.ParameterCompleteness;

            if (!_requiredParameters.TryGetValue(methodName, out var required))
            {
                // Unknown method - assume parameters are complete
                return ConfidenceFactor.Pass(ConfidenceFactorNames.ParameterCompleteness, weight,
                    "No required parameters defined for this method");
            }

            var missing = new List<string>();
            foreach (var param in required)
            {
                if (parameters[param] == null)
                    missing.Add(param);
            }

            if (missing.Count == 0)
            {
                return ConfidenceFactor.Pass(ConfidenceFactorNames.ParameterCompleteness, weight,
                    "All required parameters present");
            }

            var score = 1.0 - ((double)missing.Count / required.Length);
            return ConfidenceFactor.Partial(ConfidenceFactorNames.ParameterCompleteness, weight, score,
                $"Missing parameters: {string.Join(", ", missing)}");
        }

        /// <summary>
        /// Calculate type/element validation factor
        /// </summary>
        private ConfidenceFactor CalculateTypeValidation(string methodName, JObject parameters)
        {
            const double weight = ConfidenceWeights.TypeValidation;

            if (_uiApp?.ActiveUIDocument?.Document == null)
            {
                return ConfidenceFactor.Partial(ConfidenceFactorNames.TypeValidation, weight, 0.5,
                    "No active document to validate against");
            }

            var doc = _uiApp.ActiveUIDocument.Document;
            var issues = new List<string>();
            var checks = 0;
            var passed = 0;

            // Check element IDs exist
            foreach (var idParam in new[] { "elementId", "wallId", "levelId", "viewId", "sheetId", "roomId" })
            {
                var idToken = parameters[idParam];
                if (idToken != null)
                {
                    checks++;
                    var id = idToken.Value<int>();
                    var element = doc.GetElement(new ElementId(id));
                    if (element != null)
                    {
                        passed++;
                    }
                    else
                    {
                        issues.Add($"{idParam}={id} not found");
                    }
                }
            }

            // Check type names exist
            var typeNameParam = parameters["typeName"] ?? parameters["wallTypeName"];
            if (typeNameParam != null)
            {
                checks++;
                // Type validation would require more complex lookup - assume valid for now
                passed++;
            }

            if (checks == 0)
            {
                return ConfidenceFactor.Pass(ConfidenceFactorNames.TypeValidation, weight,
                    "No element IDs to validate");
            }

            var score = (double)passed / checks;
            if (issues.Count == 0)
            {
                return ConfidenceFactor.Pass(ConfidenceFactorNames.TypeValidation, weight,
                    $"All {checks} element references valid");
            }

            return ConfidenceFactor.Partial(ConfidenceFactorNames.TypeValidation, weight, score,
                $"Issues: {string.Join("; ", issues)}");
        }

        /// <summary>
        /// Calculate correction history factor using existing CorrectionLearner
        /// </summary>
        private ConfidenceFactor CalculateCorrectionHistory(string methodName, JObject parameters)
        {
            const double weight = ConfidenceWeights.CorrectionHistory;

            try
            {
                // Try to use existing CorrectionLearner
                var learner = GetCorrectionLearner();
                if (learner == null)
                {
                    return ConfidenceFactor.Pass(ConfidenceFactorNames.CorrectionHistory, weight,
                        "CorrectionLearner not available");
                }

                // Get corrections for this method
                var corrections = learner.GetMethodCorrections(methodName);
                if (corrections == null || corrections.Count == 0)
                {
                    return ConfidenceFactor.Pass(ConfidenceFactorNames.CorrectionHistory, weight,
                        "No correction history for this method");
                }

                // More corrections = lower confidence (this method has been problematic)
                var score = Math.Max(0.3, 1.0 - (corrections.Count * 0.1));
                return ConfidenceFactor.Partial(ConfidenceFactorNames.CorrectionHistory, weight, score,
                    $"{corrections.Count} past corrections recorded for {methodName}");
            }
            catch (Exception ex)
            {
                Log.Debug("[CIPS] Could not access CorrectionLearner: {Error}", ex.Message);
                return ConfidenceFactor.Pass(ConfidenceFactorNames.CorrectionHistory, weight,
                    "CorrectionLearner not accessible");
            }
        }

        /// <summary>
        /// Calculate PreFlight check factor using existing ValidationMethods
        /// </summary>
        private ConfidenceFactor CalculatePreFlightCheck(string methodName, JObject parameters)
        {
            const double weight = ConfidenceWeights.PreFlightCheck;

            try
            {
                // Try to call existing PreFlightCheck
                var checkParams = new JObject
                {
                    ["operation"] = methodName,
                    ["parameters"] = parameters
                };

                var result = ValidationMethods.PreFlightCheck(_uiApp, checkParams);
                var resultObj = JObject.Parse(result);

                var canProceed = resultObj["canProceed"]?.Value<bool>() ?? true;
                var message = resultObj["message"]?.ToString() ?? "Check passed";

                if (canProceed)
                {
                    return ConfidenceFactor.Pass(ConfidenceFactorNames.PreFlightCheck, weight, message);
                }

                // Check severity
                var warnings = resultObj["warnings"] as JArray;
                var errors = resultObj["errors"] as JArray;

                if (errors != null && errors.Count > 0)
                {
                    return ConfidenceFactor.Fail(ConfidenceFactorNames.PreFlightCheck, weight,
                        $"PreFlight errors: {string.Join("; ", errors)}");
                }

                if (warnings != null && warnings.Count > 0)
                {
                    var score = Math.Max(0.5, 1.0 - (warnings.Count * 0.15));
                    return ConfidenceFactor.Partial(ConfidenceFactorNames.PreFlightCheck, weight, score,
                        $"PreFlight warnings: {string.Join("; ", warnings)}");
                }

                return ConfidenceFactor.Partial(ConfidenceFactorNames.PreFlightCheck, weight, 0.7, message);
            }
            catch (Exception ex)
            {
                Log.Debug("[CIPS] PreFlightCheck not available: {Error}", ex.Message);
                return ConfidenceFactor.Partial(ConfidenceFactorNames.PreFlightCheck, weight, 0.8,
                    "PreFlightCheck not available, assuming valid");
            }
        }

        /// <summary>
        /// Calculate pattern match factor from feedback history.
        /// Phase 5 Enhancement: Also queries Memory MCP for cross-session historical accuracy.
        /// </summary>
        private ConfidenceFactor CalculatePatternMatch(string methodName, JObject parameters)
        {
            const double weight = ConfidenceWeights.PatternMatch;

            try
            {
                // 1. Get local accuracy (fast, always available) - from current session/feedback
                double localAccuracy = 0.7; // Default if no data
                int localSamples = 0;

                if (_feedbackLearner != null)
                {
                    var stats = _feedbackLearner.GetMethodStats(methodName);
                    if (stats != null && stats.TotalFeedback >= CIPSConfiguration.Instance.Feedback.MinSamplesToLearn)
                    {
                        localAccuracy = stats.AccuracyRate;
                        localSamples = stats.TotalFeedback;
                    }
                }

                // 2. Get memory accuracy (cached per session) - from cross-session history
                double? memoryAccuracy = GetCachedMemoryAccuracy(methodName);

                // 3. Combine: weight local (recent) higher than memory (historical)
                double finalAccuracy;
                string reason;

                if (memoryAccuracy.HasValue && localSamples >= 3)
                {
                    // Both sources available: blend 70% local, 30% memory
                    finalAccuracy = (localAccuracy * 0.7) + (memoryAccuracy.Value * 0.3);
                    reason = $"Combined accuracy: {finalAccuracy:P0} (local: {localAccuracy:P0} [{localSamples}], memory: {memoryAccuracy.Value:P0})";
                }
                else if (memoryAccuracy.HasValue)
                {
                    // Only memory available: use memory with slight penalty for no local data
                    finalAccuracy = memoryAccuracy.Value * 0.9;
                    reason = $"Memory-based accuracy: {memoryAccuracy.Value:P0} (no recent local data)";
                }
                else if (localSamples >= 3)
                {
                    // Only local available
                    finalAccuracy = localAccuracy;
                    reason = $"Local accuracy: {localAccuracy:P0} ({localSamples} samples)";
                }
                else
                {
                    // Neither available - use default
                    finalAccuracy = 0.7;
                    reason = "Insufficient history for pattern matching";
                }

                return ConfidenceFactor.Partial(ConfidenceFactorNames.PatternMatch, weight, finalAccuracy, reason);
            }
            catch (Exception ex)
            {
                Log.Debug("[CIPS] Pattern match error: {Error}", ex.Message);
                return ConfidenceFactor.Partial(ConfidenceFactorNames.PatternMatch, weight, 0.7,
                    "Pattern matching unavailable");
            }
        }

        /// <summary>
        /// Get memory-based accuracy with caching (Phase 5)
        /// </summary>
        private double? GetCachedMemoryAccuracy(string methodName)
        {
            // Check if cache has expired
            if ((DateTime.Now - _memoryCacheTime) > _memoryCacheExpiry)
            {
                _memoryAccuracyCache.Clear();
                _memoryCacheTime = DateTime.Now;
            }

            // Check cache first
            if (_memoryAccuracyCache.TryGetValue(methodName, out var cached))
            {
                return cached;
            }

            // Query Memory MCP
            try
            {
                var memoryBridge = MemoryMCPBridge.Instance;
                if (!memoryBridge.IsAvailable)
                {
                    Log.Debug("[CIPS] Memory MCP not available for accuracy query");
                    return null;
                }

                var accuracy = memoryBridge.GetHistoricalAccuracy(methodName);
                if (accuracy != null)
                {
                    _memoryAccuracyCache[methodName] = accuracy.AccuracyRate;
                    Log.Debug("[CIPS] Got memory accuracy for {Method}: {Accuracy:P0}",
                        methodName, accuracy.AccuracyRate);
                    return accuracy.AccuracyRate;
                }
            }
            catch (Exception ex)
            {
                Log.Debug("[CIPS] Failed to query memory accuracy: {Error}", ex.Message);
            }

            return null;
        }

        /// <summary>
        /// Clear the memory accuracy cache (call after storing new corrections)
        /// </summary>
        public void ClearMemoryCache()
        {
            _memoryAccuracyCache.Clear();
            _memoryCacheTime = DateTime.MinValue;
        }

        /// <summary>
        /// Find alternative interpretations or parameter sets
        /// </summary>
        private List<Alternative> FindAlternatives(string methodName, JObject parameters)
        {
            var alternatives = new List<Alternative>();

            try
            {
                // Try to get alternatives from CorrectionLearner
                var learner = GetCorrectionLearner();
                if (learner != null)
                {
                    var corrections = learner.GetRelevantCorrections(methodName, parameters.ToString());
                    foreach (var correction in corrections.Take(3))
                    {
                        alternatives.Add(new Alternative
                        {
                            Description = correction.Description,
                            Confidence = 0.6,
                            Source = "correction_history"
                        });
                    }
                }

                // Try to get alternatives from feedback patterns
                if (_feedbackLearner != null)
                {
                    var patterns = _feedbackLearner.GetMatchingPatterns(methodName, parameters);
                    foreach (var pattern in patterns.Take(3))
                    {
                        alternatives.Add(new Alternative
                        {
                            Description = pattern.Description,
                            Confidence = 0.5 + pattern.ConfidenceAdjustment,
                            Source = "pattern_match"
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Debug("[CIPS] Error finding alternatives: {Error}", ex.Message);
            }

            return alternatives;
        }

        /// <summary>
        /// Get CorrectionLearner instance via reflection (to avoid modifying existing code)
        /// </summary>
        private dynamic GetCorrectionLearner()
        {
            try
            {
                var mcpServerType = typeof(MCPServer);
                var learnerField = mcpServerType.GetField("_correctionLearner",
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

                if (learnerField != null)
                {
                    return learnerField.GetValue(null);
                }

                // Try property
                var learnerProp = mcpServerType.GetProperty("CorrectionLearnerInstance",
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

                if (learnerProp != null)
                {
                    return learnerProp.GetValue(null);
                }
            }
            catch (Exception ex)
            {
                Log.Debug("[CIPS] Could not get CorrectionLearner: {Error}", ex.Message);
            }

            return null;
        }
    }
}
