# Get Area Plans from Revit to Calculate Total Building SF

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
Write-Host "AREA PLAN ANALYSIS - Building Square Footage" -ForegroundColor Cyan
Write-Host "Project: 20 NW 76 ST - 4-STORY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get all views to find area plans
Write-Host "`n[1/2] Getting all views to find Area Plans..." -ForegroundColor Yellow
$viewsResponse = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{}

if ($viewsResponse.success) {
    $allViews = $viewsResponse.result.views

    # Filter for area plans
    $areaPlans = $allViews | Where-Object {
        $_.viewType -eq "AreaPlan" -or
        $_.name -like "*Area*" -or
        $_.name -like "*GSF*" -or
        $_.name -like "*Gross*"
    }

    Write-Host "✅ Found $($areaPlans.Count) Area Plan(s)" -ForegroundColor Green

    if ($areaPlans.Count -gt 0) {
        Write-Host "`nArea Plans found:" -ForegroundColor Cyan
        $areaPlans | ForEach-Object {
            Write-Host "  - $($_.name) (ID: $($_.id), Type: $($_.viewType))" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  No Area Plans found. Showing all views:" -ForegroundColor Yellow
        $allViews | Select-Object -First 20 | ForEach-Object {
            Write-Host "  - $($_.name) (Type: $($_.viewType))" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "❌ Failed to get views: $($viewsResponse.error)" -ForegroundColor Red
}

# Get schedules to find area schedules
Write-Host "`n[2/2] Getting schedules to find Area Schedules..." -ForegroundColor Yellow
$schedulesResponse = Send-RevitCommand -PipeName $pipeName -Method "getSchedules" -Params @{}

if ($schedulesResponse.success) {
    $allSchedules = $schedulesResponse.result.schedules

    # Filter for area schedules
    $areaSchedules = $allSchedules | Where-Object {
        $_.name -like "*Area*" -or
        $_.name -like "*GSF*" -or
        $_.name -like "*Gross*" -or
        $_.name -like "*SF*" -or
        $_.name -like "*Square*"
    }

    Write-Host "✅ Found $($areaSchedules.Count) Area Schedule(s)" -ForegroundColor Green

    if ($areaSchedules.Count -gt 0) {
        Write-Host "`nArea Schedules:" -ForegroundColor Cyan
        $areaSchedules | ForEach-Object {
            Write-Host "`n  Schedule: $($_.name) (ID: $($_.id))" -ForegroundColor Yellow
            Write-Host "  Type: $($_.scheduleType)" -ForegroundColor White

            # Try to get schedule data
            $scheduleDataResponse = Send-RevitCommand -PipeName $pipeName -Method "getScheduleData" -Params @{ scheduleId = $_.id.ToString() }

            if ($scheduleDataResponse.success) {
                $scheduleData = $scheduleDataResponse.result

                Write-Host "  Headers: $($scheduleData.headers -join ', ')" -ForegroundColor Gray
                Write-Host "  Rows: $($scheduleData.rows.Count)" -ForegroundColor Gray

                # Display schedule data
                if ($scheduleData.rows.Count -gt 0) {
                    $scheduleData.rows | ForEach-Object {
                        $rowData = $_
                        Write-Host "    $($rowData -join ' | ')" -ForegroundColor Cyan
                    }

                    # Calculate total if there's an area column
                    $areaColumnIndex = -1
                    for ($i = 0; $i -lt $scheduleData.headers.Count; $i++) {
                        if ($scheduleData.headers[$i] -like "*Area*" -or
                            $scheduleData.headers[$i] -like "*SF*" -or
                            $scheduleData.headers[$i] -like "*Square*") {
                            $areaColumnIndex = $i
                            break
                        }
                    }

                    if ($areaColumnIndex -ge 0) {
                        $totalArea = 0
                        $scheduleData.rows | ForEach-Object {
                            $value = $_[$areaColumnIndex]
                            if ($value -match '[\d,]+\.?\d*') {
                                $numValue = [double]($value -replace '[^\d.]', '')
                                $totalArea += $numValue
                            }
                        }
                        Write-Host "`n  TOTAL AREA FROM THIS SCHEDULE: $([math]::Round($totalArea, 2)) SF" -ForegroundColor Green
                    }
                }
            }
        }
    } else {
        Write-Host "⚠️  No Area Schedules found." -ForegroundColor Yellow
        Write-Host "`nAll schedules:" -ForegroundColor Gray
        $allSchedules | ForEach-Object {
            Write-Host "  - $($_.name)" -ForegroundColor DarkGray
        }
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "PARKING EXEMPTION THRESHOLD CHECK" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Miami 21 Article 4, Table 4:" -ForegroundColor White
Write-Host "  Buildings < 10,000 SF in T5 zones = ZERO PARKING REQUIRED" -ForegroundColor Green
Write-Host "  (if in designated areas: Opportunity Zones, UCBD, DDA, etc.)" -ForegroundColor White
