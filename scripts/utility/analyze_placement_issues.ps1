# Comprehensive Placement Analysis
# Compares source and target geometry to identify issues

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

Write-Host "=== Comprehensive Placement Analysis ===" -ForegroundColor Cyan
Write-Host ""

# ============================================
# PART 1: Analyze Source Project (Avon Park)
# ============================================
Write-Host "=== PART 1: Source Project Analysis (Avon Park) ===" -ForegroundColor Yellow

$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "1700 West Sheffield Road" }
Write-Host "Active: $($switchResult.result.activatedDocument)" -ForegroundColor Gray
Write-Host ""

# Get project base point / survey point info
Write-Host "Getting project info..." -ForegroundColor Gray
$projectInfoResult = Invoke-MCPMethod -Method "getProjectInfo" -Params @{}

# Get walls from source
Write-Host "Getting walls..." -ForegroundColor Gray
$sourceWallsResult = Invoke-MCPMethod -Method "getWalls" -Params @{}
$sourceWalls = @()
if ($sourceWallsResult.success) {
    $sourceWalls = $sourceWallsResult.walls
    Write-Host "  Found $($sourceWalls.Count) walls" -ForegroundColor White
}

# Get levels
$sourceLevelsResult = Invoke-MCPMethod -Method "getLevels" -Params @{}
Write-Host "  Levels:" -ForegroundColor White
foreach ($level in $sourceLevelsResult.levels) {
    Write-Host "    $($level.name): elevation $($level.elevation)" -ForegroundColor Gray
}

# Get rooms for spatial context
Write-Host "Getting rooms..." -ForegroundColor Gray
$sourceRoomsResult = Invoke-MCPMethod -Method "getRooms" -Params @{}
if ($sourceRoomsResult.success -and $sourceRoomsResult.rooms) {
    Write-Host "  Found $($sourceRoomsResult.rooms.Count) rooms" -ForegroundColor White
    foreach ($room in $sourceRoomsResult.rooms | Select-Object -First 5) {
        $loc = $room.location
        Write-Host "    $($room.name): ($([math]::Round($loc.x, 2)), $([math]::Round($loc.y, 2)))" -ForegroundColor Gray
    }
}

# Get beds from source
Write-Host ""
Write-Host "Source Beds:" -ForegroundColor Cyan
$sourceBeds = Invoke-MCPMethod -Method "getFamilyInstances" -Params @{ familyName = "FN-BED-RESIDENTIAL" }
if ($sourceBeds.success) {
    foreach ($bed in $sourceBeds.instances) {
        $loc = $bed.location
        $facing = $bed.facingOrientation
        Write-Host "  $($bed.typeName)" -ForegroundColor White
        Write-Host "    Location: ($([math]::Round($loc.x, 2)), $([math]::Round($loc.y, 2)), $([math]::Round($loc.z, 2)))" -ForegroundColor Gray
        Write-Host "    Facing: ($([math]::Round($facing.x, 2)), $([math]::Round($facing.y, 2)))" -ForegroundColor Gray
        Write-Host "    Mirrored: $($bed.mirrored)" -ForegroundColor Gray

        # Find nearest wall
        $minDist = 1000
        $nearestWall = $null
        foreach ($wall in $sourceWalls) {
            if ($wall.startPoint -and $wall.endPoint) {
                # Calculate distance to wall line
                $wx = ($wall.startPoint.x + $wall.endPoint.x) / 2
                $wy = ($wall.startPoint.y + $wall.endPoint.y) / 2
                $dist = [math]::Sqrt([math]::Pow($loc.x - $wx, 2) + [math]::Pow($loc.y - $wy, 2))
                if ($dist -lt $minDist) {
                    $minDist = $dist
                    $nearestWall = $wall
                }
            }
        }
        if ($nearestWall) {
            Write-Host "    Nearest wall: $($nearestWall.wallType) @ $([math]::Round($minDist, 2)) ft" -ForegroundColor Gray
        }
    }
}

# Get kitchen sink
Write-Host ""
Write-Host "Source Kitchen Sink:" -ForegroundColor Cyan
$sourceSink = Invoke-MCPMethod -Method "getFamilyInstances" -Params @{ familyName = "Sink Kitchen-Double" }
if ($sourceSink.success -and $sourceSink.instances.Count -gt 0) {
    $sink = $sourceSink.instances[0]
    $loc = $sink.location
    Write-Host "  Location: ($([math]::Round($loc.x, 2)), $([math]::Round($loc.y, 2)))" -ForegroundColor Gray
}

# Get countertop
Write-Host ""
Write-Host "Source Countertops:" -ForegroundColor Cyan
$sourceCountertop = Invoke-MCPMethod -Method "getFamilyInstances" -Params @{ familyName = "Counter Top" }
if ($sourceCountertop.success) {
    foreach ($ct in $sourceCountertop.instances) {
        $loc = $ct.location
        Write-Host "  $($ct.typeName)" -ForegroundColor White
        Write-Host "    Location: ($([math]::Round($loc.x, 2)), $([math]::Round($loc.y, 2)))" -ForegroundColor Gray
    }
}

# Calculate bounding box of all source elements
$allSourceInstances = @()
$sourceData = Get-Content "D:\RevitMCPBridge2026\avon_park_family_instances.json" | ConvertFrom-Json
$allSourceInstances += $sourceData.casework
$allSourceInstances += $sourceData.furniture
$allSourceInstances += $sourceData.plumbingFixtures
$allSourceInstances += $sourceData.specialtyEquipment

$minX = 1000; $maxX = -1000; $minY = 1000; $maxY = -1000
foreach ($inst in $allSourceInstances) {
    if ($inst.location) {
        if ($inst.location.x -lt $minX) { $minX = $inst.location.x }
        if ($inst.location.x -gt $maxX) { $maxX = $inst.location.x }
        if ($inst.location.y -lt $minY) { $minY = $inst.location.y }
        if ($inst.location.y -gt $maxY) { $maxY = $inst.location.y }
    }
}

Write-Host ""
Write-Host "Source Element Bounds:" -ForegroundColor Cyan
Write-Host "  X: $([math]::Round($minX, 2)) to $([math]::Round($maxX, 2)) (span: $([math]::Round($maxX - $minX, 2)) ft)" -ForegroundColor White
Write-Host "  Y: $([math]::Round($minY, 2)) to $([math]::Round($maxY, 2)) (span: $([math]::Round($maxY - $minY, 2)) ft)" -ForegroundColor White

# ============================================
# PART 2: Analyze Target Project
# ============================================
Write-Host ""
Write-Host "=== PART 2: Target Project Analysis (SF-project-test-2) ===" -ForegroundColor Yellow

$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active: $($switchResult.result.activatedDocument)" -ForegroundColor Gray
Write-Host ""

# Get walls from target
Write-Host "Getting walls..." -ForegroundColor Gray
$targetWallsResult = Invoke-MCPMethod -Method "getWalls" -Params @{}
$targetWalls = @()
if ($targetWallsResult.success) {
    $targetWalls = $targetWallsResult.walls
    Write-Host "  Found $($targetWalls.Count) walls" -ForegroundColor White
}

# Get levels
$targetLevelsResult = Invoke-MCPMethod -Method "getLevels" -Params @{}
Write-Host "  Levels:" -ForegroundColor White
foreach ($level in $targetLevelsResult.levels) {
    Write-Host "    $($level.name): elevation $($level.elevation)" -ForegroundColor Gray
}

# Get rooms
Write-Host "Getting rooms..." -ForegroundColor Gray
$targetRoomsResult = Invoke-MCPMethod -Method "getRooms" -Params @{}
if ($targetRoomsResult.success -and $targetRoomsResult.rooms) {
    Write-Host "  Found $($targetRoomsResult.rooms.Count) rooms" -ForegroundColor White
    foreach ($room in $targetRoomsResult.rooms | Select-Object -First 5) {
        $loc = $room.location
        Write-Host "    $($room.name): ($([math]::Round($loc.x, 2)), $([math]::Round($loc.y, 2)))" -ForegroundColor Gray
    }
}

# Get beds from target
Write-Host ""
Write-Host "Target Beds:" -ForegroundColor Cyan
$targetBeds = Invoke-MCPMethod -Method "getFamilyInstances" -Params @{ familyName = "FN-BED-RESIDENTIAL" }
if ($targetBeds.success) {
    foreach ($bed in $targetBeds.instances) {
        $loc = $bed.location
        $facing = $bed.facingOrientation
        Write-Host "  $($bed.typeName)" -ForegroundColor White
        Write-Host "    Location: ($([math]::Round($loc.x, 2)), $([math]::Round($loc.y, 2)), $([math]::Round($loc.z, 2)))" -ForegroundColor Gray
        Write-Host "    Facing: ($([math]::Round($facing.x, 2)), $([math]::Round($facing.y, 2)))" -ForegroundColor Gray
        Write-Host "    Mirrored: $($bed.mirrored)" -ForegroundColor Gray

        # Find nearest wall in target
        $minDist = 1000
        $nearestWall = $null
        foreach ($wall in $targetWalls) {
            if ($wall.startPoint -and $wall.endPoint) {
                $wx = ($wall.startPoint.x + $wall.endPoint.x) / 2
                $wy = ($wall.startPoint.y + $wall.endPoint.y) / 2
                $dist = [math]::Sqrt([math]::Pow($loc.x - $wx, 2) + [math]::Pow($loc.y - $wy, 2))
                if ($dist -lt $minDist) {
                    $minDist = $dist
                    $nearestWall = $wall
                }
            }
        }
        if ($nearestWall) {
            Write-Host "    Nearest wall: $($nearestWall.wallType) @ $([math]::Round($minDist, 2)) ft" -ForegroundColor Gray
        } else {
            Write-Host "    NO NEARBY WALL FOUND!" -ForegroundColor Red
        }
    }
}

# Calculate bounding box of target walls
$wallMinX = 1000; $wallMaxX = -1000; $wallMinY = 1000; $wallMaxY = -1000
foreach ($wall in $targetWalls) {
    if ($wall.startPoint) {
        if ($wall.startPoint.x -lt $wallMinX) { $wallMinX = $wall.startPoint.x }
        if ($wall.startPoint.x -gt $wallMaxX) { $wallMaxX = $wall.startPoint.x }
        if ($wall.startPoint.y -lt $wallMinY) { $wallMinY = $wall.startPoint.y }
        if ($wall.startPoint.y -gt $wallMaxY) { $wallMaxY = $wall.startPoint.y }
    }
    if ($wall.endPoint) {
        if ($wall.endPoint.x -lt $wallMinX) { $wallMinX = $wall.endPoint.x }
        if ($wall.endPoint.x -gt $wallMaxX) { $wallMaxX = $wall.endPoint.x }
        if ($wall.endPoint.y -lt $wallMinY) { $wallMinY = $wall.endPoint.y }
        if ($wall.endPoint.y -gt $wallMaxY) { $wallMaxY = $wall.endPoint.y }
    }
}

Write-Host ""
Write-Host "Target Wall Bounds:" -ForegroundColor Cyan
Write-Host "  X: $([math]::Round($wallMinX, 2)) to $([math]::Round($wallMaxX, 2)) (span: $([math]::Round($wallMaxX - $wallMinX, 2)) ft)" -ForegroundColor White
Write-Host "  Y: $([math]::Round($wallMinY, 2)) to $([math]::Round($wallMaxY, 2)) (span: $([math]::Round($wallMaxY - $wallMinY, 2)) ft)" -ForegroundColor White

# ============================================
# PART 3: Identify Issues
# ============================================
Write-Host ""
Write-Host "=== PART 3: Issue Analysis ===" -ForegroundColor Yellow

# Check if source elements are within target wall bounds
$outsideCount = 0
foreach ($inst in $allSourceInstances) {
    if ($inst.location) {
        $x = $inst.location.x
        $y = $inst.location.y
        if ($x -lt $wallMinX -or $x -gt $wallMaxX -or $y -lt $wallMinY -or $y -gt $wallMaxY) {
            $outsideCount++
        }
    }
}

if ($outsideCount -gt 0) {
    Write-Host "ISSUE: $outsideCount elements are OUTSIDE target wall bounds!" -ForegroundColor Red
    Write-Host "  This means the target project has different wall layout than source." -ForegroundColor Yellow
} else {
    Write-Host "OK: All source element locations are within target wall bounds." -ForegroundColor Green
}

# Check coordinate system offset
$sourceCenter = @{
    x = ($minX + $maxX) / 2
    y = ($minY + $maxY) / 2
}
$targetCenter = @{
    x = ($wallMinX + $wallMaxX) / 2
    y = ($wallMinY + $wallMaxY) / 2
}

$offsetX = $targetCenter.x - $sourceCenter.x
$offsetY = $targetCenter.y - $sourceCenter.y

Write-Host ""
Write-Host "Coordinate Comparison:" -ForegroundColor Cyan
Write-Host "  Source center: ($([math]::Round($sourceCenter.x, 2)), $([math]::Round($sourceCenter.y, 2)))" -ForegroundColor Gray
Write-Host "  Target center: ($([math]::Round($targetCenter.x, 2)), $([math]::Round($targetCenter.y, 2)))" -ForegroundColor Gray
Write-Host "  Offset needed: ($([math]::Round($offsetX, 2)), $([math]::Round($offsetY, 2)))" -ForegroundColor Yellow

if ([math]::Abs($offsetX) -gt 10 -or [math]::Abs($offsetY) -gt 10) {
    Write-Host ""
    Write-Host "CRITICAL ISSUE: Large coordinate offset detected!" -ForegroundColor Red
    Write-Host "The source and target projects have different origins/layouts." -ForegroundColor Yellow
    Write-Host "Elements placed at source coordinates will be far from target walls." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Analysis Complete ===" -ForegroundColor Cyan
