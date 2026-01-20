# Capture current Revit view and get room/wall information
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
Write-Host "Capturing Current Revit View" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Step 1: Export current view as image
Write-Host "[1/3] Exporting current view image..." -ForegroundColor Yellow

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$imagePath = "D:\RevitMCPBridge2026\floor_plan_$timestamp.png"

$exportResult = Send-RevitCommand -PipeName $pipeName -Method "exportViewImage" -Params @{
    outputPath = $imagePath
}

if ($exportResult.success) {
    Write-Host "✅ View exported to: $imagePath" -ForegroundColor Green

    # Open the image
    if (Test-Path $imagePath) {
        Write-Host "   Opening image..." -ForegroundColor Cyan
        Start-Process $imagePath
    }
} else {
    Write-Host "❌ Failed to export view: $($exportResult.error)" -ForegroundColor Red
}

# Step 2: Get all rooms
Write-Host "`n[2/3] Getting all rooms in document..." -ForegroundColor Yellow

$roomsResult = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}

if ($roomsResult.success) {
    $rooms = $roomsResult.result.rooms
    Write-Host "✅ Found $($rooms.Count) rooms" -ForegroundColor Green

    if ($rooms.Count -gt 0) {
        Write-Host "`nAll rooms:" -ForegroundColor Cyan
        $rooms | Sort-Object number | ForEach-Object {
            $marker = if ($_.number -eq "40") { " ← OFFICE 40" } else { "" }
            Write-Host "  - Room $($_.number): $($_.name) ($([math]::Round($_.area, 1)) sq ft)$marker" -ForegroundColor $(if ($_.number -eq "40") { "Green" } else { "White" })
        }

        # Find Office 40
        $office40 = $rooms | Where-Object { $_.number -eq "40" }

        if ($office40) {
            Write-Host "`n✅ Found Office 40!" -ForegroundColor Green
            Write-Host "   Room ID: $($office40.roomId)" -ForegroundColor Cyan
            Write-Host "   Name: $($office40.name)" -ForegroundColor Cyan
            Write-Host "   Area: $([math]::Round($office40.area, 1)) sq ft" -ForegroundColor Cyan
            Write-Host "   Level: $($office40.level)" -ForegroundColor Cyan
        }
    }
} else {
    Write-Host "❌ Failed: $($roomsResult.error)" -ForegroundColor Red
}

# Step 3: Get walls in current view
Write-Host "`n[3/3] Getting walls in current view..." -ForegroundColor Yellow

$wallsResult = Send-RevitCommand -PipeName $pipeName -Method "getWallsInView" -Params @{}

if ($wallsResult.success) {
    $walls = $wallsResult.result.walls
    Write-Host "✅ Found $($walls.Count) walls in current view" -ForegroundColor Green

    if ($walls.Count -gt 0) {
        Write-Host "`nWalls (showing first 20):" -ForegroundColor Cyan
        $walls | Select-Object -First 20 | ForEach-Object {
            Write-Host "  - Wall ID $($_.wallId): $($_.wallType) (Length: $([math]::Round($_.length, 1)) ft)"
        }
    }
} else {
    Write-Host "❌ Failed: $($wallsResult.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Capture Complete!" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
