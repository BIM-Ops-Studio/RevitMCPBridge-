# Draw X markers at origin (0,0) and at element centroid
# This shows where the coordinate system origin is

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

Write-Host "=== Draw Origin and Element Markers ===" -ForegroundColor Cyan
Write-Host ""

# Load source element data
$sourceData = Get-Content "D:\RevitMCPBridge2026\avon_park_family_instances.json" | ConvertFrom-Json
$allElements = @()
$allElements += $sourceData.casework
$allElements += $sourceData.furniture
$allElements += $sourceData.plumbingFixtures
$allElements += $sourceData.specialtyEquipment

# Calculate centroid of all elements
$sumX = 0; $sumY = 0; $count = 0
foreach ($elem in $allElements) {
    if ($elem.location) {
        $sumX += $elem.location.x
        $sumY += $elem.location.y
        $count++
    }
}
$centroidX = $sumX / $count
$centroidY = $sumY / $count

Write-Host "Source Element Centroid: ($([math]::Round($centroidX, 2)), $([math]::Round($centroidY, 2)))" -ForegroundColor Yellow
Write-Host "Number of elements: $count" -ForegroundColor Gray
Write-Host ""

# Switch to target
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active: $($switchResult.result.activatedDocument)" -ForegroundColor Gray
Write-Host ""

# Draw X at ORIGIN (0,0) - this is where the Project Base Point is
Write-Host "Drawing X at ORIGIN (0,0)..." -ForegroundColor Yellow
$size = 10  # 10 feet

$line1 = Invoke-MCPMethod -Method "createModelLine" -Params @{
    startPoint = @(-$size, -$size, 0)
    endPoint = @($size, $size, 0)
}
$line2 = Invoke-MCPMethod -Method "createModelLine" -Params @{
    startPoint = @(-$size, $size, 0)
    endPoint = @($size, -$size, 0)
}

if ($line1.success -and $line2.success) {
    Write-Host "  SUCCESS - X drawn at (0, 0)" -ForegroundColor Green
} else {
    Write-Host "  FAILED: $($line1.error)" -ForegroundColor Red
}

# Draw X at ELEMENT CENTROID
Write-Host ""
Write-Host "Drawing X at Element Centroid ($([math]::Round($centroidX, 2)), $([math]::Round($centroidY, 2)))..." -ForegroundColor Yellow
$size = 5  # Smaller

$line1 = Invoke-MCPMethod -Method "createModelLine" -Params @{
    startPoint = @($centroidX - $size, $centroidY - $size, 0)
    endPoint = @($centroidX + $size, $centroidY + $size, 0)
}
$line2 = Invoke-MCPMethod -Method "createModelLine" -Params @{
    startPoint = @($centroidX - $size, $centroidY + $size, 0)
    endPoint = @($centroidX + $size, $centroidY - $size, 0)
}

if ($line1.success -and $line2.success) {
    Write-Host "  SUCCESS - X drawn at centroid" -ForegroundColor Green
} else {
    Write-Host "  FAILED: $($line1.error)" -ForegroundColor Red
}

# Draw box around element extents
Write-Host ""
Write-Host "Drawing bounding box of all elements..." -ForegroundColor Yellow

$minX = 1000; $maxX = -1000; $minY = 1000; $maxY = -1000
foreach ($elem in $allElements) {
    if ($elem.location) {
        if ($elem.location.x -lt $minX) { $minX = $elem.location.x }
        if ($elem.location.x -gt $maxX) { $maxX = $elem.location.x }
        if ($elem.location.y -lt $minY) { $minY = $elem.location.y }
        if ($elem.location.y -gt $maxY) { $maxY = $elem.location.y }
    }
}

Write-Host "  Bounds: X($([math]::Round($minX, 2)) to $([math]::Round($maxX, 2))), Y($([math]::Round($minY, 2)) to $([math]::Round($maxY, 2)))" -ForegroundColor Gray

# Draw rectangle
$l1 = Invoke-MCPMethod -Method "createModelLine" -Params @{
    startPoint = @($minX, $minY, 0)
    endPoint = @($maxX, $minY, 0)
}
$l2 = Invoke-MCPMethod -Method "createModelLine" -Params @{
    startPoint = @($maxX, $minY, 0)
    endPoint = @($maxX, $maxY, 0)
}
$l3 = Invoke-MCPMethod -Method "createModelLine" -Params @{
    startPoint = @($maxX, $maxY, 0)
    endPoint = @($minX, $maxY, 0)
}
$l4 = Invoke-MCPMethod -Method "createModelLine" -Params @{
    startPoint = @($minX, $maxY, 0)
    endPoint = @($minX, $minY, 0)
}

if ($l1.success) {
    Write-Host "  SUCCESS - Bounding box drawn" -ForegroundColor Green
} else {
    Write-Host "  FAILED: $($l1.error)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Look in the target project for:" -ForegroundColor White
Write-Host "  1. Large X at (0,0) = Project Origin" -ForegroundColor White
Write-Host "  2. Small X at ($([math]::Round($centroidX, 2)), $([math]::Round($centroidY, 2))) = Element Centroid" -ForegroundColor White
Write-Host "  3. Rectangle = Bounding box of all source elements" -ForegroundColor White
Write-Host ""
Write-Host "If elements appear outside the rectangle, there's a coordinate offset issue." -ForegroundColor Yellow
