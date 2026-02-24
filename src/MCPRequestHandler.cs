using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Autodesk.Revit.UI;
using Serilog;

namespace RevitMCPBridge
{
    /// <summary>
    /// Handles execution of MCP requests in Revit's main thread context using ExternalEvent.
    /// Supports request cancellation for timeout handling.
    /// </summary>
    public class MCPRequestHandler : IExternalEventHandler
    {
        private readonly Queue<RequestItem> _requestQueue;
        private readonly object _queueLock = new object();

        public MCPRequestHandler()
        {
            _requestQueue = new Queue<RequestItem>();
        }

        /// <summary>
        /// Queue a request to be executed in Revit's context.
        /// Returns a cancellable task — if the CancellationToken fires before execution,
        /// the request will be skipped when dequeued.
        /// </summary>
        public Task<string> QueueRequest(Func<UIApplication, string> action, CancellationToken cancellationToken = default)
        {
            var requestItem = new RequestItem
            {
                Action = action,
                CompletionSource = new TaskCompletionSource<string>(),
                CancellationToken = cancellationToken,
                QueuedAt = DateTime.UtcNow
            };

            // If already cancelled, don't even queue
            if (cancellationToken.IsCancellationRequested)
            {
                requestItem.CompletionSource.SetCanceled();
                return requestItem.CompletionSource.Task;
            }

            lock (_queueLock)
            {
                _requestQueue.Enqueue(requestItem);
            }

            Log.Debug("Request queued. Queue size: {QueueSize}", _requestQueue.Count);
            return requestItem.CompletionSource.Task;
        }

        /// <summary>
        /// Execute queued requests in Revit's main thread
        /// </summary>
        public void Execute(UIApplication app)
        {
            int processedCount = 0;
            int skippedCount = 0;
            const int maxBatchSize = 10;

            while (processedCount < maxBatchSize)
            {
                RequestItem requestItem = null;

                try
                {
                    lock (_queueLock)
                    {
                        if (_requestQueue.Count > 0)
                        {
                            requestItem = _requestQueue.Dequeue();
                        }
                        else
                        {
                            break;
                        }
                    }

                    if (requestItem == null)
                    {
                        break;
                    }

                    // Skip cancelled/timed-out requests
                    if (requestItem.CancellationToken.IsCancellationRequested)
                    {
                        Log.Warning("Skipping cancelled request (queued {QueuedAt}, waited {WaitMs}ms)",
                            requestItem.QueuedAt, (DateTime.UtcNow - requestItem.QueuedAt).TotalMilliseconds);
                        requestItem.CompletionSource.TrySetCanceled();
                        skippedCount++;
                        continue;
                    }

                    // Skip requests that have been waiting too long (stale requests)
                    var waitTime = DateTime.UtcNow - requestItem.QueuedAt;
                    if (waitTime.TotalMinutes > 10)
                    {
                        Log.Warning("Skipping stale request (queued {WaitMs}ms ago, max 10 minutes)",
                            waitTime.TotalMilliseconds);
                        requestItem.CompletionSource.TrySetResult(
                            Helpers.ResponseBuilder.Error(
                                "Request expired while waiting in queue",
                                "REQUEST_EXPIRED")
                                .With("waitTimeMs", (long)waitTime.TotalMilliseconds)
                                .Build());
                        skippedCount++;
                        continue;
                    }

                    // Execute the action in Revit's main thread context
                    var sw = Stopwatch.StartNew();
                    Log.Debug("Executing request {Num} (queued {WaitMs}ms ago). Remaining: {Remaining}",
                        processedCount + 1, (long)waitTime.TotalMilliseconds, _requestQueue.Count);

                    var result = requestItem.Action(app);
                    sw.Stop();

                    Log.Information("[MCPRequestHandler] Action completed in {ElapsedMs}ms", sw.ElapsedMilliseconds);
                    requestItem.CompletionSource.TrySetResult(result);
                    processedCount++;

                    // Small delay between requests to let Revit breathe (50ms)
                    if (_requestQueue.Count > 0)
                    {
                        Thread.Sleep(50);
                    }
                }
                catch (OperationCanceledException)
                {
                    if (requestItem != null)
                    {
                        requestItem.CompletionSource.TrySetCanceled();
                    }
                    skippedCount++;
                }
                catch (Exception ex)
                {
                    Log.Error(ex, "Error executing request in Revit context: {ExType}", ex.GetType().Name);

                    if (requestItem != null)
                    {
                        // Try to return a structured error instead of throwing
                        try
                        {
                            var errorResult = Helpers.ResponseBuilder.Error(
                                $"Revit execution error: {ex.Message}",
                                "REVIT_EXECUTION_ERROR")
                                .With("exceptionType", ex.GetType().FullName)
                                .With("stackTrace", ex.StackTrace)
                                .Build();
                            requestItem.CompletionSource.TrySetResult(errorResult);
                        }
                        catch
                        {
                            // Last resort: propagate the exception
                            requestItem.CompletionSource.TrySetException(ex);
                        }
                    }
                    processedCount++;
                }
            }

            if (processedCount == 0 && skippedCount == 0)
            {
                Log.Debug("Execute called but queue is empty");
            }
            else
            {
                Log.Information("Processed {Processed} requests, skipped {Skipped} in this Execute cycle",
                    processedCount, skippedCount);
            }
        }

        public string GetName()
        {
            return "MCPRequestHandler";
        }

        /// <summary>
        /// Check if there are pending requests
        /// </summary>
        public bool HasPendingRequests()
        {
            lock (_queueLock)
            {
                return _requestQueue.Count > 0;
            }
        }

        /// <summary>
        /// Get current queue depth for diagnostics
        /// </summary>
        public int QueueDepth
        {
            get
            {
                lock (_queueLock)
                {
                    return _requestQueue.Count;
                }
            }
        }

        private class RequestItem
        {
            public Func<UIApplication, string> Action { get; set; }
            public TaskCompletionSource<string> CompletionSource { get; set; }
            public CancellationToken CancellationToken { get; set; }
            public DateTime QueuedAt { get; set; }
        }
    }
}
