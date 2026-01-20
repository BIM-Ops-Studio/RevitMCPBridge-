using System;
using System.IO;
using Newtonsoft.Json;
using Serilog;

namespace RevitMCPBridge.Configuration
{
    /// <summary>
    /// Configuration manager for RevitMCPBridge.
    /// Loads settings from appsettings.json with fallback defaults.
    /// </summary>
    public class BridgeConfiguration
    {
        private static BridgeConfiguration _instance;
        private static readonly object _lock = new object();

        /// <summary>
        /// Singleton instance of the configuration
        /// </summary>
        public static BridgeConfiguration Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = Load();
                        }
                    }
                }
                return _instance;
            }
        }

        #region Configuration Properties

        /// <summary>
        /// Named pipe settings
        /// </summary>
        public PipeSettings Pipe { get; set; } = new PipeSettings();

        /// <summary>
        /// Logging settings
        /// </summary>
        public LoggingSettings Logging { get; set; } = new LoggingSettings();

        /// <summary>
        /// Autonomy settings (Level 5)
        /// </summary>
        public AutonomySettings Autonomy { get; set; } = new AutonomySettings();

        /// <summary>
        /// AI/MCP settings
        /// </summary>
        public AISettings AI { get; set; } = new AISettings();

        /// <summary>
        /// Performance settings
        /// </summary>
        public PerformanceSettings Performance { get; set; } = new PerformanceSettings();

        /// <summary>
        /// Version information
        /// </summary>
        public VersionInfo Version { get; set; } = new VersionInfo();

        #endregion

        #region Settings Classes

        public class PipeSettings
        {
            public string Name { get; set; } = "RevitMCPBridge2026";
            public int TimeoutMs { get; set; } = 30000;
            public int MaxConnections { get; set; } = 10;
            public int BufferSize { get; set; } = 65536;
        }

        public class LoggingSettings
        {
            public string Level { get; set; } = "Information";
            public string LogDirectory { get; set; } = null; // null = use default
            public int RetainedFileDays { get; set; } = 7;
            public bool IncludeStackTraces { get; set; } = true;
            public bool LogMethodCalls { get; set; } = true;
        }

        public class AutonomySettings
        {
            public bool Enabled { get; set; } = true;
            public int MaxRetries { get; set; } = 3;
            public int MaxElementsPerBatch { get; set; } = 100;
            public int MaxDeletionsPerBatch { get; set; } = 20;
            public bool RequireConfirmation { get; set; } = true;
            public string[] ProtectedElementTypes { get; set; } = new[] { "Grid", "Level", "SharedParameter" };
        }

        public class AISettings
        {
            public bool EnableLearning { get; set; } = true;
            public bool StoreCorrections { get; set; } = true;
            public string CorrectionsPath { get; set; } = null; // null = use default
            public bool EnableProactiveAssistance { get; set; } = true;
        }

        public class PerformanceSettings
        {
            public int TransactionBatchSize { get; set; } = 50;
            public bool EnableCaching { get; set; } = true;
            public int CacheExpirationMinutes { get; set; } = 5;
            public bool ParallelProcessing { get; set; } = false; // Revit is single-threaded
        }

        public class VersionInfo
        {
            public string Major { get; set; } = "2";
            public string Minor { get; set; } = "0";
            public string Patch { get; set; } = "0";
            public string BuildDate { get; set; } = DateTime.Now.ToString("yyyy-MM-dd");
            public string RevitVersion { get; set; } = "2026";

            public string FullVersion => $"{Major}.{Minor}.{Patch}";
            public string DisplayVersion => $"RevitMCPBridge {FullVersion} for Revit {RevitVersion}";
        }

        #endregion

        #region Load/Save

        private static string ConfigPath
        {
            get
            {
                // Look for config in add-in directory first
                var addinPath = Path.GetDirectoryName(typeof(BridgeConfiguration).Assembly.Location);
                var configPath = Path.Combine(addinPath, "appsettings.json");

                if (File.Exists(configPath))
                    return configPath;

                // Fallback to user's roaming folder
                var roamingPath = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "RevitMCPBridge",
                    "appsettings.json");

                return roamingPath;
            }
        }

        private static BridgeConfiguration Load()
        {
            try
            {
                if (File.Exists(ConfigPath))
                {
                    var json = File.ReadAllText(ConfigPath);
                    var config = JsonConvert.DeserializeObject<BridgeConfiguration>(json);
                    Log.Information("Configuration loaded from {Path}", ConfigPath);
                    return config ?? new BridgeConfiguration();
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Failed to load configuration from {Path}, using defaults", ConfigPath);
            }

            // Return defaults
            return new BridgeConfiguration();
        }

        /// <summary>
        /// Reload configuration from disk
        /// </summary>
        public static void Reload()
        {
            lock (_lock)
            {
                _instance = Load();
            }
        }

        /// <summary>
        /// Save current configuration to disk
        /// </summary>
        public void Save()
        {
            try
            {
                var directory = Path.GetDirectoryName(ConfigPath);
                if (!Directory.Exists(directory))
                    Directory.CreateDirectory(directory);

                var json = JsonConvert.SerializeObject(this, Formatting.Indented);
                File.WriteAllText(ConfigPath, json);
                Log.Information("Configuration saved to {Path}", ConfigPath);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to save configuration to {Path}", ConfigPath);
            }
        }

        /// <summary>
        /// Create a default configuration file
        /// </summary>
        public static void CreateDefault(string path = null)
        {
            var config = new BridgeConfiguration();
            var targetPath = path ?? ConfigPath;

            var directory = Path.GetDirectoryName(targetPath);
            if (!Directory.Exists(directory))
                Directory.CreateDirectory(directory);

            var json = JsonConvert.SerializeObject(config, Formatting.Indented);
            File.WriteAllText(targetPath, json);
        }

        #endregion

        #region Helpers

        /// <summary>
        /// Get the log directory, using default if not specified
        /// </summary>
        public string GetLogDirectory()
        {
            if (!string.IsNullOrEmpty(Logging.LogDirectory))
                return Logging.LogDirectory;

            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "RevitMCPBridge",
                "Logs");
        }

        /// <summary>
        /// Get the corrections storage path
        /// </summary>
        public string GetCorrectionsPath()
        {
            if (!string.IsNullOrEmpty(AI.CorrectionsPath))
                return AI.CorrectionsPath;

            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "RevitMCPBridge",
                "corrections.json");
        }

        /// <summary>
        /// Get the full pipe name with prefix
        /// </summary>
        public string GetFullPipeName()
        {
            return $"\\\\.\\pipe\\{Pipe.Name}";
        }

        #endregion
    }
}
