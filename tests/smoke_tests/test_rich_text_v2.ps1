# Test Rich Text Note - v2
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
Write-Host "Testing Rich Text Note Feature - v2" -ForegroundColor Cyan
Write-Host "=" * 60

# Get all sheets and find A0.3
Write-Host "`nGetting sheets..." -ForegroundColor Yellow
$sheets = Send-MCPRequest -Method "getSheets" -Params @{}

if ($sheets -and $sheets.success) {
    Write-Host "Raw result keys: $($sheets.result.PSObject.Properties.Name -join ', ')" -ForegroundColor Gray

    # Try different possible structures
    $sheetList = $null
    if ($sheets.result.sheets) {
        $sheetList = $sheets.result.sheets
    } elseif ($sheets.result -is [Array]) {
        $sheetList = $sheets.result
    }

    if ($sheetList) {
        Write-Host "Found $($sheetList.Count) sheets" -ForegroundColor Green

        # Find A0.3
        foreach ($s in $sheetList) {
            $num = $s.number
            if (-not $num) { $num = $s.sheetNumber }
            if ($num -like "*0.3*" -or $num -like "*A0.3*") {
                Write-Host "Found sheet: $num (ID: $($s.sheetId))" -ForegroundColor Green
                $sheetId = $s.sheetId
                if (-not $sheetId) { $sheetId = $s.id }
                break
            }
        }
    }
}

# Use the known sheet ID (2548220) from earlier
$sheetId = 2548220
Write-Host "`nUsing known sheet A0.3 ID: $sheetId" -ForegroundColor Yellow

# Create Rich Text Note
Write-Host "`nCreating Rich Text Note on sheet..." -ForegroundColor Yellow
Write-Host "  Span 1: 'ALTERATION ' (black #000000)" -ForegroundColor Gray
Write-Host "  Span 2: 'LEVEL II' (red #FF0000)" -ForegroundColor Gray

$spans = @(
    @{ text = "ALTERATION "; color = "#000000" }
    @{ text = "LEVEL II"; color = "#FF0000" }
)

$result = Send-MCPRequest -Method "createRichTextNote" -Params @{
    viewId = $sheetId
    location = @(1.5, 1.5, 0)
    spans = $spans
}

Write-Host "`nResult:" -ForegroundColor Cyan
if ($result) {
    if ($result.success) {
        Write-Host "SUCCESS!" -ForegroundColor Green
        Write-Host "  Group ID: $($result.groupId)" -ForegroundColor White
        Write-Host "  Text Note IDs: $($result.textNoteIds -join ', ')" -ForegroundColor White
        Write-Host "  Span Count: $($result.spanCount)" -ForegroundColor White
    } else {
        Write-Host "FAILED: $($result.error)" -ForegroundColor Red
    }
} else {
    Write-Host "No response received" -ForegroundColor Red
}
