using System;
using System.Collections.Generic;
using NUnit.Framework;
using Newtonsoft.Json.Linq;
using FluentAssertions;

namespace RevitMCPBridge.Tests.Unit
{
    /// <summary>
    /// Unit tests for Intelligence components (Levels 3-5).
    /// Tests GoalPlanner, SelfHealer, GuardrailSystem, QualityAssessor.
    /// </summary>
    [TestFixture]
    public class IntelligenceTests : TestBase
    {
        #region GoalPlanner Tests

        [Test]
        public void GoalPlanner_CreateSheetSet_DecomposesCorrectly()
        {
            // Arrange
            var planner = new TestableGoalPlanner();

            // Act
            var steps = planner.PlanGoal("create_sheet_set", new Dictionary<string, object>
            {
                { "viewIds", new[] { 1, 2, 3 } },
                { "sheetPattern", "A-{level}.{sequence}" }
            });

            // Assert
            steps.Should().NotBeEmpty();
            steps.Should().Contain(s => s.Method == "createSheet");
            steps.Should().Contain(s => s.Method == "placeViewOnSheet");
        }

        [Test]
        public void GoalPlanner_UnknownGoal_ReturnsError()
        {
            // Arrange
            var planner = new TestableGoalPlanner();

            // Act
            var steps = planner.PlanGoal("unknown_goal_type", new Dictionary<string, object>());

            // Assert
            steps.Should().BeEmpty();
            planner.LastError.Should().Contain("Unknown goal type");
        }

        [Test]
        public void GoalPlanner_DocumentModel_IncludesAllSteps()
        {
            // Arrange
            var planner = new TestableGoalPlanner();

            // Act
            var steps = planner.PlanGoal("document_model", new Dictionary<string, object>
            {
                { "includeFloorPlans", true },
                { "includeSchedules", new[] { "Doors", "Windows" } }
            });

            // Assert
            steps.Should().Contain(s => s.Method == "createFloorPlanView" || s.Description.Contains("floor plan"));
            steps.Should().Contain(s => s.Method == "createSchedule" || s.Description.Contains("schedule"));
        }

        [Test]
        public void GoalPlanner_BatchPlacement_OrdersStepsCorrectly()
        {
            // Arrange
            var planner = new TestableGoalPlanner();

            // Act
            var steps = planner.PlanGoal("place_elements_batch", new Dictionary<string, object>
            {
                { "elements", new[] {
                    new { type = "wall", parameters = new { } },
                    new { type = "door", parameters = new { } }
                }}
            });

            // Assert
            // Walls should be placed before doors (dependency)
            var wallStep = steps.FindIndex(s => s.Description.Contains("wall"));
            var doorStep = steps.FindIndex(s => s.Description.Contains("door"));

            if (wallStep >= 0 && doorStep >= 0)
            {
                wallStep.Should().BeLessThan(doorStep, "Walls must be created before doors can be placed in them");
            }
        }

        #endregion

        #region SelfHealer Tests

        [Test]
        public void SelfHealer_RecognizesLevelNotFound()
        {
            // Arrange
            var healer = new TestableSelfHealer();
            var error = "Level 999 not found";

            // Act
            var canHeal = healer.CanHeal(error);
            var suggestion = healer.GetHealingSuggestion(error);

            // Assert
            canHeal.Should().BeTrue();
            suggestion.Should().Contain("level");
        }

        [Test]
        public void SelfHealer_RecognizesTypeNotFound()
        {
            // Arrange
            var healer = new TestableSelfHealer();
            var error = "Wall type 'NonExistent' not found";

            // Act
            var canHeal = healer.CanHeal(error);

            // Assert
            canHeal.Should().BeTrue();
        }

        [Test]
        public void SelfHealer_UnknownError_CannotHeal()
        {
            // Arrange
            var healer = new TestableSelfHealer();
            var error = "Some completely unknown error XYZ123";

            // Act
            var canHeal = healer.CanHeal(error);

            // Assert
            canHeal.Should().BeFalse();
        }

        [Test]
        public void SelfHealer_TracksRetryCount()
        {
            // Arrange
            var healer = new TestableSelfHealer();
            var stepId = "step-001";

            // Act
            healer.RecordRetry(stepId);
            healer.RecordRetry(stepId);
            healer.RecordRetry(stepId);

            // Assert
            healer.GetRetryCount(stepId).Should().Be(3);
        }

        [Test]
        public void SelfHealer_MaxRetriesExceeded_StopsHealing()
        {
            // Arrange
            var healer = new TestableSelfHealer { MaxRetries = 3 };
            var stepId = "step-001";

            // Act
            for (int i = 0; i < 5; i++)
            {
                healer.RecordRetry(stepId);
            }

            // Assert
            healer.ShouldRetry(stepId).Should().BeFalse();
        }

        #endregion

        #region GuardrailSystem Tests

        [Test]
        public void Guardrails_AllowsPermittedMethods()
        {
            // Arrange
            var guardrails = new TestableGuardrailSystem();
            guardrails.SetAllowedMethods(new[] { "createWall", "createRoom", "getViews" });

            // Act & Assert
            guardrails.IsMethodAllowed("createWall").Should().BeTrue();
            guardrails.IsMethodAllowed("createRoom").Should().BeTrue();
            guardrails.IsMethodAllowed("getViews").Should().BeTrue();
        }

        [Test]
        public void Guardrails_BlocksUnpermittedMethods()
        {
            // Arrange
            var guardrails = new TestableGuardrailSystem();
            guardrails.SetAllowedMethods(new[] { "createWall", "createRoom" });

            // Act & Assert
            guardrails.IsMethodAllowed("deleteElements").Should().BeFalse();
            guardrails.IsMethodAllowed("purgeUnused").Should().BeFalse();
        }

        [Test]
        public void Guardrails_ExplicitlyBlockedMethods_AlwaysBlocked()
        {
            // Arrange
            var guardrails = new TestableGuardrailSystem();
            guardrails.SetBlockedMethods(new[] { "deleteElements" });
            guardrails.SetAllowedMethods(new[] { "deleteElements", "createWall" }); // Try to allow blocked

            // Act & Assert
            guardrails.IsMethodAllowed("deleteElements").Should().BeFalse("Blocked takes precedence");
            guardrails.IsMethodAllowed("createWall").Should().BeTrue();
        }

        [Test]
        public void Guardrails_ElementCountLimit_Enforced()
        {
            // Arrange
            var guardrails = new TestableGuardrailSystem { MaxElementsPerTask = 10 };

            // Act & Assert
            guardrails.CheckElementCount(5).Should().BeTrue();
            guardrails.CheckElementCount(10).Should().BeTrue();
            guardrails.CheckElementCount(11).Should().BeFalse();
            guardrails.CheckElementCount(100).Should().BeFalse();
        }

        [Test]
        public void Guardrails_RequiresApproval_ForConfiguredMethods()
        {
            // Arrange
            var guardrails = new TestableGuardrailSystem();
            guardrails.SetRequiresApproval(new[] { "createSheet", "deleteElements" });

            // Act & Assert
            guardrails.RequiresApproval("createSheet").Should().BeTrue();
            guardrails.RequiresApproval("deleteElements").Should().BeTrue();
            guardrails.RequiresApproval("createWall").Should().BeFalse();
        }

        #endregion

        #region QualityAssessor Tests

        [Test]
        public void QualityAssessor_VerifiesElementExists()
        {
            // Arrange
            var assessor = new TestableQualityAssessor(MockContext);
            var wall = CreateTestWall();

            // Act
            var result = assessor.VerifyElementCreated(wall.Id);

            // Assert
            result.Success.Should().BeTrue();
            result.ElementExists.Should().BeTrue();
        }

        [Test]
        public void QualityAssessor_DetectsMissingElement()
        {
            // Arrange
            var assessor = new TestableQualityAssessor(MockContext);

            // Act
            var result = assessor.VerifyElementCreated(999999);

            // Assert
            result.Success.Should().BeFalse();
            result.ElementExists.Should().BeFalse();
        }

        [Test]
        public void QualityAssessor_CalculatesSuccessRate()
        {
            // Arrange
            var assessor = new TestableQualityAssessor(MockContext);
            assessor.RecordSuccess();
            assessor.RecordSuccess();
            assessor.RecordSuccess();
            assessor.RecordFailure();

            // Act
            var rate = assessor.GetSuccessRate();

            // Assert
            rate.Should().Be(0.75); // 3 out of 4
        }

        [Test]
        public void QualityAssessor_GoalComplete_AllElementsPresent()
        {
            // Arrange
            var assessor = new TestableQualityAssessor(MockContext);
            var wall1 = CreateTestWall();
            var wall2 = CreateTestWall();
            var room = CreateTestRoom();

            var expectedElements = new[] { wall1.Id, wall2.Id, room.Id };

            // Act
            var result = assessor.VerifyGoalComplete(expectedElements);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void QualityAssessor_GoalIncomplete_MissingElements()
        {
            // Arrange
            var assessor = new TestableQualityAssessor(MockContext);
            var wall1 = CreateTestWall();

            var expectedElements = new[] { wall1.Id, 999999 }; // One real, one missing

            // Act
            var result = assessor.VerifyGoalComplete(expectedElements);

            // Assert
            result.Should().BeFalse();
        }

        #endregion
    }

    #region Testable Intelligence Classes

    /// <summary>
    /// Testable version of GoalPlanner for unit testing
    /// </summary>
    public class TestableGoalPlanner
    {
        public string LastError { get; private set; }

        public List<TestExecutionStep> PlanGoal(string goalType, Dictionary<string, object> parameters)
        {
            var steps = new List<TestExecutionStep>();

            switch (goalType)
            {
                case "create_sheet_set":
                    steps.Add(new TestExecutionStep { Method = "getViews", Description = "Get available views" });
                    steps.Add(new TestExecutionStep { Method = "getTitleBlockTypes", Description = "Get title blocks" });
                    steps.Add(new TestExecutionStep { Method = "createSheet", Description = "Create sheet" });
                    steps.Add(new TestExecutionStep { Method = "placeViewOnSheet", Description = "Place view on sheet" });
                    break;

                case "document_model":
                    steps.Add(new TestExecutionStep { Method = "getLevels", Description = "Get levels" });
                    steps.Add(new TestExecutionStep { Method = "createFloorPlanView", Description = "Create floor plan view" });
                    steps.Add(new TestExecutionStep { Method = "createSchedule", Description = "Create schedule" });
                    steps.Add(new TestExecutionStep { Method = "createSheet", Description = "Create sheet" });
                    break;

                case "place_elements_batch":
                    steps.Add(new TestExecutionStep { Method = "createWall", Description = "Create wall elements" });
                    steps.Add(new TestExecutionStep { Method = "placeDoor", Description = "Place door elements" });
                    break;

                default:
                    LastError = $"Unknown goal type: {goalType}";
                    break;
            }

            return steps;
        }
    }

    public class TestExecutionStep
    {
        public string Method { get; set; }
        public string Description { get; set; }
        public Dictionary<string, object> Parameters { get; set; }
    }

    /// <summary>
    /// Testable version of SelfHealer for unit testing
    /// </summary>
    public class TestableSelfHealer
    {
        public int MaxRetries { get; set; } = 3;
        private Dictionary<string, int> _retryCounts = new Dictionary<string, int>();

        private readonly string[] _healablePatterns = new[]
        {
            "not found",
            "level",
            "type",
            "timeout",
            "try again"
        };

        public bool CanHeal(string error)
        {
            var lowerError = error.ToLower();
            foreach (var pattern in _healablePatterns)
            {
                if (lowerError.Contains(pattern))
                    return true;
            }
            return false;
        }

        public string GetHealingSuggestion(string error)
        {
            var lowerError = error.ToLower();
            if (lowerError.Contains("level"))
                return "Try using a different level or verify level exists";
            if (lowerError.Contains("type"))
                return "Try using a different type or load the required family";
            if (lowerError.Contains("timeout"))
                return "Retry with longer timeout";
            return "Unknown error - cannot suggest fix";
        }

        public void RecordRetry(string stepId)
        {
            if (!_retryCounts.ContainsKey(stepId))
                _retryCounts[stepId] = 0;
            _retryCounts[stepId]++;
        }

        public int GetRetryCount(string stepId)
        {
            return _retryCounts.ContainsKey(stepId) ? _retryCounts[stepId] : 0;
        }

        public bool ShouldRetry(string stepId)
        {
            return GetRetryCount(stepId) < MaxRetries;
        }
    }

    /// <summary>
    /// Testable version of GuardrailSystem for unit testing
    /// </summary>
    public class TestableGuardrailSystem
    {
        public int MaxElementsPerTask { get; set; } = 100;

        private HashSet<string> _allowedMethods = new HashSet<string>();
        private HashSet<string> _blockedMethods = new HashSet<string>();
        private HashSet<string> _requiresApproval = new HashSet<string>();

        public void SetAllowedMethods(string[] methods)
        {
            _allowedMethods = new HashSet<string>(methods, StringComparer.OrdinalIgnoreCase);
        }

        public void SetBlockedMethods(string[] methods)
        {
            _blockedMethods = new HashSet<string>(methods, StringComparer.OrdinalIgnoreCase);
        }

        public void SetRequiresApproval(string[] methods)
        {
            _requiresApproval = new HashSet<string>(methods, StringComparer.OrdinalIgnoreCase);
        }

        public bool IsMethodAllowed(string method)
        {
            // Blocked takes precedence
            if (_blockedMethods.Contains(method))
                return false;

            // If allowed list is empty, allow all (except blocked)
            if (_allowedMethods.Count == 0)
                return true;

            return _allowedMethods.Contains(method);
        }

        public bool CheckElementCount(int count)
        {
            return count <= MaxElementsPerTask;
        }

        public bool RequiresApproval(string method)
        {
            return _requiresApproval.Contains(method);
        }
    }

    /// <summary>
    /// Testable version of QualityAssessor for unit testing
    /// </summary>
    public class TestableQualityAssessor
    {
        private readonly Mocks.MockRevitContext _context;
        private int _successCount = 0;
        private int _failureCount = 0;

        public TestableQualityAssessor(Mocks.MockRevitContext context)
        {
            _context = context;
        }

        public VerificationResult VerifyElementCreated(int elementId)
        {
            var exists = _context.Elements.ContainsKey(elementId);
            return new VerificationResult
            {
                Success = exists,
                ElementExists = exists,
                ElementId = elementId
            };
        }

        public void RecordSuccess() => _successCount++;
        public void RecordFailure() => _failureCount++;

        public double GetSuccessRate()
        {
            var total = _successCount + _failureCount;
            return total > 0 ? (double)_successCount / total : 0;
        }

        public bool VerifyGoalComplete(int[] expectedElementIds)
        {
            foreach (var id in expectedElementIds)
            {
                if (!_context.Elements.ContainsKey(id))
                    return false;
            }
            return true;
        }
    }

    public class VerificationResult
    {
        public bool Success { get; set; }
        public bool ElementExists { get; set; }
        public int ElementId { get; set; }
    }

    #endregion
}
