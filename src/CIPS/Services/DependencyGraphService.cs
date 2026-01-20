using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Manages dependencies between operations and handles cascade invalidation.
    /// This is Enhancement #4: Decision Dependency Graph
    /// </summary>
    public class DependencyGraphService
    {
        // Maps operationId -> set of operationIds it depends on
        private readonly Dictionary<string, HashSet<string>> _dependsOn = new Dictionary<string, HashSet<string>>();

        // Maps operationId -> set of operationIds that depend on it
        private readonly Dictionary<string, HashSet<string>> _dependedBy = new Dictionary<string, HashSet<string>>();

        private readonly object _lock = new object();

        /// <summary>
        /// Register a dependency between two operations
        /// </summary>
        public void RegisterDependency(string operationId, string dependsOnId)
        {
            lock (_lock)
            {
                if (!_dependsOn.ContainsKey(operationId))
                    _dependsOn[operationId] = new HashSet<string>();
                _dependsOn[operationId].Add(dependsOnId);

                if (!_dependedBy.ContainsKey(dependsOnId))
                    _dependedBy[dependsOnId] = new HashSet<string>();
                _dependedBy[dependsOnId].Add(operationId);

                Log.Debug("[CIPS] Registered dependency: {Op} depends on {Dep}", operationId, dependsOnId);
            }
        }

        /// <summary>
        /// Register all dependencies for an envelope
        /// </summary>
        public void RegisterEnvelopeDependencies(ConfidenceEnvelope envelope)
        {
            if (envelope.Dependencies == null || envelope.Dependencies.Count == 0)
                return;

            foreach (var depId in envelope.Dependencies)
            {
                RegisterDependency(envelope.OperationId, depId);
            }
        }

        /// <summary>
        /// Get the execution order for a list of operations using topological sort
        /// </summary>
        public List<string> GetExecutionOrder(List<ConfidenceEnvelope> operations)
        {
            var result = new List<string>();
            var visited = new HashSet<string>();
            var inProgress = new HashSet<string>();
            var opMap = operations.ToDictionary(o => o.OperationId);

            foreach (var op in operations)
            {
                if (!visited.Contains(op.OperationId))
                {
                    if (!TopologicalSort(op.OperationId, opMap, visited, inProgress, result))
                    {
                        // Circular dependency detected - fall back to original order
                        Log.Warning("[CIPS] Circular dependency detected, using original order");
                        return operations.Select(o => o.OperationId).ToList();
                    }
                }
            }

            // Reverse because topological sort adds in post-order
            result.Reverse();
            return result;
        }

        private bool TopologicalSort(
            string operationId,
            Dictionary<string, ConfidenceEnvelope> opMap,
            HashSet<string> visited,
            HashSet<string> inProgress,
            List<string> result)
        {
            if (inProgress.Contains(operationId))
                return false; // Circular dependency

            if (visited.Contains(operationId))
                return true;

            inProgress.Add(operationId);

            // Visit all dependencies first
            if (_dependsOn.TryGetValue(operationId, out var dependencies))
            {
                foreach (var depId in dependencies)
                {
                    if (opMap.ContainsKey(depId))
                    {
                        if (!TopologicalSort(depId, opMap, visited, inProgress, result))
                            return false;
                    }
                }
            }

            inProgress.Remove(operationId);
            visited.Add(operationId);
            result.Add(operationId);

            return true;
        }

        /// <summary>
        /// Get all operations that depend on a given operation (transitive)
        /// </summary>
        public List<string> GetAffectedByChange(string operationId)
        {
            var affected = new List<string>();
            var visited = new HashSet<string>();
            var queue = new Queue<string>();
            queue.Enqueue(operationId);

            while (queue.Count > 0)
            {
                var current = queue.Dequeue();

                if (_dependedBy.TryGetValue(current, out var dependents))
                {
                    foreach (var dep in dependents)
                    {
                        if (!visited.Contains(dep))
                        {
                            visited.Add(dep);
                            affected.Add(dep);
                            queue.Enqueue(dep);
                        }
                    }
                }
            }

            return affected;
        }

        /// <summary>
        /// Get direct dependencies for an operation
        /// </summary>
        public List<string> GetDirectDependencies(string operationId)
        {
            if (_dependsOn.TryGetValue(operationId, out var deps))
                return deps.ToList();
            return new List<string>();
        }

        /// <summary>
        /// Get operations that directly depend on this one
        /// </summary>
        public List<string> GetDirectDependents(string operationId)
        {
            if (_dependedBy.TryGetValue(operationId, out var deps))
                return deps.ToList();
            return new List<string>();
        }

        /// <summary>
        /// Invalidate a decision and cascade to dependents
        /// </summary>
        public CascadeResult InvalidateDecision(string operationId, WorkflowState workflow)
        {
            var result = new CascadeResult
            {
                TriggerOperationId = operationId,
                AffectedOperations = new List<string>()
            };

            var affected = GetAffectedByChange(operationId);

            foreach (var affectedId in affected)
            {
                if (workflow.Operations.TryGetValue(affectedId, out var op))
                {
                    var previousStatus = op.Status;

                    if (op.Status == ProcessingStatus.Executed || op.Status == ProcessingStatus.Verified)
                    {
                        op.Status = ProcessingStatus.NeedsVerification;
                        result.NeedsVerificationCount++;
                    }
                    else if (op.Status == ProcessingStatus.Pending)
                    {
                        op.CurrentPass = 1; // Re-evaluate from start
                        result.ResetCount++;
                    }

                    result.AffectedOperations.Add(affectedId);

                    Log.Information("[CIPS] Cascade: {Op} status changed from {Old} to {New}",
                        affectedId, previousStatus, op.Status);
                }
            }

            return result;
        }

        /// <summary>
        /// Check if any dependencies are still unresolved
        /// </summary>
        public bool HasUnresolvedDependencies(string operationId, WorkflowState workflow)
        {
            if (!_dependsOn.TryGetValue(operationId, out var dependencies))
                return false;

            foreach (var depId in dependencies)
            {
                if (workflow.Operations.TryGetValue(depId, out var dep))
                {
                    if (dep.Status != ProcessingStatus.Executed &&
                        dep.Status != ProcessingStatus.Verified)
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        /// <summary>
        /// Get dependency graph as a serializable object
        /// </summary>
        public DependencyGraphData GetGraphData()
        {
            lock (_lock)
            {
                return new DependencyGraphData
                {
                    Nodes = _dependsOn.Keys.Union(_dependedBy.Keys).ToList(),
                    Edges = _dependsOn.SelectMany(kvp =>
                        kvp.Value.Select(dep => new DependencyEdge
                        {
                            From = kvp.Key,
                            To = dep,
                            Type = DependencyType.DependsOn
                        })).ToList()
                };
            }
        }

        /// <summary>
        /// Clear all dependencies
        /// </summary>
        public void Clear()
        {
            lock (_lock)
            {
                _dependsOn.Clear();
                _dependedBy.Clear();
            }
        }
    }

    /// <summary>
    /// Result of a cascade invalidation
    /// </summary>
    public class CascadeResult
    {
        [JsonProperty("triggerOperationId")]
        public string TriggerOperationId { get; set; }

        [JsonProperty("affectedOperations")]
        public List<string> AffectedOperations { get; set; } = new List<string>();

        [JsonProperty("needsVerificationCount")]
        public int NeedsVerificationCount { get; set; }

        [JsonProperty("resetCount")]
        public int ResetCount { get; set; }

        [JsonProperty("totalAffected")]
        public int TotalAffected => AffectedOperations.Count;
    }

    /// <summary>
    /// Serializable dependency graph data
    /// </summary>
    public class DependencyGraphData
    {
        [JsonProperty("nodes")]
        public List<string> Nodes { get; set; } = new List<string>();

        [JsonProperty("edges")]
        public List<DependencyEdge> Edges { get; set; } = new List<DependencyEdge>();
    }

    /// <summary>
    /// A single edge in the dependency graph
    /// </summary>
    public class DependencyEdge
    {
        [JsonProperty("from")]
        public string From { get; set; }

        [JsonProperty("to")]
        public string To { get; set; }

        [JsonProperty("type")]
        public DependencyType Type { get; set; }

        [JsonProperty("strength")]
        public double Strength { get; set; } = 1.0;

        [JsonProperty("notes")]
        public string Notes { get; set; }
    }

    /// <summary>
    /// Types of dependencies between operations
    /// </summary>
    public enum DependencyType
    {
        /// <summary>Operation A depends on operation B completing first</summary>
        DependsOn,

        /// <summary>Element A is spatially adjacent to element B</summary>
        SpatialAdjacency,

        /// <summary>Element A connects to element B at an endpoint</summary>
        ConnectionEndpoint,

        /// <summary>Element A is contained within element B (door in wall)</summary>
        ContainedWithin,

        /// <summary>Confidence was inferred from another operation</summary>
        InferredFrom,

        /// <summary>Element defines a room boundary</summary>
        RoomBoundary
    }
}
