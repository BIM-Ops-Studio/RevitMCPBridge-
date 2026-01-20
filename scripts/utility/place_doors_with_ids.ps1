# Place doors with type IDs
$pipeName = 'RevitMCPBridge2026'

$placementData = Get-Content "D:\RevitMCPBridge2026\door_placement_data.json" -Raw | ConvertFrom-Json

Write-Host "Placing $($placementData.Count) doors..."
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($door in $placementData) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $x = $door.location[0]
    $y = $door.location[1]
    $z = $door.location[2]

    $request = @{
        method = "placeFamilyInstance"
        params = @{
            familyTypeId = $door.typeId
            location = @($x, $y, $z)
            levelId = 30
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    $result = $response | ConvertFrom-Json
    if ($result.success) {
        $successCount++
        Write-Host "Placed door $($door.index): $($door.familyName) - $($door.typeName)"
    } else {
        $failCount++
        Write-Host "FAILED door $($door.index): $($result.error)"
    }

    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Door placement complete!"
Write-Host "Success: $successCount"
Write-Host "Failed: $failCount"
Write-Host "=========================================="
