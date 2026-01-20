# Show all text annotations in the active view

function Send-RevitCommand {
    param([string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        return $response | ConvertFrom-Json
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient) { try { $pipeClient.Dispose() } catch {} }
    }
}

# Get active view
$viewResult = Send-RevitCommand -Method "getActiveView" -Params @{}
$viewId = $viewResult.viewId

Write-Host "`nActive View: $($viewResult.viewName)" -ForegroundColor Cyan
Write-Host "Level: $($viewResult.level)`n" -ForegroundColor Cyan

# Get all text notes
$textResult = Send-RevitCommand -Method "getTextNotesInView" -Params @{ viewId = $viewId }

Write-Host "Found $($textResult.textNoteCount) text annotations`n" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "TEXT ANNOTATIONS:" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

$counter = 1
foreach ($note in $textResult.textNotes) {
    Write-Host "[$counter] Text: $($note.text)" -ForegroundColor White
    Write-Host "    Type: $($note.typeName)" -ForegroundColor Gray
    Write-Host ""
    $counter++
}
