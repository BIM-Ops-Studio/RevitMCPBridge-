# Complete Wall Transfer from Avon Park to SF-project-test-2
# Extracts walls from source and creates them in target

# MCP helper function
function Invoke-MCPMethod {
    param(
        [string]$Method,
        [hashtable]$Params = @{}
    )

    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Depth 10 -Compress

    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    return $response | ConvertFrom-Json
}

Write-Host "=== Complete Wall Transfer ===" -ForegroundColor Cyan
Write-Host ""

# ============================================
# STEP 1: Extract walls from Avon Park
# ============================================
Write-Host "=== STEP 1: Extracting Walls from Avon Park ===" -ForegroundColor Yellow

$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "1700 West Sheffield Road" }
Write-Host "Active: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

# Get all walls
$wallsResult = Invoke-MCPMethod -Method "getWalls" -Params @{}

if (-not $wallsResult.success) {
    Write-Host "Error getting walls: $($wallsResult.error)" -ForegroundColor Red
    exit
}

$sourceWalls = $wallsResult.walls
Write-Host "Found $($sourceWalls.Count) walls" -ForegroundColor Green

# Get levels for reference
$levelsResult = Invoke-MCPMethod -Method "getLevels" -Params @{}
$sourceLevels = @{}
foreach ($level in $levelsResult.levels) {
    $sourceLevels[$level.name] = $level
}

# Extract wall data
$wallData = @()
foreach ($wall in $sourceWalls) {
    if ($wall.startPoint -and $wall.endPoint) {
        $wallData += @{
            wallId = $wall.wallId
            wallType = $wall.wallType
            startPoint = $wall.startPoint
            endPoint = $wall.endPoint
            height = $wall.height
            baseLevel = $wall.baseLevel
            topLevel = $wall.topLevel
            baseOffset = $wall.baseOffset
            topOffset = $wall.topOffset
        }
    }
}

Write-Host "Extracted $($wallData.Count) walls with geometry" -ForegroundColor Gray

# Get unique wall types
$uniqueTypes = $wallData | ForEach-Object { $_.wallType } | Sort-Object -Unique
Write-Host "Unique wall types: $($uniqueTypes.Count)" -ForegroundColor Gray
foreach ($type in $uniqueTypes) {
    Write-Host "  - $type" -ForegroundColor White
}

# Save wall data
$wallData | ConvertTo-Json -Depth 10 | Out-File "D:\RevitMCPBridge2026\avon_park_walls.json" -Encoding UTF8
Write-Host "Saved wall data to avon_park_walls.json" -ForegroundColor Gray

# Note: Wall types will be matched by name in target, or default type used if not found

# ============================================
# STEP 3: Create walls in target
# ============================================
Write-Host ""
Write-Host "=== STEP 3: Creating Walls in Target ===" -ForegroundColor Yellow

$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

# Get target levels
$targetLevelsResult = Invoke-MCPMethod -Method "getLevels" -Params @{}
$targetLevels = @{}
foreach ($level in $targetLevelsResult.levels) {
    $targetLevels[$level.name] = $level
}

# Map source levels to target levels
# Avon Park: T.O.F., F.F., T.O.B.
# Target: L1, L2
# F.F. (0) -> L1, T.O.B. (10) -> L2

$levelMap = @{
    "F.F." = "L1"
    "T.O.F." = "L1"
    "T.O.B." = "L2"
}

# Get target level IDs
$targetL1 = $targetLevels["L1"]
$targetL2 = $targetLevels["L2"]

Write-Host "Level mapping:" -ForegroundColor Gray
Write-Host "  F.F. -> L1 (ID: $($targetL1.levelId))" -ForegroundColor Gray
Write-Host "  T.O.B. -> L2 (ID: $($targetL2.levelId))" -ForegroundColor Gray

# Create walls
$results = @{
    success = @()
    failed = @()
}

$counter = 0
foreach ($wall in $wallData) {
    $counter++

    # Determine target level
    $targetLevelId = $targetL1.levelId
    if ($wall.baseLevel -eq "T.O.B.") {
        $targetLevelId = $targetL2.levelId
    }

    # Calculate wall height (default 10 ft if not specified)
    $height = $wall.height
    if ($null -eq $height -or $height -eq 0) {
        $height = 10
    }

    Write-Host "[$counter/$($wallData.Count)] Creating wall: $($wall.wallType)" -ForegroundColor White

    $createResult = Invoke-MCPMethod -Method "createWall" -Params @{
        wallTypeName = $wall.wallType
        startPoint = @($wall.startPoint.x, $wall.startPoint.y, 0)
        endPoint = @($wall.endPoint.x, $wall.endPoint.y, 0)
        height = $height
        levelId = $targetLevelId
    }

    if ($createResult.success) {
        Write-Host "  SUCCESS: ID $($createResult.wallId)" -ForegroundColor Green
        $results.success += @{
            wallType = $wall.wallType
            wallId = $createResult.wallId
        }
    } else {
        Write-Host "  FAILED: $($createResult.error)" -ForegroundColor Red
        $results.failed += @{
            wallType = $wall.wallType
            error = $createResult.error
        }
    }

    Start-Sleep -Milliseconds 50
}

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "=== Wall Transfer Complete ===" -ForegroundColor Cyan
Write-Host "Successful: $($results.success.Count)" -ForegroundColor Green
Write-Host "Failed: $($results.failed.Count)" -ForegroundColor $(if ($results.failed.Count -gt 0) { "Red" } else { "Gray" })

# Save results
$results | ConvertTo-Json -Depth 10 | Out-File "D:\RevitMCPBridge2026\wall_transfer_results.json" -Encoding UTF8
Write-Host "Results saved to wall_transfer_results.json" -ForegroundColor Gray
