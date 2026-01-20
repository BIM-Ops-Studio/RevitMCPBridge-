# Add door type labels using correct positioning
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== ADDING DOOR TYPE LABELS (ATTEMPT 2) ===" -ForegroundColor Cyan

# Make sure we're on the legend view
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
Write-Host "On TYPES - DOOR legend"

# Looking at the screenshot, the doors are spaced approximately:
# - TYPE A at x ~ -0.5 (left edge)
# - TYPE B at x ~ 1.5
# - TYPE C at x ~ 3.5
# - 4th door at x ~ 5.0
# - 5th door at x ~ 6.5
#
# The labels appear below the doors at y ~ -0.4 to -0.6
# But the view might be scaled differently

# Try placing with feet-based coordinates relative to view origin
# These doors appear to be about 2 feet apart based on scale

# TYPE D - under 4th door (approximately 4 door-widths from left)
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(4.5, -0.5, 0)
        text = "TYPE D`nSLIDING GLASS"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE D placed: success=$($result.success)"
if (-not $result.success) { Write-Host "  Error: $($result.error)" -ForegroundColor Red }

# TYPE E - under 5th door
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(5.8, -0.5, 0)
        text = "TYPE E`nBYPASS SLIDER"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE E placed: success=$($result.success)"
if (-not $result.success) { Write-Host "  Error: $($result.error)" -ForegroundColor Red }

# TYPE F - in the SEE SCHEDULE area (lower left)
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(0.5, -2.0, 0)
        text = "TYPE F`nFIRE-RATED`n(SEE SCHEDULE FOR RATING)"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE F placed: success=$($result.success)"
if (-not $result.success) { Write-Host "  Error: $($result.error)" -ForegroundColor Red }

$pipe.Close()
Write-Host "`nDone - please verify placement"
