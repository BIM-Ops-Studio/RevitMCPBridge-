# Place Doors from Avon Park into SF-project-test-2
# Using correct wall-to-wall mapping based on geometry

# Wall mapping from Avon Park to SF-project-test-2 (by geometry)
$wallMapping = @{
    1946509 = 1240472
    1946577 = 1240473
    1946691 = 1240474
    1946751 = 1240475
    1946817 = 1240476
    1946869 = 1240477
    1946938 = 1240478
    1947064 = 1240479
    1948066 = 1240480
    1948260 = 1240481
    1948338 = 1240482
    1948441 = 1240483
    1948500 = 1240484
    1948604 = 1240485
    1949292 = 1240486
    1949620 = 1240487
    1949756 = 1240488
    1950244 = 1240490
    1950457 = 1240491
    1950593 = 1240492
    1950706 = 1240493
    1950828 = 1240494
    1950932 = 1240495
    1951210 = 1240496
    1951475 = 1240497
    1951626 = 1240498
    1951760 = 1240499
    1951973 = 1240500
    1952173 = 1240501
    1952605 = 1240502
    1952712 = 1240503
    1952823 = 1240505
    1974542 = 1240489
}

# Door type mapping from Avon Park to SF-project-test-2
$doorTypeMap = @{
    # Door-Garage-Embossed_Panel 192'' x 84''
    1221586 = 1249218

    # Door-Opening types
    1956166 = 1256428  # 11'-11 1/2" x 7'-0"
    1956330 = 1256426  # 11'-0" x 7'-0"
    1956471 = 1256424  # 6'-10 1/8" x 7'-0"
    1283971 = 1256450  # 48" x 80"
    1955857 = 1256434  # 3'-7 1/2" x 7'-0"
    1955926 = 1256432  # 3'-11 1/2" x 7'-0"
    1956029 = 1256430  # 12'-3 1/2" x 7'-0"

    # Door-Double-Sliding 68" x 80"
    1248818 = 1242587

    # Door-Passage-Single-Flush 36" x 80"
    387958 = 387958

    # Door-Exterior-Single-Entry-Half Flat Glass-Wood_Clad 36" x 84"
    1960691 = 1246410

    # Door-Interior-Single-Flush_Panel-Wood types
    1241774 = 1254078  # 32" x 80"
    1241772 = 1254080  # 30" x 80"
    1241778 = 1254074  # 36" x 80"

    # Door-Interior-Double-Sliding-2_Panel-Wood types
    1225636 = 1251092  # 60" x 80"
    1242141 = 1251088  # 48" x 80"

    # Door-Interior-Single-Pocket-2_Panel-Wood 36" x 80"
    1964292 = 1255549

    # Door-Bifold 3'-6" x 6'-8"
    1957606 = 1241512
}

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

# Load door data
$doorData = Get-Content "D:\RevitMCPBridge2026\avon_park_doors_windows.json" | ConvertFrom-Json

Write-Host "=== Door Placement Script (Correct Mapping) ===" -ForegroundColor Cyan
Write-Host "Total doors to place: $($doorData.doorCount)" -ForegroundColor Yellow
Write-Host ""

# Make sure we're in SF-project-test-2
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray
Write-Host ""

# Process each door
$successCount = 0
$failCount = 0
$skippedCount = 0
$results = @()

foreach ($door in $doorData.doors) {
    $doorMark = $door.mark
    $sourceTypeId = $door.typeId
    $sourceHostId = $door.hostId
    $doorLocation = $door.location

    Write-Host "Processing door $doorMark..." -ForegroundColor White
    Write-Host "  Source host wall: $sourceHostId" -ForegroundColor Gray
    Write-Host "  Location: ($([math]::Round($doorLocation[0], 2)), $([math]::Round($doorLocation[1], 2)), $([math]::Round($doorLocation[2], 2)))" -ForegroundColor Gray

    # Get mapped wall ID
    $targetWallId = $wallMapping[$sourceHostId]
    if ($targetWallId -eq $null) {
        Write-Host "  SKIPPED: No wall mapping for source wall $sourceHostId" -ForegroundColor Yellow
        $skippedCount++
        continue
    }

    Write-Host "  Target wall: $targetWallId" -ForegroundColor Gray

    # Get mapped door type
    $targetTypeId = $doorTypeMap[$sourceTypeId]
    if ($targetTypeId -eq $null) {
        Write-Host "  WARNING: No type mapping for $sourceTypeId, using default 36x80" -ForegroundColor Yellow
        $targetTypeId = 387958
    }

    # Place the door
    $placeResult = Invoke-MCPMethod -Method "placeDoor" -Params @{
        wallId = $targetWallId
        doorTypeId = $targetTypeId
        location = $doorLocation
    }

    if ($placeResult.success) {
        Write-Host "  SUCCESS: Door placed (ID: $($placeResult.doorId))" -ForegroundColor Green
        $successCount++
        $results += @{
            mark = $doorMark
            doorId = $placeResult.doorId
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
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host "Skipped (no wall mapping): $skippedCount" -ForegroundColor Yellow
Write-Host ""

# Save results
$resultsJson = $results | ForEach-Object { [PSCustomObject]$_ } | ConvertTo-Json -Depth 10
$resultsJson | Out-File "D:\RevitMCPBridge2026\door_placement_results_correct.json"
Write-Host "Results saved to door_placement_results_correct.json" -ForegroundColor Yellow
