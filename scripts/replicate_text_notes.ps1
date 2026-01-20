# Replicate text notes from source view to target view
# Source: 2136700 (SECTION DETAIL @ GARAGE ROOF)
# Target: 2238350 (New Drafting View)

$sourceViewId = 2136700
$targetViewId = 2238350

# Coordinate offsets
$offsetX = 31.28
$offsetZ = 2.17

Write-Host "=== Text Note Replication ===" -ForegroundColor Cyan

# Get text notes from source
$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

$json = @{method = "getTextNotePositions"; params = @{viewId = $sourceViewId}} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$writer.Flush()
Start-Sleep -Milliseconds 2000
$response = $reader.ReadLine()
$data = $response | ConvertFrom-Json

if (-not $data.success) {
    Write-Host "Failed to get text notes: $($data.error)" -ForegroundColor Red
    $pipe.Close()
    exit 1
}

$notes = $data.result.textNotes
Write-Host "Retrieved $($notes.Count) text notes" -ForegroundColor Green

$successCount = 0
$failCount = 0

foreach ($note in $notes) {
    # Normalize coordinates
    $textX = [Math]::Round($note.x - $offsetX, 4)
    $textY = [Math]::Round($note.z - $offsetZ, 4)

    # Clean text (replace \r with newlines for display)
    $cleanText = $note.text -replace '\\r', "`n"
    $displayText = ($cleanText.Substring(0, [Math]::Min(30, $cleanText.Length))) -replace "`n", " "

    if ($note.hasLeader -and $note.leaderEndpoints.Count -gt 0) {
        # Create text with leader
        $leaderX = [Math]::Round($note.leaderEndpoints[0].x - $offsetX, 4)
        $leaderY = [Math]::Round($note.leaderEndpoints[0].z - $offsetZ, 4)

        $createJson = @{
            method = "createTextNoteWithLeader"
            params = @{
                viewId = $targetViewId
                text = $note.text -replace '\\r', "`r`n"
                textX = $textX
                textY = $textY
                leaderEndX = $leaderX
                leaderEndY = $leaderY
            }
        } | ConvertTo-Json -Compress -Depth 3

        $writer.WriteLine($createJson)
        $writer.Flush()
        Start-Sleep -Milliseconds 500
        $createResponse = $reader.ReadLine()
        $result = $createResponse | ConvertFrom-Json

        if ($result.success) {
            $successCount++
            Write-Host "  Created: '$displayText...' at ($textX, $textY) with leader" -ForegroundColor Green
        } else {
            # Try without leader
            $createJson2 = @{
                method = "createTextNote"
                params = @{
                    viewId = $targetViewId
                    text = $note.text -replace '\\r', "`r`n"
                    x = $textX
                    y = $textY
                }
            } | ConvertTo-Json -Compress

            $writer.WriteLine($createJson2)
            $writer.Flush()
            Start-Sleep -Milliseconds 500
            $createResponse2 = $reader.ReadLine()
            $result2 = $createResponse2 | ConvertFrom-Json

            if ($result2.success) {
                $successCount++
                Write-Host "  Created: '$displayText...' at ($textX, $textY) (no leader)" -ForegroundColor Yellow
            } else {
                $failCount++
                Write-Host "  Failed: '$displayText...' - $($result2.error)" -ForegroundColor Red
            }
        }
    } else {
        # Create text without leader
        $createJson = @{
            method = "createTextNote"
            params = @{
                viewId = $targetViewId
                text = $note.text -replace '\\r', "`r`n"
                x = $textX
                y = $textY
            }
        } | ConvertTo-Json -Compress

        $writer.WriteLine($createJson)
        $writer.Flush()
        Start-Sleep -Milliseconds 500
        $createResponse = $reader.ReadLine()
        $result = $createResponse | ConvertFrom-Json

        if ($result.success) {
            $successCount++
            Write-Host "  Created: '$displayText...' at ($textX, $textY)" -ForegroundColor Green
        } else {
            $failCount++
            Write-Host "  Failed: '$displayText...' - $($result.error)" -ForegroundColor Red
        }
    }
}

$pipe.Close()

Write-Host "`n=== Replication Complete ===" -ForegroundColor Cyan
Write-Host "Total notes: $($notes.Count)"
Write-Host "Created: $successCount"
Write-Host "Failed: $failCount"
