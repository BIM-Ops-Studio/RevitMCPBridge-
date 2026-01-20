using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Serilog;

namespace RevitMCPBridge
{
    /// <summary>
    /// Level 5 Intelligence: Autonomous Executor
    /// Enables goal-directed execution with self-healing, bounded autonomy,
    /// and quality self-assessment.
    /// </summary>
    public class AutonomousExecutor
    {
        private static AutonomousExecutor _instance;
        private static readonly object _lock = new object();

        // Execution state
        private readonly List<AutonomousTask> _activeTasks = new List<AutonomousTask>();
        private readonly Dictionary<string, ExecutionResult> _taskResults = new Dictionary<string, ExecutionResult>();
        private readonly List<ExecutionLog> _executionHistory = new List<ExecutionLog>();

        // Components
        private readonly GoalPlanner _planner;
        private readonly SelfHealer _healer;
        private readonly GuardrailSystem _guardrails;
        private readonly QualityAssessor _assessor;

        // Configuration
        private int _maxRetries = 3;
        private int _maxConcurrentTasks = 1;
        private bool _requireApprovalForDestructive = true;

        public static AutonomousExecutor Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new AutonomousExecutor();
                        }
                    }
                }
                return _instance;
            }
        }

        private AutonomousExecutor()
        {
            _planner = new GoalPlanner();
            _healer = new SelfHealer();
            _guardrails = new GuardrailSystem();
            _assessor = new QualityAssessor();
        }

        #region Goal Execution

        /// <summary>
        /// Execute a high-level goal autonomously
        /// </summary>
        public async Task<ExecutionResult> ExecuteGoal(UIApplication uiApp, string goal, JObject context = null)
        {
            var taskId = Guid.NewGuid().ToString("N").Substring(0, 8);
            var task = new AutonomousTask
            {
                Id = taskId,
                Goal = goal,
                Context = context ?? new JObject(),
                Status = TaskStatus.Planning,
                StartTime = DateTime.Now
            };

            _activeTasks.Add(task);
            Log.Information("Starting autonomous execution of goal: {Goal} (Task: {TaskId})", goal, taskId);

            try
            {
                // Step 1: Plan - Break goal into steps
                task.Status = TaskStatus.Planning;
                var plan = _planner.CreatePlan(goal, context, uiApp);
                task.Plan = plan;

                if (plan.Steps.Count == 0)
                {
                    return CompleteTask(task, false, "Could not create execution plan for goal");
                }

                Log.Information("Created plan with {StepCount} steps for goal: {Goal}", plan.Steps.Count, goal);

                // Step 2: Validate - Check guardrails
                task.Status = TaskStatus.Validating;
                var validation = _guardrails.ValidatePlan(plan);
                if (!validation.IsValid)
                {
                    if (validation.RequiresApproval)
                    {
                        task.Status = TaskStatus.AwaitingApproval;
                        task.PendingApprovalReason = validation.Reason;
                        return new ExecutionResult
                        {
                            TaskId = taskId,
                            Success = false,
                            Status = "awaiting_approval",
                            Message = validation.Reason,
                            Plan = plan
                        };
                    }
                    return CompleteTask(task, false, $"Plan validation failed: {validation.Reason}");
                }

                // Step 3: Execute - Run each step
                task.Status = TaskStatus.Executing;
                var executionResult = await ExecutePlan(uiApp, task, plan);

                // Step 4: Assess - Verify quality
                task.Status = TaskStatus.Assessing;
                var assessment = _assessor.AssessExecution(uiApp, goal, executionResult);
                task.Assessment = assessment;

                if (!assessment.MeetsGoal && assessment.CanRetry && task.RetryCount < _maxRetries)
                {
                    Log.Warning("Goal not fully met, attempting retry {Retry}/{Max}", task.RetryCount + 1, _maxRetries);
                    task.RetryCount++;

                    // Self-heal: Apply corrections and retry
                    var healedPlan = _healer.HealPlan(plan, executionResult, assessment);
                    if (healedPlan != null)
                    {
                        task.Plan = healedPlan;
                        return await ExecuteGoal(uiApp, goal, context);
                    }
                }

                return CompleteTask(task, assessment.MeetsGoal, assessment.Summary, executionResult);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error executing goal: {Goal}", goal);
                return CompleteTask(task, false, $"Execution error: {ex.Message}");
            }
        }

        /// <summary>
        /// Execute a plan step by step
        /// </summary>
        private async Task<PlanExecutionResult> ExecutePlan(UIApplication uiApp, AutonomousTask task, ExecutionPlan plan)
        {
            var result = new PlanExecutionResult
            {
                PlanId = plan.Id,
                StartTime = DateTime.Now,
                StepResults = new List<StepExecutionResult>()
            };

            foreach (var step in plan.Steps)
            {
                task.CurrentStep = step.StepNumber;
                Log.Information("Executing step {Step}/{Total}: {Description}",
                    step.StepNumber, plan.Steps.Count, step.Description);

                var stepResult = await ExecuteStep(uiApp, step, task);
                result.StepResults.Add(stepResult);

                // Log execution
                _executionHistory.Add(new ExecutionLog
                {
                    Timestamp = DateTime.Now,
                    TaskId = task.Id,
                    StepNumber = step.StepNumber,
                    Method = step.Method,
                    Success = stepResult.Success,
                    Duration = stepResult.Duration
                });

                if (!stepResult.Success)
                {
                    // Attempt self-healing
                    var healed = _healer.TryHealStep(uiApp, step, stepResult);
                    if (healed != null && healed.Success)
                    {
                        Log.Information("Self-healed step {Step} successfully", step.StepNumber);
                        stepResult = healed;
                        result.StepResults[result.StepResults.Count - 1] = healed;
                    }
                    else if (step.IsRequired)
                    {
                        Log.Error("Required step {Step} failed, aborting plan", step.StepNumber);
                        result.Success = false;
                        result.FailedAtStep = step.StepNumber;
                        result.EndTime = DateTime.Now;
                        return result;
                    }
                    else
                    {
                        Log.Warning("Optional step {Step} failed, continuing", step.StepNumber);
                    }
                }

                // Update context with results for subsequent steps
                if (stepResult.Success && stepResult.OutputData != null)
                {
                    foreach (var prop in stepResult.OutputData.Properties())
                    {
                        task.Context[prop.Name] = prop.Value;
                    }
                }
            }

            result.Success = true;
            result.EndTime = DateTime.Now;
            return result;
        }

        /// <summary>
        /// Execute a single step
        /// </summary>
#pragma warning disable CS1998 // Async method lacks await - designed for future async operations
        private async Task<StepExecutionResult> ExecuteStep(UIApplication uiApp, ExecutionStep step, AutonomousTask task)
#pragma warning restore CS1998
        {
            var startTime = DateTime.Now;
            var result = new StepExecutionResult
            {
                StepNumber = step.StepNumber,
                Method = step.Method,
                StartTime = startTime
            };

            try
            {
                // Resolve parameters (replace placeholders with context values)
                var resolvedParams = ResolveParameters(step.Parameters, task.Context);

                // Check guardrails for this specific method
                var methodCheck = _guardrails.CheckMethodExecution(step.Method, resolvedParams);
                if (!methodCheck.Allowed)
                {
                    result.Success = false;
                    result.Error = $"Guardrail blocked: {methodCheck.Reason}";
                    result.Duration = DateTime.Now - startTime;
                    return result;
                }

                // Execute the method
                var methodResult = MCPServer.ExecuteMethod(uiApp, step.Method, resolvedParams);
                var resultObj = JObject.Parse(methodResult);

                result.Success = resultObj["success"]?.Value<bool>() ?? false;
                result.RawResult = resultObj;
                result.Duration = DateTime.Now - startTime;

                if (result.Success)
                {
                    // Extract output data for context
                    result.OutputData = ExtractOutputData(step, resultObj);
                }
                else
                {
                    result.Error = resultObj["error"]?.ToString() ?? "Unknown error";
                }

                return result;
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.Error = ex.Message;
                result.Duration = DateTime.Now - startTime;
                return result;
            }
        }

        /// <summary>
        /// Resolve parameter placeholders with context values
        /// </summary>
        private JObject ResolveParameters(JObject parameters, JObject context)
        {
            if (parameters == null) return new JObject();

            var resolved = new JObject();
            foreach (var prop in parameters.Properties())
            {
                var value = prop.Value;

                // Check for placeholder pattern: {{contextKey}}
                if (value.Type == JTokenType.String)
                {
                    var strValue = value.ToString();
                    if (strValue.StartsWith("{{") && strValue.EndsWith("}}"))
                    {
                        var key = strValue.Substring(2, strValue.Length - 4);
                        if (context.ContainsKey(key))
                        {
                            resolved[prop.Name] = context[key];
                            continue;
                        }
                    }
                }

                resolved[prop.Name] = value;
            }

            return resolved;
        }

        /// <summary>
        /// Extract relevant output data from step result
        /// </summary>
        private JObject ExtractOutputData(ExecutionStep step, JObject result)
        {
            var output = new JObject();

            // Extract specified output mappings
            if (step.OutputMappings != null)
            {
                foreach (var mapping in step.OutputMappings)
                {
                    var token = result.SelectToken(mapping.Value);
                    if (token != null)
                    {
                        output[mapping.Key] = token;
                    }
                }
            }

            // Auto-extract common patterns
            if (result["elementId"] != null)
                output["lastElementId"] = result["elementId"];
            if (result["elementIds"] != null)
                output["lastElementIds"] = result["elementIds"];
            if (result["viewId"] != null)
                output["lastViewId"] = result["viewId"];
            if (result["sheetId"] != null)
                output["lastSheetId"] = result["sheetId"];

            return output;
        }

        private ExecutionResult CompleteTask(AutonomousTask task, bool success, string message, PlanExecutionResult planResult = null)
        {
            task.Status = success ? TaskStatus.Completed : TaskStatus.Failed;
            task.EndTime = DateTime.Now;

            var result = new ExecutionResult
            {
                TaskId = task.Id,
                Success = success,
                Status = task.Status.ToString().ToLower(),
                Message = message,
                Plan = task.Plan,
                PlanResult = planResult,
                Assessment = task.Assessment,
                Duration = task.EndTime - task.StartTime
            };

            _taskResults[task.Id] = result;
            _activeTasks.Remove(task);

            Log.Information("Task {TaskId} completed. Success: {Success}, Message: {Message}",
                task.Id, success, message);

            return result;
        }

        #endregion

        #region Task Management

        /// <summary>
        /// Approve a task that requires approval
        /// </summary>
        public async Task<ExecutionResult> ApproveTask(UIApplication uiApp, string taskId)
        {
            var task = _activeTasks.FirstOrDefault(t => t.Id == taskId);
            if (task == null)
            {
                return new ExecutionResult
                {
                    TaskId = taskId,
                    Success = false,
                    Message = "Task not found or already completed"
                };
            }

            if (task.Status != TaskStatus.AwaitingApproval)
            {
                return new ExecutionResult
                {
                    TaskId = taskId,
                    Success = false,
                    Message = $"Task is not awaiting approval (status: {task.Status})"
                };
            }

            Log.Information("Task {TaskId} approved, resuming execution", taskId);
            task.Status = TaskStatus.Executing;

            // Resume execution
            var executionResult = await ExecutePlan(uiApp, task, task.Plan);

            task.Status = TaskStatus.Assessing;
            var assessment = _assessor.AssessExecution(uiApp, task.Goal, executionResult);
            task.Assessment = assessment;

            return CompleteTask(task, assessment.MeetsGoal, assessment.Summary, executionResult);
        }

        /// <summary>
        /// Cancel an active task
        /// </summary>
        public bool CancelTask(string taskId)
        {
            var task = _activeTasks.FirstOrDefault(t => t.Id == taskId);
            if (task == null) return false;

            task.Status = TaskStatus.Cancelled;
            task.EndTime = DateTime.Now;
            _activeTasks.Remove(task);

            Log.Information("Task {TaskId} cancelled", taskId);
            return true;
        }

        /// <summary>
        /// Get status of all active tasks
        /// </summary>
        public List<TaskStatusInfo> GetActiveTasks()
        {
            return _activeTasks.Select(t => new TaskStatusInfo
            {
                Id = t.Id,
                Goal = t.Goal,
                Status = t.Status.ToString(),
                CurrentStep = t.CurrentStep,
                TotalSteps = t.Plan?.Steps.Count ?? 0,
                StartTime = t.StartTime,
                RetryCount = t.RetryCount,
                PendingApprovalReason = t.PendingApprovalReason
            }).ToList();
        }

        /// <summary>
        /// Get result of a completed task
        /// </summary>
        public ExecutionResult GetTaskResult(string taskId)
        {
            return _taskResults.TryGetValue(taskId, out var result) ? result : null;
        }

        #endregion

        #region Configuration

        /// <summary>
        /// Configure autonomous execution settings
        /// </summary>
        public void Configure(int? maxRetries = null, int? maxConcurrentTasks = null, bool? requireApprovalForDestructive = null)
        {
            if (maxRetries.HasValue)
                _maxRetries = maxRetries.Value;
            if (maxConcurrentTasks.HasValue)
                _maxConcurrentTasks = maxConcurrentTasks.Value;
            if (requireApprovalForDestructive.HasValue)
                _requireApprovalForDestructive = requireApprovalForDestructive.Value;

            _guardrails.RequireApprovalForDestructive = _requireApprovalForDestructive;
        }

        /// <summary>
        /// Get current configuration
        /// </summary>
        public object GetConfiguration()
        {
            return new
            {
                maxRetries = _maxRetries,
                maxConcurrentTasks = _maxConcurrentTasks,
                requireApprovalForDestructive = _requireApprovalForDestructive,
                guardrails = _guardrails.GetConfiguration()
            };
        }

        /// <summary>
        /// Get execution statistics
        /// </summary>
        public object GetStatistics()
        {
            var recentHistory = _executionHistory.Where(e => e.Timestamp > DateTime.Now.AddHours(-24)).ToList();

            return new
            {
                activeTasks = _activeTasks.Count,
                completedTasks = _taskResults.Count,
                last24Hours = new
                {
                    totalSteps = recentHistory.Count,
                    successfulSteps = recentHistory.Count(e => e.Success),
                    failedSteps = recentHistory.Count(e => !e.Success),
                    averageDuration = recentHistory.Any()
                        ? TimeSpan.FromMilliseconds(recentHistory.Average(e => e.Duration.TotalMilliseconds))
                        : TimeSpan.Zero
                }
            };
        }

        #endregion
    }

    #region Supporting Classes

    /// <summary>
    /// Plans execution steps for a goal
    /// </summary>
    public class GoalPlanner
    {
        // Common goal patterns and their execution plans
        private readonly Dictionary<string, Func<JObject, UIApplication, ExecutionPlan>> _goalTemplates;

        public GoalPlanner()
        {
            _goalTemplates = new Dictionary<string, Func<JObject, UIApplication, ExecutionPlan>>(StringComparer.OrdinalIgnoreCase)
            {
                ["create sheet set"] = CreateSheetSetPlan,
                ["place views on sheets"] = PlaceViewsOnSheetsPlan,
                ["tag all rooms"] = TagAllRoomsPlan,
                ["create room schedule"] = CreateRoomSchedulePlan,
                ["setup project levels"] = SetupProjectLevelsPlan,
                ["create wall layout"] = CreateWallLayoutPlan
            };
        }

        public ExecutionPlan CreatePlan(string goal, JObject context, UIApplication uiApp)
        {
            // Try to match goal to template
            foreach (var template in _goalTemplates)
            {
                if (goal.ToLower().Contains(template.Key))
                {
                    return template.Value(context, uiApp);
                }
            }

            // Fall back to AI-assisted planning or return empty plan
            return CreateGenericPlan(goal, context, uiApp);
        }

        private ExecutionPlan CreateSheetSetPlan(JObject context, UIApplication uiApp)
        {
            var plan = new ExecutionPlan
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Goal = "Create sheet set",
                Steps = new List<ExecutionStep>()
            };

            // Step 1: Get levels
            plan.Steps.Add(new ExecutionStep
            {
                StepNumber = 1,
                Description = "Get project levels",
                Method = "getLevels",
                Parameters = new JObject(),
                IsRequired = true,
                OutputMappings = new Dictionary<string, string> { ["levels"] = "levels" }
            });

            // Step 2: Get available views
            plan.Steps.Add(new ExecutionStep
            {
                StepNumber = 2,
                Description = "Get floor plan views",
                Method = "getViews",
                Parameters = new JObject { ["viewType"] = "FloorPlan" },
                IsRequired = true,
                OutputMappings = new Dictionary<string, string> { ["floorPlanViews"] = "views" }
            });

            // Step 3: Create sheets for each level
            plan.Steps.Add(new ExecutionStep
            {
                StepNumber = 3,
                Description = "Create sheets from pattern",
                Method = "createSheetsFromPattern",
                Parameters = new JObject
                {
                    ["pattern"] = "A{{levelIndex}}.1",
                    ["titleTemplate"] = "FLOOR PLAN - {{levelName}}"
                },
                IsRequired = true
            });

            // Step 4: Place views on sheets
            plan.Steps.Add(new ExecutionStep
            {
                StepNumber = 4,
                Description = "Auto-place views on sheets",
                Method = "autoPlaceView",
                Parameters = new JObject { ["matchByLevel"] = true },
                IsRequired = false
            });

            return plan;
        }

        private ExecutionPlan PlaceViewsOnSheetsPlan(JObject context, UIApplication uiApp)
        {
            var plan = new ExecutionPlan
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Goal = "Place views on sheets",
                Steps = new List<ExecutionStep>
                {
                    new ExecutionStep
                    {
                        StepNumber = 1,
                        Description = "Analyze unplaced views",
                        Method = "analyzeUnplacedViews",
                        Parameters = new JObject(),
                        IsRequired = true
                    },
                    new ExecutionStep
                    {
                        StepNumber = 2,
                        Description = "Get available sheets",
                        Method = "getAllSheets",
                        Parameters = new JObject(),
                        IsRequired = true
                    },
                    new ExecutionStep
                    {
                        StepNumber = 3,
                        Description = "Auto-place views",
                        Method = "autoPlaceView",
                        Parameters = new JObject { ["matchByLevel"] = true },
                        IsRequired = true
                    }
                }
            };

            return plan;
        }

        private ExecutionPlan TagAllRoomsPlan(JObject context, UIApplication uiApp)
        {
            var plan = new ExecutionPlan
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Goal = "Tag all rooms",
                Steps = new List<ExecutionStep>
                {
                    new ExecutionStep
                    {
                        StepNumber = 1,
                        Description = "Find untagged rooms",
                        Method = "analyzeUntaggedRooms",
                        Parameters = new JObject(),
                        IsRequired = true,
                        OutputMappings = new Dictionary<string, string> { ["untaggedRooms"] = "rooms" }
                    },
                    new ExecutionStep
                    {
                        StepNumber = 2,
                        Description = "Tag rooms in batch",
                        Method = "tagRooms",
                        Parameters = new JObject { ["roomIds"] = "{{untaggedRoomIds}}" },
                        IsRequired = true
                    }
                }
            };

            return plan;
        }

        private ExecutionPlan CreateRoomSchedulePlan(JObject context, UIApplication uiApp)
        {
            var plan = new ExecutionPlan
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Goal = "Create room schedule",
                Steps = new List<ExecutionStep>
                {
                    new ExecutionStep
                    {
                        StepNumber = 1,
                        Description = "Create schedule",
                        Method = "createSchedule",
                        Parameters = new JObject
                        {
                            ["category"] = "Rooms",
                            ["name"] = context?["scheduleName"]?.ToString() ?? "Room Schedule"
                        },
                        IsRequired = true,
                        OutputMappings = new Dictionary<string, string> { ["scheduleId"] = "scheduleId" }
                    },
                    new ExecutionStep
                    {
                        StepNumber = 2,
                        Description = "Add schedule fields",
                        Method = "addScheduleFields",
                        Parameters = new JObject
                        {
                            ["scheduleId"] = "{{scheduleId}}",
                            ["fields"] = new JArray { "Number", "Name", "Area", "Level" }
                        },
                        IsRequired = true
                    }
                }
            };

            return plan;
        }

        private ExecutionPlan SetupProjectLevelsPlan(JObject context, UIApplication uiApp)
        {
            var levels = context?["levels"] as JArray ?? new JArray { "Level 1", "Level 2" };
            var elevation = 0.0;
            var floorHeight = context?["floorHeight"]?.Value<double>() ?? 10.0;

            var plan = new ExecutionPlan
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Goal = "Setup project levels",
                Steps = new List<ExecutionStep>()
            };

            int stepNum = 1;
            foreach (var level in levels)
            {
                plan.Steps.Add(new ExecutionStep
                {
                    StepNumber = stepNum++,
                    Description = $"Create level: {level}",
                    Method = "createLevel",
                    Parameters = new JObject
                    {
                        ["name"] = level.ToString(),
                        ["elevation"] = elevation
                    },
                    IsRequired = true
                });
                elevation += floorHeight;
            }

            return plan;
        }

        private ExecutionPlan CreateWallLayoutPlan(JObject context, UIApplication uiApp)
        {
            var plan = new ExecutionPlan
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Goal = "Create wall layout",
                Steps = new List<ExecutionStep>
                {
                    new ExecutionStep
                    {
                        StepNumber = 1,
                        Description = "Get level for walls",
                        Method = "getLevels",
                        Parameters = new JObject(),
                        IsRequired = true
                    },
                    new ExecutionStep
                    {
                        StepNumber = 2,
                        Description = "Get wall types",
                        Method = "getWallTypes",
                        Parameters = new JObject(),
                        IsRequired = true
                    },
                    new ExecutionStep
                    {
                        StepNumber = 3,
                        Description = "Create walls from coordinates",
                        Method = "createWalls",
                        Parameters = new JObject
                        {
                            ["walls"] = context?["walls"] ?? new JArray(),
                            ["levelId"] = "{{levelId}}",
                            ["wallTypeId"] = "{{wallTypeId}}"
                        },
                        IsRequired = true
                    }
                }
            };

            return plan;
        }

        private ExecutionPlan CreateGenericPlan(string goal, JObject context, UIApplication uiApp)
        {
            // For unrecognized goals, return empty plan
            // In a more advanced version, this could use NLP to parse the goal
            Log.Warning("No template found for goal: {Goal}", goal);

            return new ExecutionPlan
            {
                Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                Goal = goal,
                Steps = new List<ExecutionStep>()
            };
        }
    }

    /// <summary>
    /// Self-healing system for automatic error recovery
    /// </summary>
    public class SelfHealer
    {
        // Known error patterns and their fixes
        private readonly Dictionary<string, Func<JObject, JObject>> _errorFixes;

        public SelfHealer()
        {
            _errorFixes = new Dictionary<string, Func<JObject, JObject>>(StringComparer.OrdinalIgnoreCase)
            {
                // Common error patterns and how to fix them
                ["level not found"] = p => { p["levelId"] = 0; return p; }, // Use first level
                ["type not found"] = p => { p.Remove("typeId"); return p; }, // Let system pick default
                ["element not found"] = p => null, // Can't fix, skip step
                ["invalid parameter"] = p => null // Can't fix, skip step
            };
        }

        public StepExecutionResult TryHealStep(UIApplication uiApp, ExecutionStep step, StepExecutionResult failedResult)
        {
            Log.Information("Attempting to self-heal step {Step}: {Error}", step.StepNumber, failedResult.Error);

            // Try known error patterns
            foreach (var errorFix in _errorFixes)
            {
                if (failedResult.Error.IndexOf(errorFix.Key, StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    Log.Information("Found error pattern: {Pattern}", errorFix.Key);

                    var healedParams = step.Parameters != null
                        ? JObject.Parse(step.Parameters.ToString())
                        : new JObject();

                    healedParams = errorFix.Value(healedParams);
                    if (healedParams == null)
                    {
                        Log.Warning("Error pattern {Pattern} cannot be auto-fixed", errorFix.Key);
                        continue;
                    }

                    // Retry with fixed parameters
                    try
                    {
                        var retryResult = MCPServer.ExecuteMethod(uiApp, step.Method, healedParams);
                        var resultObj = JObject.Parse(retryResult);

                        if (resultObj["success"]?.Value<bool>() == true)
                        {
                            return new StepExecutionResult
                            {
                                StepNumber = step.StepNumber,
                                Method = step.Method,
                                Success = true,
                                RawResult = resultObj,
                                Duration = TimeSpan.Zero,
                                HealedWith = $"fixed_{errorFix.Key.Replace(" ", "_")}"
                            };
                        }
                    }
                    catch (Exception ex)
                    {
                        Log.Warning(ex, "Healing attempt failed for pattern: {Pattern}", errorFix.Key);
                    }
                }
            }

            // Simple retry without modifications (for transient errors)
            try
            {
                Log.Information("Attempting simple retry for step {Step}", step.StepNumber);
                var retryResult = MCPServer.ExecuteMethod(uiApp, step.Method, step.Parameters ?? new JObject());
                var resultObj = JObject.Parse(retryResult);

                if (resultObj["success"]?.Value<bool>() == true)
                {
                    return new StepExecutionResult
                    {
                        StepNumber = step.StepNumber,
                        Method = step.Method,
                        Success = true,
                        RawResult = resultObj,
                        Duration = TimeSpan.Zero,
                        HealedWith = "simple_retry"
                    };
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Simple retry failed");
            }

            return null;
        }

        public ExecutionPlan HealPlan(ExecutionPlan originalPlan, PlanExecutionResult result, QualityAssessment assessment)
        {
            if (result.FailedAtStep.HasValue)
            {
                // Create a plan that retries from the failed step
                var healedPlan = new ExecutionPlan
                {
                    Id = Guid.NewGuid().ToString("N").Substring(0, 8),
                    Goal = originalPlan.Goal,
                    Steps = originalPlan.Steps
                        .Where(s => s.StepNumber >= result.FailedAtStep.Value)
                        .ToList()
                };

                // Re-number steps
                for (int i = 0; i < healedPlan.Steps.Count; i++)
                {
                    healedPlan.Steps[i].StepNumber = i + 1;
                }

                return healedPlan;
            }

            return null;
        }
    }

    /// <summary>
    /// Guardrail system for bounded autonomy
    /// </summary>
    public class GuardrailSystem
    {
        // Methods that require approval
        private readonly HashSet<string> _destructiveMethods = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "deleteElements", "deleteAllElements", "purgeUnused",
            "closeProject", "deleteView", "deleteSheet"
        };

        // Methods that are always allowed
        private readonly HashSet<string> _safeReadMethods = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "getLevels", "getViews", "getRooms", "getElements", "getProjectInfo",
            "getAllSheets", "getWallTypes", "getDoorTypes", "getWindowTypes",
            "analyzeProjectState", "analyzeUnplacedViews", "analyzeUntaggedRooms"
        };

        // Limits for autonomous operations
        private int _maxElementsPerBatch = 100;
        private int _maxSheetsPerOperation = 20;

        public bool RequireApprovalForDestructive { get; set; } = true;

        public ValidationResult ValidatePlan(ExecutionPlan plan)
        {
            foreach (var step in plan.Steps)
            {
                var check = CheckMethodExecution(step.Method, step.Parameters);
                if (!check.Allowed)
                {
                    return new ValidationResult
                    {
                        IsValid = false,
                        RequiresApproval = check.RequiresApproval,
                        Reason = check.Reason,
                        FailedStep = step.StepNumber
                    };
                }
            }

            return new ValidationResult { IsValid = true };
        }

        public MethodCheckResult CheckMethodExecution(string method, JObject parameters)
        {
            // Safe methods are always allowed
            if (_safeReadMethods.Contains(method))
            {
                return new MethodCheckResult { Allowed = true };
            }

            // Destructive methods require approval
            if (RequireApprovalForDestructive && _destructiveMethods.Contains(method))
            {
                return new MethodCheckResult
                {
                    Allowed = false,
                    RequiresApproval = true,
                    Reason = $"Method '{method}' is destructive and requires approval"
                };
            }

            // Check batch limits
            if (parameters != null)
            {
                var elementIds = parameters["elementIds"] as JArray;
                if (elementIds != null && elementIds.Count > _maxElementsPerBatch)
                {
                    return new MethodCheckResult
                    {
                        Allowed = false,
                        RequiresApproval = true,
                        Reason = $"Batch size ({elementIds.Count}) exceeds limit ({_maxElementsPerBatch})"
                    };
                }
            }

            return new MethodCheckResult { Allowed = true };
        }

        public object GetConfiguration()
        {
            return new
            {
                requireApprovalForDestructive = RequireApprovalForDestructive,
                maxElementsPerBatch = _maxElementsPerBatch,
                maxSheetsPerOperation = _maxSheetsPerOperation,
                destructiveMethods = _destructiveMethods.ToList(),
                safeReadMethods = _safeReadMethods.ToList()
            };
        }

        public void SetLimits(int? maxElementsPerBatch = null, int? maxSheetsPerOperation = null)
        {
            if (maxElementsPerBatch.HasValue)
                _maxElementsPerBatch = maxElementsPerBatch.Value;
            if (maxSheetsPerOperation.HasValue)
                _maxSheetsPerOperation = maxSheetsPerOperation.Value;
        }
    }

    /// <summary>
    /// Quality assessor for self-verification
    /// </summary>
    public class QualityAssessor
    {
        public QualityAssessment AssessExecution(UIApplication uiApp, string goal, PlanExecutionResult result)
        {
            var assessment = new QualityAssessment
            {
                Goal = goal,
                AssessmentTime = DateTime.Now,
                StepsExecuted = result.StepResults.Count,
                StepsSucceeded = result.StepResults.Count(r => r.Success),
                StepsFailed = result.StepResults.Count(r => !r.Success)
            };

            // Calculate success rate
            assessment.SuccessRate = assessment.StepsExecuted > 0
                ? (double)assessment.StepsSucceeded / assessment.StepsExecuted
                : 0;

            // Determine if goal is met
            assessment.MeetsGoal = result.Success && assessment.SuccessRate >= 0.8;

            // Generate summary
            if (assessment.MeetsGoal)
            {
                assessment.Summary = $"Goal achieved: {assessment.StepsSucceeded}/{assessment.StepsExecuted} steps completed successfully";
                assessment.CanRetry = false;
            }
            else if (result.FailedAtStep.HasValue)
            {
                assessment.Summary = $"Execution failed at step {result.FailedAtStep}: {result.StepResults.LastOrDefault()?.Error}";
                assessment.CanRetry = true;
            }
            else
            {
                assessment.Summary = $"Partial success: {assessment.StepsSucceeded}/{assessment.StepsExecuted} steps completed";
                assessment.CanRetry = assessment.SuccessRate < 1.0;
            }

            // Add recommendations
            if (!assessment.MeetsGoal)
            {
                var failedSteps = result.StepResults.Where(r => !r.Success).ToList();
                foreach (var failed in failedSteps)
                {
                    assessment.Recommendations.Add($"Step {failed.StepNumber} ({failed.Method}): {failed.Error}");
                }
            }

            return assessment;
        }
    }

    #endregion

    #region Data Classes

    public class AutonomousTask
    {
        public string Id { get; set; }
        public string Goal { get; set; }
        public JObject Context { get; set; }
        public TaskStatus Status { get; set; }
        public ExecutionPlan Plan { get; set; }
        public int CurrentStep { get; set; }
        public int RetryCount { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public string PendingApprovalReason { get; set; }
        public QualityAssessment Assessment { get; set; }
    }

    public enum TaskStatus
    {
        Planning,
        Validating,
        AwaitingApproval,
        Executing,
        Assessing,
        Completed,
        Failed,
        Cancelled
    }

    public class ExecutionPlan
    {
        public string Id { get; set; }
        public string Goal { get; set; }
        public List<ExecutionStep> Steps { get; set; } = new List<ExecutionStep>();
    }

    public class ExecutionStep
    {
        public int StepNumber { get; set; }
        public string Description { get; set; }
        public string Method { get; set; }
        public JObject Parameters { get; set; }
        public bool IsRequired { get; set; } = true;
        public Dictionary<string, string> OutputMappings { get; set; }
    }

    public class ExecutionResult
    {
        public string TaskId { get; set; }
        public bool Success { get; set; }
        public string Status { get; set; }
        public string Message { get; set; }
        public ExecutionPlan Plan { get; set; }
        public PlanExecutionResult PlanResult { get; set; }
        public QualityAssessment Assessment { get; set; }
        public TimeSpan? Duration { get; set; }
    }

    public class PlanExecutionResult
    {
        public string PlanId { get; set; }
        public bool Success { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public int? FailedAtStep { get; set; }
        public List<StepExecutionResult> StepResults { get; set; }
    }

    public class StepExecutionResult
    {
        public int StepNumber { get; set; }
        public string Method { get; set; }
        public bool Success { get; set; }
        public string Error { get; set; }
        public JObject RawResult { get; set; }
        public JObject OutputData { get; set; }
        public TimeSpan Duration { get; set; }
        public DateTime StartTime { get; set; }
        public string HealedWith { get; set; }
    }

    public class QualityAssessment
    {
        public string Goal { get; set; }
        public DateTime AssessmentTime { get; set; }
        public bool MeetsGoal { get; set; }
        public double SuccessRate { get; set; }
        public int StepsExecuted { get; set; }
        public int StepsSucceeded { get; set; }
        public int StepsFailed { get; set; }
        public string Summary { get; set; }
        public bool CanRetry { get; set; }
        public List<string> Recommendations { get; set; } = new List<string>();
    }

    public class ValidationResult
    {
        public bool IsValid { get; set; }
        public bool RequiresApproval { get; set; }
        public string Reason { get; set; }
        public int? FailedStep { get; set; }
    }

    public class MethodCheckResult
    {
        public bool Allowed { get; set; }
        public bool RequiresApproval { get; set; }
        public string Reason { get; set; }
    }

    public class TaskStatusInfo
    {
        public string Id { get; set; }
        public string Goal { get; set; }
        public string Status { get; set; }
        public int CurrentStep { get; set; }
        public int TotalSteps { get; set; }
        public DateTime StartTime { get; set; }
        public int RetryCount { get; set; }
        public string PendingApprovalReason { get; set; }
    }

    public class ExecutionLog
    {
        public DateTime Timestamp { get; set; }
        public string TaskId { get; set; }
        public int StepNumber { get; set; }
        public string Method { get; set; }
        public bool Success { get; set; }
        public TimeSpan Duration { get; set; }
    }

    #endregion
}
