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

Write-Host "=== Checking All Walls in Model ===" -ForegroundColor Cyan

# Get all walls
$result = Send-MCPCommand -method 'getWalls' -parameters @{}

if ($result.success) {
    Write-Host "Total walls found: $($result.walls.Count)" -ForegroundColor Green
    Write-Host ""

    if ($result.walls.Count -gt 0) {
        foreach ($wall in $result.walls) {
            Write-Host "Wall ID: $($wall.elementId)" -ForegroundColor Yellow
            Write-Host "  Type ID: $($wall.wallTypeId)" -ForegroundColor Gray
            Write-Host "  Type Name: $($wall.wallTypeName)" -ForegroundColor Gray
            Write-Host "  Level: $($wall.levelName) (ID: $($wall.levelId))" -ForegroundColor Gray
            if ($wall.length) {
                Write-Host "  Length: $($wall.length) ft" -ForegroundColor Gray
            }
            if ($wall.height) {
                Write-Host "  Height: $($wall.height) ft" -ForegroundColor Gray
            }
            Write-Host ""
        }
    } else {
        Write-Host "No walls found in the model!" -ForegroundColor Red
        Write-Host "This suggests walls were not committed or were undone." -ForegroundColor Yellow
    }
} else {
    Write-Host "Error querying walls: $($result.error)" -ForegroundColor Red
}

Write-Host "`n=== Attempting to Re-create Shell ===" -ForegroundColor Cyan

# Get level
$levels = Send-MCPCommand -method 'getLevels' -parameters @{}
$levelId = $levels.levels[0].levelId
Write-Host "Using Level: $($levels.levels[0].name) (ID: $levelId)"

# Define dimensions
$width = 45 + (4/12)   # 45'-4"
$depth = 28 + (8/12)   # 28'-8"
$height = 10.0

# Try creating shell again with polyline method
$points = @(
    @(0, 0, 0),
    @($width, 0, 0),
    @($width, $depth, 0),
    @(0, $depth, 0),
    @(0, 0, 0)
)

Write-Host "Creating shell with polyline method..."
$result = Send-MCPCommand -method 'createWallsFromPolyline' -parameters @{
    points = $points
    levelId = $levelId
    height = $height
    isClosed = $true
}

if ($result.success) {
    Write-Host "[SUCCESS] Walls created: $($result.wallIds -join ', ')" -ForegroundColor Green

    # Immediately verify they exist
    Write-Host "`nVerifying walls exist..."
    Start-Sleep -Seconds 1

    $verify = Send-MCPCommand -method 'getWalls' -parameters @{}
    if ($verify.success) {
        Write-Host "Walls now in model: $($verify.walls.Count)" -ForegroundColor $(if ($verify.walls.Count -ge 4) { 'Green' } else { 'Yellow' })
    }
} else {
    Write-Host "[FAIL] Error: $($result.error)" -ForegroundColor Red
}
