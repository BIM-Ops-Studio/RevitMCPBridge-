# Get actual door family types from model
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== DOOR FAMILY TYPES IN MODEL ===" -ForegroundColor Cyan

# Get all doors using getElements with Door category
$json = '{"method":"getElements","params":{"categoryName":"Doors"}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    # Group by family:type
    $familyTypes = @{}

    foreach ($elem in $result.result.elements) {
        $familyName = $elem.familyName
        $typeName = $elem.typeName
        $key = "$familyName : $typeName"

        if (-not $familyTypes.ContainsKey($key)) {
            $familyTypes[$key] = @{
                familyName = $familyName
                typeName = $typeName
                count = 0
                typeId = $elem.typeId
            }
        }
        $familyTypes[$key].count++
    }

    Write-Host "`nDoor Family Types:" -ForegroundColor Yellow
    foreach ($key in $familyTypes.Keys | Sort-Object) {
        $info = $familyTypes[$key]
        Write-Host "  $key"
        Write-Host "    Count: $($info.count), TypeId: $($info.typeId)"
    }

    Write-Host "`nTotal unique family:type combinations: $($familyTypes.Count)"
    Write-Host "Total door instances: $($result.result.elements.Count)"
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

$pipe.Close()
