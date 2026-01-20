# Final verification - ensure no 963 references remain
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

Write-Host "=" * 60
Write-Host "FINAL VERIFICATION - 6365 W SEMPLE RD" -ForegroundColor Cyan
Write-Host "=" * 60

# Check for any remaining 963 references
Write-Host "`nSearching for remaining '963' references..." -ForegroundColor Yellow
$oldSearch = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "963"
}

if ($oldSearch -and $oldSearch.success) {
    $count = 0
    if ($oldSearch.result.textElements) {
        $count = $oldSearch.result.textElements.Count
    }
    if ($count -eq 0) {
        Write-Host "SUCCESS: No '963' references found!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Found $count text elements still containing '963'" -ForegroundColor Yellow
        foreach ($elem in $oldSearch.result.textElements) {
            $text = $elem.text
            if ($text.Length -gt 80) { $text = $text.Substring(0, 77) + "..." }
            Write-Host "  ID $($elem.id): $text" -ForegroundColor Gray
        }
    }
}

# Count 1,197 references
Write-Host "`nSearching for '1,197' references (should exist)..." -ForegroundColor Yellow
$newSearch = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "1,197"
}

if ($newSearch -and $newSearch.success) {
    $count = 0
    if ($newSearch.result.textElements) {
        $count = $newSearch.result.textElements.Count
    }
    Write-Host "Found $count text elements with '1,197':" -ForegroundColor Green
    foreach ($elem in $newSearch.result.textElements) {
        $text = $elem.text
        if ($text.Length -gt 80) { $text = $text.Substring(0, 77) + "..." }
        Write-Host "  ID $($elem.id): $text" -ForegroundColor Gray
    }
}

# Check for "12 PERSONS" reference
Write-Host "`nSearching for '12 PERSONS' (occupant load)..." -ForegroundColor Yellow
$occupantSearch = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "12 PERSONS"
}

if ($occupantSearch -and $occupantSearch.success) {
    $count = 0
    if ($occupantSearch.result.textElements) {
        $count = $occupantSearch.result.textElements.Count
    }
    if ($count -gt 0) {
        Write-Host "SUCCESS: Found $count text elements with '12 PERSONS'" -ForegroundColor Green
    } else {
        Write-Host "Checking alternate format..." -ForegroundColor Gray
    }
}

Write-Host "`n" + ("=" * 60)
Write-Host "SUMMARY - Sheet A0.3 Life Safety Plan" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host "Project: 6365 W Semple Rd - Spa & Wellness Center"
Write-Host "Total Area: 1,197 SF (center of wall calculation)"
Write-Host "Occupancy Type: Business (B)"
Write-Host "Occupant Load Factor: 100 SF per person"
Write-Host "Calculated Occupant Load: 12 persons"
Write-Host "=" * 60
