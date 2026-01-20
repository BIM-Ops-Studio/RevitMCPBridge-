# Place Doors from Avon Park into SF-project-test-2
# This script maps door types and finds nearest walls for placement

# Door type mapping from Avon Park to SF-project-test-2
$doorTypeMap = @{
    # Door-Garage-Embossed_Panel 192'' x 84''
    1221586 = 1249218  # Door-Garage-Embossed_Panel_20251123121643173

    # Door-Opening types
    1956166 = 1256428  # 11'-11 1/2" x 7'-0"
    1956330 = 1256426  # 11'-0" x 7'-0"
    1956471 = 1256424  # 6'-10 1/8" x 7'-0"
    1283971 = 1256450  # 48" x 80"
    1955857 = 1256434  # 3'-7 1/2" x 7'-0"
    1955926 = 1256432  # 3'-11 1/2" x 7'-0"
    1956029 = 1256430  # 12'-3 1/2" x 7'-0"

    # Door-Double-Sliding 68" x 80"
    1248818 = 1242587  # Door-Double-Sliding_20251123121635682

    # Door-Passage-Single-Flush 36" x 80"
    387958 = 387958    # Same type exists in target

    # Door-Exterior-Single-Entry-Half Flat Glass-Wood_Clad 36" x 84"
    1960691 = 1246410  # Door-Exterior-Single-Entry-Half Flat Glass-Wood_Clad_20251123121639043

    # Door-Interior-Single-Flush_Panel-Wood types
    1241774 = 1254078  # 32" x 80"
    1241772 = 1254080  # 30" x 80"
    1241778 = 1254074  # 36" x 80"

    # Door-Interior-Double-Sliding-2_Panel-Wood types
    1225636 = 1251092  # 60" x 80"
    1242141 = 1251088  # 48" x 80"

    # Door-Interior-Single-Pocket-2_Panel-Wood 36" x 80"
    1964292 = 1255549  # Door-Interior-Single-Pocket-2_Panel-Wood_20251123121654441

    # Door-Bifold 3'-6" x 6'-8"
    1957606 = 1241512  # Door-Bifold_4-Panel_Flush_SlimFold_Dunbarton_20251123121632203
}

# Target walls in SF-project-test-2 (from getWallsInView)
$targetWalls = @(1240472, 1240473, 1240474, 1240475, 1240476, 1240477, 1240478, 1240479,
                 1240480, 1240481, 1240482, 1240483, 1240484, 1240485, 1240486, 1240487,
                 1240488, 1240489, 1240490, 1240491, 1240492, 1240493, 1240494, 1240495,
                 1240496, 1240497, 1240498, 1240499, 1240500, 1240501, 1240502, 1240503, 1240505)

# Function to call MCP method
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

# Function to get wall geometry
function Get-WallGeometry {
    param([int]$WallId)

    $result = Invoke-MCPMethod -Method "getWallInfo" -Params @{ wallId = $WallId }
    if ($result.success) {
        return @{
            startPoint = $result.startPoint
            endPoint = $result.endPoint
            wallId = $WallId
        }
    }
    return $null
}

# Function to find distance from point to line segment
function Get-DistanceToWall {
    param(
        [double[]]$point,
        [double[]]$wallStart,
        [double[]]$wallEnd
    )

    $px = $point[0]; $py = $point[1]
    $x1 = $wallStart[0]; $y1 = $wallStart[1]
    $x2 = $wallEnd[0]; $y2 = $wallEnd[1]

    $dx = $x2 - $x1
    $dy = $y2 - $y1

    if ($dx -eq 0 -and $dy -eq 0) {
        return [math]::Sqrt(($px - $x1) * ($px - $x1) + ($py - $y1) * ($py - $y1))
    }

    $t = (($px - $x1) * $dx + ($py - $y1) * $dy) / ($dx * $dx + $dy * $dy)
    $t = [math]::Max(0, [math]::Min(1, $t))

    $nearestX = $x1 + $t * $dx
    $nearestY = $y1 + $t * $dy

    return [math]::Sqrt(($px - $nearestX) * ($px - $nearestX) + ($py - $nearestY) * ($py - $nearestY))
}

# Load door data
$doorData = Get-Content "D:\RevitMCPBridge2026\avon_park_doors_windows.json" | ConvertFrom-Json

Write-Host "=== Door Placement Script ===" -ForegroundColor Cyan
Write-Host "Total doors to place: $($doorData.doorCount)" -ForegroundColor Yellow
Write-Host ""

# Get geometry for all target walls
Write-Host "Loading wall geometry..." -ForegroundColor Yellow
$wallGeometries = @{}
foreach ($wallId in $targetWalls) {
    $geom = Get-WallGeometry -WallId $wallId
    if ($geom) {
        $wallGeometries[$wallId] = $geom
    }
    Start-Sleep -Milliseconds 100  # Avoid overwhelming Revit
}
Write-Host "Loaded geometry for $($wallGeometries.Count) walls" -ForegroundColor Green
Write-Host ""

# Process each door
$successCount = 0
$failCount = 0
$results = @()

foreach ($door in $doorData.doors) {
    $doorMark = $door.mark
    $sourceTypeId = $door.typeId
    $doorLocation = $door.location

    Write-Host "Processing door $doorMark at ($($doorLocation[0]), $($doorLocation[1]))..." -ForegroundColor White

    # Find nearest wall
    $nearestWall = $null
    $minDistance = [double]::MaxValue

    foreach ($wallId in $wallGeometries.Keys) {
        $geom = $wallGeometries[$wallId]
        $dist = Get-DistanceToWall -point $doorLocation -wallStart $geom.startPoint -wallEnd $geom.endPoint

        if ($dist -lt $minDistance) {
            $minDistance = $dist
            $nearestWall = $wallId
        }
    }

    if ($nearestWall -eq $null) {
        Write-Host "  ERROR: No wall found for door $doorMark" -ForegroundColor Red
        $failCount++
        continue
    }

    Write-Host "  Nearest wall: $nearestWall (distance: $([math]::Round($minDistance, 2)) ft)" -ForegroundColor Gray

    # Get mapped door type
    $targetTypeId = $doorTypeMap[$sourceTypeId]
    if ($targetTypeId -eq $null) {
        Write-Host "  WARNING: No type mapping for $sourceTypeId, using default" -ForegroundColor Yellow
        $targetTypeId = 387958  # Default to 36" x 80" passage door
    }

    # Place the door
    $placeResult = Invoke-MCPMethod -Method "placeDoor" -Params @{
        wallId = $nearestWall
        doorTypeId = $targetTypeId
        location = $doorLocation
    }

    if ($placeResult.success) {
        Write-Host "  SUCCESS: Door placed (ID: $($placeResult.doorId))" -ForegroundColor Green
        $successCount++
        $results += @{
            mark = $doorMark
            doorId = $placeResult.doorId
            wallId = $nearestWall
            typeId = $targetTypeId
        }
    } else {
        Write-Host "  FAILED: $($placeResult.error)" -ForegroundColor Red
        $failCount++
    }

    Start-Sleep -Milliseconds 300  # Give Revit time to process
}

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host ""

# Save results
$results | ConvertTo-Json -Depth 10 | Out-File "D:\RevitMCPBridge2026\door_placement_results.json"
Write-Host "Results saved to door_placement_results.json" -ForegroundColor Yellow
