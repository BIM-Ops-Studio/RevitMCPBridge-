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

Write-Host "=== Checking Existing Walls ===" -ForegroundColor Cyan

# Get all walls
$result = Send-MCPCommand -method 'getWallsByLevel' -parameters @{levelId=30}

if ($result.success) {
    Write-Host "Total walls: $($result.walls.Count)" -ForegroundColor Green
    foreach ($wall in $result.walls) {
        $sp = $wall.startPoint
        $ep = $wall.endPoint
        Write-Host "Wall ID $($wall.wallId): ($($sp[0]),$($sp[1])) to ($($ep[0]),$($ep[1])) Height: $($wall.height)" -ForegroundColor Yellow
    }
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

Write-Host "`n=== Trying Wall 1 with Slight Offset ===" -ForegroundColor Cyan
# Try creating Wall 1 with a slight offset to avoid potential intersection
$w1 = Send-MCPCommand -method 'createWall' -parameters @{
    startPoint = @(0.1, 0.1, 0)
    endPoint = @(45.33, 0.1, 0)
    levelId = 30
    height = 10.0
}

if ($w1.success) {
    Write-Host "[SUCCESS] Wall ID: $($w1.wallId)" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Error: $($w1.error)" -ForegroundColor Red
}
