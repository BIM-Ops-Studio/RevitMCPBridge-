# Create all walls from extracted Avon Park data
$pipeName = 'RevitMCPBridge2026'

# Type mapping: Avon Park wallTypeId -> Blank file wallTypeId
$typeMap = @{
    # "8" CMU Exterior Wall - W1" -> "Generic - 8" Masonry"
    1200718 = 441456
    # "Interior - 4 1/2" Partition" -> "Interior - 4 1/2" Partition"
    441519 = 441519
    # "8" CMU Exterior Wall - W1-2" (upper level) -> "Generic - 8" Masonry"
    1201136 = 441456
    # "Foundation - 8" Concrete" -> "Concrete 8""
    441965 = 944915
    # "5/8" Stone Veneer" -> "Generic - 6""
    2073952 = 441445
}

# Default wall type if not mapped
$defaultWallType = 441451  # Generic - 8"

# Read the extracted wall data
$wallData = Get-Content "D:\RevitMCPBridge2026\avon_park_walls.json" -Raw | ConvertFrom-Json

Write-Host "Creating $($wallData.wallCount) walls in blank file..."
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($wall in $wallData.walls) {
    if (-not $wall.success) {
        Write-Host "Skipping wall $($wall.wallId) - extraction failed"
        $failCount++
        continue
    }

    # Get mapped wall type or use default
    $wallTypeId = $defaultWallType
    if ($typeMap.ContainsKey($wall.wallTypeId)) {
        $wallTypeId = $typeMap[$wall.wallTypeId]
    }

    # Create pipe connection
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    # Build request - use level 30 (L1) for all walls in blank file
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
        Write-Host "Created wall $successCount - $($wall.wallType) (length: $([math]::Round($wall.length, 1))')"
    } else {
        $failCount++
        Write-Host "FAILED wall $($wall.wallId): $($result.error)"
    }
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Wall creation complete!"
Write-Host "Success: $successCount"
Write-Host "Failed: $failCount"
Write-Host "=========================================="
