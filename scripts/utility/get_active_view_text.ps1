# Get text from currently active view

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
Write-Host "GETTING TEXT FROM ACTIVE VIEW" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# First, get current view info
Write-Host "`nGetting active view info..." -ForegroundColor Yellow
$viewsResult = Send-RevitCommand -PipeName $pipeName -Method "getViews" -Params @{}

if ($viewsResult.success) {
    Write-Host "SUCCESS" -ForegroundColor Green

    # Get all views to find active one
    $allViews = $viewsResult.result.views

    # Try to get view name from project info or use a known view
    # For now, let's search for ZONING DATA in all views
    Write-Host "`nSearching all views for 'ZONING DATA'..." -ForegroundColor Yellow
    $zoningView = $allViews | Where-Object { $_.name -eq "ZONING DATA" }

    if ($zoningView) {
        Write-Host "Found ZONING DATA view!" -ForegroundColor Green
        Write-Host "  Name: $($zoningView.name)" -ForegroundColor White
        Write-Host "  ID: $($zoningView.id)" -ForegroundColor White
        Write-Host "  Type: $($zoningView.viewType)" -ForegroundColor White

        # Get text notes in ZONING DATA view
        Write-Host "`nGetting text notes in ZONING DATA view..." -ForegroundColor Yellow
        $textResult = Send-RevitCommand -PipeName $pipeName -Method "getTextNotesInView" -Params @{
            viewId = $zoningView.id.ToString()
        }

        if ($textResult.success) {
            $textNotes = $textResult.result.textNotes
            Write-Host "Found $($textNotes.Count) text notes" -ForegroundColor Green

            if ($textNotes.Count -gt 0) {
                Write-Host "`nAll text notes in ZONING DATA:" -ForegroundColor Cyan
                foreach ($note in $textNotes) {
                    $color = if ($note.text -eq "TN-R") { "Green" } else { "White" }
                    Write-Host "  ID: $($note.textNoteId) | Text: '$($note.text)'" -ForegroundColor $color
                }

                # Find and update TN-R
                $tnrNote = $textNotes | Where-Object { $_.text -eq "TN-R" }
                if ($tnrNote) {
                    Write-Host "`n============================================================" -ForegroundColor Green
                    Write-Host "FOUND TN-R TEXT!" -ForegroundColor Green
                    Write-Host "============================================================" -ForegroundColor Green
                    Write-Host "  Text ID: $($tnrNote.textNoteId)" -ForegroundColor Yellow
                    Write-Host "  Current text: '$($tnrNote.text)'" -ForegroundColor Yellow

                    Write-Host "`nUpdating TN-R -> T5-O..." -ForegroundColor Yellow
                    $updateResult = Send-RevitCommand -PipeName $pipeName -Method "modifyTextNote" -Params @{
                        elementId = $tnrNote.textNoteId.ToString()
                        text = "T5-O"
                    }

                    if ($updateResult.success) {
                        Write-Host "`nSUCCESS! ZONING UPDATED!" -ForegroundColor Green
                        Write-Host "  Old: TN-R" -ForegroundColor Red
                        Write-Host "  New: T5-O" -ForegroundColor Green
                        Write-Host "`n============================================================" -ForegroundColor Green
                        Write-Host "COMPLETE!" -ForegroundColor Green
                        Write-Host "============================================================" -ForegroundColor Green
                    } else {
                        Write-Host "FAILED to update: $($updateResult.error)" -ForegroundColor Red
                    }
                } else {
                    Write-Host "`nNo TN-R text found in this view" -ForegroundColor Yellow
                }
            } else {
                Write-Host "No text notes in this view" -ForegroundColor Yellow
                Write-Host "The data may be in a schedule or table format" -ForegroundColor Yellow
            }
        } else {
            Write-Host "FAILED: $($textResult.error)" -ForegroundColor Red
        }
    } else {
        Write-Host "ZONING DATA view not found" -ForegroundColor Red
        Write-Host "`nSearching for views with 'ZONING' in name:" -ForegroundColor Yellow
        $zoningViews = $allViews | Where-Object { $_.name -like "*ZONING*" }
        foreach ($v in $zoningViews) {
            Write-Host "  - $($v.name) (ID: $($v.id), Type: $($v.viewType))" -ForegroundColor White
        }
    }
} else {
    Write-Host "FAILED: $($viewsResult.error)" -ForegroundColor Red
}
