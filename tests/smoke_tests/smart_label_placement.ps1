# Smart label placement - find existing labels first
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== SMART LABEL PLACEMENT ===" -ForegroundColor Cyan

# First, delete the misplaced labels we just created
$json = '{"method":"getTextNotesInView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

Write-Host "Text notes found in legend: $($result.result.textNotes.Count)"

if ($result.result.textNotes.Count -gt 0) {
    foreach ($note in $result.result.textNotes) {
        $preview = $note.text -replace "`r`n", " " -replace "`n", " "
        Write-Host "  ID:$($note.id) at ($($note.location.x), $($note.location.y)): $preview"

        # Delete our misplaced labels
        if ($note.text -like "*TYPE D*" -or $note.text -like "*TYPE E*" -or $note.text -like "*TYPE F*" -or $note.text -like "*SLIDING*" -or $note.text -like "*BYPASS*" -or $note.text -like "*RATING*") {
            Write-Host "    -> Deleting..." -ForegroundColor Yellow
            $deleteJson = "{`"method`":`"deleteTextNote`",`"params`":{`"elementId`":$($note.id)}}"
            $writer.WriteLine($deleteJson)
            $delResponse = $reader.ReadLine()
        }
    }
} else {
    Write-Host "No text notes found via API in this view"
}

# The legend view likely uses legend components (not text notes) for the labels
# Let me try getting element info from a specific location or using the sheet

Write-Host "`nChecking the sheet that contains this legend..."

# Navigate to sheet A-7.1 DOOR SCHEDULES
$json = '{"method":"setActiveView","params":{"viewId":1545074}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

# Get text notes on the sheet
$json = '{"method":"getTextNotesInView","params":{"viewId":1545074}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

Write-Host "Text notes on sheet: $($result.result.textNotes.Count)"
foreach ($note in $result.result.textNotes) {
    $preview = $note.text -replace "`r`n", " " -replace "`n", " "
    if ($preview.Length -gt 60) { $preview = $preview.Substring(0,60) + "..." }

    # Show position for TYPE labels to understand coordinate system
    if ($note.text -like "*TYPE*" -and $note.text -notlike "*WALL TYPE*") {
        Write-Host "  Door TYPE label: ($($note.location.x), $($note.location.y)) - $preview" -ForegroundColor Cyan
    }

    # Delete our misplaced labels if they're on the sheet
    if ($note.text -like "*TYPE D*" -or $note.text -like "*TYPE E*" -or $note.text -like "*TYPE F*" -or $note.text -like "*SLIDING*" -or $note.text -like "*BYPASS*" -or $note.text -like "*RATING*") {
        Write-Host "  -> Deleting misplaced label..." -ForegroundColor Yellow
        $deleteJson = "{`"method`":`"deleteTextNote`",`"params`":{`"elementId`":$($note.id)}}"
        $writer.WriteLine($deleteJson)
        $delResponse = $reader.ReadLine()
    }
}

$pipe.Close()
