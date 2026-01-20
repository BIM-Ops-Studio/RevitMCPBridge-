# Check door types legend and hardware legends
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CHECKING DOOR TYPE LEGEND ===" -ForegroundColor Cyan

# Set active view to TYPES - DOOR legend
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
Write-Host "Set active view: $($result.success)"

# Get text notes in this view
$json = '{"method":"getTextNotesInView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nText Notes in TYPES - DOOR:" -ForegroundColor Yellow
    foreach ($note in $result.result.textNotes) {
        $preview = $note.text -replace "`r`n", " " -replace "`n", " "
        if ($preview.Length -gt 80) { $preview = $preview.Substring(0, 80) + "..." }
        Write-Host "  $preview"
    }
}

Write-Host "`n=== CHECKING DOOR HARDWARE LEGEND ===" -ForegroundColor Cyan

$json = '{"method":"getTextNotesInView","params":{"viewId":1481720}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nText Notes in DOOR HARDWARE:" -ForegroundColor Yellow
    foreach ($note in $result.result.textNotes) {
        $preview = $note.text -replace "`r`n", " " -replace "`n", " "
        if ($preview.Length -gt 100) { $preview = $preview.Substring(0, 100) + "..." }
        Write-Host "  $preview"
    }
}

Write-Host "`n=== CHECKING DOOR AND HARDWARE NOTES ===" -ForegroundColor Cyan

$json = '{"method":"getTextNotesInView","params":{"viewId":1481694}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nText Notes in DOOR AND HARDWARE NOTES:" -ForegroundColor Yellow
    foreach ($note in $result.result.textNotes) {
        $preview = $note.text -replace "`r`n", " " -replace "`n", " "
        if ($preview.Length -gt 100) { $preview = $preview.Substring(0, 100) + "..." }
        Write-Host "  $preview"
    }
}

$pipe.Close()
