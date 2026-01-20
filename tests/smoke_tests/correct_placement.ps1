# Correct placement with proper X coordinates (X=10 ≈ TYPE B position)
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CORRECT LABEL PLACEMENT ===" -ForegroundColor Cyan

# Based on TEST X=10 landing near TYPE B:
# - TYPE B is at X ≈ 10
# - TYPE C is at X ≈ 15 (5 units spacing)
# - 4th door at X ≈ 20
# - 5th door at X ≈ 24
# Labels appear at Y ≈ 5 (below doors at Y ≈ 6)

# Navigate to legend view
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

# Place "SEE SCH." above 4th door
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(20.0, 7.0, 0)
        text = "SEE SCH."
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "SEE SCH (4th door): $($result.success)"

# Place TYPE D label
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(20.0, 4.5, 0)
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
        location = @(24.0, 7.0, 0)
        text = "SEE SCH."
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "SEE SCH (5th door): $($result.success)"

# Place TYPE E label
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(24.0, 4.5, 0)
        text = "TYPE E`nBYPASS SLIDER"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE E: $($result.success)"

# Place TYPE F in the SEE SCHEDULE area (lower on the view)
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(8.0, 1.0, 0)
        text = "TYPE F`nFIRE-RATED`n(SEE SCHEDULE)"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "TYPE F: $($result.success)"

$pipe.Close()
Write-Host "`nDone - verify placement"
