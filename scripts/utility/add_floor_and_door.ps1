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

Write-Host "=== Step 1: Create Floor ===" -ForegroundColor Cyan

# Get level
$levels = Send-MCPCommand -method 'getLevels' -parameters @{}
$levelId = $levels.levels[0].levelId
Write-Host "Using Level: $($levels.levels[0].name) (ID: $levelId)"

# Define dimensions
$width = 45 + (4/12)   # 45'-4"
$depth = 28 + (8/12)   # 28'-8"

# Floor boundary (inset slightly from walls)
$inset = 0.5
$floorPoints = @(
    @($inset, $inset, 0),
    @(($width - $inset), $inset, 0),
    @(($width - $inset), ($depth - $inset), 0),
    @($inset, ($depth - $inset), 0)
)

Write-Host "Creating floor boundary with 4 points..."
$floor = Send-MCPCommand -method 'createFloor' -parameters @{
    boundaryPoints = $floorPoints
    levelId = $levelId
    structural = $false
}

if ($floor.success) {
    Write-Host "  [SUCCESS] Floor ID: $($floor.floorId)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] $($floor.error)" -ForegroundColor Red
}

Write-Host "`n=== Step 2: Get Door Types ===" -ForegroundColor Cyan
$doorTypes = Send-MCPCommand -method 'getDoorTypes' -parameters @{}

if ($doorTypes.success -and $doorTypes.doorTypes.Count -gt 0) {
    Write-Host "Found $($doorTypes.doorTypes.Count) door types" -ForegroundColor Green

    # Find a standard single door (looking for 3'-0" single flush)
    $standardDoor = $doorTypes.doorTypes | Where-Object {
        $_.familyName -match 'Single' -and
        ($_.typeName -match "3'-0" -or $_.typeName -match "36")
    } | Select-Object -First 1

    if (-not $standardDoor) {
        # Just take the first door type available
        $standardDoor = $doorTypes.doorTypes[0]
    }

    Write-Host "Selected door type: $($standardDoor.typeName)" -ForegroundColor Yellow
    Write-Host "  Family: $($standardDoor.familyName)" -ForegroundColor Gray
    Write-Host "  Type ID: $($standardDoor.typeId)" -ForegroundColor Gray

    Write-Host "`n=== Step 3: Add Main Entrance Door ===" -ForegroundColor Cyan
    # Place door on south wall (bottom wall) centered at ~22.5 ft from left
    $doorX = $width / 2  # Center of width
    $doorY = 0.0         # On bottom wall
    $doorZ = 0.0

    Write-Host "Placing door at ($doorX, $doorY, $doorZ)..."
    $door = Send-MCPCommand -method 'placeFamilyInstance' -parameters @{
        familyTypeId = $standardDoor.typeId
        location = @($doorX, $doorY, $doorZ)
        levelId = $levelId
    }

    if ($door.success) {
        Write-Host "  [SUCCESS] Door ID: $($door.elementId)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $($door.error)" -ForegroundColor Red
        Write-Host "  Note: Door needs host wall. May need manual placement." -ForegroundColor Yellow
    }
} else {
    Write-Host "No door types found. Need to load door families first." -ForegroundColor Yellow
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Floor: $(if ($floor.success) { 'Created' } else { 'Failed' })" -ForegroundColor $(if ($floor.success) { 'Green' } else { 'Red' })
Write-Host "Door: $(if ($door.success) { 'Placed' } else { 'Needs manual placement' })" -ForegroundColor $(if ($door.success) { 'Green' } else { 'Yellow' })
Write-Host "`nRecommendation: Check Revit 3D view to verify shell structure" -ForegroundColor Cyan
