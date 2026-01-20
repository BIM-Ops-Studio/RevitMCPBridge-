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

Write-Host "=== Step 1: Verify Shell Creation ===" -ForegroundColor Cyan

# Query the 4 walls we just created
$wallIds = @(1240493, 1240494, 1240495, 1240496)
Write-Host "Querying walls: $($wallIds -join ', ')"

$allWallsExist = $true
foreach ($wallId in $wallIds) {
    $result = Send-MCPCommand -method 'getWallInfo' -parameters @{wallId=$wallId}
    if ($result.success) {
        Write-Host "  [OK] Wall $wallId exists - $($result.wallTypeName)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Wall $wallId - $($result.error)" -ForegroundColor Red
        $allWallsExist = $false
    }
}

if (-not $allWallsExist) {
    Write-Host "`n[ERROR] Not all walls exist. Stopping." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Step 2: Get Available 3D Views ===" -ForegroundColor Cyan
$views = Send-MCPCommand -method 'getViews' -parameters @{}
if ($views.success) {
    $view3D = $views.views | Where-Object { $_.viewType -eq '3D' -or $_.viewName -match '3D' } | Select-Object -First 1
    if ($view3D) {
        Write-Host "Found 3D view: $($view3D.viewName) (ID: $($view3D.viewId))" -ForegroundColor Green

        # Try to set as active view
        Write-Host "Setting as active view..." -ForegroundColor Yellow
        $setView = Send-MCPCommand -method 'setActiveView' -parameters @{viewId=$view3D.viewId}
        if ($setView.success) {
            Write-Host "  [OK] 3D view is now active" -ForegroundColor Green
        } else {
            Write-Host "  [INFO] Could not set active view: $($setView.error)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No 3D view found. User should manually switch to 3D view in Revit." -ForegroundColor Yellow
    }
} else {
    Write-Host "Could not query views: $($views.error)" -ForegroundColor Yellow
}

Write-Host "`n=== Step 3: Create Floor Inside Shell ===" -ForegroundColor Cyan

# Get level info
$levels = Send-MCPCommand -method 'getLevels' -parameters @{}
$levelId = $levels.levels[0].levelId
Write-Host "Using Level: $($levels.levels[0].name) (ID: $levelId)"

# Define floor boundary (same as shell perimeter, but slightly inset to avoid overlapping walls)
$width = 45 + (4/12)   # 45'-4" = 45.333 ft
$depth = 28 + (8/12)   # 28'-8" = 28.667 ft
$inset = 0.5  # Inset 6 inches from wall centerline

$floorPoints = @(
    @($inset, $inset, 0),
    @(($width - $inset), $inset, 0),
    @(($width - $inset), ($depth - $inset), 0),
    @($inset, ($depth - $inset), 0)
)

Write-Host "Creating floor with boundary: $($floorPoints.Count) points"
$floor = Send-MCPCommand -method 'createFloor' -parameters @{
    points = $floorPoints
    levelId = $levelId
    structural = $false
}

if ($floor.success) {
    Write-Host "  [SUCCESS] Floor created - ID: $($floor.floorId)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Floor creation failed: $($floor.error)" -ForegroundColor Red
}

Write-Host "`n=== Verification Complete ===" -ForegroundColor Cyan
Write-Host "Shell: 4 walls created and verified" -ForegroundColor Green
Write-Host "Floor: $(if ($floor.success) { 'Created successfully' } else { 'Failed - needs manual creation' })" -ForegroundColor $(if ($floor.success) { 'Green' } else { 'Yellow' })
Write-Host "`nNext: Add doors and windows to complete the shell" -ForegroundColor Cyan
