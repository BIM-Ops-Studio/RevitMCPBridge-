# Final Office 40 Wall Modification Script
# This script finds Office 40, gets walls, and allows modification

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
Write-Host "Office 40 - Wall Boundary Modifier (FINAL)" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Target Settings:" -ForegroundColor Yellow
Write-Host "  • Exterior walls → FinishFaceExterior" -ForegroundColor Yellow
Write-Host "  • Hallway walls → FinishFaceExterior" -ForegroundColor Yellow
Write-Host "  • Interior walls → WallCenterline`n" -ForegroundColor Yellow

# Step 1: Find Office 40
Write-Host "[Step 1/4] Finding Office 40..." -ForegroundColor Cyan

$roomsResult = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}

if (-not $roomsResult.success) {
    Write-Host "❌ Failed to get rooms: $($roomsResult.error)" -ForegroundColor Red
    exit 1
}

Write-Host "  Found $($roomsResult.roomCount) total rooms" -ForegroundColor Gray

$office40 = $roomsResult.rooms | Where-Object { $_.number -eq "40" } | Select-Object -First 1

if (-not $office40) {
    Write-Host "❌ Office 40 not found!" -ForegroundColor Red
    Write-Host "`nAvailable rooms:" -ForegroundColor Yellow
    $roomsResult.rooms | Select-Object -First 20 | ForEach-Object {
        Write-Host "  - Room $($_.number): $($_.name)" -ForegroundColor Gray
    }
    exit 1
}

Write-Host "✅ Found Office 40!" -ForegroundColor Green
Write-Host "   Room ID: $($office40.roomId)" -ForegroundColor Gray
Write-Host "   Name: $($office40.name)" -ForegroundColor Gray
Write-Host "   Area: $([math]::Round($office40.area, 1)) sq ft" -ForegroundColor Gray
Write-Host "   Level: $($office40.level)" -ForegroundColor Gray

# Step 2: Get all views
Write-Host "`n[Step 2/4] Getting floor plan views..." -ForegroundColor Cyan

$viewsResult = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{}

if (-not $viewsResult.success) {
    Write-Host "❌ Failed to get views: $($viewsResult.error)" -ForegroundColor Red
    exit 1
}

$floorPlans = $viewsResult.views | Where-Object { $_.viewType -eq "FloorPlan" }

Write-Host "  Found $($floorPlans.Count) floor plan views" -ForegroundColor Gray

# Try to find Level 7 or ask user
$level7View = $floorPlans | Where-Object { $_.viewName -like "*LEVEL-7*" -or $_.viewName -like "*Level 7*" } | Select-Object -First 1

if ($level7View) {
    $viewId = $level7View.viewId
    Write-Host "✅ Using view: $($level7View.viewName) (ID: $viewId)" -ForegroundColor Green
} else {
    Write-Host "`nAvailable floor plan views:" -ForegroundColor Yellow
    for ($i = 0; $i -lt [Math]::Min(10, $floorPlans.Count); $i++) {
        Write-Host "  $($i+1). $($floorPlans[$i].viewName) (ID: $($floorPlans[$i].viewId))" -ForegroundColor Gray
    }

    $choice = Read-Host "`nEnter view number to use (1-$([Math]::Min(10, $floorPlans.Count)))"
    $viewId = $floorPlans[[int]$choice - 1].viewId
    Write-Host "✅ Using view ID: $viewId" -ForegroundColor Green
}

# Step 3: Get walls in view
Write-Host "`n[Step 3/4] Getting walls in view..." -ForegroundColor Cyan

$wallsResult = Send-RevitCommand -PipeName $pipeName -Method "getWallsInView" -Params @{
    viewId = $viewId.ToString()
}

if (-not $wallsResult.success) {
    Write-Host "❌ Failed to get walls: $($wallsResult.error)" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found $($wallsResult.wallCount) walls in view`n" -ForegroundColor Green

# Step 4: Interactive wall modification
Write-Host "[Step 4/4] Wall Modification" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Walls in view (showing first 50):" -ForegroundColor Yellow
$wallsResult.walls | Select-Object -First 50 | ForEach-Object {
    $lengthStr = [math]::Round($_.length, 1)
    Write-Host "  Wall ID $($_.wallId): $($_.wallType) ($lengthStr ft)" -ForegroundColor Gray
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Ready to modify walls!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Options:" -ForegroundColor Yellow
Write-Host "  1. Modify a single wall by ID" -ForegroundColor White
Write-Host "  2. Exit`n" -ForegroundColor White

$choice = Read-Host "Choice (1-2)"

if ($choice -eq "1") {
    $wallId = Read-Host "`nEnter Wall ID"

    Write-Host "`nLocation Line options:" -ForegroundColor Yellow
    Write-Host "  1. WallCenterline (for interior walls)" -ForegroundColor White
    Write-Host "  2. CoreCenterline" -ForegroundColor White
    Write-Host "  3. FinishFaceExterior (for exterior/hallway walls)" -ForegroundColor White
    Write-Host "  4. FinishFaceInterior`n" -ForegroundColor White

    $locChoice = Read-Host "Choice (1-4)"

    $locationLines = @("WallCenterline", "CoreCenterline", "FinishFaceExterior", "FinishFaceInterior")
    $locationLine = $locationLines[[int]$locChoice - 1]

    Write-Host "`nModifying Wall $wallId to $locationLine..." -ForegroundColor Cyan

    $modifyResult = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
        wallId = $wallId
        locationLine = $locationLine
        roomBounding = $true
    }

    if ($modifyResult.success) {
        Write-Host "✅ SUCCESS! Wall modified." -ForegroundColor Green
        Write-Host "   Modified: $($modifyResult.result.modified -join ', ')" -ForegroundColor Green

        $another = Read-Host "`nModify another wall? (y/n)"
        if ($another -eq "y") {
            & $PSCommandPath
        }
    } else {
        Write-Host "❌ Failed: $($modifyResult.error)" -ForegroundColor Red
    }
} else {
    Write-Host "`nExiting..." -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Done! Check Office 40 in Revit to see room boundary changes." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
