using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace RevitMCPBridge.CIPS.Models
{
    /// <summary>
    /// Visual debug output for CIPS operations.
    /// This is Enhancement #2: Visual Debug Overlay
    /// </summary>
    public class DebugVisualization
    {
        [JsonProperty("operationId")]
        public string OperationId { get; set; }

        [JsonProperty("htmlReport")]
        public string HtmlReport { get; set; }

        [JsonProperty("svgDiagram")]
        public string SvgDiagram { get; set; }

        [JsonProperty("jsonData")]
        public string JsonData { get; set; }

        [JsonProperty("generatedAt")]
        public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

        [JsonProperty("outputPath")]
        public string OutputPath { get; set; }
    }

    /// <summary>
    /// An element detected by the AI with confidence scoring
    /// </summary>
    public class DetectedElement
    {
        [JsonProperty("elementId")]
        public string ElementId { get; set; }

        [JsonProperty("elementType")]
        public string ElementType { get; set; }  // wall, door, window, room, unknown

        [JsonProperty("bounds")]
        public BoundingBox2D Bounds { get; set; }

        [JsonProperty("outline")]
        public List<Point2D> Outline { get; set; }

        [JsonProperty("confidence")]
        public double Confidence { get; set; }

        [JsonProperty("overlayColor")]
        public string OverlayColor { get; set; }  // CSS color based on confidence

        [JsonProperty("label")]
        public string Label { get; set; }

        [JsonProperty("properties")]
        public Dictionary<string, object> Properties { get; set; } = new Dictionary<string, object>();

        /// <summary>
        /// Get color based on confidence level
        /// </summary>
        public string GetConfidenceColor()
        {
            if (Confidence >= 0.85) return "#22c55e";  // Green
            if (Confidence >= 0.60) return "#f59e0b";  // Yellow/Orange
            return "#ef4444";  // Red
        }
    }

    /// <summary>
    /// 2D point for visualization
    /// </summary>
    public class Point2D
    {
        [JsonProperty("x")]
        public double X { get; set; }

        [JsonProperty("y")]
        public double Y { get; set; }

        public Point2D() { }

        public Point2D(double x, double y)
        {
            X = x;
            Y = y;
        }
    }

    /// <summary>
    /// 2D bounding box for visualization
    /// </summary>
    public class BoundingBox2D
    {
        [JsonProperty("minX")]
        public double MinX { get; set; }

        [JsonProperty("minY")]
        public double MinY { get; set; }

        [JsonProperty("maxX")]
        public double MaxX { get; set; }

        [JsonProperty("maxY")]
        public double MaxY { get; set; }

        [JsonProperty("width")]
        public double Width => MaxX - MinX;

        [JsonProperty("height")]
        public double Height => MaxY - MinY;

        [JsonProperty("centerX")]
        public double CenterX => (MinX + MaxX) / 2;

        [JsonProperty("centerY")]
        public double CenterY => (MinY + MaxY) / 2;
    }

    /// <summary>
    /// Settings for generating debug overlays
    /// </summary>
    public class OverlaySettings
    {
        [JsonProperty("showConfidenceColors")]
        public bool ShowConfidenceColors { get; set; } = true;

        [JsonProperty("showElementLabels")]
        public bool ShowElementLabels { get; set; } = true;

        [JsonProperty("showBoundingBoxes")]
        public bool ShowBoundingBoxes { get; set; } = true;

        [JsonProperty("showDetectedLines")]
        public bool ShowDetectedLines { get; set; } = false;

        [JsonProperty("showInferredConnections")]
        public bool ShowInferredConnections { get; set; } = false;

        [JsonProperty("showReasoningChain")]
        public bool ShowReasoningChain { get; set; } = true;

        [JsonProperty("showValidationResults")]
        public bool ShowValidationResults { get; set; } = true;

        [JsonProperty("confidenceThresholdFilter")]
        public double ConfidenceThresholdFilter { get; set; } = 0.0;  // Show all by default

        [JsonProperty("outputFormat")]
        public VisualizationFormat OutputFormat { get; set; } = VisualizationFormat.Html;
    }

    /// <summary>
    /// Output format for visualizations
    /// </summary>
    public enum VisualizationFormat
    {
        Html,
        Svg,
        Json,
        All
    }

    /// <summary>
    /// Comparison overlay showing source vs result alignment
    /// </summary>
    public class ComparisonOverlay
    {
        [JsonProperty("sourceElements")]
        public List<DetectedElement> SourceElements { get; set; } = new List<DetectedElement>();

        [JsonProperty("resultElements")]
        public List<DetectedElement> ResultElements { get; set; } = new List<DetectedElement>();

        [JsonProperty("alignmentScore")]
        public double AlignmentScore { get; set; }

        [JsonProperty("deviations")]
        public List<ElementDeviation> Deviations { get; set; } = new List<ElementDeviation>();
    }

    /// <summary>
    /// Deviation between source and result element
    /// </summary>
    public class ElementDeviation
    {
        [JsonProperty("sourceElementId")]
        public string SourceElementId { get; set; }

        [JsonProperty("resultElementId")]
        public string ResultElementId { get; set; }

        [JsonProperty("deviationType")]
        public string DeviationType { get; set; }  // position, size, type, missing, extra

        [JsonProperty("deviationAmount")]
        public double DeviationAmount { get; set; }

        [JsonProperty("description")]
        public string Description { get; set; }
    }
}
