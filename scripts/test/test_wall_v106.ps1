function Send-MCPCommand($method, $parameters) {
    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'RevitMCPBridge2026', [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(3000)

        $writer = New-Object System.IO.StreamWriter($pipe)
        $writer.AutoFlush = $true
        $reader = New-Object System.IO.StreamReader($pipe)

        $request = @{
            method = $method
            parameters = $parameters
        } | ConvertTo-Json -Compress

        Write-Host "[SEND] $request"
        $writer.WriteLine($request)

        $response = $reader.ReadLine()
        $pipe.Close()

        return $response | ConvertFrom-Json
    }
    catch {
        Write-Host "[ERROR] $_" -ForegroundColor Red
        return $null
    }
}

Write-Host "`n=== RevitMCPBridge v1.0.6.0 Test ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Ping to verify connection and version
Write-Host "[TEST 1] Testing connection..." -ForegroundColor Yellow
$pingResult = Send-MCPCommand -method "ping" -parameters @{}

if ($pingResult -and $pingResult.success) {
    Write-Host "[SUCCESS] Connected! Version: $($pingResult.assemblyVersion)" -ForegroundColor Green
    Write-Host "Test Message: $($pingResult.testMessage)" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Ping failed" -ForegroundColor Red
    exit 1
}

# Test 2: Get levels to verify read operations work
Write-Host ""
Write-Host "[TEST 2] Getting levels..." -ForegroundColor Yellow
$levelsResult = Send-MCPCommand -method "getLevels" -parameters @{}

if ($levelsResult -and $levelsResult.success) {
    Write-Host "[SUCCESS] Found $($levelsResult.levels.Count) levels" -ForegroundColor Green
    $firstLevel = $levelsResult.levels[0]
    Write-Host "First level: $($firstLevel.name) (ID: $($firstLevel.id))" -ForegroundColor Gray
} else {
    Write-Host "[FAIL] getLevels failed: $($levelsResult.error)" -ForegroundColor Red
    exit 1
}

# Test 3: Create wall with detailed logging in v1.0.6.0
Write-Host ""
Write-Host "[TEST 3] Creating wall..." -ForegroundColor Yellow
$levelId = $levelsResult.levels[0].id

$wallParams = @{
    startPoint = @(0, 0, 0)
    endPoint = @(10, 0, 0)
    levelId = $levelId
    height = 10.0
}

$wallResult = Send-MCPCommand -method "createWall" -parameters $wallParams

if ($wallResult -and $wallResult.success) {
    Write-Host "[SUCCESS] Wall created! ID: $($wallResult.wallId)" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Wall creation failed" -ForegroundColor Red
    Write-Host "Error: $($wallResult.error)" -ForegroundColor Red
    if ($wallResult.stackTrace) {
        Write-Host "Stack trace:" -ForegroundColor Red
        Write-Host $wallResult.stackTrace -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "[IMPORTANT] Check the log file for detailed diagnostic info:" -ForegroundColor Yellow
    Write-Host "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\Logs\mcp_2025112520251125.log" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Look for these log messages:" -ForegroundColor Yellow
    Write-Host "  - [CreateWallByPoints] Method called" -ForegroundColor Gray
    Write-Host "  - [CreateWallByPoints] uiApp is NULL" -ForegroundColor Gray
    Write-Host "  - [CreateWallByPoints] ActiveUIDocument is NULL" -ForegroundColor Gray
    Write-Host "  - [CreateWallByPoints] Document is NULL" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "=== All tests passed! ===" -ForegroundColor Green
