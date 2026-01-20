# Find walls by view name and modify them
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
Write-Host "Wall Finder and Modifier for Office 40" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Step 1: Get all views to find the floor plan
Write-Host "[1/3] Getting all views..." -ForegroundColor Yellow

$viewsResult = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{ viewType = "FloorPlan" }

if (-not $viewsResult.success) {
    Write-Host "❌ Failed to get views: $($viewsResult.error)" -ForegroundColor Red
    exit 1
}

$views = $viewsResult.result.views

Write-Host "✅ Found $($views.Count) floor plan views`n" -ForegroundColor Green

# Find the Level 7 floor plan
$level7View = $views | Where-Object { $_.viewName -like "*LEVEL-7*" -or $_.viewName -like "*Level 7*" } | Select-Object -First 1

if (-not $level7View) {
    Write-Host "Available floor plans:" -ForegroundColor Cyan
    $views | Select-Object -First 20 | ForEach-Object {
        Write-Host "  - $($_.viewName) (ID: $($_.viewId))"
    }

    Write-Host "`nEnter the View ID to use:" -ForegroundColor Yellow
    $viewId = Read-Host "View ID"
} else {
    Write-Host "✅ Found view: $($level7View.viewName) (ID: $($level7View.viewId))" -ForegroundColor Green
    $viewId = $level7View.viewId
}

# Step 2: Get walls in this view
Write-Host "`n[2/3] Getting walls in view $viewId..." -ForegroundColor Yellow

$wallsResult = Send-RevitCommand -PipeName $pipeName -Method "getWallsInView" -Params @{
    viewId = $viewId.ToString()
}

if (-not $wallsResult.success) {
    Write-Host "❌ Failed to get walls: $($wallsResult.error)" -ForegroundColor Red
    exit 1
}

$walls = $wallsResult.result.walls
Write-Host "✅ Found $($walls.Count) walls in view`n" -ForegroundColor Green

if ($walls.Count -eq 0) {
    Write-Host "❌ No walls found in this view!" -ForegroundColor Red
    exit 1
}

# Step 3: Display walls and allow modification
Write-Host "[3/3] Walls in view (showing first 100):" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$walls | Select-Object -First 100 | ForEach-Object {
    $lengthStr = [math]::Round($_.length, 1)
    Write-Host "Wall ID $($_.wallId): $($_.wallType) (Length: $lengthStr ft)"
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Modification Options" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Settings for Office 40 room boundaries:" -ForegroundColor Yellow
Write-Host "  - Exterior walls → FinishFaceExterior" -ForegroundColor Yellow
Write-Host "  - Hallway walls → FinishFaceExterior" -ForegroundColor Yellow
Write-Host "  - Interior/demising walls → WallCenterline`n" -ForegroundColor Yellow

Write-Host "Enter Wall ID to modify (or 'exit' to quit):" -ForegroundColor Cyan
$wallId = Read-Host "Wall ID"

if ($wallId -eq "exit") {
    Write-Host "Exiting..." -ForegroundColor Yellow
    exit 0
}

Write-Host "`nChoose location line:"
Write-Host "  1. WallCenterline (interior/demising)"
Write-Host "  2. CoreCenterline"
Write-Host "  3. FinishFaceExterior (exterior/hallway)"
Write-Host "  4. FinishFaceInterior"

$locChoice = Read-Host "`nChoice (1-4)"

$locationLines = @("WallCenterline", "CoreCenterline", "FinishFaceExterior", "FinishFaceInterior")
$locationLine = $locationLines[[int]$locChoice - 1]

Write-Host "`nModifying Wall $wallId..." -ForegroundColor Cyan

$result = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
    wallId = $wallId
    locationLine = $locationLine
    roomBounding = $true
}

if ($result.success) {
    Write-Host "✅ SUCCESS! Modified: $($result.result.modified -join ', ')" -ForegroundColor Green

    $another = Read-Host "`nModify another wall? (y/n)"
    if ($another -eq "y") {
        & $PSCommandPath
    }
} else {
    Write-Host "❌ Failed: $($result.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Done!" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
