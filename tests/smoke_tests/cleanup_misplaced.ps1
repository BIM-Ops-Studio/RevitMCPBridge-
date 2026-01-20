# Clean up misplaced labels in the legend
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CLEANING UP MISPLACED LABELS ===" -ForegroundColor Cyan

# Navigate to legend
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

# Get all text notes and identify ones to delete
# We want to keep the correctly placed TYPE D, E, F but delete:
# - TEST X=10, TEST X=-2
# - The old misplaced duplicates at bottom left

$json = '{"method":"getTextNotesInView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success -and $result.result.textNotes.Count -gt 0) {
    Write-Host "Found $($result.result.textNotes.Count) text notes"

    foreach ($note in $result.result.textNotes) {
        $text = $note.text -replace "`r`n", " " -replace "`n", " "
        $x = [math]::Round($note.location.x, 1)
        $y = [math]::Round($note.location.y, 1)

        Write-Host "  ID:$($note.id) at ($x, $y): $text"

        # Delete if it's a test label or misplaced (low X coordinate)
        $shouldDelete = $false

        if ($text -like "*TEST*") {
            $shouldDelete = $true
            Write-Host "    -> DELETE (test label)" -ForegroundColor Yellow
        }
        elseif ($x -lt 15 -and ($text -like "*TYPE D*" -or $text -like "*TYPE E*" -or $text -like "*TYPE F*" -or $text -like "*SLIDING*" -or $text -like "*BYPASS*" -or $text -like "*FIRE-RATED*" -or $text -like "*SCHEDULE*" -or $text -like "*RATING*")) {
            # This is a misplaced duplicate (correct ones are at X >= 20)
            $shouldDelete = $true
            Write-Host "    -> DELETE (misplaced duplicate)" -ForegroundColor Yellow
        }

        if ($shouldDelete) {
            $deleteJson = "{`"method`":`"deleteTextNote`",`"params`":{`"elementId`":$($note.id)}}"
            $writer.WriteLine($deleteJson)
            $delResponse = $reader.ReadLine()
            $delResult = $delResponse | ConvertFrom-Json
            if ($delResult.success) {
                Write-Host "    Deleted" -ForegroundColor Green
            } else {
                Write-Host "    Failed: $($delResult.error)" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "No text notes found via API"
}

$pipe.Close()
Write-Host "`nCleanup complete"
