# Add missing door type labels to TYPES - DOOR legend
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== ADDING DOOR TYPE LABELS ===" -ForegroundColor Cyan

# Navigate to TYPES - DOOR legend (ID: 1760142)
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
Write-Host "Navigated to TYPES - DOOR legend"

Start-Sleep -Milliseconds 500

# Add TYPE D label - SLIDING GLASS (position next to 4th door)
# Based on screenshot, the unlabeled doors are on the right side
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(4.5, -0.4, 0)
        text = "TYPE D`nSLIDING GLASS"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
if ($result.success) {
    Write-Host "Added TYPE D label" -ForegroundColor Green
} else {
    Write-Host "TYPE D Error: $($result.error)" -ForegroundColor Red
}

# Add TYPE E label - CLOSET BYPASS (position for 5th door)
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(5.5, -0.4, 0)
        text = "TYPE E`nCLOSET BYPASS"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
if ($result.success) {
    Write-Host "Added TYPE E label" -ForegroundColor Green
} else {
    Write-Host "TYPE E Error: $($result.error)" -ForegroundColor Red
}

# Add TYPE F label - FIRE-RATED (in the SEE SCHEDULE section below)
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(1.0, -1.5, 0)
        text = "TYPE F`nFIRE-RATED"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
if ($result.success) {
    Write-Host "Added TYPE F label" -ForegroundColor Green
} else {
    Write-Host "TYPE F Error: $($result.error)" -ForegroundColor Red
}

$pipe.Close()
Write-Host "`nDone adding labels"
