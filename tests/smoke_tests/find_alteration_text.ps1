# Find "Alteration" text in Life Safety Legends 2
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

Write-Host "Searching for 'Alteration' text..." -ForegroundColor Cyan

$result = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "Alteration"
}

if ($result -and $result.success) {
    $elements = $result.result.textElements
    Write-Host "Found $($elements.Count) elements:" -ForegroundColor Green

    foreach ($elem in $elements) {
        Write-Host "`nID: $($elem.id)" -ForegroundColor Yellow
        Write-Host "Text: $($elem.text)" -ForegroundColor White
        if ($elem.viewId) {
            Write-Host "ViewId: $($elem.viewId)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "Search failed or no results" -ForegroundColor Red
    if ($result) { Write-Host $result.error }
}
