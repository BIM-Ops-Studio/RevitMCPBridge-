# Get door instances and their family types using collector
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== GETTING ALL DOORS ===" -ForegroundColor Cyan

# Try getDoors method
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    # Group by family and type
    $families = @{}

    foreach ($door in $result.result.doors) {
        $familyName = $door.familyName
        $typeName = $door.typeName

        if (-not $families.ContainsKey($familyName)) {
            $families[$familyName] = @{}
        }
        if (-not $families[$familyName].ContainsKey($typeName)) {
            $families[$familyName][$typeName] = 0
        }
        $families[$familyName][$typeName]++
    }

    Write-Host "`nDoor Families and Types:" -ForegroundColor Yellow
    foreach ($family in $families.Keys | Sort-Object) {
        Write-Host "`n  FAMILY: $family" -ForegroundColor Cyan
        foreach ($type in $families[$family].Keys | Sort-Object) {
            Write-Host "    $type : $($families[$family][$type]) instances"
        }
    }

    Write-Host "`nTotal doors: $($result.result.doors.Count)"
} else {
    Write-Host "getDoors failed: $($result.error)" -ForegroundColor Yellow

    # Try alternative - get from loaded families
    Write-Host "`nTrying getLoadedFamilies..." -ForegroundColor Yellow
    $json = '{"method":"getLoadedFamilies","params":{"category":"Doors"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $famResult = $response | ConvertFrom-Json

    if ($famResult.success) {
        Write-Host "`nLoaded Door Families:" -ForegroundColor Yellow
        foreach ($fam in $famResult.result.families) {
            Write-Host "  $($fam.name)"
            foreach ($type in $fam.types) {
                Write-Host "    - $($type.name)"
            }
        }
    } else {
        Write-Host "Error: $($famResult.error)" -ForegroundColor Red
    }
}

$pipe.Close()
