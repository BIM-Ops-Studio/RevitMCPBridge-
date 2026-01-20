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

Write-Host "=== Adding Windows to Shell ===" -ForegroundColor Cyan

# Get level
$levels = Send-MCPCommand -method 'getLevels' -parameters @{}
$levelId = $levels.levels[0].levelId
Write-Host "Using Level: $($levels.levels[0].name) (ID: $levelId)"

# Define dimensions
$width = 45 + (4/12)   # 45'-4"
$depth = 28 + (8/12)   # 28'-8"

Write-Host "`n=== Step 1: Get Window Types ===" -ForegroundColor Cyan
$windowTypes = Send-MCPCommand -method 'getWindowTypes' -parameters @{}

if ($windowTypes.success -and $windowTypes.windowTypes.Count -gt 0) {
    Write-Host "Found $($windowTypes.windowTypes.Count) window types" -ForegroundColor Green

    # Find a standard fixed window (3'-0" x 4'-0")
    $standardWindow = $windowTypes.windowTypes | Where-Object {
        $_.familyName -match 'Fixed' -and
        ($_.typeName -match "3'" -or $_.typeName -match "36")
    } | Select-Object -First 1

    if (-not $standardWindow) {
        # Just take the first window type available
        $standardWindow = $windowTypes.windowTypes[0]
    }

    Write-Host "Selected window type: $($standardWindow.typeName)" -ForegroundColor Yellow
    Write-Host "  Family: $($standardWindow.familyName)" -ForegroundColor Gray
    Write-Host "  Type ID: $($standardWindow.typeId)" -ForegroundColor Gray

    Write-Host "`n=== Step 2: Place Windows ===" -ForegroundColor Cyan

    $windowsPlaced = 0
    $windowHeight = 3.5  # Typical sill height

    # Front wall (bottom) - 2 windows flanking the door
    Write-Host "Adding windows to front wall..."
    $frontWindows = @(
        @{ x = $width * 0.25; y = 0; z = $windowHeight; name = "Front Left" },
        @{ x = $width * 0.75; y = 0; z = $windowHeight; name = "Front Right" }
    )

    foreach ($win in $frontWindows) {
        Write-Host "  Placing $($win.name) window at ($($win.x), $($win.y), $($win.z))..."
        $result = Send-MCPCommand -method 'placeFamilyInstance' -parameters @{
            familyTypeId = $standardWindow.typeId
            location = @($win.x, $win.y, $win.z)
            levelId = $levelId
        }

        if ($result.success) {
            Write-Host "    [OK]" -ForegroundColor Green
            $windowsPlaced++
        } else {
            Write-Host "    [FAIL] $($result.error)" -ForegroundColor Red
        }
    }

    # Back wall (top) - 2 windows
    Write-Host "Adding windows to back wall..."
    $backWindows = @(
        @{ x = $width * 0.33; y = $depth; z = $windowHeight; name = "Back Left" },
        @{ x = $width * 0.67; y = $depth; z = $windowHeight; name = "Back Right" }
    )

    foreach ($win in $backWindows) {
        Write-Host "  Placing $($win.name) window at ($($win.x), $($win.y), $($win.z))..."
        $result = Send-MCPCommand -method 'placeFamilyInstance' -parameters @{
            familyTypeId = $standardWindow.typeId
            location = @($win.x, $win.y, $win.z)
            levelId = $levelId
        }

        if ($result.success) {
            Write-Host "    [OK]" -ForegroundColor Green
            $windowsPlaced++
        } else {
            Write-Host "    [FAIL] $($result.error)" -ForegroundColor Red
        }
    }

    # Left wall - 1 window
    Write-Host "Adding window to left wall..."
    $result = Send-MCPCommand -method 'placeFamilyInstance' -parameters @{
        familyTypeId = $standardWindow.typeId
        location = @(0, ($depth * 0.5), $windowHeight)
        levelId = $levelId
    }

    if ($result.success) {
        Write-Host "  [OK]" -ForegroundColor Green
        $windowsPlaced++
    } else {
        Write-Host "  [FAIL] $($result.error)" -ForegroundColor Red
    }

    # Right wall - 1 window
    Write-Host "Adding window to right wall..."
    $result = Send-MCPCommand -method 'placeFamilyInstance' -parameters @{
        familyTypeId = $standardWindow.typeId
        location = @($width, ($depth * 0.5), $windowHeight)
        levelId = $levelId
    }

    if ($result.success) {
        Write-Host "  [OK]" -ForegroundColor Green
        $windowsPlaced++
    } else {
        Write-Host "  [FAIL] $($result.error)" -ForegroundColor Red
    }

    Write-Host "`n=== Summary ===" -ForegroundColor Cyan
    Write-Host "Windows placed: $windowsPlaced / 6" -ForegroundColor $(if ($windowsPlaced -eq 6) { 'Green' } else { 'Yellow' })

} else {
    Write-Host "No window types found. Need to load window families first." -ForegroundColor Yellow
}

Write-Host "`n=== Shell Complete! ===" -ForegroundColor Green
Write-Host "Components created:" -ForegroundColor Cyan
Write-Host "  - 4 walls (45'-4`" x 28'-8`" x 10' high)" -ForegroundColor White
Write-Host "  - 1 floor" -ForegroundColor White
Write-Host "  - 1 entrance door" -ForegroundColor White
Write-Host "  - $windowsPlaced windows" -ForegroundColor White
Write-Host "`nRecommendation: Switch to Revit 3D view to see the completed shell!" -ForegroundColor Cyan
