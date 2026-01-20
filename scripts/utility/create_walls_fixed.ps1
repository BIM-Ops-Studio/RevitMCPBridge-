# Create ALL walls from scratch with CORRECT type mapping
$pipeName = 'RevitMCPBridge2026'

# CORRECTED Type mapping: Avon Park wallTypeId -> Target file wallTypeId
$typeMap = @{
    # Interior - 4 1/2" Partition (same in both)
    441519 = 441519
    # 8" CMU Exterior Wall - W1 -> Generic - 8" Masonry
    1200718 = 441456
    # 5/8" Stone Veneer -> Generic - 6"
    1936965 = 441445
    # Foundation - 8" Concrete -> Concrete 8"
    1215709 = 944915
    # 8" CMU Exterior Wall - W1-2 -> Generic - 8" Masonry
    1960903 = 441456
}

# Default wall type if not mapped
$defaultWallType = 441451  # Generic - 8"

# Read the extracted wall data
$wallData = Get-Content "D:\RevitMCPBridge2026\avon_park_walls.json" -Raw | ConvertFrom-Json

Write-Host "Creating all 58 walls with CORRECTED type mapping..."
Write-Host "500ms delay between each wall to prevent timeouts"
Write-Host ""

$successCount = 0
$failCount = 0

for ($i = 0; $i -lt $wallData.walls.Count; $i++) {
    $wall = $wallData.walls[$i]

    if (-not $wall.success) {
        Write-Host "Skipping wall $($i+1) - extraction failed"
        $failCount++
        continue
    }

    # Get mapped wall type or use default
    $wallTypeId = $defaultWallType
    $sourceTypeId = [string]$wall.wallTypeId

    if ($typeMap.ContainsKey([int]$wall.wallTypeId)) {
        $wallTypeId = $typeMap[[int]$wall.wallTypeId]
    } else {
        Write-Host "  Warning: Unknown type $($wall.wallTypeId) ($($wall.wallType)) - using default"
    }

    # Create pipe connection
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    # Build request - use level 30 (GROUND FLOOR) for all walls
    $startX = $wall.startPoint[0]
    $startY = $wall.startPoint[1]
    $startZ = $wall.startPoint[2]
    $endX = $wall.endPoint[0]
    $endY = $wall.endPoint[1]
    $endZ = $wall.endPoint[2]
    $height = $wall.height

    $request = '{"method":"createWallByPoints","params":{"startPoint":[' + $startX + ',' + $startY + ',' + $startZ + '],"endPoint":[' + $endX + ',' + $endY + ',' + $endZ + '],"levelId":30,"height":' + $height + ',"wallTypeId":' + $wallTypeId + '}}'

    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    $result = $response | ConvertFrom-Json
    if ($result.success) {
        $successCount++
        Write-Host "Created wall $($i+1) of $($wallData.walls.Count) - $($wall.wallType) -> Type $wallTypeId"
    } else {
        $failCount++
        Write-Host "FAILED wall $($i+1) ($($wall.wallType) type $($wall.wallTypeId)): $($result.error)"
    }

    # Add delay between walls to prevent Idling event from stopping
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Wall creation complete!"
Write-Host "Success: $successCount"
Write-Host "Failed: $failCount"
Write-Host "=========================================="
