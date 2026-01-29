using System;
using System.IO;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Serilog;

namespace RevitMCPBridge
{
    /// <summary>
    /// Configuration settings for RevitMCPBridge
    /// </summary>
    public class AppSettings
    {
        private static AppSettings _instance;
        private static readonly object _lock = new object();
        private JObject _settings;
        private DateTime _lastLoaded;
        private readonly string _configPath;

        public static AppSettings Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new AppSettings();
                        }
                    }
                }
                return _instance;
            }
        }

        private AppSettings()
        {
            // Look for config in multiple locations
            var assemblyDir = Path.GetDirectoryName(typeof(AppSettings).Assembly.Location);
            var possiblePaths = new[]
            {
                Path.Combine(assemblyDir, "config", "appsettings.json"),
                Path.Combine(assemblyDir, "appsettings.json"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "RevitMCPBridge", "appsettings.json")
            };

            foreach (var path in possiblePaths)
            {
                if (File.Exists(path))
                {
                    _configPath = path;
                    break;
                }
            }

            LoadSettings();
        }

        private void LoadSettings()
        {
            try
            {
                if (!string.IsNullOrEmpty(_configPath) && File.Exists(_configPath))
                {
                    var json = File.ReadAllText(_configPath);
                    _settings = JObject.Parse(json);
                    _lastLoaded = DateTime.Now;
                    Log.Information("Configuration loaded from {Path}", _configPath);
                }
                else
                {
                    // Use defaults
                    _settings = GetDefaultSettings();
                    Log.Warning("No configuration file found, using defaults");
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error loading configuration, using defaults");
                _settings = GetDefaultSettings();
            }
        }

        private JObject GetDefaultSettings()
        {
            return JObject.Parse(@"{
                'pipeName': 'RevitMCPBridge2026',
                'logging': {
                    'level': 'Information',
                    'retentionDays': 7
                },
                'autonomy': {
                    'maxElementsPerBatch': 100,
                    'requireApprovalThreshold': 50,
                    'enableSelfHealing': true,
                    'enableCorrectionLearning': true,
                    'maxRetries': 3
                },
                'performance': {
                    'batchSize': 50,
                    'timeoutMs': 30000,
                    'maxConcurrentConnections': 5
                },
                'validation': {
                    'validateCoordinates': true,
                    'warnOnLargeOperations': true,
                    'largeOperationThreshold': 100
                },
                'features': {
                    'enableSketchPad': true,
                    'enableDialogHandler': true,
                    'enableViewportCapture': true,
                    'enableAIRender': false
                }
            }");
        }

        /// <summary>
        /// Reload settings from disk
        /// </summary>
        public void Reload()
        {
            lock (_lock)
            {
                LoadSettings();
            }
        }

        /// <summary>
        /// Get a setting value by path (e.g., "logging.level")
        /// </summary>
        public T Get<T>(string path, T defaultValue = default)
        {
            try
            {
                var token = _settings.SelectToken(path);
                if (token == null) return defaultValue;
                return token.ToObject<T>();
            }
            catch
            {
                return defaultValue;
            }
        }

        // Convenience properties
        public string PipeName => Get("pipeName", "RevitMCPBridge2026");
        public string LogLevel => Get("logging.level", "Information");
        public int LogRetentionDays => Get("logging.retentionDays", 7);

        public int MaxElementsPerBatch => Get("autonomy.maxElementsPerBatch", 100);
        public int ApprovalThreshold => Get("autonomy.requireApprovalThreshold", 50);
        public bool EnableSelfHealing => Get("autonomy.enableSelfHealing", true);
        public bool EnableCorrectionLearning => Get("autonomy.enableCorrectionLearning", true);
        public int MaxRetries => Get("autonomy.maxRetries", 3);

        public int BatchSize => Get("performance.batchSize", 50);
        public int TimeoutMs => Get("performance.timeoutMs", 30000);
        public int MaxConcurrentConnections => Get("performance.maxConcurrentConnections", 5);

        public bool ValidateCoordinates => Get("validation.validateCoordinates", true);
        public bool WarnOnLargeOperations => Get("validation.warnOnLargeOperations", true);
        public int LargeOperationThreshold => Get("validation.largeOperationThreshold", 100);

        public bool EnableSketchPad => Get("features.enableSketchPad", true);
        public bool EnableDialogHandler => Get("features.enableDialogHandler", true);
        public bool EnableViewportCapture => Get("features.enableViewportCapture", true);
        public bool EnableAIRender => Get("features.enableAIRender", false);

        /// <summary>
        /// Get configuration status for MCP endpoint
        /// </summary>
        public object GetStatus()
        {
            return new
            {
                configPath = _configPath ?? "using defaults",
                lastLoaded = _lastLoaded,
                pipeName = PipeName,
                logLevel = LogLevel,
                maxElementsPerBatch = MaxElementsPerBatch,
                enableSelfHealing = EnableSelfHealing,
                timeoutMs = TimeoutMs
            };
        }
    }
}
