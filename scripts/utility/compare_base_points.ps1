# Compare Project Base Points between Avon Park and SF-project-test-2
# Also draws X markers at base point locations

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

Write-Host "=== Compare Project Base Points ===" -ForegroundColor Cyan
Write-Host ""

# Get base point from Avon Park
Write-Host "=== Avon Park Base Point ===" -ForegroundColor Yellow
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "1700 West Sheffield Road" }
Write-Host "Active: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

# Get project base point using getElements
$basePointResult = Invoke-MCPMethod -Method "getElements" -Params @{
    categoryName = "Project Base Point"
}

$avonBasePoint = $null
if ($basePointResult.success -and $basePointResult.elements.Count -gt 0) {
    # Get the location of the base point element
    $bpElement = $basePointResult.elements[0]
    $locResult = Invoke-MCPMethod -Method "getElementLocation" -Params @{
        elementId = $bpElement.elementId
    }

    if ($locResult.success -and $locResult.location) {
        $avonBasePoint = $locResult.location
        Write-Host "  Location: ($([math]::Round($avonBasePoint.x, 4)), $([math]::Round($avonBasePoint.y, 4)), $([math]::Round($avonBasePoint.z, 4)))" -ForegroundColor White
    } else {
        Write-Host "  Could not get base point location" -ForegroundColor Red
    }
} else {
    Write-Host "  Base point not found or error: $($basePointResult.error)" -ForegroundColor Red
}

# Also get Survey Point
$surveyResult = Invoke-MCPMethod -Method "getElements" -Params @{
    categoryName = "Survey Point"
}

if ($surveyResult.success -and $surveyResult.elements.Count -gt 0) {
    $spElement = $surveyResult.elements[0]
    $locResult = Invoke-MCPMethod -Method "getElementLocation" -Params @{
        elementId = $spElement.elementId
    }

    if ($locResult.success -and $locResult.location) {
        Write-Host "  Survey Point: ($([math]::Round($locResult.location.x, 4)), $([math]::Round($locResult.location.y, 4)))" -ForegroundColor Gray
    }
}

Write-Host ""

# Get base point from SF-project-test-2
Write-Host "=== SF-project-test-2 Base Point ===" -ForegroundColor Yellow
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

$targetBasePoint = $null
$basePointResult = Invoke-MCPMethod -Method "getElements" -Params @{
    categoryName = "Project Base Point"
}

if ($basePointResult.success -and $basePointResult.elements.Count -gt 0) {
    $bpElement = $basePointResult.elements[0]
    $locResult = Invoke-MCPMethod -Method "getElementLocation" -Params @{
        elementId = $bpElement.elementId
    }

    if ($locResult.success -and $locResult.location) {
        $targetBasePoint = $locResult.location
        Write-Host "  Location: ($([math]::Round($targetBasePoint.x, 4)), $([math]::Round($targetBasePoint.y, 4)), $([math]::Round($targetBasePoint.z, 4)))" -ForegroundColor White
    } else {
        Write-Host "  Could not get base point location" -ForegroundColor Red
    }
} else {
    Write-Host "  Base point not found or error: $($basePointResult.error)" -ForegroundColor Red
}

# Also get Survey Point
$surveyResult = Invoke-MCPMethod -Method "getElements" -Params @{
    categoryName = "Survey Point"
}

if ($surveyResult.success -and $surveyResult.elements.Count -gt 0) {
    $spElement = $surveyResult.elements[0]
    $locResult = Invoke-MCPMethod -Method "getElementLocation" -Params @{
        elementId = $spElement.elementId
    }

    if ($locResult.success -and $locResult.location) {
        Write-Host "  Survey Point: ($([math]::Round($locResult.location.x, 4)), $([math]::Round($locResult.location.y, 4)))" -ForegroundColor Gray
    }
}

Write-Host ""

# Calculate difference
if ($avonBasePoint -and $targetBasePoint) {
    $diffX = $targetBasePoint.x - $avonBasePoint.x
    $diffY = $targetBasePoint.y - $avonBasePoint.y
    $diffZ = $targetBasePoint.z - $avonBasePoint.z

    Write-Host "=== Base Point Difference ===" -ForegroundColor Cyan
    Write-Host "  Delta X: $([math]::Round($diffX, 4)) ft" -ForegroundColor White
    Write-Host "  Delta Y: $([math]::Round($diffY, 4)) ft" -ForegroundColor White
    Write-Host "  Delta Z: $([math]::Round($diffZ, 4)) ft" -ForegroundColor White

    if ([math]::Abs($diffX) -gt 0.001 -or [math]::Abs($diffY) -gt 0.001) {
        Write-Host ""
        Write-Host "  BASE POINTS ARE DIFFERENT!" -ForegroundColor Red
        Write-Host "  To align elements, apply offset: (-$([math]::Round($diffX, 4)), -$([math]::Round($diffY, 4)))" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "  Base points are aligned." -ForegroundColor Green
    }
}

Write-Host ""

# Draw X markers at both base point locations in target project
Write-Host "=== Drawing X Markers ===" -ForegroundColor Yellow

# Draw X at Avon Park base point location (where source elements expect to be)
if ($avonBasePoint) {
    $size = 5  # 5 feet
    $x = $avonBasePoint.x
    $y = $avonBasePoint.y

    # Create two crossing lines to form X
    $line1Result = Invoke-MCPMethod -Method "createModelLine" -Params @{
        startPoint = @($x - $size, $y - $size, 0)
        endPoint = @($x + $size, $y + $size, 0)
    }

    $line2Result = Invoke-MCPMethod -Method "createModelLine" -Params @{
        startPoint = @($x - $size, $y + $size, 0)
        endPoint = @($x + $size, $y - $size, 0)
    }

    if ($line1Result.success -and $line2Result.success) {
        Write-Host "  Drew X at AVON PARK base point: ($([math]::Round($x, 2)), $([math]::Round($y, 2)))" -ForegroundColor Green
    } else {
        Write-Host "  Failed to draw X at Avon Park location" -ForegroundColor Red
    }
}

# Draw X at Target base point location
if ($targetBasePoint) {
    $size = 3  # Smaller to differentiate
    $x = $targetBasePoint.x
    $y = $targetBasePoint.y

    $line1Result = Invoke-MCPMethod -Method "createModelLine" -Params @{
        startPoint = @($x - $size, $y - $size, 0)
        endPoint = @($x + $size, $y + $size, 0)
    }

    $line2Result = Invoke-MCPMethod -Method "createModelLine" -Params @{
        startPoint = @($x - $size, $y + $size, 0)
        endPoint = @($x + $size, $y - $size, 0)
    }

    if ($line1Result.success -and $line2Result.success) {
        Write-Host "  Drew X at TARGET base point: ($([math]::Round($x, 2)), $([math]::Round($y, 2)))" -ForegroundColor Cyan
    } else {
        Write-Host "  Failed to draw X at Target location" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "Look for two X markers in the target project:" -ForegroundColor White
Write-Host "  - Larger X = Avon Park base point (where elements are placed)" -ForegroundColor White
Write-Host "  - Smaller X = Target base point (project origin)" -ForegroundColor White
