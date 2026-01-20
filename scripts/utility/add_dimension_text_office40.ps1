# Add text annotations showing Office 40 dimensions
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

Write-Host "Adding dimension text to Office 40..." -ForegroundColor Cyan

# Get Office 40 info
$room = Send-RevitCommand -Method "getRoomInfo" -Params @{ roomId = "1314059" }

if ($room.success) {
    $area = [math]::Round($room.area, 2)
    $perimeter = [math]::Round($room.perimeter, 2)

    # Calculate approximate dimensions (assuming rectangular)
    # Perimeter = 2(W + H), so we can estimate dimensions
    $avgSide = $perimeter / 4

    Write-Host "Room $($room.roomNumber): $($room.roomName)" -ForegroundColor Green
    Write-Host "  Area: $area sq ft" -ForegroundColor White
    Write-Host "  Perimeter: $perimeter ft" -ForegroundColor White
    Write-Host "  Approx dimensions: ~$([math]::Round($avgSide, 1)) ft average side" -ForegroundColor White

    # Get active view
    $project = Send-RevitCommand -Method "getProjectInfo" -Params @{}
    $viewId = $project.activeViewId

    # Add text note showing dimensions
    $text = "OFFICE 40 - Area: $area SF, Perimeter: $perimeter LF"

    $result = Send-RevitCommand -Method "createTextNote" -Params @{
        viewId = $viewId.ToString()
        text = $text
        x = 179.54  # Center X from our analysis
        y = 218.00  # Below center Y
        textSize = 0.25
    }

    if ($result.success) {
        Write-Host "`nSUCCESS! Added dimension text annotation" -ForegroundColor Green
    } else {
        Write-Host "`nERROR: $($result.error)" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR getting room info: $($room.error)" -ForegroundColor Red
}
