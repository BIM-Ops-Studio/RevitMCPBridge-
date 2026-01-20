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

Write-Host "=== Creating 4-Wall Rectangular Shell ===" -ForegroundColor Cyan
Write-Host "Dimensions: 45'-4`" x 28'-8`" at 10' height" -ForegroundColor Yellow

# Get level
$levels = Send-MCPCommand -method 'getLevels' -parameters @{}
$levelId = $levels.levels[0].levelId
Write-Host "Using Level: $($levels.levels[0].name) (ID: $levelId)"

# Convert feet-inches to decimal feet
$width = 45 + (4/12)   # 45'-4" = 45.333 ft
$depth = 28 + (8/12)   # 28'-8" = 28.667 ft
$height = 10.0

Write-Host "`nCreating walls..."

# Wall 1: Bottom (along X-axis)
Write-Host "Wall 1 (Bottom): (0,0) to ($width,0)"
$w1 = Send-MCPCommand -method 'createWall' -parameters @{startPoint=@(0,0,0); endPoint=@($width,0,0); levelId=$levelId; height=$height}
if ($w1.success) { Write-Host "  [OK] Wall ID: $($w1.wallId)" -ForegroundColor Green } else { Write-Host "  [FAIL] $($w1.error)" -ForegroundColor Red }

# Wall 2: Right (along Y-axis)
Write-Host "Wall 2 (Right): ($width,0) to ($width,$depth)"
$w2 = Send-MCPCommand -method 'createWall' -parameters @{startPoint=@($width,0,0); endPoint=@($width,$depth,0); levelId=$levelId; height=$height}
if ($w2.success) { Write-Host "  [OK] Wall ID: $($w2.wallId)" -ForegroundColor Green } else { Write-Host "  [FAIL] $($w2.error)" -ForegroundColor Red }

# Wall 3: Top (along X-axis, reverse)
Write-Host "Wall 3 (Top): ($width,$depth) to (0,$depth)"
$w3 = Send-MCPCommand -method 'createWall' -parameters @{startPoint=@($width,$depth,0); endPoint=@(0,$depth,0); levelId=$levelId; height=$height}
if ($w3.success) { Write-Host "  [OK] Wall ID: $($w3.wallId)" -ForegroundColor Green } else { Write-Host "  [FAIL] $($w3.error)" -ForegroundColor Red }

# Wall 4: Left (along Y-axis, reverse)
Write-Host "Wall 4 (Left): (0,$depth) to (0,0)"
$w4 = Send-MCPCommand -method 'createWall' -parameters @{startPoint=@(0,$depth,0); endPoint=@(0,0,0); levelId=$levelId; height=$height}
if ($w4.success) { Write-Host "  [OK] Wall ID: $($w4.wallId)" -ForegroundColor Green } else { Write-Host "  [FAIL] $($w4.error)" -ForegroundColor Red }

Write-Host "`n=== Shell Complete! ===" -ForegroundColor Green
Write-Host "Rectangular shell: $width ft x $depth ft x $height ft high"
