# Modify Wall Types Script
# Changes exterior walls in SF-project-test-2 to use 8" CMU Exterior Wall - W1

# Load Avon Park wall data
$wallData = Get-Content "D:\RevitMCPBridge2026\avon_park_walls.json" | ConvertFrom-Json

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

# New wall type ID in SF-project-test-2 (8" CMU Exterior Wall - W1)
$newWallTypeId = 1265024

# Find W1 walls (typeId 1200718) and get their SF-project-test-2 IDs
$w1Walls = $wallData.walls | Where-Object { $_.wallTypeId -eq 1200718 }
$targetWallIds = @()
foreach ($wall in $w1Walls) {
    $targetId = $wallMapping[[int]$wall.wallId]
    if ($targetId) {
        $targetWallIds += $targetId
    }
}

Write-Host "=== Wall Type Modification ===" -ForegroundColor Cyan
Write-Host "Found $($w1Walls.Count) exterior walls (W1 type) in Avon Park" -ForegroundColor Yellow
Write-Host "Target walls in SF-project-test-2: $($targetWallIds.Count)" -ForegroundColor Yellow
Write-Host ""

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

# Make sure we're on SF-project-test-2
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

# Use batch modify to change all wall types at once
Write-Host ""
Write-Host "Modifying $($targetWallIds.Count) walls to use W1 type..." -ForegroundColor White

$result = Invoke-MCPMethod -Method "batchModifyWallTypes" -Params @{
    wallIds = $targetWallIds
    newWallTypeId = $newWallTypeId
}

if ($result.success) {
    Write-Host "SUCCESS: Modified $($result.modifiedCount) walls" -ForegroundColor Green
    if ($result.failedCount -gt 0) {
        Write-Host "Failed: $($result.failedCount)" -ForegroundColor Yellow
    }
} else {
    Write-Host "FAILED: $($result.error)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Wall IDs modified: $($targetWallIds -join ', ')" -ForegroundColor Gray
