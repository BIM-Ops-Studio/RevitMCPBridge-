# Get details of the Alteration text elements
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

# Get full details of element 2570218
Write-Host "Getting details of ID 2570218 (ALTERATION LEVEL:)..." -ForegroundColor Cyan

$result = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "ALTERATION LEVEL:"
}

if ($result -and $result.success) {
    foreach ($elem in $result.result.textElements) {
        if ($elem.id -eq 2570218) {
            Write-Host "`nElement ID: $($elem.id)" -ForegroundColor Green
            Write-Host "Full Text: '$($elem.text)'" -ForegroundColor White
            Write-Host "Position: $($elem.position | ConvertTo-Json -Compress)" -ForegroundColor Gray
            Write-Host "ViewId: $($elem.viewId)" -ForegroundColor Gray
            Write-Host "TypeId: $($elem.typeId)" -ForegroundColor Gray
        }
    }
}

# Also get element 2570340
Write-Host "`n" + ("=" * 50)
Write-Host "Getting details of ID 2570340..." -ForegroundColor Cyan

$result2 = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "ALTERATION LEVEL II"
}

if ($result2 -and $result2.success) {
    foreach ($elem in $result2.result.textElements) {
        if ($elem.id -eq 2570340) {
            Write-Host "`nElement ID: $($elem.id)" -ForegroundColor Green
            Write-Host "Full Text: '$($elem.text)'" -ForegroundColor White
            Write-Host "Position: $($elem.position | ConvertTo-Json -Compress)" -ForegroundColor Gray
        }
    }
}

# Get the view that contains these elements
Write-Host "`n" + ("=" * 50)
Write-Host "Looking for the view containing these elements..." -ForegroundColor Cyan

# Check what sheet these are on
$result3 = Send-MCPRequest -Method "getSheets" -Params @{}
if ($result3 -and $result3.success) {
    $sheets = $result3.result.sheets
    $a03 = $sheets | Where-Object { $_.number -eq "A0.3" }
    if ($a03) {
        Write-Host "Sheet A0.3 ID: $($a03.sheetId)" -ForegroundColor Green
    }
}
