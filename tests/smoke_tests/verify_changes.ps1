# Verify changes and search for occupant load text
$pipeName = "RevitMCPBridge2026"

function Send-MCPRequest {
    param(
        [string]$Method,
        [hashtable]$Params
    )

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Compress

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)

        $writer = New-Object System.IO.StreamWriter($pipe)
        $writer.AutoFlush = $true
        $reader = New-Object System.IO.StreamReader($pipe)

        $writer.WriteLine($request)
        $response = $reader.ReadLine()

        $pipe.Close()
        return $response | ConvertFrom-Json
    }
    catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Get sheet A0.3 view info
Write-Host "=" * 60
Write-Host "Checking sheet A0.3 - Life Safety Plan" -ForegroundColor Cyan
Write-Host "=" * 60

# Search for text containing "occupant" across all views
Write-Host "`nSearching for 'occupant' text..." -ForegroundColor Yellow
$occupantSearch = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "occupant"
}

if ($occupantSearch -and $occupantSearch.success) {
    $textElements = $occupantSearch.result.textElements
    if ($textElements -and $textElements.Count -gt 0) {
        Write-Host "Found $($textElements.Count) text elements with 'occupant':" -ForegroundColor Green
        foreach ($elem in $textElements) {
            Write-Host "  ID $($elem.id): $($elem.text)" -ForegroundColor Gray
        }
    } else {
        Write-Host "No text found containing 'occupant'" -ForegroundColor Gray
    }
}

# Search for "egress" text
Write-Host "`nSearching for 'egress' text..." -ForegroundColor Yellow
$egressSearch = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "egress"
}

if ($egressSearch -and $egressSearch.success) {
    $textElements = $egressSearch.result.textElements
    if ($textElements -and $textElements.Count -gt 0) {
        Write-Host "Found $($textElements.Count) text elements with 'egress':" -ForegroundColor Green
        foreach ($elem in $textElements) {
            Write-Host "  ID $($elem.id): $($elem.text)" -ForegroundColor Gray
        }
    } else {
        Write-Host "No text found containing 'egress'" -ForegroundColor Gray
    }
}

# Search for "963" to verify it was changed
Write-Host "`nSearching for '963' (should not exist after update)..." -ForegroundColor Yellow
$oldValueSearch = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "963"
}

if ($oldValueSearch -and $oldValueSearch.success) {
    $textElements = $oldValueSearch.result.textElements
    if ($textElements -and $textElements.Count -gt 0) {
        Write-Host "WARN: Found $($textElements.Count) text elements with '963' (may need updating):" -ForegroundColor Yellow
        foreach ($elem in $textElements) {
            Write-Host "  ID $($elem.id): $($elem.text)" -ForegroundColor Gray
        }
    } else {
        Write-Host "Good - no '963' text found (old values were updated)" -ForegroundColor Green
    }
}

# Search for "1,197" to verify update worked
Write-Host "`nSearching for '1,197' (verifying update)..." -ForegroundColor Yellow
$newValueSearch = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "1,197"
}

if ($newValueSearch -and $newValueSearch.success) {
    $textElements = $newValueSearch.result.textElements
    if ($textElements -and $textElements.Count -gt 0) {
        Write-Host "Good - found $($textElements.Count) text elements with '1,197':" -ForegroundColor Green
        foreach ($elem in $textElements) {
            Write-Host "  ID $($elem.id): $($elem.text)" -ForegroundColor Gray
        }
    } else {
        Write-Host "No '1,197' text found - checking if update applied..." -ForegroundColor Yellow
    }
}

# Take a screenshot of the active view
Write-Host "`nCapturing screenshot of current view..." -ForegroundColor Cyan
$screenshot = Send-MCPRequest -Method "captureActiveView" -Params @{
    filePath = "D:\\RevitMCPBridge2026\\smoke_tests\\area_legend_verification.png"
    width = 1920
    height = 1080
}

if ($screenshot -and $screenshot.success) {
    Write-Host "Screenshot saved: $($screenshot.result.filePath)" -ForegroundColor Green
} else {
    Write-Host "Screenshot failed" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 60)
Write-Host "Verification complete" -ForegroundColor Cyan
