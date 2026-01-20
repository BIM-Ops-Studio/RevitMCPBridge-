function Send-MCPCommand($method, $parameters) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'RevitMCPBridge2026', [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(3000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true
    $reader = New-Object System.IO.StreamReader($pipe)
    $request = @{method=$method; params=$parameters} | ConvertTo-Json -Compress
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()
    return $response | ConvertFrom-Json
}

Write-Host '=== Version Check ===' -ForegroundColor Cyan
$ping = Send-MCPCommand -method 'ping' -parameters @{}
Write-Host "Version: $($ping.assemblyVersion)" -ForegroundColor Yellow
Write-Host "Message: $($ping.testMessage)" -ForegroundColor Yellow

Write-Host "`n=== Wall Creation Test ===" -ForegroundColor Cyan
$levels = Send-MCPCommand -method 'getLevels' -parameters @{}
$levelId = $levels.levels[0].levelId
Write-Host "Using level ID: $levelId"

$result = Send-MCPCommand -method 'createWall' -parameters @{
    startPoint = @(0, 0, 0)
    endPoint = @(10, 0, 0)
    levelId = $levelId
    height = 10.0
}

if ($result.success) {
    Write-Host '[SUCCESS] Wall created!' -ForegroundColor Green
} else {
    Write-Host '[FAIL] Error message:' -ForegroundColor Red
    Write-Host $result.error -ForegroundColor White
    if ($result.error -like '*V1.0.8.0-TEST*') {
        Write-Host "`n*** NEW CODE IS RUNNING! ***" -ForegroundColor Green
    } else {
        Write-Host "`n*** OLD CODE IS STILL RUNNING ***" -ForegroundColor Red
    }
}
