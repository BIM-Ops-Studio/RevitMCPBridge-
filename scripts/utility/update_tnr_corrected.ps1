# Update TN-R to T5-O on SP-1.0 Sheet - CORRECTED

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
Write-Host "UPDATING SP-1.0 ZONING: TN-R -> T5-O" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Get all sheets
Write-Host "`n[1/3] Finding SP-1.0 sheet..." -ForegroundColor Yellow
$sheetsResult = Send-RevitCommand -PipeName $pipeName -Method "getAllSheets" -Params @{}

if ($sheetsResult.success) {
    $sheets = $sheetsResult.result.sheets
    Write-Host "SUCCESS: Found $($sheets.Count) sheets" -ForegroundColor Green

    # Find SP-1.0 sheet
    $sp10Sheet = $null
    foreach ($sheet in $sheets) {
        if ($sheet.sheetNumber -eq "SP-1.0" -or $sheet.sheetName -like "*SP-1.0*") {
            $sp10Sheet = $sheet
            break
        }
    }

    if ($sp10Sheet) {
        Write-Host "SUCCESS: Found SP-1.0" -ForegroundColor Green
        Write-Host "  Number: $($sp10Sheet.sheetNumber)" -ForegroundColor White
        Write-Host "  Name: $($sp10Sheet.sheetName)" -ForegroundColor White
        Write-Host "  ID: $($sp10Sheet.id)" -ForegroundColor White

        # Step 2: Get text notes on sheet (sheets ARE views!)
        Write-Host "`n[2/3] Getting text notes on SP-1.0..." -ForegroundColor Yellow
        $textResult = Send-RevitCommand -PipeName $pipeName -Method "getTextNotesInView" -Params @{
            viewId = $sp10Sheet.id.ToString()
        }

        if ($textResult.success) {
            $textNotes = $textResult.result.textNotes
            Write-Host "SUCCESS: Found $($textNotes.Count) text notes" -ForegroundColor Green

            # Find TN-R text
            $tnrNote = $null
            foreach ($note in $textNotes) {
                if ($note.text -eq "TN-R") {
                    $tnrNote = $note
                    break
                }
            }

            if ($tnrNote) {
                Write-Host "`nFOUND TN-R text!" -ForegroundColor Green
                Write-Host "  ID: $($tnrNote.textNoteId)" -ForegroundColor White
                Write-Host "  Current text: '$($tnrNote.text)'" -ForegroundColor Yellow

                # Step 3: Update TN-R to T5-O
                Write-Host "`n[3/3] Updating TN-R -> T5-O..." -ForegroundColor Yellow
                $updateResult = Send-RevitCommand -PipeName $pipeName -Method "modifyTextNote" -Params @{
                    elementId = $tnrNote.textNoteId.ToString()
                    text = "T5-O"
                }

                if ($updateResult.success) {
                    Write-Host "`nSUCCESS! Zoning updated!" -ForegroundColor Green
                    Write-Host "  Old: TN-R" -ForegroundColor Red
                    Write-Host "  New: T5-O" -ForegroundColor Green
                } else {
                    Write-Host "FAILED to update: $($updateResult.error)" -ForegroundColor Red
                }
            } else {
                Write-Host "`nNo exact 'TN-R' text found" -ForegroundColor Yellow
                Write-Host "`nAll text notes on sheet:" -ForegroundColor Cyan
                foreach ($note in $textNotes) {
                    Write-Host "  ID: $($note.textNoteId) | Text: '$($note.text)'" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "FAILED to get text notes: $($textResult.error)" -ForegroundColor Red
        }
    } else {
        Write-Host "SP-1.0 sheet not found" -ForegroundColor Red
        Write-Host "`nAvailable sheets:" -ForegroundColor Yellow
        foreach ($sheet in $sheets | Select-Object -First 10) {
            Write-Host "  $($sheet.sheetNumber): $($sheet.sheetName)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "FAILED to get sheets: $($sheetsResult.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Building: 20 NW 76 ST - 4-STORY" -ForegroundColor Yellow
Write-Host "Gross Building Area: 8,022 SF (under 10,000 SF)" -ForegroundColor Green
Write-Host "Zoning: T5-O (Urban Center - Open)" -ForegroundColor Green
Write-Host "Parking Required: 0 SPACES (EXEMPT)" -ForegroundColor Green
Write-Host "Code: Miami 21 Article 4, Table 4" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
