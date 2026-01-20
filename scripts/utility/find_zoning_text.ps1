# Find TN-R text in all site-related legends

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
Write-Host "SEARCHING ALL LEGENDS FOR TN-R TEXT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get all legends
$legendsResult = Send-RevitCommand -PipeName $pipeName -Method "getLegends" -Params @{}

if ($legendsResult.success) {
    $legends = $legendsResult.result.legends

    # Filter site-related legends
    $siteLegends = $legends | Where-Object {
        $_.name -like "*SITE*" -or
        $_.name -like "*DATA*" -or
        $_.name -like "*ZONING*" -or
        $_.name -like "*INFORMATION*"
    }

    Write-Host "`nChecking $($siteLegends.Count) site-related legends:" -ForegroundColor Yellow
    foreach ($legend in $siteLegends) {
        Write-Host "`n  Legend: $($legend.name)" -ForegroundColor Cyan

        # Get text notes in this legend
        $textResult = Send-RevitCommand -PipeName $pipeName -Method "getTextNotesInView" -Params @{
            viewId = $legend.id.ToString()
        }

        if ($textResult.success) {
            $textNotes = $textResult.result.textNotes
            Write-Host "    Text notes: $($textNotes.Count)" -ForegroundColor White

            if ($textNotes.Count -gt 0) {
                # Check for TN-R or zoning-related text
                $zoningTexts = $textNotes | Where-Object {
                    $_.text -eq "TN-R" -or
                    $_.text -like "*TN-R*" -or
                    $_.text -like "*ZONING*" -or
                    $_.text -like "*T5*" -or
                    $_.text -like "*PARKING*"
                }

                if ($zoningTexts) {
                    Write-Host "    FOUND ZONING-RELATED TEXT:" -ForegroundColor Green
                    foreach ($txt in $zoningTexts) {
                        Write-Host "      ID: $($txt.textNoteId) | Text: '$($txt.text)'" -ForegroundColor Yellow
                    }
                }

                # Also show first few text notes for context
                Write-Host "    First 5 text notes:" -ForegroundColor Gray
                foreach ($note in ($textNotes | Select-Object -First 5)) {
                    Write-Host "      '$($note.text)'" -ForegroundColor Gray
                }
            }
        }
    }

    # Also search ALL legends for TN-R specifically
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "SEARCHING ALL 70 LEGENDS FOR 'TN-R' TEXT" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan

    $foundInLegends = @()
    foreach ($legend in $legends) {
        $textResult = Send-RevitCommand -PipeName $pipeName -Method "getTextNotesInView" -Params @{
            viewId = $legend.id.ToString()
        }

        if ($textResult.success) {
            $textNotes = $textResult.result.textNotes
            $tnrNote = $textNotes | Where-Object { $_.text -eq "TN-R" }

            if ($tnrNote) {
                $foundInLegends += @{
                    legend = $legend.name
                    id = $legend.id
                    textId = $tnrNote.textNoteId
                }
                Write-Host "`nFOUND 'TN-R' in: $($legend.name) (ID: $($legend.id))" -ForegroundColor Green
                Write-Host "  Text ID: $($tnrNote.textNoteId)" -ForegroundColor Yellow
            }
        }
    }

    if ($foundInLegends.Count -eq 0) {
        Write-Host "`nNo 'TN-R' text found in any legend view" -ForegroundColor Red
        Write-Host "The zoning data may be in a schedule or different format" -ForegroundColor Yellow
    } else {
        Write-Host "`n============================================================" -ForegroundColor Green
        Write-Host "READY TO UPDATE!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "`nFound TN-R in $($foundInLegends.Count) legend(s)" -ForegroundColor Green
    }
} else {
    Write-Host "FAILED to get legends: $($legendsResult.error)" -ForegroundColor Red
}
