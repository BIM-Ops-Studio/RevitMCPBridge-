# Test Rich Text Note - Replace ALTERATION LEVEL: with multi-color version
$pipeName = "RevitMCPBridge2026"

function Send-MCPRequest {
    param(
        [string]$Method,
        [hashtable]$Params
    )

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Compress -Depth 10

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(10000)

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
Write-Host "Testing Rich Text Note Feature" -ForegroundColor Cyan
Write-Host "=" * 60

# First, let's get the sheet ID for A0.3 to place on a sheet (MVP requirement)
Write-Host "`nGetting sheet A0.3..." -ForegroundColor Yellow
$sheets = Send-MCPRequest -Method "getSheets" -Params @{}

$sheetId = $null
if ($sheets -and $sheets.success) {
    $a03 = $sheets.result.sheets | Where-Object { $_.number -eq "A0.3" }
    if ($a03) {
        $sheetId = $a03.sheetId
        Write-Host "Found Sheet A0.3: ID $sheetId" -ForegroundColor Green
    }
}

if (-not $sheetId) {
    Write-Host "Sheet A0.3 not found!" -ForegroundColor Red
    exit
}

# Create a test Rich Text Note on the sheet
Write-Host "`nCreating Rich Text Note..." -ForegroundColor Yellow
Write-Host "Spans: 'ALTERATION ' (black) + 'LEVEL II' (red)" -ForegroundColor Gray

$spans = @(
    @{ text = "ALTERATION "; color = "#000000" }
    @{ text = "LEVEL II"; color = "#FF0000" }
)

$result = Send-MCPRequest -Method "createRichTextNote" -Params @{
    viewId = $sheetId
    location = @(1.5, 1.5, 0)  # Position on sheet
    spans = $spans
}

if ($result) {
    Write-Host "`nResult:" -ForegroundColor Cyan
    Write-Host ($result | ConvertTo-Json -Depth 5) -ForegroundColor White
}
