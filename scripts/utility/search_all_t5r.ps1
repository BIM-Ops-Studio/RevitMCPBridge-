# Search ALL views for T5-R text

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
Write-Host "SEARCHING ENTIRE PROJECT FOR 'T5-R' TEXT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get all views
Write-Host "`nGetting all views..." -ForegroundColor Yellow
$viewsResult = Send-RevitCommand -PipeName $pipeName -Method "getViews" -Params @{}

if ($viewsResult.success) {
    $allViews = $viewsResult.result.views
    Write-Host "Found $($allViews.Count) views total" -ForegroundColor Green

    $foundLocations = @()

    Write-Host "`nSearching each view for T5-R text..." -ForegroundColor Yellow
    $progressCount = 0

    foreach ($view in $allViews) {
        $progressCount++
        if ($progressCount % 20 -eq 0) {
            Write-Host "  Searched $progressCount views..." -ForegroundColor Gray
        }

        # Get text notes in this view
        $textResult = Send-RevitCommand -PipeName $pipeName -Method "getTextNotesInView" -Params @{
            viewId = $view.id.ToString()
        }

        if ($textResult.success) {
            $textNotes = $textResult.result.textNotes

            # Check for T5-R in any text
            $t5rNotes = $textNotes | Where-Object {
                $_.text -eq "T5-R" -or $_.text -like "*T5-R*"
            }

            if ($t5rNotes) {
                foreach ($note in $t5rNotes) {
                    $foundLocations += @{
                        viewName = $view.name
                        viewId = $view.id
                        viewType = $view.viewType
                        textId = $note.textNoteId
                        text = $note.text
                    }
                    Write-Host "`nFOUND in view: $($view.name)" -ForegroundColor Green
                    Write-Host "  View Type: $($view.viewType)" -ForegroundColor White
                    Write-Host "  View ID: $($view.id)" -ForegroundColor Gray
                    Write-Host "  Text ID: $($note.textNoteId)" -ForegroundColor Yellow
                    Write-Host "  Text: '$($note.text)'" -ForegroundColor Cyan
                }
            }
        }
    }

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "SEARCH COMPLETE" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Searched $progressCount views" -ForegroundColor White
    Write-Host "Found T5-R in $($foundLocations.Count) location(s)" -ForegroundColor Green

    if ($foundLocations.Count -gt 0) {
        Write-Host "`nREADY TO UPDATE:" -ForegroundColor Yellow
        foreach ($loc in $foundLocations) {
            Write-Host "`n  View: $($loc.viewName) ($($loc.viewType))" -ForegroundColor Cyan
            Write-Host "  Text to update: '$($loc.text)'" -ForegroundColor White
            Write-Host "  Text ID: $($loc.textId)" -ForegroundColor Gray

            # Update this text
            Write-Host "  Updating to 'T5-O'..." -ForegroundColor Yellow
            $updateResult = Send-RevitCommand -PipeName $pipeName -Method "modifyTextNote" -Params @{
                elementId = $loc.textId.ToString()
                text = "T5-O"
            }

            if ($updateResult.success) {
                Write-Host "  SUCCESS! Updated!" -ForegroundColor Green
            } else {
                Write-Host "  FAILED: $($updateResult.error)" -ForegroundColor Red
            }
        }

        Write-Host "`n============================================================" -ForegroundColor Green
        Write-Host "ALL UPDATES COMPLETE!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
    } else {
        Write-Host "`nNo T5-R text found in any view" -ForegroundColor Red
        Write-Host "The text may be in a different format (table, schedule, or model element)" -ForegroundColor Yellow
    }
} else {
    Write-Host "FAILED: $($viewsResult.error)" -ForegroundColor Red
}
