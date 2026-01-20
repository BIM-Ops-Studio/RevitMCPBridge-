# Interactive script to modify Office 40 wall boundaries
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
Write-Host "Office 40 Wall Boundary Modifier" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "User Requirements:" -ForegroundColor Yellow
Write-Host "  - Exterior walls: Room boundary on EXTERIOR FACE" -ForegroundColor Yellow
Write-Host "  - Hallway walls: Room boundary on EXTERIOR FACE" -ForegroundColor Yellow
Write-Host "  - Interior/demising walls: Room boundary at CENTER`n" -ForegroundColor Yellow

# Step 1: Get active view
Write-Host "[1/2] Getting active view..." -ForegroundColor Cyan

$viewsResult = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{}

if (-not $viewsResult.success) {
    Write-Host "❌ Failed to get views: $($viewsResult.error)" -ForegroundColor Red
    exit 1
}

$activeView = $viewsResult.result.views | Where-Object { $_.isActive -eq $true } | Select-Object -First 1

if (-not $activeView) {
    Write-Host "❌ No active view found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Active view: $($activeView.name) (ID: $($activeView.viewId))" -ForegroundColor Green

# Step 2: Get walls in active view
Write-Host "`n[2/2] Getting walls in active view..." -ForegroundColor Cyan

$wallsResult = Send-RevitCommand -PipeName $pipeName -Method "getWallsInView" -Params @{
    viewId = $activeView.viewId.ToString()
}

if (-not $wallsResult.success) {
    Write-Host "❌ Failed to get walls: $($wallsResult.error)" -ForegroundColor Red
    exit 1
}

$walls = $wallsResult.result.walls
Write-Host "✅ Found $($walls.Count) walls in view`n" -ForegroundColor Green

if ($walls.Count -eq 0) {
    Write-Host "⚠️  No walls found in current view!" -ForegroundColor Yellow
    exit 1
}

# Display walls
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Available Walls (showing first 50):" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$walls | Select-Object -First 50 | ForEach-Object -Begin { $i = 1 } -Process {
    $lengthStr = [math]::Round($_.length, 1)
    Write-Host "$i. Wall ID $($_.wallId): $($_.wallType) (Length: $lengthStr ft, Height: $([math]::Round($_.height, 1)) ft)"
    $i++
}

# Interactive modification
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Wall Modification Options" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Choose an option:"
Write-Host "  1. Modify specific wall by ID (manual input)"
Write-Host "  2. Batch modify walls by wall type"
Write-Host "  3. Exit`n"

$choice = Read-Host "Enter choice (1-3)"

switch ($choice) {
    "1" {
        # Single wall modification
        $wallId = Read-Host "`nEnter Wall ID to modify"

        Write-Host "`nChoose location line setting:"
        Write-Host "  1. WallCenterline (interior walls)"
        Write-Host "  2. CoreCenterline"
        Write-Host "  3. FinishFaceExterior (for exterior/hallway walls)"
        Write-Host "  4. FinishFaceInterior (for demising walls)"
        Write-Host "  5. CoreExterior"
        Write-Host "  6. CoreInterior"

        $locChoice = Read-Host "`nEnter choice (1-6)"

        $locationLines = @(
            "WallCenterline",
            "CoreCenterline",
            "FinishFaceExterior",
            "FinishFaceInterior",
            "CoreExterior",
            "CoreInterior"
        )

        $locationLine = $locationLines[[int]$locChoice - 1]

        Write-Host "`nModifying Wall $wallId..." -ForegroundColor Cyan
        Write-Host "  Location Line: $locationLine" -ForegroundColor Yellow
        Write-Host "  Room Bounding: Yes`n" -ForegroundColor Yellow

        $result = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
            wallId = $wallId
            locationLine = $locationLine
            roomBounding = $true
        }

        if ($result.success) {
            Write-Host "✅ Success! Modified: $($result.result.modified -join ', ')" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed: $($result.error)" -ForegroundColor Red
        }
    }

    "2" {
        # Batch modification by wall type
        Write-Host "`nAvailable wall types:" -ForegroundColor Cyan
        $wallTypes = $walls | Group-Object wallType | Select-Object Name, Count
        $wallTypes | ForEach-Object -Begin { $i = 1 } -Process {
            Write-Host "$i. $($_.Name) ($($_.Count) walls)"
            $i++
        }

        $typeChoice = Read-Host "`nEnter wall type number to modify (or 'all' for all walls)"

        if ($typeChoice -eq "all") {
            $wallsToModify = $walls
        } else {
            $selectedType = $wallTypes[[int]$typeChoice - 1].Name
            $wallsToModify = $walls | Where-Object { $_.wallType -eq $selectedType }
        }

        Write-Host "`nChoose location line for these walls:"
        Write-Host "  1. WallCenterline"
        Write-Host "  2. CoreCenterline"
        Write-Host "  3. FinishFaceExterior"
        Write-Host "  4. FinishFaceInterior"

        $locChoice = Read-Host "`nEnter choice (1-4)"

        $locationLines = @("WallCenterline", "CoreCenterline", "FinishFaceExterior", "FinishFaceInterior")
        $locationLine = $locationLines[[int]$locChoice - 1]

        Write-Host "`nModifying $($wallsToModify.Count) walls..." -ForegroundColor Cyan

        $successCount = 0
        $failCount = 0

        foreach ($wall in $wallsToModify) {
            $result = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
                wallId = $wall.wallId.ToString()
                locationLine = $locationLine
                roomBounding = $true
            }

            if ($result.success) {
                $successCount++
                Write-Host "  ✅ Wall $($wall.wallId) modified" -ForegroundColor Green
            } else {
                $failCount++
                Write-Host "  ❌ Wall $($wall.wallId) failed: $($result.error)" -ForegroundColor Red
            }
        }

        Write-Host "`n✅ Modified $successCount walls successfully" -ForegroundColor Green
        if ($failCount -gt 0) {
            Write-Host "❌ Failed to modify $failCount walls" -ForegroundColor Red
        }
    }

    default {
        Write-Host "`nExiting without changes." -ForegroundColor Yellow
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Complete!" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
