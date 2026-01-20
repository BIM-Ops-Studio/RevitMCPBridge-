using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge
{
    /// <summary>
    /// Plans multi-step workflows and manages project-specific context.
    /// Breaks down complex requests into actionable steps.
    /// </summary>
    public class WorkflowPlanner
    {
        private readonly string _projectContextFile;
        private ProjectContext _currentProject;
        private List<WorkflowStep> _currentPlan;
        private int _currentStepIndex;

        // Common multi-step workflow templates
        private readonly Dictionary<string, List<string>> _workflowTemplates;

        public WorkflowPlanner()
        {
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var bimOpsDir = Path.Combine(appData, "BIMOpsStudio");
            Directory.CreateDirectory(bimOpsDir);
            _projectContextFile = Path.Combine(bimOpsDir, "project_context.json");

            _currentPlan = new List<WorkflowStep>();
            _currentStepIndex = 0;

            // Initialize workflow templates
            _workflowTemplates = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase)
            {
                // Sheet workflows
                ["create sheet set"] = new List<string>
                {
                    "createSheet", // Create first sheet
                    "duplicateSheet", // Duplicate for additional sheets
                    "placeViewOnSheet" // Place views
                },
                ["add view to sheet"] = new List<string>
                {
                    "findEmptySpaceOnSheet", // Find good location
                    "placeViewOnSheet" // Place the view
                },

                // Room workflows
                ["set up rooms"] = new List<string>
                {
                    "getRooms", // Get existing rooms
                    "createRoom", // Create new rooms if needed
                    "tagRoom" // Tag the rooms
                },

                // Wall workflows
                ["create walls from sketch"] = new List<string>
                {
                    "createWall", // Create first wall
                    "createWall", // Continue creating walls
                    "joinWalls" // Join walls at corners
                },

                // Annotation workflows
                ["annotate floor plan"] = new List<string>
                {
                    "tagRooms", // Tag all rooms
                    "placeKeynotes", // Add keynotes
                    "placeTextNote" // Add notes
                },

                // Documentation workflows
                ["create cd set"] = new List<string>
                {
                    "createSheet", // Cover sheet
                    "createSheet", // Floor plans
                    "createSheet", // Sections/elevations
                    "placeViewOnSheet" // Place views
                }
            };

            LoadProjectContext();
        }

        #region Workflow Planning

        /// <summary>
        /// Analyze a user request and create a multi-step plan if needed
        /// </summary>
        public WorkflowPlan AnalyzeRequest(string userRequest)
        {
            var requestLower = userRequest.ToLower();

            // Check for template matches
            foreach (var template in _workflowTemplates)
            {
                if (requestLower.Contains(template.Key))
                {
                    return CreatePlanFromTemplate(template.Key, template.Value, userRequest);
                }
            }

            // Check for compound requests (keywords that suggest multiple steps)
            var compoundKeywords = new[] { "and then", "after that", "also", "next", "then" };
            if (compoundKeywords.Any(k => requestLower.Contains(k)))
            {
                return ParseCompoundRequest(userRequest);
            }

            // Check for quantity indicators (multiple elements)
            if (System.Text.RegularExpressions.Regex.IsMatch(requestLower, @"\b(\d+|several|multiple|many|all)\b"))
            {
                return CreateBatchPlan(userRequest);
            }

            // Simple single-step request
            return new WorkflowPlan
            {
                IsMultiStep = false,
                OriginalRequest = userRequest,
                Steps = new List<WorkflowStep>
                {
                    new WorkflowStep { StepNumber = 1, Description = userRequest, Status = StepStatus.Pending }
                }
            };
        }

        private WorkflowPlan CreatePlanFromTemplate(string templateName, List<string> methods, string originalRequest)
        {
            var plan = new WorkflowPlan
            {
                IsMultiStep = true,
                OriginalRequest = originalRequest,
                TemplateName = templateName,
                Steps = methods.Select((m, i) => new WorkflowStep
                {
                    StepNumber = i + 1,
                    Method = m,
                    Description = $"Step {i + 1}: {GetMethodDescription(m)}",
                    Status = StepStatus.Pending
                }).ToList()
            };

            return plan;
        }

        private WorkflowPlan ParseCompoundRequest(string request)
        {
            // Split on compound keywords
            var parts = System.Text.RegularExpressions.Regex.Split(request,
                @"\b(and then|after that|also|next|then)\b",
                System.Text.RegularExpressions.RegexOptions.IgnoreCase)
                .Where(p => !string.IsNullOrWhiteSpace(p))
                .Where(p => !new[] { "and then", "after that", "also", "next", "then" }
                    .Contains(p.Trim().ToLower()))
                .ToList();

            var plan = new WorkflowPlan
            {
                IsMultiStep = parts.Count > 1,
                OriginalRequest = request,
                Steps = parts.Select((p, i) => new WorkflowStep
                {
                    StepNumber = i + 1,
                    Description = p.Trim(),
                    Status = StepStatus.Pending
                }).ToList()
            };

            return plan;
        }

        private WorkflowPlan CreateBatchPlan(string request)
        {
            // For batch operations, create a single step with batch flag
            return new WorkflowPlan
            {
                IsMultiStep = false,
                IsBatchOperation = true,
                OriginalRequest = request,
                Steps = new List<WorkflowStep>
                {
                    new WorkflowStep
                    {
                        StepNumber = 1,
                        Description = request,
                        Status = StepStatus.Pending,
                        IsBatch = true
                    }
                }
            };
        }

        private string GetMethodDescription(string method)
        {
            var descriptions = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
            {
                ["createSheet"] = "Create a new sheet",
                ["duplicateSheet"] = "Duplicate an existing sheet",
                ["placeViewOnSheet"] = "Place a view on the sheet",
                ["getRooms"] = "Get existing rooms",
                ["createRoom"] = "Create a new room",
                ["tagRoom"] = "Tag the room",
                ["createWall"] = "Create a wall",
                ["joinWalls"] = "Join walls at corners",
                ["tagRooms"] = "Tag all rooms",
                ["placeKeynotes"] = "Add keynotes",
                ["placeTextNote"] = "Add text annotations",
                ["findEmptySpaceOnSheet"] = "Find available space on sheet"
            };

            return descriptions.TryGetValue(method, out var desc) ? desc : method;
        }

        /// <summary>
        /// Mark current step as complete and get next step
        /// </summary>
        public WorkflowStep CompleteCurrentStep(bool success)
        {
            if (_currentStepIndex < _currentPlan.Count)
            {
                _currentPlan[_currentStepIndex].Status = success ? StepStatus.Completed : StepStatus.Failed;
                _currentStepIndex++;
            }

            return GetCurrentStep();
        }

        /// <summary>
        /// Get the current step in the workflow
        /// </summary>
        public WorkflowStep GetCurrentStep()
        {
            if (_currentStepIndex < _currentPlan.Count)
            {
                return _currentPlan[_currentStepIndex];
            }
            return null;
        }

        /// <summary>
        /// Get progress as formatted string
        /// </summary>
        public string GetProgressSummary()
        {
            if (_currentPlan.Count == 0) return "No active workflow";

            var completed = _currentPlan.Count(s => s.Status == StepStatus.Completed);
            var failed = _currentPlan.Count(s => s.Status == StepStatus.Failed);
            var total = _currentPlan.Count;

            return $"Progress: {completed}/{total} steps complete" +
                   (failed > 0 ? $" ({failed} failed)" : "");
        }

        /// <summary>
        /// Get available workflow templates
        /// </summary>
        public Dictionary<string, List<string>> GetAvailableTemplates()
        {
            return _workflowTemplates;
        }

        #endregion

        #region Project Context

        /// <summary>
        /// Set project context for workflow planning (simplified version)
        /// </summary>
        public void SetProjectContext(string projectName, string projectType, string clientFirm)
        {
            _currentProject = new ProjectContext
            {
                ProjectName = projectName,
                ProjectType = projectType ?? "General",
                ClientFirm = clientFirm,
                LastAccessed = DateTime.Now
            };

            // Set relevant knowledge based on type
            SetRelevantKnowledge(projectType);
            SaveProjectContext();
        }

        /// <summary>
        /// Get current project context
        /// </summary>
        public ProjectContext GetProjectContext()
        {
            return _currentProject;
        }

        private void SetRelevantKnowledge(string projectType)
        {
            if (_currentProject == null || string.IsNullOrEmpty(projectType)) return;

            var typeLower = projectType.ToLower();

            if (typeLower.Contains("residential") || typeLower.Contains("single"))
            {
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "single-family-residential.md",
                    "florida-residential-code.md",
                    "kitchen-bath-design.md"
                };
            }
            else if (typeLower.Contains("multi") || typeLower.Contains("apartment"))
            {
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "multi-family-design.md",
                    "florida-building-code-egress.md",
                    "accessibility-detailed.md"
                };
            }
            else if (typeLower.Contains("office") || typeLower.Contains("commercial"))
            {
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "office-design.md",
                    "code-compliance.md",
                    "egress-design.md"
                };
            }
            else
            {
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "code-compliance.md",
                    "room-standards.md"
                };
            }
        }

        /// <summary>
        /// Detect and load project context from Revit project info
        /// </summary>
        public void UpdateProjectContext(string projectName, string projectNumber, string projectPath)
        {
            _currentProject = new ProjectContext
            {
                ProjectName = projectName,
                ProjectNumber = projectNumber,
                ProjectPath = projectPath,
                LastAccessed = DateTime.Now
            };

            // Detect project type and load relevant knowledge
            DetectProjectType(projectName);

            SaveProjectContext();
        }

        private void DetectProjectType(string projectName)
        {
            if (_currentProject == null) return;

            var nameLower = projectName?.ToLower() ?? "";

            // Detect project type from name
            if (nameLower.Contains("residence") || nameLower.Contains("house") ||
                nameLower.Contains("home") || nameLower.Contains("sfr"))
            {
                _currentProject.ProjectType = "Residential - Single Family";
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "single-family-residential.md",
                    "florida-residential-code.md",
                    "kitchen-bath-design.md"
                };
            }
            else if (nameLower.Contains("multi") || nameLower.Contains("apartment") ||
                     nameLower.Contains("condo"))
            {
                _currentProject.ProjectType = "Residential - Multi-Family";
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "multi-family-design.md",
                    "florida-building-code-egress.md",
                    "accessibility-detailed.md"
                };
            }
            else if (nameLower.Contains("office") || nameLower.Contains("commercial"))
            {
                _currentProject.ProjectType = "Commercial - Office";
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "office-design.md",
                    "code-compliance.md",
                    "egress-design.md"
                };
            }
            else if (nameLower.Contains("retail") || nameLower.Contains("store"))
            {
                _currentProject.ProjectType = "Commercial - Retail";
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "retail-design.md",
                    "accessibility-detailed.md"
                };
            }
            else
            {
                _currentProject.ProjectType = "General";
                _currentProject.RelevantKnowledge = new List<string>
                {
                    "code-compliance.md",
                    "room-standards.md"
                };
            }
        }

        /// <summary>
        /// Get current project context as knowledge for local model
        /// </summary>
        public string GetProjectContextAsKnowledge()
        {
            if (_currentProject == null) return "";

            var knowledge = $"CURRENT PROJECT CONTEXT:\n";
            knowledge += $"- Project: {_currentProject.ProjectName}\n";
            knowledge += $"- Type: {_currentProject.ProjectType}\n";

            if (_currentProject.RelevantKnowledge?.Any() == true)
            {
                knowledge += $"- Relevant knowledge files: {string.Join(", ", _currentProject.RelevantKnowledge)}\n";
            }

            return knowledge;
        }

        /// <summary>
        /// Get list of relevant knowledge files for current project
        /// </summary>
        public List<string> GetRelevantKnowledgeFiles()
        {
            return _currentProject?.RelevantKnowledge ?? new List<string>();
        }

        private void LoadProjectContext()
        {
            if (File.Exists(_projectContextFile))
            {
                try
                {
                    var json = File.ReadAllText(_projectContextFile);
                    _currentProject = JsonConvert.DeserializeObject<ProjectContext>(json);
                }
                catch
                {
                    _currentProject = null;
                }
            }
        }

        private void SaveProjectContext()
        {
            try
            {
                var json = JsonConvert.SerializeObject(_currentProject, Formatting.Indented);
                File.WriteAllText(_projectContextFile, json);
            }
            catch { }
        }

        #endregion
    }

    #region Data Classes

    public class WorkflowPlan
    {
        public bool IsMultiStep { get; set; }
        public bool IsBatchOperation { get; set; }
        public string OriginalRequest { get; set; }
        public string TemplateName { get; set; }
        public bool TemplateMatched => !string.IsNullOrEmpty(TemplateName);
        public List<WorkflowStep> Steps { get; set; } = new List<WorkflowStep>();
    }

    public class WorkflowStep
    {
        public int StepNumber { get; set; }
        public string Method { get; set; }
        public string Description { get; set; }
        public StepStatus Status { get; set; }
        public bool IsBatch { get; set; }
        public bool DependsOnPreviousStep { get; set; }
        public JObject Parameters { get; set; }
        public string Result { get; set; }
    }

    public enum StepStatus
    {
        Pending,
        InProgress,
        Completed,
        Failed,
        Skipped
    }

    public class ProjectContext
    {
        public string ProjectName { get; set; }
        public string ProjectNumber { get; set; }
        public string ProjectPath { get; set; }
        public string ProjectType { get; set; }
        public string ClientFirm { get; set; }
        public List<string> RelevantKnowledge { get; set; }
        public DateTime LastAccessed { get; set; }
    }

    #endregion
}
