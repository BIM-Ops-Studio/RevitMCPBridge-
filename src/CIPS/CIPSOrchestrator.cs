using System;
using System.Collections.Generic;
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.CIPS.Models;
using RevitMCPBridge.CIPS.Services;
using Serilog;

namespace RevitMCPBridge.CIPS
{
    /// <summary>
    /// Main orchestrator for the Confidence-Based Iterative Processing System.
    /// Coordinates all CIPS components and provides the primary entry point.
    /// </summary>
    public class CIPSOrchestrator
    {
        private static CIPSOrchestrator _instance;
        private static readonly object _lock = new object();

        private readonly FeedbackLearner _feedbackLearner;
        private readonly ReviewQueueManager _reviewQueueManager;
        private ConfidenceCalculator _calculator;
        private PassCoordinator _passCoordinator;
        private UIApplication _uiApp;

        // Track all envelopes for lookup (Enhancement #2, #6)
        private readonly Dictionary<string, ConfidenceEnvelope> _envelopeCache = new Dictionary<string, ConfidenceEnvelope>();
        private WorkflowState _currentWorkflow;

        /// <summary>
        /// Get the singleton instance
        /// </summary>
        public static CIPSOrchestrator Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new CIPSOrchestrator();
                        }
                    }
                }
                return _instance;
            }
        }

        private CIPSOrchestrator()
        {
            _feedbackLearner = new FeedbackLearner();
            _reviewQueueManager = new ReviewQueueManager();
        }

        /// <summary>
        /// Initialize with UIApplication context
        /// </summary>
        public void Initialize(UIApplication uiApp)
        {
            _uiApp = uiApp;
            _calculator = new ConfidenceCalculator(uiApp, _feedbackLearner);
            _passCoordinator = new PassCoordinator(uiApp, _calculator, _reviewQueueManager, _feedbackLearner);
            Log.Information("[CIPS] Orchestrator initialized");
        }

        /// <summary>
        /// Check if CIPS is enabled
        /// </summary>
        public bool IsEnabled => CIPSConfiguration.Instance.Enabled;

        /// <summary>
        /// Process a single operation with confidence assessment
        /// </summary>
        public ConfidenceEnvelope ProcessOperation(string methodName, JObject parameters, bool autoExecute = true)
        {
            EnsureInitialized();

            if (!IsEnabled)
            {
                throw new InvalidOperationException("CIPS is not enabled. Set CIPS.Enabled = true in appsettings.json");
            }

            var envelope = _passCoordinator.ProcessSingle(methodName, parameters, autoExecute);

            // Cache envelope for later retrieval (Enhancement #2, #6)
            CacheEnvelope(envelope);

            return envelope;
        }

        /// <summary>
        /// Calculate confidence without executing
        /// </summary>
        public ConfidenceEnvelope CalculateConfidence(string methodName, JObject parameters)
        {
            EnsureInitialized();
            return _calculator.Calculate(methodName, parameters);
        }

        /// <summary>
        /// Process a batch of operations with multi-pass workflow
        /// </summary>
        public WorkflowState ProcessBatch(List<(string method, JObject parameters)> operations,
            string description = null, bool autoExecute = true)
        {
            EnsureInitialized();

            if (!IsEnabled)
            {
                throw new InvalidOperationException("CIPS is not enabled");
            }

            var workflow = _passCoordinator.ProcessBatch(operations, description, autoExecute);

            // Track workflow and cache all envelopes (Enhancement #2, #6)
            _currentWorkflow = workflow;
            foreach (var envelope in workflow.Operations.Values)
            {
                CacheEnvelope(envelope);
            }

            return workflow;
        }

        /// <summary>
        /// Get the review queue manager
        /// </summary>
        public ReviewQueueManager ReviewQueue => _reviewQueueManager;

        /// <summary>
        /// Get the feedback learner
        /// </summary>
        public FeedbackLearner FeedbackLearner => _feedbackLearner;

        /// <summary>
        /// Get the pass coordinator (Enhancement #4, #6)
        /// </summary>
        public PassCoordinator PassCoordinator => _passCoordinator;

        /// <summary>
        /// Get the confidence calculator (Enhancement #3)
        /// </summary>
        public ConfidenceCalculator Calculator => _calculator;

        /// <summary>
        /// Get pending review items
        /// </summary>
        public List<ReviewItem> GetPendingReviews()
        {
            return _reviewQueueManager.GetPendingItems();
        }

        /// <summary>
        /// Submit a review decision
        /// </summary>
        public bool SubmitReview(string reviewId, ReviewDecision decision,
            JObject modifiedParams = null, string notes = null)
        {
            var result = _reviewQueueManager.SubmitDecision(reviewId, decision, modifiedParams, notes);

            if (result)
            {
                // Record feedback for learning
                var item = _reviewQueueManager.GetItem(reviewId);
                if (item != null)
                {
                    _feedbackLearner.RecordFeedback(item);
                }
            }

            return result;
        }

        /// <summary>
        /// Get queue statistics
        /// </summary>
        public QueueStats GetQueueStats()
        {
            return _reviewQueueManager.GetStats();
        }

        /// <summary>
        /// Get feedback statistics
        /// </summary>
        public OverallFeedbackStats GetFeedbackStats()
        {
            return _feedbackLearner.GetOverallStats();
        }

        /// <summary>
        /// Force execute an operation regardless of confidence
        /// </summary>
        public ConfidenceEnvelope ForceExecute(string methodName, JObject parameters)
        {
            EnsureInitialized();

            var envelope = _calculator.Calculate(methodName, parameters);

            // Execute via MCPServer directly
            try
            {
                var result = MCPServer.ExecuteMethod(_uiApp, methodName, parameters);
                var resultObj = JObject.Parse(result);
                envelope.MarkExecuted(resultObj);

                var success = resultObj["success"]?.Value<bool>() ?? false;
                if (!success)
                {
                    envelope.MarkFailed(resultObj["error"]?.ToString() ?? "Unknown error");
                }
            }
            catch (Exception ex)
            {
                envelope.MarkFailed(ex.Message);
            }

            return envelope;
        }

        /// <summary>
        /// Ensure the orchestrator is initialized
        /// </summary>
        private void EnsureInitialized()
        {
            if (_calculator == null || _passCoordinator == null)
            {
                throw new InvalidOperationException(
                    "CIPS Orchestrator not initialized. Call Initialize(uiApp) first.");
            }
        }

        #region Envelope Tracking (Enhancements #2, #6)

        /// <summary>
        /// Get an envelope by its operation ID
        /// </summary>
        public ConfidenceEnvelope GetEnvelopeById(string operationId)
        {
            if (string.IsNullOrEmpty(operationId))
                return null;

            // Check cache first
            if (_envelopeCache.TryGetValue(operationId, out var envelope))
                return envelope;

            // Check current workflow
            if (_currentWorkflow?.Operations != null &&
                _currentWorkflow.Operations.TryGetValue(operationId, out envelope))
            {
                return envelope;
            }

            return null;
        }

        /// <summary>
        /// Cache an envelope for later retrieval
        /// </summary>
        public void CacheEnvelope(ConfidenceEnvelope envelope)
        {
            if (envelope != null && !string.IsNullOrEmpty(envelope.OperationId))
            {
                _envelopeCache[envelope.OperationId] = envelope;
            }
        }

        /// <summary>
        /// Get all cached envelopes
        /// </summary>
        public IReadOnlyDictionary<string, ConfidenceEnvelope> GetAllEnvelopes()
        {
            return _envelopeCache;
        }

        /// <summary>
        /// Get the current workflow state
        /// </summary>
        public WorkflowState CurrentWorkflow => _currentWorkflow;

        /// <summary>
        /// Clear the envelope cache
        /// </summary>
        public void ClearCache()
        {
            _envelopeCache.Clear();
            _currentWorkflow = null;
        }

        #endregion
    }
}
