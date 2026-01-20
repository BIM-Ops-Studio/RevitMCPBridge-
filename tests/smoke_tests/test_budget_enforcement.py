#!/usr/bin/env python3
"""
Budget Enforcement Tests

Test D: max_steps stop - ping loop exceeds step limit
Test E: max_total_retries stop - failing method exceeds retry limit

These prove budget enforcement is real.
"""

import json
import subprocess
import time
from pathlib import Path

from workflow_report import WorkflowReport, RunStatus, Severity


def send_mcp_request(method: str, params: dict = None, timeout: int = 10) -> tuple:
    """Send MCP request. Returns (response_dict, elapsed_ms)."""
    request = {"method": method}
    if params:
        request["params"] = params

    start_time = time.time()

    try:
        cmd = [
            "powershell.exe", "-Command",
            f'''
            $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
            $pipe.Connect({timeout * 1000})
            $writer = New-Object System.IO.StreamWriter($pipe)
            $reader = New-Object System.IO.StreamReader($pipe)
            $writer.WriteLine('{json.dumps(request).replace("'", "''")}')
            $writer.Flush()
            $response = $reader.ReadLine()
            $pipe.Close()
            Write-Output $response
            '''
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        output = result.stdout.strip()
        elapsed_ms = (time.time() - start_time) * 1000

        json_start = output.find('{')
        if json_start == -1:
            return {"success": False, "error": "No JSON in response"}, elapsed_ms

        response = json.loads(output[json_start:])
        return response, elapsed_ms

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {"success": False, "error": str(e)}, elapsed_ms


def test_d_max_steps():
    """
    Test D: max_steps stop

    Create a workflow that loops getLevels 60 times.
    With max_steps=10, expect STOPPED at step 11.
    """
    print("\n" + "=" * 60)
    print("TEST D: max_steps Budget Enforcement")
    print("=" * 60)

    report = WorkflowReport("test_d_max_steps")

    # Set LOW step limit for testing
    report.set_budget_limits(max_steps=10)

    print(f"Run ID: {report.run_id}")
    print(f"Budget: max_steps={report.budget_limits.max_steps}")
    print("-" * 60)

    step_count = 0
    target_steps = 60  # Way more than budget allows

    for i in range(target_steps):
        step_id = f"step_{i+1:02d}_ping"

        # This is the enforcement choke point - returns False when budget exceeded
        can_continue = report.start_step(step_id)

        if not can_continue:
            print(f"\n  STOPPED at step {i+1} (budget enforcement triggered)")
            break

        step_count += 1
        print(f"  Step {step_count}: {step_id}...", end=" ")

        resp, elapsed = send_mcp_request("getLevels")
        report.log_mcp_call("getLevels", {}, resp, elapsed)

        if resp.get("success"):
            print("ok")
        else:
            print(f"fail: {resp.get('error')}")

        report.end_step(outputs={"levels": len(resp.get("levels", []))})

    # Best-effort cleanup (none needed for getLevels)
    report.record_cleanup("ok", "No artifacts to clean")
    report.add_postcondition("CLEANUP_STATUS", "pass")

    # Finalize
    report.finalize()
    report.save()

    # Print results
    print("\n" + "-" * 60)
    print("RESULT:")
    print(f"  run.status:      {report.status.value}")
    print(f"  stopped_reason:  {report.stopped_reason}")
    print(f"  steps executed:  {step_count}")
    print(f"  budget.usage.steps: {report.budget_usage.steps}")

    if report.issues:
        print("\n  Blocker Issue:")
        issue = report.issues[0]
        print(f"    id: {issue.id}")
        print(f"    severity: {issue.severity}")
        print(f"    message: {issue.message}")
        if issue.evidence:
            print(f"    evidence: {issue.evidence}")

    print(f"\n  cleanup.status: {report.cleanup_status}")
    print("-" * 60)

    # Verify expectations
    expected_status = RunStatus.STOPPED
    expected_steps = 10  # Should stop at 10, not execute 11

    passed = (
        report.status == expected_status and
        report.budget_usage.steps == expected_steps and
        report.budget_exceeded and
        "max_steps" in report.exceeded_fields
    )

    print(f"\nTEST D: {'PASS' if passed else 'FAIL'}")
    print(f"  Expected: status=STOPPED, steps={expected_steps}")
    print(f"  Actual:   status={report.status.value}, steps={report.budget_usage.steps}")

    return passed, report


def test_e_max_retries():
    """
    Test E: max_total_retries stop

    Call a method with known bad args in a retry loop.
    With max_total_retries=3, expect STOPPED after 3 retries.
    """
    print("\n" + "=" * 60)
    print("TEST E: max_total_retries Budget Enforcement")
    print("=" * 60)

    report = WorkflowReport("test_e_max_retries")

    # Set LOW retry limit for testing
    report.set_budget_limits(max_total_retries=3, max_retries_per_step=5)

    print(f"Run ID: {report.run_id}")
    print(f"Budget: max_total_retries={report.budget_limits.max_total_retries}")
    print("-" * 60)

    report.start_step("01_retry_test")

    retry_count = 0
    max_attempts = 10  # Way more than budget allows

    for attempt in range(max_attempts):
        print(f"  Attempt {attempt + 1}...", end=" ")

        # Call with intentionally bad parameters to force failure
        resp, elapsed = send_mcp_request("getScheduleFields", {
            "scheduleId": -99999  # Invalid ID
        })

        # Log with retry_index > 0 for retries
        _, can_continue = report.log_mcp_call(
            "getScheduleFields",
            {"scheduleId": -99999},
            resp,
            elapsed,
            retry_index=attempt  # 0 for first call, 1+ for retries
        )

        if resp.get("success"):
            print("unexpected success!")
        else:
            print(f"fail (expected): {resp.get('error', 'unknown')[:50]}")

        if not can_continue:
            print(f"\n  STOPPED after {attempt + 1} attempts (budget enforcement triggered)")
            break

        retry_count = attempt + 1

    report.end_step(status="fail", outputs={"retries": retry_count})

    # Cleanup
    report.record_cleanup("ok", "No artifacts created")
    report.add_postcondition("CLEANUP_STATUS", "pass")

    # Finalize
    report.finalize()
    report.save()

    # Print results
    print("\n" + "-" * 60)
    print("RESULT:")
    print(f"  run.status:      {report.status.value}")
    print(f"  stopped_reason:  {report.stopped_reason}")
    print(f"  total_retries:   {report.budget_usage.total_retries}")

    if report.issues:
        print("\n  Blocker Issue:")
        issue = report.issues[0]
        print(f"    id: {issue.id}")
        print(f"    severity: {issue.severity}")
        print(f"    message: {issue.message}")
        if issue.evidence:
            print(f"    evidence: {issue.evidence}")

    print(f"\n  cleanup.status: {report.cleanup_status}")
    print("-" * 60)

    # Verify expectations
    expected_status = RunStatus.STOPPED

    passed = (
        report.status == expected_status and
        report.budget_exceeded and
        "max_total_retries" in report.exceeded_fields
    )

    print(f"\nTEST E: {'PASS' if passed else 'FAIL'}")
    print(f"  Expected: status=STOPPED, budget_exceeded=True")
    print(f"  Actual:   status={report.status.value}, budget_exceeded={report.budget_exceeded}")

    return passed, report


def main():
    """Run both budget enforcement tests."""
    print("\n" + "=" * 60)
    print("BUDGET ENFORCEMENT TEST SUITE")
    print("=" * 60)

    results = {}

    # Test D
    passed_d, report_d = test_d_max_steps()
    results["test_d"] = {
        "passed": passed_d,
        "status": report_d.status.value,
        "stopped_reason": report_d.stopped_reason,
        "cleanup": report_d.cleanup_status
    }

    # Test E
    passed_e, report_e = test_e_max_retries()
    results["test_e"] = {
        "passed": passed_e,
        "status": report_e.status.value,
        "stopped_reason": report_e.stopped_reason,
        "cleanup": report_e.cleanup_status
    }

    # Summary
    print("\n" + "=" * 60)
    print("BUDGET ENFORCEMENT SUMMARY")
    print("=" * 60)
    print(f"Test D (max_steps):        {'PASS' if results['test_d']['passed'] else 'FAIL'}")
    print(f"Test E (max_total_retries): {'PASS' if results['test_e']['passed'] else 'FAIL'}")
    print("-" * 60)

    all_passed = all(r["passed"] for r in results.values())
    print(f"OVERALL: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
