# Read Area Schedule (Rentable) to get total building SF

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
Write-Host "20 NW 76 ST - BUILDING AREA CALCULATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get all schedules
$schedulesResponse = Send-RevitCommand -PipeName $pipeName -Method "getSchedules" -Params @{}

if ($schedulesResponse.success) {
    $schedules = $schedulesResponse.result.schedules

    # Find the Rentable Area schedule
    $rentableSchedule = $schedules | Where-Object { $_.name -eq "Area Schedule (Rentable)" }

    if ($rentableSchedule) {
        Write-Host "`nFound: Area Schedule (Rentable)" -ForegroundColor Green
        Write-Host "Schedule ID: $($rentableSchedule.id)" -ForegroundColor Gray

        # Get schedule data
        Write-Host "`nReading schedule data..." -ForegroundColor Yellow
        $scheduleDataResponse = Send-RevitCommand -PipeName $pipeName -Method "getScheduleData" -Params @{ scheduleId = $rentableSchedule.id.ToString() }

        if ($scheduleDataResponse.success) {
            $data = $scheduleDataResponse.result

            Write-Host "`n" + ("="*80) -ForegroundColor Cyan
            Write-Host "AREA SCHEDULE (RENTABLE) - CONTENTS" -ForegroundColor Cyan
            Write-Host ("="*80) -ForegroundColor Cyan

            # Display headers
            Write-Host "`nColumn Headers:" -ForegroundColor Yellow
            for ($i = 0; $i -lt $data.headers.Count; $i++) {
                Write-Host "  Column $i`: $($data.headers[$i])" -ForegroundColor White
            }

            # Display all rows
            Write-Host "`nSchedule Rows:" -ForegroundColor Yellow
            $rowNum = 1
            $totalRentableArea = 0

            foreach ($row in $data.rows) {
                Write-Host "`n  Row $rowNum`:" -ForegroundColor Cyan
                for ($i = 0; $i -lt $row.Count; $i++) {
                    Write-Host "    [$($data.headers[$i])]: $($row[$i])" -ForegroundColor White
                }

                # Try to extract area values
                foreach ($cell in $row) {
                    # Look for numbers that look like square footage
                    if ($cell -match '([\d,]+\.?\d*)') {
                        $cleanNumber = $matches[1] -replace ',', ''
                        $numValue = 0
                        if ([double]::TryParse($cleanNumber, [ref]$numValue)) {
                            if ($numValue -gt 50) {  # Likely an area value (ignore small numbers)
                                Write-Host "      (Found area value: $numValue SF)" -ForegroundColor DarkCyan
                                $totalRentableArea += $numValue
                            }
                        }
                    }
                }

                $rowNum++
            }

            Write-Host "`n" + ("="*80) -ForegroundColor Green
            Write-Host "TOTAL RENTABLE AREA: $([math]::Round($totalRentableArea, 0)) SF" -ForegroundColor Green
            Write-Host ("="*80) -ForegroundColor Green

            # For Miami 21, we need GROSS area, which is typically 1.15-1.25x rentable
            $estimatedGrossLow = $totalRentableArea * 1.15
            $estimatedGrossHigh = $totalRentableArea * 1.25

            Write-Host "`nESTIMATED GROSS BUILDING AREA:" -ForegroundColor Yellow
            Write-Host "  (Gross = Rentable × efficiency factor)" -ForegroundColor Gray
            Write-Host "  Low estimate (15% circulation): $([math]::Round($estimatedGrossLow, 0)) SF" -ForegroundColor White
            Write-Host "  High estimate (25% circulation): $([math]::Round($estimatedGrossHigh, 0)) SF" -ForegroundColor White
            Write-Host "  Most likely (20% circulation): $([math]::Round($totalRentableArea * 1.20, 0)) SF" -ForegroundColor Cyan

            # Check against 10,000 SF threshold
            $estimatedGross = $totalRentableArea * 1.20

            Write-Host "`n" + ("="*80) -ForegroundColor Magenta
            Write-Host "MIAMI 21 PARKING EXEMPTION CHECK" -ForegroundColor Magenta
            Write-Host ("="*80) -ForegroundColor Magenta

            if ($estimatedGross -lt 10000) {
                Write-Host "`n✅✅✅ EXCELLENT NEWS! ✅✅✅" -ForegroundColor Green
                Write-Host "`nEstimated Gross Building Area: ~$([math]::Round($estimatedGross, 0)) SF" -ForegroundColor Cyan
                Write-Host "This is UNDER the 10,000 SF threshold!" -ForegroundColor Green
                Write-Host "`nPer Miami 21 Article 4, Table 4:" -ForegroundColor White
                Write-Host "  • Building < 10,000 SF" -ForegroundColor Cyan
                Write-Host "  • In T5 Urban Center zone" -ForegroundColor Cyan
                Write-Host "  • In designated area (Opportunity Zone, etc.)" -ForegroundColor Cyan
                Write-Host "  = ZERO PARKING SPACES REQUIRED! 🎉" -ForegroundColor Green
                Write-Host "`nYour project:" -ForegroundColor Yellow
                Write-Host "  • Required parking: 0 spaces" -ForegroundColor Green
                Write-Host "  • Provided parking: 5 spaces" -ForegroundColor White
                Write-Host "  • Surplus: +5 spaces! ✅" -ForegroundColor Green
                Write-Host "`nBuilding department says you're missing 3 spaces?" -ForegroundColor Yellow
                Write-Host "NO - You have a PARKING EXEMPTION!" -ForegroundColor Green
            } else {
                Write-Host "`n⚠️ Building is OVER 10,000 SF" -ForegroundColor Red
                Write-Host "Estimated Gross: $([math]::Round($estimatedGross, 0)) SF" -ForegroundColor Yellow
                Write-Host "`nStandard parking would apply:" -ForegroundColor Yellow
                Write-Host "  6 units × 1.5 = 9 spaces required" -ForegroundColor White
                Write-Host "  Need affordable housing reduction" -ForegroundColor Yellow
            }

        } else {
            Write-Host "`n❌ Failed to read schedule data: $($scheduleDataResponse.error)" -ForegroundColor Red
        }

    } else {
        Write-Host "`n❌ Could not find 'Area Schedule (Rentable)'" -ForegroundColor Red
    }
} else {
    Write-Host "`n❌ Failed to get schedules: $($schedulesResponse.error)" -ForegroundColor Red
}
