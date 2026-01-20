# Find CMU and stucco detail components

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 5 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 2000
    $response = $reader.ReadLine()
    return $response | ConvertFrom-Json
}

Write-Host "=== Searching for CMU and Stucco Components ===" -ForegroundColor Cyan

# Check multiple views for CMU components
$viewIds = @(1740375, 1740406, 1881592, 1743100)

foreach ($viewId in $viewIds) {
    $data = Invoke-MCP -Method "getDetailComponentsInViewVA" -Params @{viewId = $viewId}

    if ($data.success -and $data.result.components) {
        Write-Host "`nView $viewId - $($data.result.components.Count) components:" -ForegroundColor Yellow
        $data.result.components | Group-Object -Property familyName | ForEach-Object {
            Write-Host "  $($_.Name): $($_.Count)" -ForegroundColor Green
        }
    }
}

# Search for families containing CMU or Stucco
Write-Host "`n=== Searching All Detail Component Types ===" -ForegroundColor Cyan
$typesResult = Invoke-MCP -Method "getDetailComponentTypes"
if ($typesResult.success) {
    Write-Host "Total detail component types: $($typesResult.result.count)" -ForegroundColor Yellow
}

$pipe.Close()
