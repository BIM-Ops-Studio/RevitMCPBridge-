using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Coordinates multi-pass processing of operations.
    /// Pass 1: Execute high-confidence, hold low-confidence
    /// Pass 2: Re-evaluate with context from Pass 1
    /// Pass 3: Final attempt, then escalate to human review
    /// Enhanced with Dependency Graph (Enhancement #4) and Verification Loops (Enhancement #6)
    /// </summary>
    public class PassCoordinator
    {
        private readonly UIApplication _uiApp;
        private readonly ConfidenceCalculator _calculator;
        private readonly ReviewQueueManager _reviewQueue;
        private readonly FeedbackLearner _feedbackLearner;
        private readonly DependencyGraphService _dependencyGraph;
        private readonly PostExecutionVerifier _verifier;

        public PassCoordinator(UIApplication uiApp, ConfidenceCalculator calculator,
            ReviewQueueManager reviewQueue, FeedbackLearner feedbackLearner,
            DependencyGraphService dependencyGraph = null, PostExecutionVerifier verifier = null)
        {
            _uiApp = uiApp;
            _calculator = calculator;
            _reviewQueue = reviewQueue;
            _feedbackLearner = feedbackLearner;
            _dependencyGraph = dependencyGraph ?? new DependencyGraphService();
            _verifier = verifier ?? new PostExecutionVerifier(uiApp);
        }

        /// <summary>
        /// Process a single operation through the confidence system
        /// </summary>
        public ConfidenceEnvelope ProcessSingle(string methodName, JObject parameters, bool autoExecuteHigh = true)
        {
            // Calculate confidence
            var envelope = _calculator.Calculate(methodName, parameters);

            if (!autoExecuteHigh)
            {
                // Just return the envelope without executing
                return envelope;
            }

            // Check against threshold
            var threshold = CIPSConfiguration.Instance.GetPassThreshold(1, methodName);

            if (envelope.OverallConfidence >= threshold)
            {
                // High confidence - execute immediately
                envelope = ExecuteOperation(envelope);
            }
            else
            {
                // Low confidence - queue for review (single operations don't multi-pass)
                _reviewQueue.Enqueue(envelope);
            }

            return envelope;
        }

        /// <summary>
        /// Process a batch of operations through multi-pass workflow.
        /// Enhanced with dependency ordering (Enhancement #4)
        /// </summary>
        public WorkflowState ProcessBatch(List<(string method, JObject parameters)> operations,
            string description = null, bool autoExecute = true)
        {
            var workflow = WorkflowState.Create(description);
            var config = CIPSConfiguration.Instance;

            Log.Information("[CIPS] Starting batch processing. Operations: {Count}", operations.Count);

            // Create envelopes for all operations
            foreach (var (method, parameters) in operations)
            {
                var envelope = _calculator.Calculate(method, parameters);
                workflow.AddOperation(envelope);

                // Register dependencies in the graph (Enhancement #4)
                _dependencyGraph.RegisterEnvelopeDependencies(envelope);
            }

            // Determine execution order based on dependencies
            var executionOrder = _dependencyGraph.GetExecutionOrder(workflow.Operations.Values.ToList());
            Log.Debug("[CIPS] Dependency-ordered execution: {Order}", string.Join(" -> ", executionOrder.Take(5)));

            if (!autoExecute)
            {
                // Return workflow without executing
                return workflow;
            }

            // Execute passes
            for (int pass = 1; pass <= config.MultiPass.MaxPasses; pass++)
            {
                var passResult = ExecutePass(workflow, pass);
                workflow.Passes.Add(passResult);

                // Check if all operations are processed
                var pending = workflow.Operations.Values.Count(o =>
                    o.Status != ProcessingStatus.Executed &&
                    o.Status != ProcessingStatus.Verified &&
                    o.Status != ProcessingStatus.Failed &&
                    o.Status != ProcessingStatus.InReview);

                if (pending == 0)
                {
                    Log.Information("[CIPS] All operations processed after pass {Pass}", pass);
                    break;
                }
            }

            // Queue remaining operations for human review
            foreach (var envelope in workflow.Operations.Values.Where(o =>
                o.Status != ProcessingStatus.Executed &&
                o.Status != ProcessingStatus.Verified &&
                o.Status != ProcessingStatus.Failed &&
                o.Status != ProcessingStatus.InReview))
            {
                _reviewQueue.Enqueue(envelope);
            }

            workflow.Status = DetermineWorkflowStatus(workflow);
            workflow.LastUpdated = DateTime.UtcNow;

            Log.Information("[CIPS] Batch processing complete. Executed: {Executed}, Review: {Review}, Failed: {Failed}",
                workflow.Operations.Values.Count(o => o.Status == ProcessingStatus.Executed || o.Status == ProcessingStatus.Verified),
                workflow.Operations.Values.Count(o => o.Status == ProcessingStatus.InReview),
                workflow.Operations.Values.Count(o => o.Status == ProcessingStatus.Failed));

            return workflow;
        }

        /// <summary>
        /// Execute a specific pass
        /// </summary>
        public ProcessingPass ExecutePass(WorkflowState workflow, int passNumber)
        {
            var sw = Stopwatch.StartNew();
            var config = CIPSConfiguration.Instance;
            var pass = new ProcessingPass
            {
                PassNumber = passNumber,
                Threshold = config.GetPassThreshold(passNumber),
                ContextBoost = (passNumber - 1) * config.MultiPass.ContextBoostPerPass,
                Status = PassStatus.InProgress,
                StartedAt = DateTime.UtcNow
            };

            workflow.CurrentPass = passNumber;

            Log.Information("[CIPS] Executing pass {Pass}. Threshold: {Threshold:F2}, ContextBoost: {Boost:F2}",
                passNumber, pass.Threshold, pass.ContextBoost);

            // Get operations to process this pass
            var toProcess = workflow.Operations.Values.Where(o =>
                o.CurrentPass == passNumber &&
                (o.Status == ProcessingStatus.Pending ||
                 o.Status == ProcessingStatus.Pass1_Queued ||
                 o.Status == ProcessingStatus.Pass2_Queued ||
                 o.Status == ProcessingStatus.Pass3_Queued)).ToList();

            pass.QueuedOperations = toProcess.Select(o => o.OperationId).ToList();

            foreach (var envelope in toProcess)
            {
                // Apply context boost
                if (passNumber > 1)
                {
                    envelope.OverallConfidence = Math.Min(1.0, envelope.OverallConfidence + pass.ContextBoost);

                    // Re-evaluate with context from executed operations
                    AddContextFromExecuted(envelope, workflow);
                }

                // Check threshold
                var threshold = config.GetPassThreshold(passNumber, envelope.MethodName);

                if (envelope.OverallConfidence >= threshold)
                {
                    // Execute
                    var result = ExecuteOperation(envelope);
                    if (result.Status == ProcessingStatus.Executed || result.Status == ProcessingStatus.Verified)
                    {
                        pass.ExecutedOperations.Add(envelope.OperationId);
                    }
                    else
                    {
                        pass.HeldOperations.Add(envelope.OperationId);
                    }
                }
                else if (passNumber >= config.MultiPass.MaxPasses)
                {
                    // Final pass - send to review
                    envelope.Status = ProcessingStatus.InReview;
                    pass.ReviewOperations.Add(envelope.OperationId);
                }
                else
                {
                    // Hold for next pass
                    envelope.AdvancePass();
                    pass.HeldOperations.Add(envelope.OperationId);
                }
            }

            sw.Stop();
            pass.Status = PassStatus.Completed;
            pass.CompletedAt = DateTime.UtcNow;
            pass.Summary = new PassSummary
            {
                TotalOperations = toProcess.Count,
                ExecutedCount = pass.ExecutedOperations.Count,
                HeldCount = pass.HeldOperations.Count,
                ReviewCount = pass.ReviewOperations.Count,
                FailedCount = toProcess.Count(o => o.Status == ProcessingStatus.Failed),
                AverageConfidence = toProcess.Count > 0 ? toProcess.Average(o => o.OverallConfidence) : 0,
                ExecutionTimeMs = sw.ElapsedMilliseconds
            };

            Log.Information("[CIPS] Pass {Pass} complete. Executed: {Executed}, Held: {Held}, Review: {Review}",
                passNumber, pass.ExecutedOperations.Count, pass.HeldOperations.Count, pass.ReviewOperations.Count);

            return pass;
        }

        /// <summary>
        /// Execute a single operation via the existing MCP method.
        /// Enhanced with Verification Loops (Enhancement #6)
        /// </summary>
        private ConfidenceEnvelope ExecuteOperation(ConfidenceEnvelope envelope)
        {
            try
            {
                envelope.Status = ProcessingStatus.Executing;

                // Execute via MCPServer's method registry
                var result = MCPServer.ExecuteMethod(_uiApp, envelope.MethodName, envelope.Parameters);
                var resultObj = JObject.Parse(result);

                envelope.Result = resultObj;

                var success = resultObj["success"]?.Value<bool>() ?? false;
                if (success)
                {
                    envelope.MarkExecuted(resultObj);

                    // Run post-execution verification (Enhancement #6)
                    var verification = _verifier.RunVerifications(envelope);
                    envelope.VerificationReport = verification;

                    if (verification.AllPassed)
                    {
                        envelope.Status = ProcessingStatus.Verified;
                        Log.Debug("[CIPS] Operation {Op} verified successfully with {Checks} checks",
                            envelope.OperationId, verification.TotalChecks);
                    }
                    else
                    {
                        envelope.Status = ProcessingStatus.VerificationFailed;
                        Log.Warning("[CIPS] Operation {Op} verification failed: {Failures}",
                            envelope.OperationId, string.Join("; ", verification.Failures));

                        // Queue for review if verification fails
                        _reviewQueue.Enqueue(envelope, $"Verification failed: {string.Join("; ", verification.Failures)}");
                    }
                }
                else
                {
                    envelope.MarkFailed(resultObj["error"]?.ToString() ?? "Unknown error");
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[CIPS] Error executing {Method}", envelope.MethodName);
                envelope.MarkFailed(ex.Message);
            }

            return envelope;
        }

        /// <summary>
        /// Register a custom verification hook (Enhancement #6)
        /// </summary>
        public void RegisterVerificationHook(IVerificationHook hook)
        {
            _verifier.RegisterHook(hook);
        }

        /// <summary>
        /// Get the dependency graph for external inspection (Enhancement #4)
        /// </summary>
        public DependencyGraphData GetDependencyGraph()
        {
            return _dependencyGraph.GetGraphData();
        }

        /// <summary>
        /// Invalidate a decision and cascade to dependents (Enhancement #4)
        /// </summary>
        public CascadeResult InvalidateDecision(string operationId, WorkflowState workflow)
        {
            return _dependencyGraph.InvalidateDecision(operationId, workflow);
        }

        /// <summary>
        /// Add context from already-executed operations
        /// </summary>
        private void AddContextFromExecuted(ConfidenceEnvelope envelope, WorkflowState workflow)
        {
            // Find dependencies that are now complete
            var completedDeps = envelope.Dependencies
                .Where(depId => workflow.Operations.TryGetValue(depId, out var dep) &&
                    (dep.Status == ProcessingStatus.Executed || dep.Status == ProcessingStatus.Verified))
                .ToList();

            if (completedDeps.Count > 0)
            {
                // Boost confidence based on completed dependencies
                var depBoost = completedDeps.Count * 0.05;
                envelope.OverallConfidence = Math.Min(1.0, envelope.OverallConfidence + depBoost);

                envelope.Factors.Add(ConfidenceFactor.Pass(
                    ConfidenceFactorNames.ContextAlignment,
                    0.1,
                    $"{completedDeps.Count} dependencies now resolved"));
            }
        }

        /// <summary>
        /// Determine overall workflow status
        /// </summary>
        private WorkflowStatus DetermineWorkflowStatus(WorkflowState workflow)
        {
            var ops = workflow.Operations.Values.ToList();

            if (ops.All(o => o.Status == ProcessingStatus.Executed || o.Status == ProcessingStatus.Verified))
                return WorkflowStatus.Completed;

            if (ops.Any(o => o.Status == ProcessingStatus.InReview))
                return WorkflowStatus.AwaitingReview;

            if (ops.All(o => o.Status == ProcessingStatus.Failed))
                return WorkflowStatus.Failed;

            return WorkflowStatus.Pass3_Complete;
        }
    }
}
