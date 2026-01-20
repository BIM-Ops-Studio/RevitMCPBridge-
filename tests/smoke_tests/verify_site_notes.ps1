# Verify text notes on site plan after consolidation
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(15000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$json = '{"method":"getTextNotesInView","params":{"viewId":29237}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Text notes in Site Plan (viewId 29237):" -ForegroundColor Cyan
    $noteCount = 0
    foreach ($note in $result.result.textNotes) {
        $noteCount++
        $textPreview = $note.text -replace "`r`n", " " -replace "`n", " "
        if ($textPreview.Length -gt 100) {
            $textPreview = $textPreview.Substring(0, 100) + "..."
        }
        Write-Host "  ID: $($note.id) - $textPreview"
    }
    Write-Host "`nTotal notes: $noteCount"
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

$pipe.Close()
