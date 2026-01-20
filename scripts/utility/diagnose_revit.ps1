# Comprehensive Revit diagnostic script
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
        Write-Host "ERROR: $_" -ForegroundColor Red
        return @{
            success = $false
            error = $_.Exception.Message
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

$pipeName = "RevitMCPBridge2026"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Revit Connection Diagnostic" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Test 1: Check connection
Write-Host "[1/4] Testing MCP connection..." -ForegroundColor Yellow
$testResult = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}
if ($testResult.success) {
    Write-Host "✅ MCP connection successful!" -ForegroundColor Green
} else {
    Write-Host "❌ MCP connection failed: $($testResult.error)" -ForegroundColor Red
    Write-Host "`nMake sure:" -ForegroundColor Yellow
    Write-Host "  1. Revit is running" -ForegroundColor Yellow
    Write-Host "  2. RevitMCPBridge2026 add-in is loaded" -ForegroundColor Yellow
    Write-Host "  3. Named pipe 'RevitMCPBridge2026' is accessible" -ForegroundColor Yellow
    exit 1
}

# Test 2: Get all levels
Write-Host "`n[2/4] Getting all levels in the model..." -ForegroundColor Yellow
$levelsResult = Send-RevitCommand -PipeName $pipeName -Method "getAllLevels" -Params @{}

if ($levelsResult.success) {
    $levels = $levelsResult.result
    Write-Host "✅ Found $($levels.Count) levels:" -ForegroundColor Green
    $levels | Sort-Object elevation | ForEach-Object {
        Write-Host "  - $($_.name) (ID: $($_.levelId), Elevation: $([math]::Round($_.elevation, 2)) ft)"
    }
} else {
    Write-Host "❌ Failed to get levels: $($levelsResult.error)" -ForegroundColor Red
}

# Test 3: Get all views
Write-Host "`n[3/4] Getting all views..." -ForegroundColor Yellow
$viewsResult = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{}

if ($viewsResult.success) {
    $views = $viewsResult.result.views
    $activeView = $views | Where-Object { $_.isActive -eq $true } | Select-Object -First 1

    Write-Host "✅ Found $($views.Count) views" -ForegroundColor Green

    if ($activeView) {
        Write-Host "`nActive View:" -ForegroundColor Cyan
        Write-Host "  - Name: $($activeView.name)" -ForegroundColor Green
        Write-Host "  - Type: $($activeView.viewType)" -ForegroundColor Green
        Write-Host "  - ID: $($activeView.viewId)" -ForegroundColor Green
    }

    $floorPlans = $views | Where-Object { $_.viewType -eq "FloorPlan" }
    if ($floorPlans) {
        Write-Host "`nAvailable Floor Plans:" -ForegroundColor Cyan
        $floorPlans | Select-Object -First 10 | ForEach-Object {
            $activeMarker = if ($_.viewId -eq $activeView.viewId) { " (ACTIVE)" } else { "" }
            Write-Host "  - $($_.name) (ID: $($_.viewId))$activeMarker"
        }
    }
} else {
    Write-Host "❌ Failed to get views: $($viewsResult.error)" -ForegroundColor Red
}

# Test 4: Get rooms (ALL rooms, not just in current view)
Write-Host "`n[4/4] Checking for rooms in the document..." -ForegroundColor Yellow
$roomsResult = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}

if ($roomsResult.success) {
    $rooms = $roomsResult.result.rooms
    Write-Host "Found $($rooms.Count) rooms (with Area > 0)" -ForegroundColor $(if ($rooms.Count -gt 0) { "Green" } else { "Yellow" })

    if ($rooms.Count -gt 0) {
        Write-Host "`nRooms in document:" -ForegroundColor Cyan
        $rooms | Sort-Object number | Select-Object -First 20 | ForEach-Object {
            $areaStr = [math]::Round($_.area, 1)
            Write-Host "  - Room $($_.number): $($_.name) ($areaStr sq ft, Level: $($_.level), ID: $($_.roomId))"
        }

        # Look for Office 40
        Write-Host "`nSearching for Office 40..." -ForegroundColor Cyan
        $office40 = $rooms | Where-Object {
            $_.number -eq "40" -or
            $_.number -eq "040" -or
            $_.name -like "*Office 40*" -or
            $_.name -like "*40*" -or
            $_.number -like "*40"
        }

        if ($office40) {
            Write-Host "✅ Found possible matches:" -ForegroundColor Green
            $office40 | ForEach-Object {
                Write-Host "  - Room $($_.number): $($_.name) (ID: $($_.roomId), Level: $($_.level))"
            }
        } else {
            Write-Host "⚠️  No room found matching '40' or 'Office 40'" -ForegroundColor Yellow
            Write-Host "`nAll room numbers in model:" -ForegroundColor Cyan
            $rooms | Sort-Object number | ForEach-Object {
                Write-Host "  $($_.number)"
            }
        }
    } else {
        Write-Host "`n⚠️  No rooms found with Area > 0" -ForegroundColor Yellow
        Write-Host "`nPossible reasons:" -ForegroundColor Yellow
        Write-Host "  1. Rooms are not placed (unbounded)" -ForegroundColor Yellow
        Write-Host "  2. Room boundaries are not closed" -ForegroundColor Yellow
        Write-Host "  3. You're in the wrong project file" -ForegroundColor Yellow
        Write-Host "`nPlease:" -ForegroundColor Cyan
        Write-Host "  1. Open a floor plan view in Revit" -ForegroundColor Cyan
        Write-Host "  2. Make sure Office 40 is visible and bounded" -ForegroundColor Cyan
        Write-Host "  3. Re-run this diagnostic" -ForegroundColor Cyan
    }
} else {
    Write-Host "❌ Failed to get rooms: $($roomsResult.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Diagnostic Complete!" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
