# Update SP-1.0 Sheet with Correct Zoning Information

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
Write-Host "UPDATING SP-1.0 - ZONING DATA TABLE" -ForegroundColor Cyan
Write-Host "20 NW 76 ST - 4-STORY PROJECT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nBuilding Information:" -ForegroundColor Yellow
Write-Host "  - Gross Building Area: 8,022 SF (under 10,000 SF threshold)" -ForegroundColor Green
Write-Host "  - Units: 6 residential units" -ForegroundColor White
Write-Host "  - Parking Provided: 5 spaces" -ForegroundColor White
Write-Host "  - Parking Required: 0 spaces (EXEMPT!)" -ForegroundColor Green

# Step 1: Get all sheets to find SP-1.0
Write-Host "`n[1/3] Finding SP-1.0 sheet..." -ForegroundColor Yellow
$sheetsResponse = Send-RevitCommand -PipeName $pipeName -Method "getAllSheets" -Params @{}

if ($sheetsResponse.success) {
    $sheets = $sheetsResponse.result.sheets
    $sp10Sheet = $sheets | Where-Object { $_.number -eq "SP-1.0" -or $_.name -like "*SP-1.0*" -or $_.name -like "*SITE PLAN*" }

    if ($sp10Sheet) {
        Write-Host "SUCCESS: Found sheet: $($sp10Sheet.number) - $($sp10Sheet.name)" -ForegroundColor Green
        Write-Host "   Sheet ID: $($sp10Sheet.id)" -ForegroundColor Gray

        $sheetId = $sp10Sheet.id

        # Step 2: Get text elements on the sheet
        Write-Host "`n[2/3] Getting text elements on SP-1.0..." -ForegroundColor Yellow
        $textResponse = Send-RevitCommand -PipeName $pipeName -Method "getTextOnSheet" -Params @{ sheetId = $sheetId.ToString() }

        if ($textResponse.success) {
            $textElements = $textResponse.result.textNotes
            Write-Host "SUCCESS: Found $($textElements.Count) text elements" -ForegroundColor Green

            # Step 3: Find and list zoning-related text
            Write-Host "`n[3/3] Finding zoning-related text to update..." -ForegroundColor Yellow

            # Find TN-R text
            $tnrText = $textElements | Where-Object { $_.text -eq "TN-R" }
            if ($tnrText) {
                Write-Host "`n  FOUND: Zoning designation 'TN-R' (ID: $($tnrText.id))" -ForegroundColor Cyan
                Write-Host "         Will change to: T5-O" -ForegroundColor Green
            } else {
                Write-Host "`n  Note: 'TN-R' text not found as exact match" -ForegroundColor Yellow
                Write-Host "         Searching for similar text..." -ForegroundColor Gray
                $similarText = $textElements | Where-Object { $_.text -like "*TN*" -or $_.text -like "*T5*" }
                if ($similarText) {
                    foreach ($txt in $similarText) {
                        Write-Host "         Found: '$($txt.text)' (ID: $($txt.id))" -ForegroundColor Gray
                    }
                }
            }

            # Find parking-related text
            Write-Host "`n  Looking for parking-related text..." -ForegroundColor Cyan
            $parkingTexts = $textElements | Where-Object {
                $_.text -like "*PARKING*" -or
                $_.text -like "*1.5*" -or
                $_.text -like "*SPACE*UNIT*"
            }

            if ($parkingTexts) {
                Write-Host "  FOUND parking text to review:" -ForegroundColor Cyan
                foreach ($parkText in $parkingTexts) {
                    Write-Host "    - '$($parkText.text)' (ID: $($parkText.id))" -ForegroundColor Gray
                }
            }

        } else {
            Write-Host "ERROR: Failed to get text: $($textResponse.error)" -ForegroundColor Red
        }

    } else {
        Write-Host "ERROR: Could not find SP-1.0 sheet" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: Failed to get sheets: $($sheetsResponse.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS - Manual Updates Needed" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nZONING DATA Table changes:" -ForegroundColor Yellow
Write-Host "  1. ZONING: TN-R -> T5-O (Urban Center - Open)" -ForegroundColor White
Write-Host "  2. PARKING REQUIRED: 0 SPACES" -ForegroundColor White
Write-Host "  3. CODE REFERENCE: Miami 21 Article 4, Table 4" -ForegroundColor White
Write-Host "  4. BUILDING AREA: 8,022 SF" -ForegroundColor White
Write-Host "`nCode Reference Text to Add:" -ForegroundColor Yellow
Write-Host "  'Buildings under 10,000 SF in T5 zones" -ForegroundColor Cyan
Write-Host "   = ZERO PARKING REQUIRED'" -ForegroundColor Cyan
Write-Host "   (Miami 21 Article 4, Table 4)" -ForegroundColor Cyan
