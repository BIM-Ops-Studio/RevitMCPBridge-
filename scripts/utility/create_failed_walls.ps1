# Create only the 21 FAILED walls with CORRECT type mapping
# Failed walls: 32-34, 40-42, 44-58 (21 total)
$pipeName = 'RevitMCPBridge2026'

# CORRECTED Type mapping
$typeMap = @{
    441519 = 441519    # Interior - 4 1/2" Partition
    1200718 = 441456   # 8" CMU Exterior -> Generic - 8" Masonry
    1936965 = 441445   # 5/8" Stone Veneer -> Generic - 6"
    1215709 = 944915   # Foundation -> Concrete 8"
    1960903 = 441456   # 8" CMU Exterior W1-2 -> Generic - 8" Masonry
}

$defaultWallType = 441451  # Generic - 8"

# Wall indices that failed (0-based): 31-33, 39-41, 43-57
$failedIndices = @(31, 32, 33, 39, 40, 41, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57)

$wallData = Get-Content "D:\RevitMCPBridge2026\avon_park_walls.json" -Raw | ConvertFrom-Json

Write-Host "Creating 21 failed walls with CORRECTED type mapping..."
Write-Host "500ms delay between each wall"
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($i in $failedIndices) {
    $wall = $wallData.walls[$i]

    if (-not $wall.success) {
        Write-Host "Skipping wall $($i+1) - extraction failed"
        $failCount++
        continue
    }

    # Get mapped wall type
    $wallTypeId = $defaultWallType
    if ($typeMap.ContainsKey([int]$wall.wallTypeId)) {
        $wallTypeId = $typeMap[[int]$wall.wallTypeId]
    }

    # Create pipe connection
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

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
        Write-Host "Created wall $($i+1) - $($wall.wallType) -> Type $wallTypeId"
    } else {
        $failCount++
        Write-Host "FAILED wall $($i+1): $($result.error)"
    }

    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Failed wall creation complete!"
Write-Host "Success: $successCount"
Write-Host "Failed: $failCount"
Write-Host "Total walls in model: $($successCount + 37)"
Write-Host "=========================================="
