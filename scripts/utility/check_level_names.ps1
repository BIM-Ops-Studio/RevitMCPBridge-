# Check what level names are in the project

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

Write-Host "`nGetting all rooms..." -ForegroundColor Yellow
$result = Send-RevitCommand -Method "getRooms" -Params @{}

if ($result.success) {
    Write-Host "Total rooms: $($result.rooms.Count)" -ForegroundColor Green

    # Get unique level names
    $levels = $result.rooms | Select-Object -ExpandProperty level -Unique | Sort-Object

    Write-Host "`nUnique Level Names:" -ForegroundColor Cyan
    foreach ($level in $levels) {
        $count = ($result.rooms | Where-Object { $_.level -eq $level }).Count
        Write-Host "  $level : $count rooms" -ForegroundColor White
    }

    Write-Host "`nSample rooms from first level:" -ForegroundColor Cyan
    $firstLevel = $levels[0]
    $sampleRooms = $result.rooms | Where-Object { $_.level -eq $firstLevel } | Select-Object -First 5
    $sampleRooms | Format-Table number, name, level, area -AutoSize
}
