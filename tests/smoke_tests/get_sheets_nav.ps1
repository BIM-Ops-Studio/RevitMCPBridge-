# Get all sheets and navigate through them
$pipeName = "RevitMCPBridge2026"

function Send-MCPRequest {
    param([string]$Method, [hashtable]$Params)
    $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress -Depth 10
    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(20000)
        $writer = New-Object System.IO.StreamWriter($pipe)
        $writer.AutoFlush = $true
        $reader = New-Object System.IO.StreamReader($pipe)
        $writer.WriteLine($request)
        $response = $reader.ReadLine()
        $pipe.Close()
        return $response | ConvertFrom-Json
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Get all sheets
$result = Send-MCPRequest -Method "getSheets" -Params @{}

if ($result -and $result.success) {
    $sheets = $result.result.sheets | Sort-Object { $_.number }
    Write-Host "Found $($sheets.Count) sheets:" -ForegroundColor Cyan
    Write-Host ""
    foreach ($s in $sheets) {
        Write-Host "$($s.sheetId)`t$($s.number)`t$($s.name)"
    }
}
