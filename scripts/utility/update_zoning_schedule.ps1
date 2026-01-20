# Update T5-R to T5-O in ZONING DATA schedule

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
Write-Host "UPDATING ZONING DATA SCHEDULE: T5-R -> T5-O" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get all schedules
Write-Host "`n[1/3] Finding ZONING DATA schedule..." -ForegroundColor Yellow
$schedulesResult = Send-RevitCommand -PipeName $pipeName -Method "getSchedules" -Params @{}

if ($schedulesResult.success) {
    $schedules = $schedulesResult.result.schedules
    Write-Host "Found $($schedules.Count) schedules" -ForegroundColor Green

    # Find ZONING DATA schedule
    $zoningSchedule = $schedules | Where-Object { $_.name -like "*ZONING*DATA*" -or $_.name -eq "ZONING DATA" }

    if ($zoningSchedule) {
        Write-Host "SUCCESS: Found schedule '$($zoningSchedule.name)'" -ForegroundColor Green
        Write-Host "  Schedule ID: $($zoningSchedule.id)" -ForegroundColor White

        # Get schedule data
        Write-Host "`n[2/3] Reading schedule data..." -ForegroundColor Yellow
        $dataResult = Send-RevitCommand -PipeName $pipeName -Method "getScheduleData" -Params @{
            scheduleId = $zoningSchedule.id.ToString()
        }

        if ($dataResult.success) {
            $scheduleData = $dataResult.result
            Write-Host "SUCCESS: Retrieved schedule data" -ForegroundColor Green
            Write-Host "  Rows: $($scheduleData.rowCount)" -ForegroundColor White
            Write-Host "  Columns: $($scheduleData.columnCount)" -ForegroundColor White

            # Search for T5-R in the data
            Write-Host "`nSearching for 'T5-R' in schedule cells..." -ForegroundColor Yellow

            $foundCell = $null
            if ($scheduleData.data) {
                for ($row = 0; $row -lt $scheduleData.data.Count; $row++) {
                    $rowData = $scheduleData.data[$row]
                    for ($col = 0; $col -lt $rowData.Count; $col++) {
                        if ($rowData[$col] -eq "T5-R") {
                            $foundCell = @{
                                row = $row
                                col = $col
                                value = $rowData[$col]
                            }
                            Write-Host "FOUND 'T5-R' at Row: $row, Column: $col" -ForegroundColor Green
                            break
                        }
                    }
                    if ($foundCell) { break }
                }
            }

            if ($foundCell) {
                # Update the cell
                Write-Host "`n[3/3] Updating cell to 'T5-O'..." -ForegroundColor Yellow
                $updateResult = Send-RevitCommand -PipeName $pipeName -Method "updateScheduleCell" -Params @{
                    scheduleId = $zoningSchedule.id.ToString()
                    rowIndex = $foundCell.row.ToString()
                    columnIndex = $foundCell.col.ToString()
                    newValue = "T5-O"
                }

                if ($updateResult.success) {
                    Write-Host "`n============================================================" -ForegroundColor Green
                    Write-Host "SUCCESS! ZONING UPDATED!" -ForegroundColor Green
                    Write-Host "============================================================" -ForegroundColor Green
                    Write-Host "  Schedule: $($zoningSchedule.name)" -ForegroundColor White
                    Write-Host "  Location: Row $($foundCell.row), Column $($foundCell.col)" -ForegroundColor White
                    Write-Host "  Old Value: T5-R" -ForegroundColor Red
                    Write-Host "  New Value: T5-O" -ForegroundColor Green
                } else {
                    Write-Host "FAILED to update cell: $($updateResult.error)" -ForegroundColor Red
                }
            } else {
                Write-Host "T5-R not found in schedule data" -ForegroundColor Yellow
                Write-Host "`nShowing first few rows of schedule:" -ForegroundColor Cyan
                if ($scheduleData.data) {
                    for ($i = 0; $i -lt [Math]::Min(5, $scheduleData.data.Count); $i++) {
                        $rowData = $scheduleData.data[$i] -join ' | '
                        Write-Host "  Row ${i}: $rowData" -ForegroundColor Gray
                    }
                }
            }
        } else {
            Write-Host "FAILED to get schedule data: $($dataResult.error)" -ForegroundColor Red
        }
    } else {
        Write-Host "ZONING DATA schedule not found" -ForegroundColor Red
        Write-Host "`nSearching for schedules with 'ZONING' in name:" -ForegroundColor Yellow
        $zoningSchedules = $schedules | Where-Object { $_.name -like "*ZONING*" }
        foreach ($sch in $zoningSchedules) {
            Write-Host "  - $($sch.name) (ID: $($sch.id))" -ForegroundColor White
        }
    }
} else {
    Write-Host "FAILED to get schedules: $($schedulesResult.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Project: 20 NW 76 ST - 4-STORY" -ForegroundColor Yellow
Write-Host "Zoning: T5-O (Urban Center - Open)" -ForegroundColor Green
Write-Host "Building Area: 8,022 SF (under 10,000 SF)" -ForegroundColor Green
Write-Host "Parking Required: 0 SPACES (EXEMPT per Miami 21 Art. 4, Table 4)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
