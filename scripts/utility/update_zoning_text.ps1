# Update SP-1.0 Zoning Text Using TextTagMethods

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
Write-Host "UPDATING SP-1.0 ZONING DATA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: List all sheets
Write-Host "`n[1/4] Getting all sheets..." -ForegroundColor Yellow
$sheetsResponse = Send-RevitCommand -PipeName $pipeName -Method "getAllSheets" -Params @{}

if ($sheetsResponse.success) {
    $sheets = $sheetsResponse.result.sheets
    Write-Host "Found $($sheets.Count) sheets" -ForegroundColor Green

    Write-Host "`nLooking for SP-1.0..." -ForegroundColor Yellow
    foreach ($sheet in $sheets) {
        if ($sheet.number -like "*SP*" -or $sheet.name -like "*SITE*") {
            Write-Host "  - Sheet: $($sheet.number) | Name: $($sheet.name) | ID: $($sheet.id)" -ForegroundColor Cyan
        }
    }

    # Find SP-1.0 more broadly
    $sp10 = $sheets | Where-Object {
        $_.number -eq "SP-1.0" -or
        $_.name -like "*SP-1.0*" -or
        ($_.number -like "*SP*" -and $_.name -like "*SITE PLAN*")
    } | Select-Object -First 1

    if ($sp10) {
        Write-Host "`nSUCCESS: Found SP-1.0" -ForegroundColor Green
        Write-Host "  Number: $($sp10.number)" -ForegroundColor White
        Write-Host "  Name: $($sp10.name)" -ForegroundColor White
        Write-Host "  ID: $($sp10.id)" -ForegroundColor White

        # Step 2: Get text on this sheet
        Write-Host "`n[2/4] Getting text elements on sheet..." -ForegroundColor Yellow
        $textResponse = Send-RevitCommand -PipeName $pipeName -Method "getTextOnSheet" -Params @{
            sheetId = $sp10.id.ToString()
        }

        if ($textResponse.success) {
            $textNotes = $textResponse.result.textNotes
            Write-Host "SUCCESS: Found $($textNotes.Count) text elements" -ForegroundColor Green

            # Step 3: Find TN-R text
            Write-Host "`n[3/4] Finding 'TN-R' text to update..." -ForegroundColor Yellow

            $tnrText = $textNotes | Where-Object { $_.text -eq "TN-R" }

            if ($tnrText) {
                Write-Host "FOUND 'TN-R' text!" -ForegroundColor Green
                Write-Host "  Text ID: $($tnrText.id)" -ForegroundColor Gray
                Write-Host "  Current text: '$($tnrText.text)'" -ForegroundColor Yellow

                # Step 4: Update TN-R to T5-O
                Write-Host "`n[4/4] Updating TN-R to T5-O..." -ForegroundColor Yellow

                $updateResult = Send-RevitCommand -PipeName $pipeName -Method "modifyTextNote" -Params @{
                    textId = $tnrText.id.ToString()
                    newText = "T5-O"
                }

                if ($updateResult.success) {
                    Write-Host "SUCCESS! Updated zoning designation!" -ForegroundColor Green
                    Write-Host "  Old: TN-R" -ForegroundColor Red
                    Write-Host "  New: T5-O" -ForegroundColor Green
                } else {
                    Write-Host "FAILED to update: $($updateResult.error)" -ForegroundColor Red
                }
            } else {
                Write-Host "Could not find exact 'TN-R' text" -ForegroundColor Yellow
                Write-Host "`nSearching for similar text..." -ForegroundColor Gray

                $similarTexts = $textNotes | Where-Object {
                    $_.text -like "*TN*" -or $_.text -like "*T5*" -or $_.text -eq "TN-R"
                }

                if ($similarTexts) {
                    Write-Host "Found similar text elements:" -ForegroundColor Cyan
                    foreach ($txt in $similarTexts) {
                        Write-Host "  ID: $($txt.id) | Text: '$($txt.text)'" -ForegroundColor Gray
                    }
                }
            }

        } else {
            Write-Host "FAILED to get text: $($textResponse.error)" -ForegroundColor Red
        }

    } else {
        Write-Host "Could not find SP-1.0 sheet" -ForegroundColor Red
        Write-Host "`nAll sheets:" -ForegroundColor Yellow
        foreach ($sheet in $sheets) {
            Write-Host "  $($sheet.number): $($sheet.name)" -ForegroundColor Gray
        }
    }

} else {
    Write-Host "FAILED to get sheets: $($sheetsResponse.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Updates Needed:" -ForegroundColor Yellow
Write-Host "  1. ZONING: TN-R -> T5-O" -ForegroundColor White
Write-Host "  2. PARKING: -> 0 SPACES REQUIRED" -ForegroundColor White
Write-Host "  3. CODE REF: Miami 21 Article 4, Table 4" -ForegroundColor White
Write-Host "  4. BLDG AREA: 8,022 SF" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
