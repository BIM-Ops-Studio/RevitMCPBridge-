# Get Building Area from Revit Project
# Connects to RevitMCPBridge2026 to extract area information

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
        if ($reader -ne $null) {
            try { $reader.Dispose() } catch {}
        }
        if ($writer -ne $null) {
            try { $writer.Dispose() } catch {}
        }
        if ($pipeClient -ne $null -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

$pipeName = "RevitMCPBridge2026"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Building Square Footage Extraction" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get all schedules to find area schedules
Write-Host "`n[1/3] Getting all schedules..." -ForegroundColor Yellow
$schedulesResponse = Send-RevitCommand -PipeName $pipeName -Method "getSchedules" -Params @{}

if ($schedulesResponse.success) {
    $schedules = $schedulesResponse.result.schedules
    Write-Host "✅ Found $($schedules.Count) schedules" -ForegroundColor Green

    # Look for area schedules
    $areaSchedules = $schedules | Where-Object {
        $_.name -like "*Area*" -or
        $_.name -like "*GSF*" -or
        $_.name -like "*Gross*" -or
        $_.name -like "*Building*"
    }

    if ($areaSchedules.Count -gt 0) {
        Write-Host "`nFound potential area schedules:" -ForegroundColor Cyan
        $areaSchedules | ForEach-Object {
            Write-Host "  - $($_.name) (ID: $($_.id))" -ForegroundColor White
        }
    }
} else {
    Write-Host "❌ Failed: $($schedulesResponse.error)" -ForegroundColor Red
}

# Get rooms to calculate total area
Write-Host "`n[2/3] Getting all rooms to calculate total area..." -ForegroundColor Yellow
$roomsResponse = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}

if ($roomsResponse.success) {
    $rooms = $roomsResponse.result.rooms

    # Filter to only this project's rooms (6 units on levels L1, L2, L3)
    $projectRooms = $rooms | Where-Object {
        $_.level -match "L[123]" -and
        $_.name -notlike "*HALLWAY*" -and
        $_.name -notlike "*MALE*" -and
        $_.name -notlike "*FEMALE*"
    }

    $totalRoomArea = ($projectRooms | Measure-Object -Property area -Sum).Sum

    Write-Host "✅ Found $($projectRooms.Count) rooms" -ForegroundColor Green
    Write-Host "   Total Room Area: $([math]::Round($totalRoomArea, 2)) SF" -ForegroundColor Cyan

    # Estimate gross building area (typically 1.3x to 1.5x of room area for residential)
    $estimatedGrossLow = $totalRoomArea * 1.3
    $estimatedGrossHigh = $totalRoomArea * 1.5

    Write-Host "`n   Estimated Gross Building Area:" -ForegroundColor Yellow
    Write-Host "   Low estimate (1.3x factor): $([math]::Round($estimatedGrossLow, 0)) SF" -ForegroundColor White
    Write-Host "   High estimate (1.5x factor): $([math]::Round($estimatedGrossHigh, 0)) SF" -ForegroundColor White
} else {
    Write-Host "❌ Failed: $($roomsResponse.error)" -ForegroundColor Red
}

# Get levels to understand building structure
Write-Host "`n[3/3] Getting building levels..." -ForegroundColor Yellow
$levelsResponse = Send-RevitCommand -PipeName $pipeName -Method "getAllLevels" -Params @{}

if ($levelsResponse.success) {
    $levels = $levelsResponse.result.levels
    $projectLevels = $levels | Where-Object { $_.name -match "L[1-4]" }

    Write-Host "✅ Found $($projectLevels.Count) levels" -ForegroundColor Green
    $projectLevels | ForEach-Object {
        Write-Host "   - $($_.name): Elevation $($_.elevation) ft" -ForegroundColor White
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "CRITICAL FOR PARKING EXEMPTION:" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "If Gross Building Area < 10,000 SF:" -ForegroundColor White
Write-Host "  + In T5 Urban Center zone" -ForegroundColor White
Write-Host "  + In Federal Opportunity Zone or designated area" -ForegroundColor White
Write-Host "  = ZERO PARKING REQUIRED per Miami 21 Article 4, Table 4" -ForegroundColor Green
Write-Host "`nYou currently have 5 spaces, which would be MORE than required!" -ForegroundColor Cyan
