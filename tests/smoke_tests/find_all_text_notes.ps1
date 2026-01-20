# Find all text notes in the model
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== FINDING ALL TEXT NOTES ===" -ForegroundColor Cyan

# Navigate to the door schedule sheet first
$json = '{"method":"setActiveView","params":{"viewId":1545074}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

# Get text notes from that view
$json = '{"method":"getTextNotesInView","params":{"viewId":1545074}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nText notes on DOOR SCHEDULES sheet:" -ForegroundColor Yellow
    $notesToDelete = @()
    foreach ($note in $result.result.textNotes) {
        $preview = $note.text -replace "`r`n", " " -replace "`n", " "
        if ($preview.Length -gt 50) { $preview = $preview.Substring(0,50) + "..." }

        # Check if this is one of our added labels
        if ($note.text -like "*TYPE D*" -or $note.text -like "*TYPE E*" -or $note.text -like "*TYPE F*" -or $note.text -like "*SLIDING GLASS*" -or $note.text -like "*CLOSET BYPASS*" -or $note.text -like "*FIRE-RATED*") {
            Write-Host "  [DELETE] ID: $($note.id) - $preview" -ForegroundColor Red
            $notesToDelete += $note.id
        }
    }

    if ($notesToDelete.Count -gt 0) {
        Write-Host "`nDeleting $($notesToDelete.Count) duplicate labels..." -ForegroundColor Yellow
        foreach ($id in $notesToDelete) {
            $deleteJson = "{`"method`":`"deleteTextNote`",`"params`":{`"elementId`":$id}}"
            $writer.WriteLine($deleteJson)
            $delResponse = $reader.ReadLine()
            $delResult = $delResponse | ConvertFrom-Json
            if ($delResult.success) {
                Write-Host "  Deleted $id" -ForegroundColor Green
            } else {
                Write-Host "  Failed to delete $id : $($delResult.error)" -ForegroundColor Red
            }
        }
    }
}

# Also try the legend view
Write-Host "`n--- Checking Legend View ---" -ForegroundColor Cyan
$json = '{"method":"getTextNotesInView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

Write-Host "Text notes in legend: $($result.result.textNotes.Count)"
foreach ($note in $result.result.textNotes) {
    $preview = $note.text -replace "`r`n", " " -replace "`n", " "
    if ($preview.Length -gt 50) { $preview = $preview.Substring(0,50) + "..." }
    Write-Host "  ID: $($note.id) - $preview"

    # Delete if it's one of ours
    if ($note.text -like "*TYPE D*" -or $note.text -like "*TYPE E*" -or $note.text -like "*TYPE F*" -or $note.text -like "*SLIDING*" -or $note.text -like "*BYPASS*" -or $note.text -like "*FIRE-RATED*") {
        $deleteJson = "{`"method`":`"deleteTextNote`",`"params`":{`"elementId`":$($note.id)}}"
        $writer.WriteLine($deleteJson)
        $delResponse = $reader.ReadLine()
        Write-Host "    Deleted" -ForegroundColor Green
    }
}

$pipe.Close()
