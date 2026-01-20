# Place Windows from Avon Park into SF-project-test-2
# Using wall-to-wall mapping based on geometry

# Wall mapping from Avon Park to SF-project-test-2
$wallMapping = @{
    1946509 = 1240472; 1946577 = 1240473; 1946691 = 1240474; 1946751 = 1240475
    1946817 = 1240476; 1946869 = 1240477; 1946938 = 1240478; 1947064 = 1240479
    1948066 = 1240480; 1948260 = 1240481; 1948338 = 1240482; 1948441 = 1240483
    1948500 = 1240484; 1948604 = 1240485; 1949292 = 1240486; 1949620 = 1240487
    1949756 = 1240488; 1950244 = 1240490; 1950457 = 1240491; 1950593 = 1240492
    1950706 = 1240493; 1950828 = 1240494; 1950932 = 1240495; 1951210 = 1240496
    1951475 = 1240497; 1951626 = 1240498; 1951760 = 1240499; 1951973 = 1240500
    1952173 = 1240501; 1952605 = 1240502; 1952712 = 1240503; 1952823 = 1240505
    1974542 = 1240489
}

# Window type mapping from Avon Park to SF-project-test-2
# Avon Park: 1260632 = "37" x 63", 1260215 = "36" x 36", 1960439 = "18" x 82"
$windowTypeMap = @{
    1260632 = 479449  # "37" x 63" -> "36" x 65"" (closest)
    1260215 = 479447  # "36" x 36" -> "36" x 48"" (same width)
    1960439 = 479445  # "18" x 82" -> "29" x 65"" (tall window)
}

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

# Load window data
$windowData = Get-Content "D:\RevitMCPBridge2026\avon_park_doors_windows.json" | ConvertFrom-Json

Write-Host "=== Window Placement Script ===" -ForegroundColor Cyan
Write-Host "Total windows to place: $($windowData.windowCount)" -ForegroundColor Yellow
Write-Host ""

# Make sure we're in SF-project-test-2
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray
Write-Host ""

# Process each window
$successCount = 0
$failCount = 0
$skippedCount = 0
$results = @()

foreach ($window in $windowData.windows) {
    $windowMark = $window.mark
    $sourceTypeId = $window.typeId
    $sourceHostId = $window.hostId
    $windowLocation = $window.location

    Write-Host "Processing window $windowMark..." -ForegroundColor White
    Write-Host "  Source host wall: $sourceHostId" -ForegroundColor Gray
    Write-Host "  Location: ($([math]::Round($windowLocation[0], 2)), $([math]::Round($windowLocation[1], 2)), $([math]::Round($windowLocation[2], 2)))" -ForegroundColor Gray

    # Get mapped wall ID
    $targetWallId = $wallMapping[[int]$sourceHostId]
    if ($null -eq $targetWallId) {
        Write-Host "  SKIPPED: No wall mapping for source wall $sourceHostId" -ForegroundColor Yellow
        $skippedCount++
        continue
    }

    Write-Host "  Target wall: $targetWallId" -ForegroundColor Gray

    # Get mapped window type
    $targetTypeId = $windowTypeMap[[int]$sourceTypeId]
    if ($null -eq $targetTypeId) {
        Write-Host "  WARNING: No type mapping for $sourceTypeId, using default 36x48" -ForegroundColor Yellow
        $targetTypeId = 479447  # Default to 36" x 48"
    }

    # Place the window
    $placeResult = Invoke-MCPMethod -Method "placeWindow" -Params @{
        wallId = $targetWallId
        windowTypeId = $targetTypeId
        location = $windowLocation
    }

    if ($placeResult.success) {
        Write-Host "  SUCCESS: Window placed (ID: $($placeResult.windowId))" -ForegroundColor Green
        $successCount++
        $results += @{
            mark = $windowMark
            windowId = $placeResult.windowId
            wallId = $targetWallId
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
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Gray" })
Write-Host "Skipped (no wall mapping): $skippedCount" -ForegroundColor $(if ($skippedCount -gt 0) { "Yellow" } else { "Gray" })
Write-Host ""

# Save results
$resultsJson = $results | ForEach-Object { [PSCustomObject]$_ } | ConvertTo-Json -Depth 10
$resultsJson | Out-File "D:\RevitMCPBridge2026\window_placement_results.json"
Write-Host "Results saved to window_placement_results.json" -ForegroundColor Yellow
