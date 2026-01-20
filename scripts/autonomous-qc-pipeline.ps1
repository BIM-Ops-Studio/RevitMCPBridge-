# Autonomous QC Pipeline for Revit
# Runs validation and compliance checks automatically
# Designed to work with RevitMCPBridge2026

param(
    [string]$PipeName = 'RevitMCPBridge2026',
    [switch]$Full,        # Run full check (all categories)
    [switch]$Quick,       # Run quick check (critical only)
    [switch]$Compliance,  # Run compliance only
    [switch]$Validation,  # Run validation only
    [string]$OutputDir = "$PSScriptRoot\..\qc-reports",
    [switch]$Silent       # Don't output to console
)

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Helper function to call MCP
function Invoke-RevitMCP {
    param(
        [string]$Method,
        [hashtable]$Params = @{}
    )

    try {
        $cmd = @{method=$Method; params=$Params} | ConvertTo-Json -Compress -Depth 10
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(10000)
        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)
        $writer.WriteLine($cmd)
        $writer.Flush()
        $result = $reader.ReadLine()
        $pipe.Close()
        return $result | ConvertFrom-Json
    }
    catch {
        return @{success=$false; error=$_.Exception.Message}
    }
}

function Write-QCLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logLine = "[$timestamp] [$Level] $Message"
    if (-not $Silent) {
        switch ($Level) {
            "ERROR" { Write-Host $logLine -ForegroundColor Red }
            "WARN"  { Write-Host $logLine -ForegroundColor Yellow }
            "PASS"  { Write-Host $logLine -ForegroundColor Green }
            default { Write-Host $logLine }
        }
    }
    return $logLine
}

# Initialize report
$report = @{
    timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    project = ""
    checks = @()
    summary = @{
        total = 0
        passed = 0
        failed = 0
        warnings = 0
    }
}

# Get project info
Write-QCLog "Starting Autonomous QC Pipeline..."
$projectInfo = Invoke-RevitMCP -Method "getProjectInfo"
if ($projectInfo.success) {
    $report.project = $projectInfo.data.projectName
    Write-QCLog "Project: $($report.project)"
} else {
    Write-QCLog "Could not get project info: $($projectInfo.error)" "WARN"
}

# Define check categories
$validationChecks = @(
    @{name="Model Health"; method="validateModelHealth"; params=@{}},
    @{name="Pre-Flight Check"; method="preFlightCheck"; params=@{}},
    @{name="Clash Detection"; method="detectClashes"; params=@{tolerance=0.1}},
    @{name="Element Spacing"; method="validateElementSpacingAndAlignment"; params=@{}}
)

$complianceChecks = @(
    @{name="Corridor Widths"; method="checkCorridorWidths"; params=@{minWidth=44}},
    @{name="Door Widths"; method="checkDoorWidths"; params=@{minWidth=32}},
    @{name="Room Areas"; method="checkRoomAreas"; params=@{}},
    @{name="Toilet Clearances"; method="checkToiletClearances"; params=@{}},
    @{name="Stair Dimensions"; method="checkStairDimensions"; params=@{}},
    @{name="Ceiling Heights"; method="checkCeilingHeights"; params=@{minHeight=7.5}},
    @{name="Door Swing"; method="checkDoorSwing"; params=@{}},
    @{name="Fire Ratings"; method="checkWallFireRatings"; params=@{}}
)

# Determine which checks to run
$checksToRun = @()

if ($Quick) {
    # Quick check - critical items only
    $checksToRun += $validationChecks | Where-Object { $_.name -in @("Model Health", "Pre-Flight Check") }
    $checksToRun += $complianceChecks | Where-Object { $_.name -in @("Corridor Widths", "Door Widths") }
} elseif ($Compliance) {
    $checksToRun = $complianceChecks
} elseif ($Validation) {
    $checksToRun = $validationChecks
} else {
    # Full check (default)
    $checksToRun = $validationChecks + $complianceChecks
}

Write-QCLog "Running $($checksToRun.Count) checks..."
Write-QCLog ("-" * 50)

# Run each check
foreach ($check in $checksToRun) {
    $report.summary.total++
    Write-QCLog "Checking: $($check.name)..."

    $result = Invoke-RevitMCP -Method $check.method -Params $check.params

    $checkResult = @{
        name = $check.name
        method = $check.method
        timestamp = (Get-Date -Format "HH:mm:ss")
        success = $false
        status = "UNKNOWN"
        details = @()
        issues = @()
    }

    if ($result.success) {
        $checkResult.success = $true

        # Analyze result for issues
        if ($result.data -and $result.data.issues) {
            $checkResult.issues = $result.data.issues
            if ($result.data.issues.Count -gt 0) {
                $checkResult.status = "WARN"
                $report.summary.warnings++
                Write-QCLog "  $($check.name): $($result.data.issues.Count) issues found" "WARN"
            } else {
                $checkResult.status = "PASS"
                $report.summary.passed++
                Write-QCLog "  $($check.name): PASSED" "PASS"
            }
        } elseif ($result.data -and $result.data.passed -eq $false) {
            $checkResult.status = "FAIL"
            $report.summary.failed++
            Write-QCLog "  $($check.name): FAILED" "ERROR"
        } else {
            $checkResult.status = "PASS"
            $report.summary.passed++
            Write-QCLog "  $($check.name): PASSED" "PASS"
        }

        if ($result.data) {
            $checkResult.details = $result.data
        }
    } else {
        $checkResult.status = "ERROR"
        $checkResult.error = $result.error
        $report.summary.failed++
        Write-QCLog "  $($check.name): ERROR - $($result.error)" "ERROR"
    }

    $report.checks += $checkResult
}

# Generate summary
Write-QCLog ("-" * 50)
Write-QCLog "QC PIPELINE COMPLETE"
Write-QCLog "  Total Checks: $($report.summary.total)"
Write-QCLog "  Passed: $($report.summary.passed)" "PASS"
Write-QCLog "  Warnings: $($report.summary.warnings)" "WARN"
Write-QCLog "  Failed: $($report.summary.failed)" "ERROR"

# Calculate overall status
if ($report.summary.failed -gt 0) {
    $report.overallStatus = "FAILED"
    Write-QCLog "OVERALL: FAILED - $($report.summary.failed) critical issues" "ERROR"
} elseif ($report.summary.warnings -gt 0) {
    $report.overallStatus = "WARNING"
    Write-QCLog "OVERALL: WARNING - $($report.summary.warnings) issues to review" "WARN"
} else {
    $report.overallStatus = "PASSED"
    Write-QCLog "OVERALL: PASSED - All checks cleared" "PASS"
}

# Save report
$reportFile = Join-Path $OutputDir "qc-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$report | ConvertTo-Json -Depth 10 | Out-File $reportFile -Encoding UTF8
Write-QCLog "Report saved: $reportFile"

# Return report object for programmatic use
return $report
