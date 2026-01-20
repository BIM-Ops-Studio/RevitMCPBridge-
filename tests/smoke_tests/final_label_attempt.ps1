# Final attempt at label placement - clean up and use larger coordinate values
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== FINAL LABEL PLACEMENT ===" -ForegroundColor Cyan

# First, get any text notes in this view and delete the misplaced ones
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

# The existing TYPE B/C labels show that the coordinate system has:
# - X increasing to the right
# - Y values for labels around 4.5 (below doors)
# - Each door is spaced about 1.2-1.5 units apart
#
# Looking at the layout:
# TYPE A at x~0.5, TYPE B at x~1.7, TYPE C at x~3.2
# 4th door should be at x~4.7, 5th door at x~5.8

# Place "SEE SCH." above 4th door
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(4.7, 6.0, 0)
        text = "SEE SCH."
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "SEE SCH (4th): $($result.success)"

# Place TYPE D label below 4th door
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(4.7, 4.5, 0)
        text = "TYPE D`nSLIDING GLASS"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE D: $($result.success)"

# Place "SEE SCH." above 5th door
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(5.8, 6.0, 0)
        text = "SEE SCH."
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "SEE SCH (5th): $($result.success)"

# Place TYPE E label below 5th door
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(5.8, 4.5, 0)
        text = "TYPE E`nBYPASS SLIDER"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE E: $($result.success)"

# Place TYPE F in the SEE SCHEDULE box area
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(2.5, 2.5, 0)
        text = "TYPE F`nFIRE-RATED`n(SEE SCHEDULE)"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE F: $($result.success)"

$pipe.Close()
Write-Host "`nPlacement complete - check positions"
