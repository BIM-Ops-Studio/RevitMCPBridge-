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

Write-Host "=== Creating Shell Using Polyline Method ===" -ForegroundColor Cyan
Write-Host "Dimensions: 45'-4`" x 28'-8`" at 10' height" -ForegroundColor Yellow

# Get level
$levels = Send-MCPCommand -method 'getLevels' -parameters @{}
$levelId = $levels.levels[0].levelId
Write-Host "Using Level: $($levels.levels[0].name) (ID: $levelId)"

# Convert feet-inches to decimal feet
$width = 45 + (4/12)   # 45'-4" = 45.333 ft
$depth = 28 + (8/12)   # 28'-8" = 28.667 ft
$height = 10.0

Write-Host "`nCreating 4-wall shell as closed polyline..."

# Define points for closed rectangular polyline
# Start at origin, go clockwise: (0,0) -> (width,0) -> (width,depth) -> (0,depth) -> back to (0,0)
$points = @(
    @(0, 0, 0),
    @($width, 0, 0),
    @($width, $depth, 0),
    @(0, $depth, 0),
    @(0, 0, 0)  # Close the loop
)

$result = Send-MCPCommand -method 'createWallsFromPolyline' -parameters @{
    points = $points
    levelId = $levelId
    height = $height
    isClosed = $true
}

if ($result.success) {
    Write-Host "`n[SUCCESS] Shell created!" -ForegroundColor Green
    Write-Host "Number of walls created: $($result.wallIds.Count)" -ForegroundColor Green
    Write-Host "Wall IDs: $($result.wallIds -join ', ')" -ForegroundColor Yellow
} else {
    Write-Host "`n[FAIL] Error: $($result.error)" -ForegroundColor Red
}

Write-Host "`n=== Complete! ===" -ForegroundColor Cyan
Write-Host "Rectangular shell: $width ft x $depth ft x $height ft high"
