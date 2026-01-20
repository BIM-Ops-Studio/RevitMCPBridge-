# Comprehensive MCP Bridge Diagnostic
# Tests all key methods to identify issues

function Send-RevitCommand {
    param(
        [string]$PipeName,
        [string]$Method,
        [hashtable]$Params
    )

    $pipeClient = $null
    $writer = $null
    $reader = $null

    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)

        if (-not $pipeClient.IsConnected) {
            throw "Failed to connect to pipe"
        }

        $request = @{
            method = $Method
            params = $Params
        } | ConvertTo-Json -Compress

        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)

        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()

        if ([string]::IsNullOrEmpty($response)) {
            throw "Empty response from server"
        }

        return $response | ConvertFrom-Json
    }
    catch {
        return @{
            success = $false
            error = $_.Exception.Message
            stackTrace = $_.Exception.StackTrace
        }
    }
    finally {
        if ($reader -ne $null) { try { $reader.Dispose() } catch {} }
        if ($writer -ne $null) { try { $writer.Dispose() } catch {} }
        if ($pipeClient -ne $null -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

function Test-Method {
    param(
        [string]$TestName,
        [string]$Method,
        [hashtable]$Params,
        [string]$PipeName
    )

    Write-Host "`n[$TestName]" -ForegroundColor Cyan
    Write-Host "  Method: $Method" -ForegroundColor Gray

    $result = Send-RevitCommand -PipeName $PipeName -Method $Method -Params $Params

    if ($result.success) {
        Write-Host "  ✅ SUCCESS" -ForegroundColor Green

        # Show relevant result info
        if ($result.result) {
            if ($result.result.rooms) {
                Write-Host "     Rooms found: $($result.result.rooms.Count)" -ForegroundColor Yellow
            }
            if ($result.result.views) {
                Write-Host "     Views found: $($result.result.views.Count)" -ForegroundColor Yellow
            }
            if ($result.result.walls) {
                Write-Host "     Walls found: $($result.result.walls.Count)" -ForegroundColor Yellow
            }
            if ($result.result.viewCount) {
                Write-Host "     View count: $($result.result.viewCount)" -ForegroundColor Yellow
            }
            if ($result.result.roomCount) {
                Write-Host "     Room count: $($result.result.roomCount)" -ForegroundColor Yellow
            }
        }

        return @{ passed = $true; result = $result }
    } else {
        Write-Host "  ❌ FAILED" -ForegroundColor Red
        Write-Host "     Error: $($result.error)" -ForegroundColor Red

        return @{ passed = $false; error = $result.error }
    }
}

$pipeName = "RevitMCPBridge2026"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "RevitMCPBridge2026 - Comprehensive Diagnostic" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Testing all key methods to identify issues...`n" -ForegroundColor Yellow

$testResults = @()

# Test 1: Connection
Write-Host "[TEST 1/10] Testing MCP Connection" -ForegroundColor Cyan
try {
    $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipeClient.Connect(2000)
    if ($pipeClient.IsConnected) {
        Write-Host "  ✅ MCP pipe connected successfully" -ForegroundColor Green
        $pipeClient.Close()
        $testResults += @{ test = "Connection"; passed = $true }
    }
} catch {
    Write-Host "  ❌ Failed to connect to MCP pipe" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{ test = "Connection"; passed = $false; error = $_.Exception.Message }
    exit 1
}

# Test 2: Export View (we know this works)
$test2 = Test-Method -TestName "TEST 2/10: exportViewImage" -Method "exportViewImage" `
    -Params @{ outputPath = "D:\RevitMCPBridge2026\diagnostic_view.png" } -PipeName $pipeName
$testResults += @{ test = "exportViewImage"; passed = $test2.passed; error = $test2.error }

# Test 3: Get Project Info
$test3 = Test-Method -TestName "TEST 3/10: getProjectInfo" -Method "getProjectInfo" `
    -Params @{} -PipeName $pipeName
$testResults += @{ test = "getProjectInfo"; passed = $test3.passed; error = $test3.error }

# Test 4: Get ALL Views (no filter)
$test4 = Test-Method -TestName "TEST 4/10: getAllViews (no filter)" -Method "getAllViews" `
    -Params @{} -PipeName $pipeName
$testResults += @{ test = "getAllViews"; passed = $test4.passed; error = $test4.error }

# Test 5: Get ALL Rooms (no filter)
$test5 = Test-Method -TestName "TEST 5/10: getRooms (no filter)" -Method "getRooms" `
    -Params @{} -PipeName $pipeName
$testResults += @{ test = "getRooms"; passed = $test5.passed; error = $test5.error }

# Test 6: Get Elements
$test6 = Test-Method -TestName "TEST 6/10: getElements (walls)" -Method "getElements" `
    -Params @{ category = "Walls" } -PipeName $pipeName
$testResults += @{ test = "getElements"; passed = $test6.passed; error = $test6.error }

# Test 7: Get Categories
$test7 = Test-Method -TestName "TEST 7/10: getCategories" -Method "getCategories" `
    -Params @{} -PipeName $pipeName
$testResults += @{ test = "getCategories"; passed = $test7.passed; error = $test7.error }

# If we got views, try to get walls in a view
if ($test4.passed -and $test4.result.result.views -and $test4.result.result.views.Count -gt 0) {
    $viewId = $test4.result.result.views[0].viewId
    Write-Host "`n  Using view ID: $viewId for wall test" -ForegroundColor Yellow

    # Test 8: Get Walls in View
    $test8 = Test-Method -TestName "TEST 8/10: getWallsInView" -Method "getWallsInView" `
        -Params @{ viewId = $viewId.ToString() } -PipeName $pipeName
    $testResults += @{ test = "getWallsInView"; passed = $test8.passed; error = $test8.error }
} else {
    Write-Host "`n[TEST 8/10: getWallsInView]" -ForegroundColor Cyan
    Write-Host "  ⚠️  SKIPPED (no views available)" -ForegroundColor Yellow
    $testResults += @{ test = "getWallsInView"; passed = $false; error = "No views available" }
}

# Test 9: Get Wall Info (if we have walls)
if ($test6.passed -and $test6.result.result.elements -and $test6.result.result.elements.Count -gt 0) {
    $wallId = $test6.result.result.elements[0].elementId
    Write-Host "`n  Using wall ID: $wallId" -ForegroundColor Yellow

    $test9 = Test-Method -TestName "TEST 9/10: getWallInfo" -Method "getWallInfo" `
        -Params @{ wallId = $wallId.ToString() } -PipeName $pipeName
    $testResults += @{ test = "getWallInfo"; passed = $test9.passed; error = $test9.error }
} else {
    Write-Host "`n[TEST 9/10: getWallInfo]" -ForegroundColor Cyan
    Write-Host "  ⚠️  SKIPPED (no walls available)" -ForegroundColor Yellow
    $testResults += @{ test = "getWallInfo"; passed = $false; error = "No walls available" }
}

# Test 10: Get Room Info (if we have rooms)
if ($test5.passed -and $test5.result.result.rooms -and $test5.result.result.rooms.Count -gt 0) {
    $roomId = $test5.result.result.rooms[0].roomId
    Write-Host "`n  Using room ID: $roomId" -ForegroundColor Yellow

    $test10 = Test-Method -TestName "TEST 10/10: getRoomInfo" -Method "getRoomInfo" `
        -Params @{ roomId = $roomId.ToString() } -PipeName $pipeName
    $testResults += @{ test = "getRoomInfo"; passed = $test10.passed; error = $test10.error }
} else {
    Write-Host "`n[TEST 10/10: getRoomInfo]" -ForegroundColor Cyan
    Write-Host "  ⚠️  SKIPPED (no rooms available)" -ForegroundColor Yellow
    $testResults += @{ test = "getRoomInfo"; passed = $false; error = "No rooms available" }
}

# Summary
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "DIAGNOSTIC SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$passedCount = ($testResults | Where-Object { $_.passed }).Count
$failedCount = ($testResults | Where-Object { -not $_.passed }).Count

Write-Host "Tests Passed: $passedCount" -ForegroundColor Green
Write-Host "Tests Failed: $failedCount`n" -ForegroundColor Red

Write-Host "Failed Tests:" -ForegroundColor Yellow
$testResults | Where-Object { -not $_.passed } | ForEach-Object {
    Write-Host "  ❌ $($_.test)" -ForegroundColor Red
    if ($_.error) {
        Write-Host "     Error: $($_.error)" -ForegroundColor Gray
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

if ($failedCount -gt 3) {
    Write-Host "⚠️  CRITICAL: Multiple methods failing!" -ForegroundColor Red
    Write-Host "`nPossible causes:" -ForegroundColor Yellow
    Write-Host "  1. Revit has an OLD VERSION of the DLL cached in memory" -ForegroundColor Yellow
    Write-Host "  2. The add-in is not properly initialized" -ForegroundColor Yellow
    Write-Host "  3. UIApplication context is not properly set up`n" -ForegroundColor Yellow

    Write-Host "RECOMMENDED ACTION:" -ForegroundColor Cyan
    Write-Host "  1. Close Revit completely" -ForegroundColor White
    Write-Host "  2. Verify DLL deployment:" -ForegroundColor White
    Write-Host "     Source: D:\RevitMCPBridge2026\bin\Release\RevitMCPBridge2026.dll" -ForegroundColor Gray
    Write-Host "     Target: C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\" -ForegroundColor Gray
    Write-Host "  3. Restart Revit" -ForegroundColor White
    Write-Host "  4. Re-run this diagnostic`n" -ForegroundColor White
} else {
    Write-Host "✅ Most methods working correctly!" -ForegroundColor Green
    Write-Host "`nNext steps: Fix the failing methods individually.`n" -ForegroundColor White
}

Write-Host "============================================================`n" -ForegroundColor Cyan
