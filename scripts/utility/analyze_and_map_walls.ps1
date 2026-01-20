# Analyze and Map Walls Between Avon Park and SF-project-test-2
# This script creates an accurate wall-to-wall mapping based on geometry

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

Write-Host "=== Wall Geometry Analysis ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get Avon Park walls with geometry
Write-Host "Step 1: Analyzing Avon Park walls..." -ForegroundColor Yellow

# Make sure we're in Avon Park
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "1700 West Sheffield Road" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

# Get walls
$avonWalls = Invoke-MCPMethod -Method "getWallsInView" -Params @{ viewId = 32 }
Write-Host "Found $($avonWalls.wallCount) walls in Avon Park" -ForegroundColor Green

# Get geometry for each wall
$avonWallGeometry = @{}
foreach ($wall in $avonWalls.walls) {
    $info = Invoke-MCPMethod -Method "getWallInfo" -Params @{ wallId = $wall.wallId }
    if ($info.success) {
        $avonWallGeometry[$wall.wallId] = @{
            wallId = $wall.wallId
            wallType = $wall.wallType
            length = $wall.length
            startPoint = $info.startPoint
            endPoint = $info.endPoint
        }
    }
    Start-Sleep -Milliseconds 50
}
Write-Host "Got geometry for $($avonWallGeometry.Count) walls" -ForegroundColor Green
Write-Host ""

# Step 2: Get SF-project-test-2 walls with geometry
Write-Host "Step 2: Analyzing SF-project-test-2 walls..." -ForegroundColor Yellow

$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

# Get walls
$sfWalls = Invoke-MCPMethod -Method "getWallsInView" -Params @{ viewId = 32 }
Write-Host "Found $($sfWalls.wallCount) walls in SF-project-test-2" -ForegroundColor Green

# Get geometry for each wall
$sfWallGeometry = @{}
foreach ($wall in $sfWalls.walls) {
    $info = Invoke-MCPMethod -Method "getWallInfo" -Params @{ wallId = $wall.wallId }
    if ($info.success) {
        $sfWallGeometry[$wall.wallId] = @{
            wallId = $wall.wallId
            wallType = $wall.wallType
            length = $wall.length
            startPoint = $info.startPoint
            endPoint = $info.endPoint
        }
    }
    Start-Sleep -Milliseconds 50
}
Write-Host "Got geometry for $($sfWallGeometry.Count) walls" -ForegroundColor Green
Write-Host ""

# Step 3: Create wall mapping based on geometry
Write-Host "Step 3: Creating wall mapping..." -ForegroundColor Yellow

# Function to check if two walls match by geometry
function Test-WallMatch {
    param($wall1, $wall2, $tolerance = 0.1)

    # Check if endpoints match (either direction)
    $s1 = $wall1.startPoint
    $e1 = $wall1.endPoint
    $s2 = $wall2.startPoint
    $e2 = $wall2.endPoint

    # Calculate distances
    $distSS = [math]::Sqrt(($s1[0]-$s2[0])*($s1[0]-$s2[0]) + ($s1[1]-$s2[1])*($s1[1]-$s2[1]))
    $distEE = [math]::Sqrt(($e1[0]-$e2[0])*($e1[0]-$e2[0]) + ($e1[1]-$e2[1])*($e1[1]-$e2[1]))
    $distSE = [math]::Sqrt(($s1[0]-$e2[0])*($s1[0]-$e2[0]) + ($s1[1]-$e2[1])*($s1[1]-$e2[1]))
    $distES = [math]::Sqrt(($e1[0]-$s2[0])*($e1[0]-$s2[0]) + ($e1[1]-$s2[1])*($e1[1]-$s2[1]))

    # Match if both endpoints match (in either order)
    $match1 = ($distSS -lt $tolerance) -and ($distEE -lt $tolerance)
    $match2 = ($distSE -lt $tolerance) -and ($distES -lt $tolerance)

    return $match1 -or $match2
}

$wallMapping = @{}
$unmappedAvonWalls = @()

foreach ($avonId in $avonWallGeometry.Keys) {
    $avonWall = $avonWallGeometry[$avonId]
    $found = $false

    foreach ($sfId in $sfWallGeometry.Keys) {
        $sfWall = $sfWallGeometry[$sfId]

        if (Test-WallMatch -wall1 $avonWall -wall2 $sfWall -tolerance 0.5) {
            $wallMapping[$avonId] = $sfId
            $found = $true
            break
        }
    }

    if (-not $found) {
        $unmappedAvonWalls += $avonId
    }
}

Write-Host "Mapped $($wallMapping.Count) walls" -ForegroundColor Green
Write-Host "Unmapped: $($unmappedAvonWalls.Count) walls" -ForegroundColor Yellow
Write-Host ""

# Step 4: Output the mapping
Write-Host "=== Wall Mapping (Avon Park -> SF-project-test-2) ===" -ForegroundColor Cyan
foreach ($avonId in $wallMapping.Keys | Sort-Object) {
    $sfId = $wallMapping[$avonId]
    Write-Host "$avonId -> $sfId"
}

Write-Host ""
Write-Host "=== Unmapped Avon Park Walls ===" -ForegroundColor Yellow
foreach ($id in $unmappedAvonWalls) {
    $wall = $avonWallGeometry[$id]
    Write-Host "$id ($($wall.wallType), $([math]::Round($wall.length, 2)) ft)"
}

# Save the mapping
$mappingData = @{
    wallMapping = $wallMapping
    unmappedWalls = $unmappedAvonWalls
    avonWallCount = $avonWallGeometry.Count
    sfWallCount = $sfWallGeometry.Count
}

$mappingData | ConvertTo-Json -Depth 10 | Out-File "D:\RevitMCPBridge2026\wall_mapping.json"
Write-Host ""
Write-Host "Mapping saved to wall_mapping.json" -ForegroundColor Green
