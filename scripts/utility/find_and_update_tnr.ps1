# Find and Update TN-R text anywhere in the project

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
Write-Host "FINDING AND UPDATING TN-R TEXT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nSearching for 'TN-R' text in current view..." -ForegroundColor Yellow

# Try to search for text containing TN-R
$searchResult = Send-RevitCommand -PipeName $pipeName -Method "searchText" -Params @{
    searchText = "TN-R"
}

if ($searchResult.success) {
    $foundTexts = $searchResult.result.textNotes
    Write-Host "SUCCESS: Found $($foundTexts.Count) text element(s) containing 'TN-R'" -ForegroundColor Green

    foreach ($textNote in $foundTexts) {
        Write-Host "`nFound text:" -ForegroundColor Cyan
        Write-Host "  ID: $($textNote.id)" -ForegroundColor White
        Write-Host "  Text: '$($textNote.text)'" -ForegroundColor Yellow

        # Update this text to T5-O
        Write-Host "  Updating to 'T5-O'..." -ForegroundColor Yellow

        $updateResult = Send-RevitCommand -PipeName $pipeName -Method "modifyTextNote" -Params @{
            textId = $textNote.id.ToString()
            newText = "T5-O"
        }

        if ($updateResult.success) {
            Write-Host "  SUCCESS! Updated!" -ForegroundColor Green
        } else {
            Write-Host "  FAILED: $($updateResult.error)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Search failed or method not available: $($searchResult.error)" -ForegroundColor Yellow
    Write-Host "`nTrying alternative: Get text in active view..." -ForegroundColor Yellow

    # Try getting text in active view
    $textInViewResult = Send-RevitCommand -PipeName $pipeName -Method "getTextInActiveView" -Params @{}

    if ($textInViewResult.success) {
        $allTexts = $textInViewResult.result.textNotes
        Write-Host "Found $($allTexts.Count) text elements in active view" -ForegroundColor Green

        # Filter for TN-R
        $tnrTexts = $allTexts | Where-Object { $_.text -eq "TN-R" -or $_.text -like "*TN-R*" }

        if ($tnrTexts) {
            Write-Host "`nFound TN-R text:" -ForegroundColor Cyan
            foreach ($txt in $tnrTexts) {
                Write-Host "  ID: $($txt.id) | Text: '$($txt.text)'" -ForegroundColor White

                # Update it
                Write-Host "  Updating to 'T5-O'..." -ForegroundColor Yellow
                $updateResult = Send-RevitCommand -PipeName $pipeName -Method "modifyTextNote" -Params @{
                    textId = $txt.id.ToString()
                    newText = "T5-O"
                }

                if ($updateResult.success) {
                    Write-Host "  SUCCESS!" -ForegroundColor Green
                } else {
                    Write-Host "  FAILED: $($updateResult.error)" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "No TN-R text found in active view" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Could not get text in active view: $($textInViewResult.error)" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "MANUAL UPDATE GUIDE" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nIf automatic update failed, manually change on SP-1.0:" -ForegroundColor White
Write-Host "  1. ZONING: TN-R -> T5-O" -ForegroundColor Cyan
Write-Host "  2. PARKING REQUIRED: 0 SPACES" -ForegroundColor Cyan
Write-Host "  3. Add note: 'Miami 21 Art. 4, Table 4 - Bldg < 10,000 SF'" -ForegroundColor Cyan
Write-Host "  4. Building Area: 8,022 SF" -ForegroundColor Cyan
