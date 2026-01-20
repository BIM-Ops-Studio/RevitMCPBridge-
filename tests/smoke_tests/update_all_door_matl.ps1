# Update all door MATL values
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== UPDATING DOOR MATERIALS ===" -ForegroundColor Cyan
Write-Host "Material Legend:"
Write-Host "  WD = Wood (interior doors)"
Write-Host "  WD/PT = Wood/Painted (frame material)"

# Get all doors
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$doorsResult = $response | ConvertFrom-Json

if ($doorsResult.success) {
    Write-Host "Found $($doorsResult.doorCount) doors"

    $successCount = 0
    $failCount = 0

    foreach ($door in $doorsResult.doors) {
        # Only process numeric-marked doors
        if ($door.mark -match '^\d+$') {
            $doorId = $door.doorId
            $mark = $door.mark

            # Update Dr Panel Mat'l Mark (DOOR MATL)
            $updateJson = @{
                method = "setParameter"
                params = @{
                    elementId = $doorId
                    parameterName = "Dr Panel Mat'l Mark"
                    value = "WD"
                }
            } | ConvertTo-Json -Compress

            $writer.WriteLine($updateJson)
            $response = $reader.ReadLine()
            $result = $response | ConvertFrom-Json

            if ($result.success) {
                $successCount++
                Write-Host "  Door $mark : MATL = WD" -ForegroundColor Green
            } else {
                $failCount++
                Write-Host "  Door $mark : FAILED - $($result.error)" -ForegroundColor Red
            }
        }
    }

    Write-Host "`n=== COMPLETE ===" -ForegroundColor Green
    Write-Host "Successfully updated: $successCount doors"
    if ($failCount -gt 0) {
        Write-Host "Failed: $failCount doors" -ForegroundColor Red
    }
}

$pipe.Close()
