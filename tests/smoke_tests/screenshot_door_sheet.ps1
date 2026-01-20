# Navigate to door schedule sheet and take screenshot
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

# Navigate to DOOR SCHEDULES sheet
$json = '{"method":"setActiveView","params":{"viewId":1545074}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
Write-Host "Navigated to DOOR SCHEDULES sheet"

Start-Sleep -Seconds 1

# Zoom to fit
$json = '{"method":"zoomToFit","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

Start-Sleep -Seconds 1

# Take screenshot
$json = '{"method":"exportViewToImage","params":{"viewId":1545074,"filePath":"D:\\RevitMCPBridge2026\\door_schedule_sheet.png","width":2400,"height":1800}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Screenshot saved: $($result.result.filePath)" -ForegroundColor Green
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

$pipe.Close()
