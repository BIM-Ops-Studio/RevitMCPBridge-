function Send-MCPCommand($method, $parameters) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'RevitMCPBridge2026', [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(3000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true
    $reader = New-Object System.IO.StreamReader($pipe)
    $request = @{method=$method; params=$parameters} | ConvertTo-Json -Compress -Depth 5
    Write-Host "[DEBUG] Sending: $request" -ForegroundColor DarkGray
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()
    return $response | ConvertFrom-Json
}

Write-Host "=== Creating Missing Wall 1 (Bottom) ===" -ForegroundColor Cyan

# Get level
$levels = Send-MCPCommand -method 'getLevels' -parameters @{}
$levelId = $levels.levels[0].levelId
Write-Host "Using Level: $($levels.levels[0].name) (ID: $levelId)"

# Wall dimensions
$width = 45 + (4/12)   # 45'-4" = 45.333 ft

Write-Host "`nAttempting to create Wall 1 (Bottom): (0,0) to ($width,0)"
$w1 = Send-MCPCommand -method 'createWall' -parameters @{
    startPoint = @(0, 0, 0)
    endPoint = @($width, 0, 0)
    levelId = $levelId
    height = 10.0
}

if ($w1.success) {
    Write-Host "[SUCCESS] Wall ID: $($w1.wallId)" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Error: $($w1.error)" -ForegroundColor Red
}
