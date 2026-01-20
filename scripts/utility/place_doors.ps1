# Place all 26 doors in target model
$pipeName = 'RevitMCPBridge2026'

# Read the door data
$doorData = Get-Content "D:\RevitMCPBridge2026\avon_park_doors_windows.json" -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host "Placing $($doorData.doors.Count) doors..."
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($i in 0..($doorData.doors.Count - 1)) {
    $door = $doorData.doors[$i]

    # Create pipe connection
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    # Get location
    $x = $door.location[0]
    $y = $door.location[1]
    $z = $door.location[2]

    # Build request for placeFamilyInstance
    $request = @{
        method = "placeFamilyInstance"
        params = @{
            familyName = $door.familyName
            typeName = $door.typeName
            location = @($x, $y, $z)
            levelId = 30  # GROUND FLOOR
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    $result = $response | ConvertFrom-Json
    if ($result.success) {
        $successCount++
        Write-Host "Placed door $($i+1): $($door.familyName) - $($door.typeName)"
    } else {
        $failCount++
        Write-Host "FAILED door $($i+1): $($result.error)"
    }

    # Small delay between placements
    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Door placement complete!"
Write-Host "Success: $successCount"
Write-Host "Failed: $failCount"
Write-Host "=========================================="
