# Navigate to TYPES - DOOR legend and zoom to see TYPE A and TYPE B clearly
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== STUDYING TYPE A AND TYPE B ===" -ForegroundColor Cyan

# Navigate to TYPES - DOOR legend
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
Write-Host "Navigated to TYPES - DOOR legend"

Start-Sleep -Milliseconds 500

# Zoom to fit to see the full legend
$json = '{"method":"zoomToFit","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

Start-Sleep -Milliseconds 500

# Try to get all annotations/elements in this view to understand the structure
$json = '{"method":"getDetailLinesInView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Detail lines found: $($result.result.lines.Count)"
} else {
    Write-Host "getDetailLinesInView: $($result.error)" -ForegroundColor Yellow
}

# Also check for dimensions
$json = '{"method":"getDimensionsInView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Dimensions found: $($result.result.dimensions.Count)"
    foreach ($dim in $result.result.dimensions) {
        Write-Host "  Dim: $($dim.value) at ($($dim.location.x), $($dim.location.y))"
    }
} else {
    Write-Host "getDimensionsInView: $($result.error)" -ForegroundColor Yellow
}

$pipe.Close()
Write-Host "`nReady for visual inspection"
