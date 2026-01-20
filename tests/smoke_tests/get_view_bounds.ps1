# Get view bounds and try different coordinate approach
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== GETTING VIEW BOUNDS ===" -ForegroundColor Cyan

# Get view info for the legend
$json = '{"method":"getViewInfo","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "View Info:" -ForegroundColor Yellow
    Write-Host $response
} else {
    Write-Host "getViewInfo: $($result.error)" -ForegroundColor Yellow
}

# Try getting crop region
$json = '{"method":"getViewCropRegion","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nCrop Region:" -ForegroundColor Yellow
    Write-Host $response
} else {
    Write-Host "getViewCropRegion: $($result.error)" -ForegroundColor Yellow
}

# Delete all misplaced text first before trying different coordinates
Write-Host "`nLooking for misplaced text to delete..." -ForegroundColor Cyan

# Try a very different coordinate range - maybe negative or very large
# Place test at x=10, y=5
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(10.0, 5.0, 0)
        text = "TEST X=10"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "Test at (10,5): $($result.success)"

# Try negative coordinates
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(-2.0, 5.0, 0)
        text = "TEST X=-2"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "Test at (-2,5): $($result.success)"

$pipe.Close()
