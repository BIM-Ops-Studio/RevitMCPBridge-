using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Autodesk.Revit.UI;
using Serilog;

namespace RevitMCPBridge
{
    /// <summary>
    /// Handles execution of MCP requests in Revit's main thread context using ExternalEvent
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
        /// Queue a request to be executed in Revit's context
        /// </summary>
        public Task<string> QueueRequest(Func<UIApplication, string> action)
        {
            var requestItem = new RequestItem
            {
                Action = action,
                CompletionSource = new TaskCompletionSource<string>()
            };

            lock (_queueLock)
            {
                _requestQueue.Enqueue(requestItem);
            }

            Log.Debug($"Request queued. Queue size: {_requestQueue.Count}");
            return requestItem.CompletionSource.Task;
        }

        /// <summary>
        /// Execute queued requests in Revit's main thread
        /// </summary>
        public void Execute(UIApplication app)
        {
            // Process all queued requests in one Execute call to reduce Idling event overhead
            int processedCount = 0;
            const int maxBatchSize = 10; // Process up to 10 requests per Execute

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
                            Log.Debug($"Executing request {processedCount + 1}. Remaining in queue: {_requestQueue.Count}");
                        }
                        else
                        {
                            break; // Queue empty, exit loop
                        }
                    }

                    if (requestItem == null)
                    {
                        break;
                    }

                    // Execute the action in Revit's main thread context
                    Log.Information($"[MCPRequestHandler] About to execute action. UIApplication is null: {app == null}");
                    var result = requestItem.Action(app);
                    Log.Information($"[MCPRequestHandler] Action executed successfully");
                    requestItem.CompletionSource.SetResult(result);
                    processedCount++;
                    Log.Debug($"Request {processedCount} completed successfully");

                    // Small delay between requests to let Revit breathe (50ms)
                    if (_requestQueue.Count > 0)
                    {
                        Thread.Sleep(50);
                    }
                }
                catch (Exception ex)
                {
                    Log.Error(ex, "Error executing request in Revit context");

                    if (requestItem != null)
                    {
                        requestItem.CompletionSource.SetException(ex);
                    }
                    processedCount++;
                }
            }

            if (processedCount == 0)
            {
                Log.Warning("Execute called but queue is empty");
            }
            else
            {
                Log.Information($"Processed {processedCount} requests in this Execute cycle");
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

        private class RequestItem
        {
            public Func<UIApplication, string> Action { get; set; }
            public TaskCompletionSource<string> CompletionSource { get; set; }
        }
    }
}
