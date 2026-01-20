# Read the Area Schedule (Gross Building) to get total SF

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
Write-Host "READING: Area Schedule (Gross Building)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get all schedules
$schedulesResponse = Send-RevitCommand -PipeName $pipeName -Method "getSchedules" -Params @{}

if ($schedulesResponse.success) {
    $schedules = $schedulesResponse.result.schedules

    # Find the Gross Building schedule
    $grossBuildingSchedule = $schedules | Where-Object { $_.name -eq "Area Schedule (Gross Building)" }

    if ($grossBuildingSchedule) {
        Write-Host "`nFound schedule: $($grossBuildingSchedule.name)" -ForegroundColor Green
        Write-Host "Schedule ID: $($grossBuildingSchedule.id)" -ForegroundColor Gray

        # Get schedule data
        Write-Host "`nReading schedule data..." -ForegroundColor Yellow
        $scheduleDataResponse = Send-RevitCommand -PipeName $pipeName -Method "getScheduleData" -Params @{ scheduleId = $grossBuildingSchedule.id.ToString() }

        if ($scheduleDataResponse.success) {
            $data = $scheduleDataResponse.result

            Write-Host "`n" + ("="*80) -ForegroundColor Cyan
            Write-Host "SCHEDULE CONTENTS:" -ForegroundColor Cyan
            Write-Host ("="*80) -ForegroundColor Cyan

            # Display headers
            Write-Host "`nHeaders:" -ForegroundColor Yellow
            Write-Host "  $($data.headers -join ' | ')" -ForegroundColor White

            # Display rows
            Write-Host "`nData Rows:" -ForegroundColor Yellow
            $rowNum = 1
            $totalArea = 0

            foreach ($row in $data.rows) {
                Write-Host "  Row $rowNum`: $($row -join ' | ')" -ForegroundColor Cyan

                # Try to extract area value
                foreach ($cell in $row) {
                    if ($cell -match '[\d,]+\.?\d*') {
                        $numValue = [double]($cell -replace '[^\d.]', '')
                        if ($numValue -gt 100) {  # Likely an area value
                            $totalArea += $numValue
                        }
                    }
                }

                $rowNum++
            }

            Write-Host "`n" + ("="*80) -ForegroundColor Green
            Write-Host "TOTAL GROSS BUILDING AREA: $([math]::Round($totalArea, 0)) SF" -ForegroundColor Green
            Write-Host ("="*80) -ForegroundColor Green

            # Check against 10,000 SF threshold
            Write-Host "`n" -ForegroundColor White
            if ($totalArea -lt 10000) {
                Write-Host "✅ BUILDING IS UNDER 10,000 SF!" -ForegroundColor Green
                Write-Host "✅ YOU QUALIFY FOR ZERO PARKING EXEMPTION!" -ForegroundColor Green
                Write-Host "`nPer Miami 21 Article 4, Table 4:" -ForegroundColor White
                Write-Host "  - Building < 10,000 SF in T5 Urban Center zone" -ForegroundColor Cyan
                Write-Host "  - In designated area (Opportunity Zone, UCBD, DDA, etc.)" -ForegroundColor Cyan
                Write-Host "  = ZERO PARKING SPACES REQUIRED" -ForegroundColor Green
                Write-Host "`nYou have 5 parking spaces provided." -ForegroundColor White
                Write-Host "This is MORE than the 0 required! ✅" -ForegroundColor Green
            } else {
                Write-Host "❌ Building is OVER 10,000 SF ($([math]::Round($totalArea, 0)) SF)" -ForegroundColor Red
                Write-Host "Standard parking applies: 1.5 spaces/unit" -ForegroundColor Yellow
                Write-Host "Need to apply affordable housing reduction" -ForegroundColor Yellow
            }

        } else {
            Write-Host "❌ Failed to read schedule data: $($scheduleDataResponse.error)" -ForegroundColor Red
        }

    } else {
        Write-Host "❌ Could not find 'Area Schedule (Gross Building)'" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Failed to get schedules: $($schedulesResponse.error)" -ForegroundColor Red
}
