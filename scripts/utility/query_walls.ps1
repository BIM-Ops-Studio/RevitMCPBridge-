function Send-MCPCommand($method, $parameters) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'RevitMCPBridge2026', [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(3000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true
    $reader = New-Object System.IO.StreamReader($pipe)
    $request = @{method=$method; params=$parameters} | ConvertTo-Json -Compress -Depth 5
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()
    return $response | ConvertFrom-Json
}

Write-Host "=== Querying All Walls ===" -ForegroundColor Cyan

# Get all walls
$result = Send-MCPCommand -method 'getWalls' -parameters @{}

if ($result.success) {
    Write-Host "Total walls: $($result.walls.Count)" -ForegroundColor Green
    Write-Host ""
    foreach ($wall in $result.walls) {
        Write-Host "Wall ID: $($wall.elementId)" -ForegroundColor Yellow
        Write-Host "  Type: $($wall.wallTypeName)" -ForegroundColor Gray
        Write-Host "  Level: $($wall.levelName)" -ForegroundColor Gray
        if ($wall.curve) {
            Write-Host "  Start: ($($wall.curve.startX | % {$_.ToString('F2')}), $($wall.curve.startY | % {$_.ToString('F2')}), $($wall.curve.startZ | % {$_.ToString('F2')}))" -ForegroundColor Gray
            Write-Host "  End: ($($wall.curve.endX | % {$_.ToString('F2')}), $($wall.curve.endY | % {$_.ToString('F2')}), $($wall.curve.endZ | % {$_.ToString('F2')}))" -ForegroundColor Gray
        }
        Write-Host ""
    }
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}
