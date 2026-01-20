# Navigate to TYPES - DOOR legend
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

# Set active view to TYPES - DOOR legend (ID: 1760142)
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Navigated to TYPES - DOOR legend" -ForegroundColor Green
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

# Zoom to fit
Start-Sleep -Seconds 1
$json = '{"method":"zoomToFit","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

$pipe.Close()
Write-Host "View ready for screenshot"
