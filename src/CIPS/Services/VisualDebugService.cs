using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Newtonsoft.Json;
using RevitMCPBridge.CIPS.Models;
using Serilog;

namespace RevitMCPBridge.CIPS.Services
{
    /// <summary>
    /// Generates visual debug outputs for CIPS operations.
    /// This is Enhancement #2: Visual Debug Overlay
    /// </summary>
    public class VisualDebugService
    {
        private readonly string _outputDirectory;

        public VisualDebugService()
        {
            _outputDirectory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "BIMOpsStudio", "cips_debug");

            if (!Directory.Exists(_outputDirectory))
            {
                Directory.CreateDirectory(_outputDirectory);
            }
        }

        /// <summary>
        /// Generate a complete debug visualization for an envelope
        /// </summary>
        public DebugVisualization GenerateVisualization(ConfidenceEnvelope envelope, OverlaySettings settings = null)
        {
            settings = settings ?? new OverlaySettings();

            var viz = new DebugVisualization
            {
                OperationId = envelope.OperationId,
                GeneratedAt = DateTime.UtcNow
            };

            switch (settings.OutputFormat)
            {
                case VisualizationFormat.Html:
                    viz.HtmlReport = GenerateHtmlReport(envelope, settings);
                    break;
                case VisualizationFormat.Svg:
                    viz.SvgDiagram = GenerateSvgDiagram(envelope, settings);
                    break;
                case VisualizationFormat.Json:
                    viz.JsonData = JsonConvert.SerializeObject(envelope, Formatting.Indented);
                    break;
                case VisualizationFormat.All:
                    viz.HtmlReport = GenerateHtmlReport(envelope, settings);
                    viz.SvgDiagram = GenerateSvgDiagram(envelope, settings);
                    viz.JsonData = JsonConvert.SerializeObject(envelope, Formatting.Indented);
                    break;
            }

            return viz;
        }

        /// <summary>
        /// Generate an HTML report for the envelope
        /// </summary>
        public string GenerateHtmlReport(ConfidenceEnvelope envelope, OverlaySettings settings)
        {
            var sb = new StringBuilder();

            sb.AppendLine("<!DOCTYPE html>");
            sb.AppendLine("<html lang=\"en\">");
            sb.AppendLine("<head>");
            sb.AppendLine("<meta charset=\"UTF-8\">");
            sb.AppendLine("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">");
            sb.AppendLine($"<title>CIPS Debug: {envelope.MethodName}</title>");
            sb.AppendLine(GetStylesheet());
            sb.AppendLine("</head>");
            sb.AppendLine("<body>");

            // Header
            sb.AppendLine("<div class=\"header\">");
            sb.AppendLine($"<h1>CIPS Debug Report</h1>");
            sb.AppendLine($"<p class=\"subtitle\">Operation: {envelope.MethodName}</p>");
            sb.AppendLine($"<p class=\"meta\">ID: {envelope.OperationId} | Generated: {DateTime.Now:yyyy-MM-dd HH:mm:ss}</p>");
            sb.AppendLine("</div>");

            // Confidence Score
            sb.AppendLine("<div class=\"section\">");
            sb.AppendLine("<h2>Overall Confidence</h2>");
            sb.AppendLine($"<div class=\"confidence-display {GetConfidenceClass(envelope.OverallConfidence)}\">");
            sb.AppendLine($"<span class=\"score\">{envelope.OverallConfidence:P1}</span>");
            sb.AppendLine($"<span class=\"level\">{envelope.GetLevel()}</span>");
            sb.AppendLine("</div>");
            sb.AppendLine(GenerateConfidenceBar(envelope.OverallConfidence));
            sb.AppendLine("</div>");

            // Status
            sb.AppendLine("<div class=\"section\">");
            sb.AppendLine("<h2>Status</h2>");
            sb.AppendLine($"<span class=\"status-badge {envelope.Status.ToString().ToLower()}\">{envelope.Status}</span>");
            sb.AppendLine($"<span class=\"pass-info\">Pass {envelope.CurrentPass}</span>");
            sb.AppendLine("</div>");

            // Confidence Factors
            if (envelope.Factors != null && envelope.Factors.Count > 0 && settings.ShowConfidenceColors)
            {
                sb.AppendLine("<div class=\"section\">");
                sb.AppendLine("<h2>Confidence Factors</h2>");
                sb.AppendLine("<div class=\"factors\">");

                foreach (var factor in envelope.Factors.OrderByDescending(f => f.WeightedScore))
                {
                    var isCritical = factor.Score < 0.7;
                    sb.AppendLine($"<div class=\"factor {(isCritical ? "critical" : "")}\">");
                    sb.AppendLine($"<div class=\"factor-header\">");
                    sb.AppendLine($"<span class=\"factor-name\">{factor.FactorName}</span>");
                    sb.AppendLine($"<span class=\"factor-score {GetConfidenceClass(factor.Score)}\">{factor.Score:P0}</span>");
                    sb.AppendLine("</div>");
                    sb.AppendLine(GenerateConfidenceBar(factor.Score));
                    sb.AppendLine($"<p class=\"factor-reason\">{factor.Reason}</p>");
                    sb.AppendLine($"<p class=\"factor-weight\">Weight: {factor.Weight:P0} | Contribution: {factor.WeightedScore:F3}</p>");
                    sb.AppendLine("</div>");
                }

                sb.AppendLine("</div>");
                sb.AppendLine("</div>");
            }

            // Reasoning Chain
            if (envelope.Reasoning != null && envelope.Reasoning.Steps.Count > 0 && settings.ShowReasoningChain)
            {
                sb.AppendLine("<div class=\"section\">");
                sb.AppendLine("<h2>Reasoning Chain</h2>");

                if (envelope.Reasoning.CriticalFactors.Count > 0)
                {
                    sb.AppendLine("<div class=\"warning\">");
                    sb.AppendLine($"<strong>Critical Factors:</strong> {string.Join(", ", envelope.Reasoning.CriticalFactors)}");
                    sb.AppendLine("</div>");
                }

                sb.AppendLine("<div class=\"reasoning-chain\">");

                foreach (var step in envelope.Reasoning.Steps)
                {
                    var isCritical = step.ConfidenceContribution < 0.7;
                    sb.AppendLine($"<div class=\"reasoning-step {(isCritical ? "critical" : "")}\">");
                    sb.AppendLine($"<div class=\"step-number\">Step {step.Step}</div>");
                    sb.AppendLine($"<div class=\"step-content\">");
                    sb.AppendLine($"<strong>{step.Factor}</strong>");
                    if (!string.IsNullOrEmpty(step.Observation))
                        sb.AppendLine($"<p><em>Observation:</em> {step.Observation}</p>");
                    if (!string.IsNullOrEmpty(step.Evidence))
                        sb.AppendLine($"<p><em>Evidence:</em> {step.Evidence}</p>");
                    if (!string.IsNullOrEmpty(step.Inference))
                        sb.AppendLine($"<p><em>Inference:</em> {step.Inference}</p>");
                    if (!string.IsNullOrEmpty(step.Uncertainty))
                        sb.AppendLine($"<p class=\"uncertainty\"><em>Uncertainty:</em> {step.Uncertainty}</p>");
                    sb.AppendLine($"<span class=\"contribution\">Contribution: {step.ConfidenceContribution:P0}</span>");
                    sb.AppendLine("</div>");
                    sb.AppendLine("</div>");
                }

                sb.AppendLine("</div>");

                if (!string.IsNullOrEmpty(envelope.Reasoning.PrimaryEvidence))
                {
                    sb.AppendLine($"<p class=\"primary\"><strong>Primary Evidence:</strong> {envelope.Reasoning.PrimaryEvidence}</p>");
                }
                if (!string.IsNullOrEmpty(envelope.Reasoning.PrimaryUncertainty))
                {
                    sb.AppendLine($"<p class=\"uncertainty\"><strong>Primary Uncertainty:</strong> {envelope.Reasoning.PrimaryUncertainty}</p>");
                }

                sb.AppendLine("</div>");
            }

            // Verification Results
            if (envelope.VerificationReport != null && envelope.VerificationReport.Checks.Count > 0 && settings.ShowValidationResults)
            {
                sb.AppendLine("<div class=\"section\">");
                sb.AppendLine("<h2>Verification Results</h2>");
                sb.AppendLine($"<p class=\"{(envelope.VerificationReport.AllPassed ? "pass" : "fail")}\">");
                sb.AppendLine(envelope.VerificationReport.GetSummary());
                sb.AppendLine("</p>");

                sb.AppendLine("<table class=\"verification-table\">");
                sb.AppendLine("<tr><th>Check</th><th>Status</th><th>Expected</th><th>Actual</th><th>Message</th></tr>");

                foreach (var check in envelope.VerificationReport.Checks)
                {
                    var statusClass = check.Passed ? "pass" : "fail";
                    sb.AppendLine("<tr>");
                    sb.AppendLine($"<td>{check.CheckName}</td>");
                    sb.AppendLine($"<td class=\"{statusClass}\">{(check.Passed ? "PASS" : "FAIL")}</td>");
                    sb.AppendLine($"<td>{check.Expected ?? "-"}</td>");
                    sb.AppendLine($"<td>{check.Actual ?? "-"}</td>");
                    sb.AppendLine($"<td>{check.Message}</td>");
                    sb.AppendLine("</tr>");
                }

                sb.AppendLine("</table>");
                sb.AppendLine("</div>");
            }

            // Alternatives
            if (envelope.Alternatives != null && envelope.Alternatives.Count > 0)
            {
                sb.AppendLine("<div class=\"section\">");
                sb.AppendLine("<h2>Alternatives Considered</h2>");
                sb.AppendLine("<ul class=\"alternatives\">");

                foreach (var alt in envelope.Alternatives)
                {
                    sb.AppendLine($"<li>{alt.Description} (Confidence: {alt.Confidence:P0})</li>");
                }

                sb.AppendLine("</ul>");
                sb.AppendLine("</div>");
            }

            // Parameters
            sb.AppendLine("<div class=\"section\">");
            sb.AppendLine("<h2>Parameters</h2>");
            sb.AppendLine("<pre class=\"json\">");
            sb.AppendLine(System.Web.HttpUtility.HtmlEncode(
                JsonConvert.SerializeObject(envelope.Parameters, Formatting.Indented)));
            sb.AppendLine("</pre>");
            sb.AppendLine("</div>");

            // Result
            if (envelope.Result != null)
            {
                sb.AppendLine("<div class=\"section\">");
                sb.AppendLine("<h2>Execution Result</h2>");
                sb.AppendLine("<pre class=\"json\">");
                sb.AppendLine(System.Web.HttpUtility.HtmlEncode(
                    JsonConvert.SerializeObject(envelope.Result, Formatting.Indented)));
                sb.AppendLine("</pre>");
                sb.AppendLine("</div>");
            }

            // Footer
            sb.AppendLine("<div class=\"footer\">");
            sb.AppendLine("<p>Generated by CIPS (Confidence-Based Iterative Processing System)</p>");
            sb.AppendLine($"<p>RevitMCPBridge2026 | BIM Ops Studio</p>");
            sb.AppendLine("</div>");

            sb.AppendLine("</body>");
            sb.AppendLine("</html>");

            return sb.ToString();
        }

        /// <summary>
        /// Generate an SVG diagram for factor visualization
        /// </summary>
        public string GenerateSvgDiagram(ConfidenceEnvelope envelope, OverlaySettings settings)
        {
            var sb = new StringBuilder();
            int width = 600;
            int barHeight = 30;
            int padding = 20;
            int labelWidth = 200;

            var factors = envelope.Factors ?? new List<ConfidenceFactor>();
            int height = (factors.Count + 1) * (barHeight + 10) + padding * 2 + 60;

            sb.AppendLine($"<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {width} {height}\" width=\"{width}\" height=\"{height}\">");

            // Background
            sb.AppendLine($"<rect width=\"{width}\" height=\"{height}\" fill=\"#1a1a2e\"/>");

            // Title
            sb.AppendLine($"<text x=\"{width / 2}\" y=\"30\" text-anchor=\"middle\" fill=\"#ffffff\" font-size=\"16\" font-weight=\"bold\">Confidence Analysis: {envelope.MethodName}</text>");

            int y = 60;

            // Overall confidence bar
            var overallColor = GetSvgColor(envelope.OverallConfidence);
            sb.AppendLine($"<text x=\"{padding}\" y=\"{y + 20}\" fill=\"#ffffff\" font-size=\"12\">Overall</text>");
            sb.AppendLine($"<rect x=\"{labelWidth}\" y=\"{y}\" width=\"{(width - labelWidth - padding) * envelope.OverallConfidence}\" height=\"{barHeight}\" fill=\"{overallColor}\" rx=\"4\"/>");
            sb.AppendLine($"<rect x=\"{labelWidth}\" y=\"{y}\" width=\"{width - labelWidth - padding}\" height=\"{barHeight}\" fill=\"none\" stroke=\"#444\" stroke-width=\"1\" rx=\"4\"/>");
            sb.AppendLine($"<text x=\"{width - padding - 5}\" y=\"{y + 20}\" text-anchor=\"end\" fill=\"#ffffff\" font-size=\"12\">{envelope.OverallConfidence:P0}</text>");

            y += barHeight + 15;

            // Factor bars
            foreach (var factor in factors.OrderByDescending(f => f.Score))
            {
                var color = GetSvgColor(factor.Score);
                var barWidth = (width - labelWidth - padding) * factor.Score;

                sb.AppendLine($"<text x=\"{padding}\" y=\"{y + 20}\" fill=\"#aaaaaa\" font-size=\"11\">{factor.FactorName}</text>");
                sb.AppendLine($"<rect x=\"{labelWidth}\" y=\"{y}\" width=\"{barWidth}\" height=\"{barHeight}\" fill=\"{color}\" rx=\"4\"/>");
                sb.AppendLine($"<rect x=\"{labelWidth}\" y=\"{y}\" width=\"{width - labelWidth - padding}\" height=\"{barHeight}\" fill=\"none\" stroke=\"#333\" stroke-width=\"1\" rx=\"4\"/>");
                sb.AppendLine($"<text x=\"{width - padding - 5}\" y=\"{y + 20}\" text-anchor=\"end\" fill=\"#ffffff\" font-size=\"11\">{factor.Score:P0}</text>");

                y += barHeight + 10;
            }

            sb.AppendLine("</svg>");

            return sb.ToString();
        }

        /// <summary>
        /// Save visualization to file
        /// </summary>
        public string SaveVisualization(DebugVisualization viz)
        {
            var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            var basePath = Path.Combine(_outputDirectory, $"{viz.OperationId}_{timestamp}");

            if (!string.IsNullOrEmpty(viz.HtmlReport))
            {
                var htmlPath = basePath + ".html";
                File.WriteAllText(htmlPath, viz.HtmlReport);
                viz.OutputPath = htmlPath;
                Log.Information("[CIPS] Saved debug HTML to {Path}", htmlPath);
            }

            if (!string.IsNullOrEmpty(viz.SvgDiagram))
            {
                var svgPath = basePath + ".svg";
                File.WriteAllText(svgPath, viz.SvgDiagram);
            }

            if (!string.IsNullOrEmpty(viz.JsonData))
            {
                var jsonPath = basePath + ".json";
                File.WriteAllText(jsonPath, viz.JsonData);
            }

            return viz.OutputPath;
        }

        #region Helper Methods

        private string GetStylesheet()
        {
            return @"
<style>
:root {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --text-primary: #ffffff;
    --text-secondary: #a0a0a0;
    --accent: #0f4c75;
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
    --border: #334155;
}

body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    margin: 0;
    padding: 20px;
    line-height: 1.6;
}

.header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
}

.header h1 {
    margin: 0;
    color: var(--text-primary);
}

.subtitle {
    font-size: 1.2em;
    color: var(--accent);
}

.meta {
    color: var(--text-secondary);
    font-size: 0.9em;
}

.section {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.section h2 {
    margin-top: 0;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
}

.confidence-display {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 10px;
}

.confidence-display .score {
    font-size: 3em;
    font-weight: bold;
}

.confidence-display .level {
    font-size: 1.2em;
    padding: 5px 15px;
    border-radius: 20px;
    background: var(--bg-primary);
}

.confidence-display.high .score { color: var(--success); }
.confidence-display.medium .score { color: var(--warning); }
.confidence-display.low .score { color: var(--danger); }

.confidence-bar {
    height: 20px;
    background: var(--bg-primary);
    border-radius: 10px;
    overflow: hidden;
}

.confidence-bar-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 0.3s ease;
}

.confidence-bar-fill.high { background: var(--success); }
.confidence-bar-fill.medium { background: var(--warning); }
.confidence-bar-fill.low { background: var(--danger); }

.factors {
    display: grid;
    gap: 15px;
}

.factor {
    background: var(--bg-primary);
    border-radius: 6px;
    padding: 15px;
    border-left: 4px solid var(--success);
}

.factor.critical {
    border-left-color: var(--danger);
}

.factor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.factor-name {
    font-weight: bold;
}

.factor-score {
    font-size: 1.2em;
    font-weight: bold;
}

.factor-score.high { color: var(--success); }
.factor-score.medium { color: var(--warning); }
.factor-score.low { color: var(--danger); }

.factor-reason {
    color: var(--text-secondary);
    margin: 10px 0 5px 0;
}

.factor-weight {
    font-size: 0.85em;
    color: var(--text-secondary);
}

.reasoning-chain {
    position: relative;
    padding-left: 30px;
}

.reasoning-step {
    position: relative;
    margin-bottom: 20px;
    padding: 15px;
    background: var(--bg-primary);
    border-radius: 6px;
    border-left: 3px solid var(--accent);
}

.reasoning-step.critical {
    border-left-color: var(--danger);
}

.step-number {
    position: absolute;
    left: -40px;
    top: 15px;
    width: 30px;
    height: 30px;
    background: var(--accent);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8em;
}

.reasoning-step.critical .step-number {
    background: var(--danger);
}

.contribution {
    display: inline-block;
    margin-top: 10px;
    padding: 3px 10px;
    background: var(--bg-secondary);
    border-radius: 15px;
    font-size: 0.85em;
}

.warning {
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid var(--warning);
    border-radius: 6px;
    padding: 10px 15px;
    margin-bottom: 15px;
}

.uncertainty {
    color: var(--warning);
}

.primary {
    color: var(--success);
}

.status-badge {
    display: inline-block;
    padding: 5px 15px;
    border-radius: 20px;
    font-weight: bold;
    margin-right: 10px;
}

.status-badge.executed { background: var(--success); }
.status-badge.verified { background: var(--success); }
.status-badge.pending { background: var(--warning); }
.status-badge.inreview { background: var(--warning); }
.status-badge.failed { background: var(--danger); }

.pass-info {
    color: var(--text-secondary);
}

.verification-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

.verification-table th,
.verification-table td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

.verification-table th {
    background: var(--bg-primary);
}

.verification-table .pass { color: var(--success); }
.verification-table .fail { color: var(--danger); }

.alternatives {
    list-style: none;
    padding: 0;
}

.alternatives li {
    padding: 10px;
    background: var(--bg-primary);
    border-radius: 6px;
    margin-bottom: 10px;
}

.json {
    background: var(--bg-primary);
    padding: 15px;
    border-radius: 6px;
    overflow-x: auto;
    font-family: 'Consolas', monospace;
    font-size: 0.9em;
    white-space: pre-wrap;
}

.footer {
    text-align: center;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: 0.9em;
}

.pass { color: var(--success); }
.fail { color: var(--danger); }
</style>";
        }

        private string GetConfidenceClass(double confidence)
        {
            if (confidence >= 0.85) return "high";
            if (confidence >= 0.60) return "medium";
            return "low";
        }

        private string GenerateConfidenceBar(double confidence)
        {
            var colorClass = GetConfidenceClass(confidence);
            return $"<div class=\"confidence-bar\"><div class=\"confidence-bar-fill {colorClass}\" style=\"width: {confidence * 100}%\"></div></div>";
        }

        private string GetSvgColor(double confidence)
        {
            if (confidence >= 0.85) return "#22c55e";
            if (confidence >= 0.60) return "#f59e0b";
            return "#ef4444";
        }

        #endregion
    }
}
