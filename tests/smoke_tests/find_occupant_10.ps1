# Find text containing "10" related to occupant load
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

Write-Host "Searching for '10 PERSONS' text..." -ForegroundColor Cyan

$search = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "10 PERSONS"
}

if ($search -and $search.success) {
    $elements = $search.result.textElements
    if ($elements -and $elements.Count -gt 0) {
        Write-Host "Found $($elements.Count) elements with '10 PERSONS':" -ForegroundColor Yellow
        foreach ($elem in $elements) {
            Write-Host "`nID: $($elem.id)" -ForegroundColor Green
            Write-Host "Text: $($elem.text)" -ForegroundColor Gray
        }
    } else {
        Write-Host "No '10 PERSONS' found" -ForegroundColor Gray
    }
}

# Also search for "OCCUPANT LOAD: 10"
Write-Host "`nSearching for 'OCCUPANT LOAD: 10'..." -ForegroundColor Cyan

$search2 = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "OCCUPANT LOAD: 10"
}

if ($search2 -and $search2.success) {
    $elements = $search2.result.textElements
    if ($elements -and $elements.Count -gt 0) {
        Write-Host "Found $($elements.Count) elements:" -ForegroundColor Yellow
        foreach ($elem in $elements) {
            Write-Host "`nID: $($elem.id)" -ForegroundColor Green
            Write-Host "Text preview: $($elem.text.Substring(0, [Math]::Min(200, $elem.text.Length)))..." -ForegroundColor Gray
        }
    } else {
        Write-Host "No 'OCCUPANT LOAD: 10' found" -ForegroundColor Gray
    }
}

# Search for just "OCCUPANT" to find all related text
Write-Host "`nSearching for all text with 'OCCUPANT'..." -ForegroundColor Cyan

$search3 = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "OCCUPANT"
}

if ($search3 -and $search3.success) {
    $elements = $search3.result.textElements
    if ($elements -and $elements.Count -gt 0) {
        Write-Host "Found $($elements.Count) elements with 'OCCUPANT':" -ForegroundColor Yellow
        foreach ($elem in $elements) {
            Write-Host "`nID: $($elem.id)" -ForegroundColor Green
            # Find the occupant line in the text
            $lines = $elem.text -split "`n"
            foreach ($line in $lines) {
                if ($line -match "OCCUPANT") {
                    Write-Host "  -> $line" -ForegroundColor White
                }
            }
        }
    } else {
        Write-Host "No 'OCCUPANT' text found" -ForegroundColor Gray
    }
}
