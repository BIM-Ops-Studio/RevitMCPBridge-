# Get door families and types, plus door elevation views
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== DOOR FAMILIES IN MODEL ===" -ForegroundColor Cyan

# Get doors by category
$json = '{"method":"getElementsByCategory","params":{"category":"Doors","includeTypes":true}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    # Get unique type names
    $typeNames = @{}
    foreach ($elem in $result.result.elements) {
        if ($elem.typeName -and -not $typeNames.ContainsKey($elem.typeName)) {
            $typeNames[$elem.typeName] = @{
                typeId = $elem.typeId
                count = 0
            }
        }
        if ($elem.typeName) {
            $typeNames[$elem.typeName].count++
        }
    }

    Write-Host "`nDoor Types Found:" -ForegroundColor Yellow
    foreach ($typeName in $typeNames.Keys | Sort-Object) {
        $info = $typeNames[$typeName]
        Write-Host "  $typeName (ID: $($info.typeId), Count: $($info.count))"
    }
    Write-Host "`nTotal Door Instances: $($result.result.elements.Count)"
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

Write-Host "`n=== DOOR ELEVATION VIEWS ===" -ForegroundColor Cyan

# Get all views and look for door-related
$json = '{"method":"getViews","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$views = $response | ConvertFrom-Json

if ($views.success) {
    Write-Host "`nViews containing 'Door' or 'Type':" -ForegroundColor Yellow
    foreach ($view in $views.result.views) {
        if ($view.name -like "*Door*" -or $view.name -like "*Type*" -or $view.name -like "*DT*") {
            Write-Host "  ID: $($view.id) - $($view.name) [$($view.viewType)]"
        }
    }
}

$pipe.Close()
