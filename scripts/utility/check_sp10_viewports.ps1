# Check what viewports and schedules are on SP-1.0

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
Write-Host "CHECKING SP-1.0 SHEET CONTENTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get SP-1.0 sheet
$sheetsResult = Send-RevitCommand -PipeName $pipeName -Method "getAllSheets" -Params @{}

if ($sheetsResult.success) {
    $sheets = $sheetsResult.result.sheets
    $sp10 = $sheets | Where-Object { $_.sheetNumber -eq "SP-1.0" }

    if ($sp10) {
        Write-Host "`nSheet: $($sp10.sheetNumber) - $($sp10.sheetName)" -ForegroundColor Green
        Write-Host "Sheet ID: $($sp10.id)" -ForegroundColor White

        # Get viewports on sheet
        Write-Host "`nGetting viewports on sheet..." -ForegroundColor Yellow
        $viewportsResult = Send-RevitCommand -PipeName $pipeName -Method "getViewportsOnSheet" -Params @{
            sheetId = $sp10.id.ToString()
        }

        if ($viewportsResult.success) {
            $viewports = $viewportsResult.result.viewports
            Write-Host "Found $($viewports.Count) viewport(s)" -ForegroundColor Green

            foreach ($vp in $viewports) {
                Write-Host "`n  Viewport:" -ForegroundColor Cyan
                Write-Host "    View Name: $($vp.viewName)" -ForegroundColor White
                Write-Host "    View ID: $($vp.viewId)" -ForegroundColor Gray
                Write-Host "    Viewport ID: $($vp.viewportId)" -ForegroundColor Gray

                # If this is ZONING DATA legend, get its text
                if ($vp.viewName -like "*ZONING*") {
                    Write-Host "`n    THIS IS THE ZONING DATA VIEW!" -ForegroundColor Green
                    Write-Host "    Checking for text notes..." -ForegroundColor Yellow

                    $textResult = Send-RevitCommand -PipeName $pipeName -Method "getTextNotesInView" -Params @{
                        viewId = $vp.viewId.ToString()
                    }

                    if ($textResult.success) {
                        $textNotes = $textResult.result.textNotes
                        Write-Host "    Found $($textNotes.Count) text notes" -ForegroundColor White

                        if ($textNotes.Count -gt 0) {
                            Write-Host "`n    All text in ZONING DATA legend:" -ForegroundColor Cyan
                            foreach ($note in $textNotes) {
                                $highlight = if ($note.text -eq "TN-R") { "Green" } else { "White" }
                                Write-Host "      ID: $($note.textNoteId) | Text: '$($note.text)'" -ForegroundColor $highlight
                            }

                            # Find TN-R
                            $tnrNote = $textNotes | Where-Object { $_.text -eq "TN-R" }
                            if ($tnrNote) {
                                Write-Host "`n    FOUND TN-R! Ready to update!" -ForegroundColor Green
                                Write-Host "      Text ID: $($tnrNote.textNoteId)" -ForegroundColor Yellow
                            }
                        } else {
                            Write-Host "    No text notes found - data may be in schedule/table format" -ForegroundColor Yellow
                        }
                    }
                }
            }
        } else {
            Write-Host "FAILED to get viewports: $($viewportsResult.error)" -ForegroundColor Red
        }

        # Also check for schedules on sheet
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "Checking for schedules..." -ForegroundColor Yellow

        $schedulesResult = Send-RevitCommand -PipeName $pipeName -Method "getSchedules" -Params @{}
        if ($schedulesResult.success) {
            $schedules = $schedulesResult.result.schedules
            Write-Host "Total schedules in project: $($schedules.Count)" -ForegroundColor White

            $zoningSchedules = $schedules | Where-Object { $_.name -like "*ZONING*" -or $_.name -like "*DATA*" }
            if ($zoningSchedules) {
                Write-Host "`nZoning-related schedules:" -ForegroundColor Cyan
                foreach ($sch in $zoningSchedules) {
                    Write-Host "  - $($sch.name) (ID: $($sch.id))" -ForegroundColor White
                }
            }
        }

    } else {
        Write-Host "SP-1.0 not found" -ForegroundColor Red
    }
} else {
    Write-Host "FAILED: $($sheetsResult.error)" -ForegroundColor Red
}
