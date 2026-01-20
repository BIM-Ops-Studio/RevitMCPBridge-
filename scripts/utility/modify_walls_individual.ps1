# Modify Wall Types Individually
# Changes exterior walls in SF-project-test-2 to use 8" CMU Exterior Wall - W1

# Wall IDs to modify (exterior walls from Avon Park mapping)
$targetWallIds = @(1240472, 1240473, 1240474, 1240475, 1240476, 1240477, 1240478, 1240479)

# New wall type ID in SF-project-test-2 (8" CMU Exterior Wall - W1)
$newWallTypeId = 1265024

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

Write-Host "=== Individual Wall Type Modification ===" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($wallId in $targetWallIds) {
    Write-Host "Modifying wall $wallId..." -NoNewline

    $result = Invoke-MCPMethod -Method "modifyWallType" -Params @{
        wallId = $wallId
        newTypeId = $newWallTypeId
    }

    if ($result.success) {
        Write-Host " SUCCESS" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host " FAILED: $($result.error)" -ForegroundColor Red
        $failCount++
    }

    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "Modified: $successCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Gray" })
