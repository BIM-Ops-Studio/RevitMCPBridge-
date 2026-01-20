# Verify occupant load text
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

Write-Host "Checking TOTAL OCCUPANT LOAD text..." -ForegroundColor Cyan

# Search for the specific text
$result = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "TOTAL OCCUPANT LOAD"
}

if ($result -and $result.success) {
    $elements = $result.result.textElements
    Write-Host "Found $($elements.Count) elements:" -ForegroundColor Green

    foreach ($elem in $elements) {
        Write-Host "`nID: $($elem.id)" -ForegroundColor Yellow
        Write-Host "Text: $($elem.text)" -ForegroundColor White

        # Check if it still says 10
        if ($elem.text -match "10") {
            Write-Host ">>> STILL SHOWS 10 - needs update!" -ForegroundColor Red
        } elseif ($elem.text -match "12") {
            Write-Host ">>> Shows 12 - OK" -ForegroundColor Green
        }
    }
}

# Also check ID 2570236 which showed "24 OCCUPANTS"
Write-Host "`n" + ("=" * 50)
Write-Host "Checking ID 2570236 (showed '24 OCCUPANTS')..." -ForegroundColor Cyan

$result2 = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "24 OCCUPANTS"
}

if ($result2 -and $result2.success -and $result2.result.textElements.Count -gt 0) {
    foreach ($elem in $result2.result.textElements) {
        Write-Host "`nID: $($elem.id)" -ForegroundColor Yellow
        Write-Host "Text: $($elem.text)" -ForegroundColor White
    }
}

# Search for "= 10" pattern specifically
Write-Host "`n" + ("=" * 50)
Write-Host "Searching for '= 10' pattern in occupancy context..." -ForegroundColor Cyan

$result3 = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "= 10"
}

if ($result3 -and $result3.success) {
    foreach ($elem in $result3.result.textElements) {
        $text = $elem.text.ToUpper()
        if ($text -match "OCCUPANT" -or $text -match "PERSON" -or $text -match "MEN" -or $text -match "WOMEN" -or $text -match "LOAD") {
            Write-Host "`nID: $($elem.id)" -ForegroundColor Red
            Write-Host "Text: $($elem.text)" -ForegroundColor White
        }
    }
}
