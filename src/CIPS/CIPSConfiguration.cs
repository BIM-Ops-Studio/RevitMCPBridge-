using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Serilog;

namespace RevitMCPBridge.CIPS
{
    /// <summary>
    /// Configuration for the Confidence-Based Iterative Processing System.
    /// Loads settings from appsettings.json "CIPS" section.
    /// </summary>
    public class CIPSConfiguration
    {
        private static CIPSConfiguration _instance;
        private static readonly object _lock = new object();

        /// <summary>
        /// Singleton instance
        /// </summary>
        public static CIPSConfiguration Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new CIPSConfiguration();
                            _instance.Load();
                        }
                    }
                }
                return _instance;
            }
        }

        /// <summary>
        /// Whether CIPS is enabled
        /// </summary>
        public bool Enabled { get; private set; } = false;

        /// <summary>
        /// Default thresholds
        /// </summary>
        public ThresholdSettings Thresholds { get; private set; } = new ThresholdSettings();

        /// <summary>
        /// Per-operation threshold overrides
        /// </summary>
        public Dictionary<string, OperationThreshold> OperationThresholds { get; private set; } = new Dictionary<string, OperationThreshold>(StringComparer.OrdinalIgnoreCase);

        /// <summary>
        /// Multi-pass settings
        /// </summary>
        public MultiPassSettings MultiPass { get; private set; } = new MultiPassSettings();

        /// <summary>
        /// Review queue settings
        /// </summary>
        public ReviewQueueSettings ReviewQueue { get; private set; } = new ReviewQueueSettings();

        /// <summary>
        /// Feedback learning settings
        /// </summary>
        public FeedbackSettings Feedback { get; private set; } = new FeedbackSettings();

        /// <summary>
        /// Architectural validation rules (Enhancement #3)
        /// </summary>
        public Models.ValidationRulesConfig ValidationRules { get; private set; } = new Models.ValidationRulesConfig();

        /// <summary>
        /// Get threshold for a specific operation
        /// </summary>
        public double GetHighThreshold(string methodName)
        {
            if (OperationThresholds.TryGetValue(methodName, out var opThreshold))
                return opThreshold.High ?? Thresholds.High;
            return Thresholds.High;
        }

        /// <summary>
        /// Get medium threshold for a specific operation
        /// </summary>
        public double GetMediumThreshold(string methodName)
        {
            if (OperationThresholds.TryGetValue(methodName, out var opThreshold))
                return opThreshold.Medium ?? Thresholds.Medium;
            return Thresholds.Medium;
        }

        /// <summary>
        /// Get low threshold for a specific operation
        /// </summary>
        public double GetLowThreshold(string methodName)
        {
            if (OperationThresholds.TryGetValue(methodName, out var opThreshold))
                return opThreshold.Low ?? Thresholds.Low;
            return Thresholds.Low;
        }

        /// <summary>
        /// Get threshold for a specific pass
        /// </summary>
        public double GetPassThreshold(int passNumber, string methodName = null)
        {
            var baseThreshold = passNumber switch
            {
                1 => GetHighThreshold(methodName),
                2 => GetMediumThreshold(methodName),
                3 => GetLowThreshold(methodName),
                _ => GetLowThreshold(methodName)
            };

            // Apply context boost for passes beyond 1
            if (passNumber > 1)
            {
                baseThreshold -= (passNumber - 1) * MultiPass.ContextBoostPerPass;
            }

            return Math.Max(0.3, baseThreshold); // Never go below 0.3
        }

        /// <summary>
        /// Get the review queue storage path
        /// </summary>
        public string GetReviewQueuePath()
        {
            if (!string.IsNullOrEmpty(ReviewQueue.Path))
                return ReviewQueue.Path;

            // Default to %APPDATA%/BIMOpsStudio/
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var bimOpsDir = Path.Combine(appData, "BIMOpsStudio");
            Directory.CreateDirectory(bimOpsDir);
            return Path.Combine(bimOpsDir, "cips_review_queue.json");
        }

        /// <summary>
        /// Get the feedback history storage path
        /// </summary>
        public string GetFeedbackHistoryPath()
        {
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var bimOpsDir = Path.Combine(appData, "BIMOpsStudio");
            Directory.CreateDirectory(bimOpsDir);
            return Path.Combine(bimOpsDir, "cips_feedback_history.json");
        }

        /// <summary>
        /// Load configuration from appsettings.json
        /// </summary>
        private void Load()
        {
            try
            {
                // Find appsettings.json
                var assemblyDir = Path.GetDirectoryName(typeof(CIPSConfiguration).Assembly.Location);
                var configPath = Path.Combine(assemblyDir, "appsettings.json");

                if (!File.Exists(configPath))
                {
                    // Try parent directory
                    configPath = Path.Combine(Directory.GetParent(assemblyDir)?.FullName ?? assemblyDir, "appsettings.json");
                }

                if (!File.Exists(configPath))
                {
                    Log.Warning("[CIPS] appsettings.json not found, using defaults");
                    return;
                }

                var json = File.ReadAllText(configPath);
                var config = JObject.Parse(json);
                var cipsSection = config["CIPS"];

                if (cipsSection == null)
                {
                    Log.Information("[CIPS] No CIPS section in appsettings.json, using defaults (disabled)");
                    return;
                }

                // Parse enabled flag
                Enabled = cipsSection["Enabled"]?.Value<bool>() ?? false;

                // Parse thresholds
                var thresholdsSection = cipsSection["Thresholds"];
                if (thresholdsSection != null)
                {
                    Thresholds = new ThresholdSettings
                    {
                        High = thresholdsSection["High"]?.Value<double>() ?? 0.85,
                        Medium = thresholdsSection["Medium"]?.Value<double>() ?? 0.60,
                        Low = thresholdsSection["Low"]?.Value<double>() ?? 0.40
                    };
                }

                // Parse operation-specific thresholds
                var opThresholdsSection = cipsSection["OperationThresholds"];
                if (opThresholdsSection != null)
                {
                    foreach (var prop in ((JObject)opThresholdsSection).Properties())
                    {
                        OperationThresholds[prop.Name] = new OperationThreshold
                        {
                            High = prop.Value["high"]?.Value<double>(),
                            Medium = prop.Value["medium"]?.Value<double>(),
                            Low = prop.Value["low"]?.Value<double>()
                        };
                    }
                }

                // Parse multi-pass settings
                var multiPassSection = cipsSection["MultiPass"];
                if (multiPassSection != null)
                {
                    MultiPass = new MultiPassSettings
                    {
                        MaxPasses = multiPassSection["MaxPasses"]?.Value<int>() ?? 3,
                        ContextBoostPerPass = multiPassSection["ContextBoostPerPass"]?.Value<double>() ?? 0.10
                    };
                }

                // Parse review queue settings
                var reviewQueueSection = cipsSection["ReviewQueue"];
                if (reviewQueueSection != null)
                {
                    ReviewQueue = new ReviewQueueSettings
                    {
                        Path = reviewQueueSection["Path"]?.Value<string>(),
                        MaxSize = reviewQueueSection["MaxSize"]?.Value<int>() ?? 100,
                        ExpireHours = reviewQueueSection["ExpireHours"]?.Value<int>() ?? 24
                    };
                }

                // Parse feedback settings
                var feedbackSection = cipsSection["Feedback"];
                if (feedbackSection != null)
                {
                    Feedback = new FeedbackSettings
                    {
                        MinSamplesToLearn = feedbackSection["MinSamplesToLearn"]?.Value<int>() ?? 5,
                        MaxAdjustment = feedbackSection["MaxAdjustment"]?.Value<double>() ?? 0.15
                    };
                }

                // Parse validation rules (Enhancement #3)
                var validationSection = cipsSection["Validation"];
                if (validationSection != null)
                {
                    ValidationRules = new Models.ValidationRulesConfig
                    {
                        Enabled = validationSection["Enabled"]?.Value<bool>() ?? true
                    };

                    var rulesSection = validationSection["Rules"];
                    if (rulesSection != null)
                    {
                        var rules = ValidationRules.Rules;

                        // Parse wall rules
                        var wallsSection = rulesSection["walls"];
                        if (wallsSection != null)
                        {
                            rules.Walls.MinLengthInches = wallsSection["minLengthInches"]?.Value<double>() ?? 6;
                            rules.Walls.MaxLengthFeet = wallsSection["maxLengthFeet"]?.Value<double>() ?? 100;
                            var thicknesses = wallsSection["validThicknessesInches"]?.ToObject<List<double>>();
                            if (thicknesses != null) rules.Walls.ValidThicknessesInches = thicknesses;
                        }

                        // Parse door rules
                        var doorsSection = rulesSection["doors"];
                        if (doorsSection != null)
                        {
                            rules.Doors.MinWidthInches = doorsSection["minWidthInches"]?.Value<double>() ?? 24;
                            rules.Doors.MaxWidthInches = doorsSection["maxWidthInches"]?.Value<double>() ?? 48;
                            var widths = doorsSection["standardWidthsInches"]?.ToObject<List<double>>();
                            if (widths != null) rules.Doors.StandardWidthsInches = widths;
                            rules.Doors.MinHeightInches = doorsSection["minHeightInches"]?.Value<double>() ?? 78;
                            rules.Doors.MaxHeightInches = doorsSection["maxHeightInches"]?.Value<double>() ?? 96;
                        }

                        // Parse window rules
                        var windowsSection = rulesSection["windows"];
                        if (windowsSection != null)
                        {
                            rules.Windows.MinWidthInches = windowsSection["minWidthInches"]?.Value<double>() ?? 12;
                            rules.Windows.MaxWidthInches = windowsSection["maxWidthInches"]?.Value<double>() ?? 120;
                            rules.Windows.MinHeightInches = windowsSection["minHeightInches"]?.Value<double>() ?? 12;
                            rules.Windows.MinSillHeightInches = windowsSection["minSillHeightInches"]?.Value<double>() ?? 18;
                        }

                        // Parse room rules
                        var roomsSection = rulesSection["rooms"];
                        if (roomsSection != null)
                        {
                            rules.Rooms.MinAreaSqft = roomsSection["minAreaSqft"]?.Value<double>() ?? 25;
                            rules.Rooms.MinDimensionFeet = roomsSection["minDimensionFeet"]?.Value<double>() ?? 4;
                            rules.Rooms.BathroomMinSqft = roomsSection["bathroomMinSqft"]?.Value<double>() ?? 35;
                            rules.Rooms.BedroomMinSqft = roomsSection["bedroomMinSqft"]?.Value<double>() ?? 70;
                            rules.Rooms.KitchenMinSqft = roomsSection["kitchenMinSqft"]?.Value<double>() ?? 50;
                        }
                    }
                }

                Log.Information("[CIPS] Configuration loaded. Enabled: {Enabled}, HighThreshold: {High}",
                    Enabled, Thresholds.High);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "[CIPS] Error loading configuration, using defaults");
            }
        }

        /// <summary>
        /// Reload configuration (for runtime changes)
        /// </summary>
        public void Reload()
        {
            Load();
        }
    }

    /// <summary>
    /// Default threshold settings
    /// </summary>
    public class ThresholdSettings
    {
        public double High { get; set; } = 0.85;
        public double Medium { get; set; } = 0.60;
        public double Low { get; set; } = 0.40;
    }

    /// <summary>
    /// Per-operation threshold override
    /// </summary>
    public class OperationThreshold
    {
        public double? High { get; set; }
        public double? Medium { get; set; }
        public double? Low { get; set; }
    }

    /// <summary>
    /// Multi-pass processing settings
    /// </summary>
    public class MultiPassSettings
    {
        public int MaxPasses { get; set; } = 3;
        public double ContextBoostPerPass { get; set; } = 0.10;
    }

    /// <summary>
    /// Review queue settings
    /// </summary>
    public class ReviewQueueSettings
    {
        public string Path { get; set; }
        public int MaxSize { get; set; } = 100;
        public int ExpireHours { get; set; } = 24;
    }

    /// <summary>
    /// Feedback learning settings
    /// </summary>
    public class FeedbackSettings
    {
        public int MinSamplesToLearn { get; set; } = 5;
        public double MaxAdjustment { get; set; } = 0.15;
    }
}
