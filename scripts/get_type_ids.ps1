# Get type IDs for detail component families

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

$elementIds = @(1737946, 1737955, 1737956, 1737958, 1737959, 1737960, 1737964, 1738086)

Write-Host "=== Detail Component Type IDs ===" -ForegroundColor Cyan

$typeMap = @{}

foreach ($id in $elementIds) {
    $json = @{method = 'getDetailComponentInfo'; params = @{elementId = $id}} | ConvertTo-Json -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 500
    $response = $reader.ReadLine()
    $data = $response | ConvertFrom-Json

    if ($data.success) {
        $key = "$($data.result.familyName):$($data.result.typeName)"
        $typeId = $data.result.typeId
        $typeMap[$key] = $typeId
        Write-Host "  $($data.result.familyName) : $($data.result.typeName) -> TypeID: $typeId" -ForegroundColor Green
    } else {
        Write-Host "  Error getting ID $id : $($data.error)" -ForegroundColor Red
    }
}

$pipe.Close()

Write-Host "`nType Map (for generation):" -ForegroundColor Yellow
$typeMap | ConvertTo-Json
