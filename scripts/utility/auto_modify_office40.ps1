# Automated Wall Modification for Office 40
function Send-RevitCommand {
    param([string]$PipeName, [string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        if (-not $pipeClient.IsConnected) { throw "Failed to connect" }
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        if ([string]::IsNullOrEmpty($response)) { throw "Empty response" }
        return $response | ConvertFrom-Json
    } catch {
        return @{ success = $false; error = $_.Exception.Message }
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

$pipeName = "RevitMCPBridge2026"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Office 40 - Automated Wall Modification Test" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Step 1: Find Office 40
Write-Host "[1/4] Finding Office 40..." -ForegroundColor Cyan
$roomsResult = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}

if (-not $roomsResult.success) {
    Write-Host "❌ Failed to get rooms: $($roomsResult.error)" -ForegroundColor Red
    exit 1
}

$office40 = $roomsResult.rooms | Where-Object { $_.number -eq "40" } | Select-Object -First 1

if (-not $office40) {
    Write-Host "❌ Office 40 not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found Office 40!" -ForegroundColor Green
Write-Host "   Room ID: $($office40.roomId)" -ForegroundColor Gray
Write-Host "   Name: $($office40.name)" -ForegroundColor Gray
Write-Host "   Area: $([math]::Round($office40.area, 1)) sq ft`n" -ForegroundColor Gray

# Step 2: Get views
Write-Host "[2/4] Getting Level 7 floor plan..." -ForegroundColor Cyan
$viewsResult = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{}

if (-not $viewsResult.success) {
    Write-Host "❌ Failed to get views: $($viewsResult.error)" -ForegroundColor Red
    exit 1
}

$level7View = $viewsResult.views | Where-Object { $_.viewName -like "*LEVEL-7*" } | Select-Object -First 1

if (-not $level7View) {
    Write-Host "❌ Level 7 view not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found view: $($level7View.viewName)`n" -ForegroundColor Green

# Step 3: Get walls in view
Write-Host "[3/4] Getting walls in view..." -ForegroundColor Cyan
$wallsResult = Send-RevitCommand -PipeName $pipeName -Method "getWallsInView" -Params @{
    viewId = $level7View.viewId.ToString()
}

if (-not $wallsResult.success) {
    Write-Host "❌ Failed to get walls: $($wallsResult.error)" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found $($wallsResult.wallCount) walls`n" -ForegroundColor Green

# Step 4: Modify test walls automatically
Write-Host "[4/4] Modifying test walls..." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Test 1: Modify an interior partition wall to WallCenterline
$interiorWall = $wallsResult.walls | Where-Object { $_.wallType -like "*Interior*Partition*" } | Select-Object -First 1

if ($interiorWall) {
    Write-Host "Test 1: Modifying interior partition wall..." -ForegroundColor Yellow
    Write-Host "  Wall ID: $($interiorWall.wallId)" -ForegroundColor Gray
    Write-Host "  Wall Type: $($interiorWall.wallType)" -ForegroundColor Gray
    Write-Host "  Setting: WallCenterline" -ForegroundColor Gray

    $result1 = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
        wallId = $interiorWall.wallId.ToString()
        locationLine = "WallCenterline"
        roomBounding = $true
    }

    if ($result1.success) {
        Write-Host "  ✅ SUCCESS! Modified: $($result1.modified -join ', ')`n" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed: $($result1.error)`n" -ForegroundColor Red
    }
}

# Test 2: Modify a generic wall to FinishFaceExterior
$genericWall = $wallsResult.walls | Where-Object { $_.wallType -like "*Generic*" } | Select-Object -First 1

if ($genericWall) {
    Write-Host "Test 2: Modifying generic wall (exterior/hallway)..." -ForegroundColor Yellow
    Write-Host "  Wall ID: $($genericWall.wallId)" -ForegroundColor Gray
    Write-Host "  Wall Type: $($genericWall.wallType)" -ForegroundColor Gray
    Write-Host "  Setting: FinishFaceExterior" -ForegroundColor Gray

    $result2 = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
        wallId = $genericWall.wallId.ToString()
        locationLine = "FinishFaceExterior"
        roomBounding = $true
    }

    if ($result2.success) {
        Write-Host "  ✅ SUCCESS! Modified: $($result2.modified -join ', ')`n" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed: $($result2.error)`n" -ForegroundColor Red
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Automated Test Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nCheck Office 40 in Revit to see the wall boundary changes." -ForegroundColor Yellow
Write-Host "The room area should recalculate based on the new wall locations.`n" -ForegroundColor Yellow
