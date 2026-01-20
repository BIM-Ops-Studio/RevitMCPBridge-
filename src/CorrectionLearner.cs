using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge
{
    /// <summary>
    /// Learns from corrections to avoid repeating mistakes.
    /// Stores corrections locally and uses them to improve future responses.
    /// </summary>
    public class CorrectionLearner
    {
        private readonly string _correctionsFile;
        private List<Correction> _corrections;
        private const int MaxCorrections = 100;

        public CorrectionLearner()
        {
            // Store corrections in a local file
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var bimOpsDir = Path.Combine(appData, "BIMOpsStudio");
            Directory.CreateDirectory(bimOpsDir);
            _correctionsFile = Path.Combine(bimOpsDir, "corrections.json");

            LoadCorrections();
        }

        /// <summary>
        /// Store a correction when something went wrong
        /// </summary>
        public void StoreCorrection(string whatWasAttempted, string whatWentWrong,
            string correctApproach, string category = "general")
        {
            var correction = new Correction
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Timestamp = DateTime.Now,
                WhatWasAttempted = whatWasAttempted,
                WhatWentWrong = whatWentWrong,
                CorrectApproach = correctApproach,
                Category = category,
                TimesApplied = 0
            };

            _corrections.Add(correction);

            // Keep only the most recent corrections
            if (_corrections.Count > MaxCorrections)
            {
                _corrections = _corrections
                    .OrderByDescending(c => c.Timestamp)
                    .Take(MaxCorrections)
                    .ToList();
            }

            SaveCorrections();
        }

        /// <summary>
        /// Store a correction from verification failure
        /// </summary>
        public void StoreFromVerification(VerificationResult verification,
            string method, JObject parameters)
        {
            if (verification == null || verification.Verified) return;

            var correction = new Correction
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Timestamp = DateTime.Now,
                WhatWasAttempted = $"Called {method} with parameters: {parameters?.ToString(Formatting.None) ?? "none"}",
                WhatWentWrong = verification.Message,
                CorrectApproach = DetermineCorrectApproach(method, verification),
                Category = "verification_failure",
                Method = method,
                TimesApplied = 0
            };

            // Avoid duplicate corrections for same method/issue
            if (!_corrections.Any(c => c.Method == method &&
                c.WhatWentWrong.Contains(verification.Message.Split('.').FirstOrDefault() ?? "")))
            {
                _corrections.Add(correction);
                SaveCorrections();
            }
        }

        /// <summary>
        /// Get relevant corrections for a given input
        /// </summary>
        public List<Correction> GetRelevantCorrections(string userInput, int limit = 5)
        {
            var inputLower = userInput.ToLower();
            var keywords = inputLower.Split(new[] { ' ', ',', '.' }, StringSplitOptions.RemoveEmptyEntries);

            // Score corrections by relevance
            var scored = _corrections
                .Select(c => new
                {
                    Correction = c,
                    Score = CalculateRelevanceScore(c, keywords)
                })
                .Where(x => x.Score > 0)
                .OrderByDescending(x => x.Score)
                .ThenByDescending(x => x.Correction.Timestamp)
                .Take(limit)
                .Select(x => x.Correction)
                .ToList();

            return scored;
        }

        /// <summary>
        /// Get corrections formatted as knowledge for the local model
        /// </summary>
        public string GetCorrectionsAsKnowledge()
        {
            if (!_corrections.Any()) return "";

            var recent = _corrections
                .OrderByDescending(c => c.Timestamp)
                .Take(10)
                .ToList();

            var knowledge = "PAST CORRECTIONS TO REMEMBER:\n";
            foreach (var c in recent)
            {
                knowledge += $"- When attempting: {c.WhatWasAttempted}\n";
                knowledge += $"  Problem: {c.WhatWentWrong}\n";
                knowledge += $"  Solution: {c.CorrectApproach}\n\n";
            }

            return knowledge;
        }

        /// <summary>
        /// Get method-specific corrections
        /// </summary>
        public List<Correction> GetMethodCorrections(string method)
        {
            return _corrections
                .Where(c => string.Equals(c.Method, method, StringComparison.OrdinalIgnoreCase))
                .OrderByDescending(c => c.Timestamp)
                .ToList();
        }

        /// <summary>
        /// Mark a correction as applied (increases its priority for future use)
        /// </summary>
        public void MarkCorrectionApplied(string correctionId)
        {
            var correction = _corrections.FirstOrDefault(c => c.Id == correctionId);
            if (correction != null)
            {
                correction.TimesApplied++;
                correction.LastApplied = DateTime.Now;
                SaveCorrections();
            }
        }

        /// <summary>
        /// Delete a correction (if user says it's wrong)
        /// </summary>
        public void DeleteCorrection(string correctionId)
        {
            _corrections.RemoveAll(c => c.Id == correctionId);
            SaveCorrections();
        }

        /// <summary>
        /// Get statistics about corrections
        /// </summary>
        public CorrectionStats GetStats()
        {
            return new CorrectionStats
            {
                TotalCorrections = _corrections.Count,
                CategoriesCount = _corrections.Select(c => c.Category).Distinct().Count(),
                MostCommonCategory = _corrections
                    .GroupBy(c => c.Category)
                    .OrderByDescending(g => g.Count())
                    .FirstOrDefault()?.Key ?? "none",
                RecentCorrections = _corrections
                    .Where(c => c.Timestamp > DateTime.Now.AddDays(-7))
                    .Count(),
                TotalTimesApplied = _corrections.Sum(c => c.TimesApplied)
            };
        }

        #region Private Methods

        private void LoadCorrections()
        {
            _corrections = new List<Correction>();

            if (File.Exists(_correctionsFile))
            {
                try
                {
                    var json = File.ReadAllText(_correctionsFile);
                    _corrections = JsonConvert.DeserializeObject<List<Correction>>(json) ?? new List<Correction>();
                }
                catch
                {
                    // If file is corrupted, start fresh
                    _corrections = new List<Correction>();
                }
            }
        }

        private void SaveCorrections()
        {
            try
            {
                var json = JsonConvert.SerializeObject(_corrections, Formatting.Indented);
                File.WriteAllText(_correctionsFile, json);
            }
            catch
            {
                // Silently fail on write errors
            }
        }

        private double CalculateRelevanceScore(Correction c, string[] keywords)
        {
            var textToSearch = $"{c.WhatWasAttempted} {c.WhatWentWrong} {c.CorrectApproach} {c.Method}".ToLower();
            double score = 0;

            foreach (var keyword in keywords)
            {
                if (textToSearch.Contains(keyword))
                {
                    score += 1;
                    // Bonus for method name match
                    if (c.Method?.ToLower().Contains(keyword) == true)
                        score += 2;
                }
            }

            // Bonus for recent corrections
            if (c.Timestamp > DateTime.Now.AddDays(-1))
                score *= 1.5;
            else if (c.Timestamp > DateTime.Now.AddDays(-7))
                score *= 1.2;

            // Bonus for frequently applied corrections
            score += c.TimesApplied * 0.5;

            return score;
        }

        private string DetermineCorrectApproach(string method, VerificationResult verification)
        {
            // Based on method and verification message, suggest fix
            if (verification.Message.Contains("not found"))
            {
                return $"Verify element exists before {method}, or check element ID is correct";
            }
            if (verification.Message.Contains("no ID"))
            {
                return "Check that the operation completed and returned an element ID";
            }
            if (verification.Message.Contains("still exists"))
            {
                return "Deletion may have failed - check if element is locked or in use";
            }

            return "Review the operation parameters and try again with verified inputs";
        }

        #endregion
    }

    /// <summary>
    /// A stored correction
    /// </summary>
    public class Correction
    {
        public string Id { get; set; }
        public DateTime Timestamp { get; set; }
        public string WhatWasAttempted { get; set; }
        public string WhatWentWrong { get; set; }
        public string CorrectApproach { get; set; }
        public string Category { get; set; }
        public string Method { get; set; }
        public int TimesApplied { get; set; }
        public DateTime? LastApplied { get; set; }
    }

    /// <summary>
    /// Statistics about corrections
    /// </summary>
    public class CorrectionStats
    {
        public int TotalCorrections { get; set; }
        public int CategoriesCount { get; set; }
        public string MostCommonCategory { get; set; }
        public int RecentCorrections { get; set; }
        public int TotalTimesApplied { get; set; }
    }
}
