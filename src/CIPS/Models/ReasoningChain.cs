using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// A single step in the reasoning chain showing why a decision was made
    /// </summary>
    public class ReasoningStep
    {
        [JsonProperty("step")]
        public int Step { get; set; }

        [JsonProperty("factor")]
        public string Factor { get; set; }

        [JsonProperty("observation")]
        public string Observation { get; set; }

        [JsonProperty("evidence")]
        public string Evidence { get; set; }

        [JsonProperty("inference")]
        public string Inference { get; set; }

        [JsonProperty("uncertainty")]
        public string Uncertainty { get; set; }

        [JsonProperty("confidenceContribution")]
        public double ConfidenceContribution { get; set; }

        [JsonProperty("timestamp")]
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    /// <summary>
    /// Complete reasoning chain explaining why a confidence score was computed
    /// </summary>
    public class ReasoningChain
    {
        [JsonProperty("steps")]
        public List<ReasoningStep> Steps { get; set; } = new List<ReasoningStep>();

        [JsonProperty("primaryEvidence")]
        public string PrimaryEvidence { get; set; }

        [JsonProperty("primaryUncertainty")]
        public string PrimaryUncertainty { get; set; }

        [JsonProperty("criticalFactors")]
        public List<string> CriticalFactors { get; set; } = new List<string>();

        [JsonProperty("createdAt")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// Threshold below which a factor is considered critical
        /// </summary>
        public const double CriticalThreshold = 0.7;

        /// <summary>
        /// Add a reasoning step with observation and evidence
        /// </summary>
        public void AddStep(string factor, double score, string observation, string evidence, string inference = null, string uncertainty = null)
        {
            var step = new ReasoningStep
            {
                Step = Steps.Count + 1,
                Factor = factor,
                Observation = observation,
                Evidence = evidence,
                Inference = inference,
                Uncertainty = uncertainty,
                ConfidenceContribution = score
            };

            Steps.Add(step);

            // Track critical factors (score below threshold)
            if (score < CriticalThreshold && !CriticalFactors.Contains(factor))
            {
                CriticalFactors.Add(factor);
            }

            // Auto-set primary uncertainty from first low-score factor
            if (score < CriticalThreshold && string.IsNullOrEmpty(PrimaryUncertainty) && !string.IsNullOrEmpty(uncertainty))
            {
                PrimaryUncertainty = uncertainty;
            }
        }

        /// <summary>
        /// Add a simple step with just factor and reason
        /// </summary>
        public void AddSimpleStep(string factor, double score, string reason)
        {
            AddStep(factor, score, reason, null);
        }

        /// <summary>
        /// Finalize the chain by setting primary evidence from highest-scoring factor
        /// </summary>
        public void Finalize()
        {
            if (Steps.Count == 0) return;

            // Primary evidence is from highest-scoring factor
            var bestStep = Steps.OrderByDescending(s => s.ConfidenceContribution).FirstOrDefault();
            if (bestStep != null && !string.IsNullOrEmpty(bestStep.Evidence))
            {
                PrimaryEvidence = $"{bestStep.Factor}: {bestStep.Evidence}";
            }

            // If no uncertainty set, use lowest-scoring factor
            if (string.IsNullOrEmpty(PrimaryUncertainty) && CriticalFactors.Count > 0)
            {
                var worstStep = Steps.OrderBy(s => s.ConfidenceContribution).FirstOrDefault();
                if (worstStep != null)
                {
                    PrimaryUncertainty = $"{worstStep.Factor}: {worstStep.Observation}";
                }
            }
        }

        /// <summary>
        /// Get a summary of the reasoning chain
        /// </summary>
        public string GetSummary()
        {
            if (Steps.Count == 0)
                return "No reasoning steps recorded";

            var summary = $"Reasoning chain with {Steps.Count} steps. ";

            if (CriticalFactors.Count > 0)
            {
                summary += $"Critical factors: {string.Join(", ", CriticalFactors)}. ";
            }
            else
            {
                summary += "All factors above threshold. ";
            }

            if (!string.IsNullOrEmpty(PrimaryEvidence))
            {
                summary += $"Primary evidence: {PrimaryEvidence}";
            }

            return summary;
        }

        /// <summary>
        /// Check if any critical factors exist
        /// </summary>
        public bool HasCriticalFactors => CriticalFactors.Count > 0;

        /// <summary>
        /// Get average confidence contribution across all steps
        /// </summary>
        public double AverageConfidence => Steps.Count > 0
            ? Steps.Average(s => s.ConfidenceContribution)
            : 0;
    }
}
