# Place door type labels on sheet A-7.1 (sheet coordinates)
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== PLACING LABELS ON SHEET ===" -ForegroundColor Cyan

# First, let's get sheet info to understand the coordinate system
# Sheet A-7.1 DOOR SCHEDULES ID: 1545074

# Navigate to sheet
$json = '{"method":"setActiveView","params":{"viewId":1545074}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

# From the screenshot, the DOOR TYPES legend is in the upper portion of the sheet
# On a typical 24x36 sheet, the legend appears to be roughly:
# - Left edge around x=0.3
# - TYPE B at roughly x=0.9
# - TYPE C at roughly x=1.3
# - 4th door at roughly x=1.6
# - 5th door at roughly x=1.9
# - Labels are at y around 1.15 (below door symbols)

# Standard sheet coordinates: origin at lower-left, units in feet

# Place TYPE D under 4th door on sheet
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1545074
        location = @(1.6, 1.15, 0)
        text = "TYPE D`nSLIDING GLASS"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE D: success=$($result.success)"
if (-not $result.success) { Write-Host "  Error: $($result.error)" -ForegroundColor Red }
if ($result.success) { Write-Host "  ID: $($result.result.textNoteId)" -ForegroundColor Green }

# Place TYPE E under 5th door on sheet
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1545074
        location = @(1.9, 1.15, 0)
        text = "TYPE E`nBYPASS SLIDER"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE E: success=$($result.success)"
if (-not $result.success) { Write-Host "  Error: $($result.error)" -ForegroundColor Red }
if ($result.success) { Write-Host "  ID: $($result.result.textNoteId)" -ForegroundColor Green }

# Place TYPE F below in the SEE SCHEDULE area
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1545074
        location = @(0.5, 0.8, 0)
        text = "TYPE F - FIRE-RATED`n(SEE SCHEDULE FOR RATING)"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE F: success=$($result.success)"
if (-not $result.success) { Write-Host "  Error: $($result.error)" -ForegroundColor Red }
if ($result.success) { Write-Host "  ID: $($result.result.textNoteId)" -ForegroundColor Green }

$pipe.Close()
Write-Host "`nDone - check sheet A-7.1"
