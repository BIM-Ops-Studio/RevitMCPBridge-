# Update Zoning Data in Legend View

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
Write-Host "UPDATING LEGEND - ZONING DATA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Get Legend views
Write-Host "`n[1/3] Finding Legend views..." -ForegroundColor Yellow
$legendsResult = Send-RevitCommand -PipeName $pipeName -Method "getLegends" -Params @{}

if ($legendsResult.success) {
    $legends = $legendsResult.result.legends
    Write-Host "SUCCESS: Found $($legends.Count) legend views" -ForegroundColor Green

    # List all legends
    Write-Host "`nAvailable Legend views:" -ForegroundColor Cyan
    foreach ($legend in $legends) {
        Write-Host "  - $($legend.name) (ID: $($legend.id))" -ForegroundColor White
    }

    # Find zoning-related legend
    $zoningLegend = $legends | Where-Object {
        $_.name -like "*ZONING*" -or
        $_.name -like "*DATA*" -or
        $_.name -like "*PROPERTY*"
    } | Select-Object -First 1

    if ($zoningLegend) {
        Write-Host "`nFound zoning legend: $($zoningLegend.name)" -ForegroundColor Green

        # Step 2: Get text notes in the legend view
        Write-Host "`n[2/3] Getting text notes in legend..." -ForegroundColor Yellow
        $textResult = Send-RevitCommand -PipeName $pipeName -Method "getTextNotesInView" -Params @{
            viewId = $zoningLegend.id.ToString()
        }

        if ($textResult.success) {
            $textNotes = $textResult.result.textNotes
            Write-Host "SUCCESS: Found $($textNotes.Count) text notes" -ForegroundColor Green

            # List all text notes
            Write-Host "`nText notes in legend:" -ForegroundColor Cyan
            foreach ($note in $textNotes) {
                Write-Host "  ID: $($note.textNoteId) | Text: '$($note.text)'" -ForegroundColor White
            }

            # Find TN-R text
            $tnrNote = $textNotes | Where-Object { $_.text -eq "TN-R" }

            if ($tnrNote) {
                Write-Host "`nFOUND 'TN-R' text!" -ForegroundColor Green
                Write-Host "  ID: $($tnrNote.textNoteId)" -ForegroundColor White
                Write-Host "  Current text: '$($tnrNote.text)'" -ForegroundColor Yellow

                # Step 3: Update TN-R to T5-O
                Write-Host "`n[3/3] Updating TN-R -> T5-O..." -ForegroundColor Yellow
                $updateResult = Send-RevitCommand -PipeName $pipeName -Method "modifyTextNote" -Params @{
                    elementId = $tnrNote.textNoteId.ToString()
                    text = "T5-O"
                }

                if ($updateResult.success) {
                    Write-Host "`nSUCCESS! Zoning updated in legend!" -ForegroundColor Green
                    Write-Host "  Old: TN-R" -ForegroundColor Red
                    Write-Host "  New: T5-O" -ForegroundColor Green
                } else {
                    Write-Host "FAILED to update: $($updateResult.error)" -ForegroundColor Red
                }
            } else {
                Write-Host "`nNo exact 'TN-R' text found" -ForegroundColor Yellow
                Write-Host "Searching for similar text..." -ForegroundColor Gray
                $similar = $textNotes | Where-Object { $_.text -like "*TN*" -or $_.text -like "*T5*" }
                if ($similar) {
                    foreach ($txt in $similar) {
                        Write-Host "  Found: '$($txt.text)' (ID: $($txt.textNoteId))" -ForegroundColor Gray
                    }
                }
            }
        } else {
            Write-Host "FAILED to get text notes: $($textResult.error)" -ForegroundColor Red
        }
    } else {
        Write-Host "`nNo zoning-related legend found" -ForegroundColor Yellow
        Write-Host "Please manually select the correct legend view" -ForegroundColor Yellow
    }
} else {
    Write-Host "FAILED to get legends: $($legendsResult.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Building: 20 NW 76 ST - 4-STORY" -ForegroundColor Yellow
Write-Host "Gross Building Area: 8,022 SF (under 10,000 SF)" -ForegroundColor Green
Write-Host "Zoning: T5-O (Urban Center - Open)" -ForegroundColor Green
Write-Host "Parking Required: 0 SPACES (EXEMPT)" -ForegroundColor Green
Write-Host "Code: Miami 21 Article 4, Table 4" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
