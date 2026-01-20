# Add dimensions to Office 40
function Send-RevitCommand {
    param([string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        return $response | ConvertFrom-Json
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient) { try { $pipeClient.Dispose() } catch {} }
    }
}

Write-Host "Adding dimensions to Office 40..." -ForegroundColor Cyan

# Get walls around Office 40
$boundaries = Send-RevitCommand -Method "getRoomBoundaryWalls" -Params @{ roomId = "1314059" }

if ($boundaries.success -and $boundaries.boundaryWalls) {
    Write-Host "Found $($boundaries.boundaryWallCount) boundary walls" -ForegroundColor Green

    # Add dimensions to the walls
    $wallIds = $boundaries.boundaryWalls | ForEach-Object { $_.wallId }

    Write-Host "Adding dimensions to walls..." -ForegroundColor Yellow

    $result = Send-RevitCommand -Method "batchDimensionWalls" -Params @{
        wallIds = $wallIds
        offset = 5.0
        dimensionType = "Linear"
    }

    if ($result.success) {
        Write-Host "SUCCESS! Added dimensions" -ForegroundColor Green
        Write-Host "  Created: $($result.dimensionCount) dimensions" -ForegroundColor White
    } else {
        Write-Host "ERROR: $($result.error)" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: Could not get boundary walls" -ForegroundColor Red
}
