# Check what room tags are displaying on the floor plan

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

# Get room tags in view
Write-Host "Getting room tags from view..." -ForegroundColor Yellow
$tagsResult = Send-RevitCommand -Method "getRoomTagsInView" -Params @{ viewId = $viewId }

if ($tagsResult.success) {
    Write-Host "Found $($tagsResult.roomTagCount) room tags`n" -ForegroundColor Green

    # Find Office 01 and Office 02
    $office01Tag = $tagsResult.roomTags | Where-Object { $_.roomNumber -eq "01" } | Select-Object -First 1
    $office02Tag = $tagsResult.roomTags | Where-Object { $_.roomNumber -eq "02" } | Select-Object -First 1

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "OFFICE 01:" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    if ($office01Tag) {
        Write-Host "  Room Number: $($office01Tag.roomNumber)" -ForegroundColor White
        Write-Host "  Room Name: $($office01Tag.roomName)" -ForegroundColor White
        Write-Host "  Tag Text: $($office01Tag.tagText)" -ForegroundColor Yellow
    } else {
        Write-Host "  Tag not found" -ForegroundColor Red
    }

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "OFFICE 02:" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    if ($office02Tag) {
        Write-Host "  Room Number: $($office02Tag.roomNumber)" -ForegroundColor White
        Write-Host "  Room Name: $($office02Tag.roomName)" -ForegroundColor White
        Write-Host "  Tag Text: $($office02Tag.tagText)" -ForegroundColor Yellow
    } else {
        Write-Host "  Tag not found" -ForegroundColor Red
    }

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "ALL ROOM TAGS (first 10):" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    $tagsResult.roomTags | Select-Object -First 10 | ForEach-Object {
        Write-Host "Room $($_.roomNumber): $($_.tagText)" -ForegroundColor White
    }
} else {
    Write-Host "ERROR: $($tagsResult.error)" -ForegroundColor Red
}
