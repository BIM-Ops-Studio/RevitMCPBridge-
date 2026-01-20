# Get all available schedulable fields for Rooms
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

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "GET ROOM SCHEDULABLE FIELDS" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Get available fields for the existing schedule
$scheduleId = "1338506"
$result = Send-RevitCommand -Method "getAvailableSchedulableFields" -Params @{
    scheduleId = $scheduleId
}

if ($result.success) {
    Write-Host "Available schedulable fields for Rooms:" -ForegroundColor Green
    Write-Host "=======================================" -ForegroundColor Cyan

    if ($result.availableFields) {
        $result.availableFields | ForEach-Object {
            Write-Host "  - $($_.name)" -ForegroundColor White
        }

        Write-Host "`nTotal: $($result.availableFields.Count) fields available" -ForegroundColor Green

        # Look for specific fields we need
        Write-Host "`nSearching for our needed fields:" -ForegroundColor Cyan
        $needed = @("Number", "Name", "Level", "Area", "Comment")

        foreach ($need in $needed) {
            $matches = $result.availableFields | Where-Object { $_.name -like "*$need*" }
            if ($matches) {
                Write-Host "  '$need' matches:" -ForegroundColor Yellow
                $matches | ForEach-Object {
                    Write-Host "    → $($_.name)" -ForegroundColor Green
                }
            } else {
                Write-Host "  '$need' - no matches" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "ERROR: $($result.error)" -ForegroundColor Red
}

Write-Host "`nDone!" -ForegroundColor Green
