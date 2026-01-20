# Diagnose why Office 29 failed
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

Write-Host "Finding Office 29..." -ForegroundColor Cyan

# First, get all rooms to find Office 29
$rooms = Send-RevitCommand -Method "getRooms" -Params @{}

if ($rooms.success) {
    $office29 = $rooms.rooms | Where-Object { $_.number -eq "29" -or $_.name -like "*Office 29*" }

    if ($office29) {
        Write-Host "Found Office 29:" -ForegroundColor Green

        # Try different property names for ID
        $roomId = $office29.id
        if (-not $roomId) { $roomId = $office29.elementId }
        if (-not $roomId) { $roomId = $office29.roomId }

        Write-Host "  Room ID: $roomId" -ForegroundColor White
        Write-Host "  Number: $($office29.number)" -ForegroundColor White
        Write-Host "  Name: $($office29.name)" -ForegroundColor White
        Write-Host "  Area: $($office29.area) sq ft" -ForegroundColor White

        Write-Host "`nAll properties:" -ForegroundColor Gray
        $office29 | ConvertTo-Json | Write-Host -ForegroundColor DarkGray

        # Try to create filled region for this specific office
        Write-Host "`nAttempting to create filled region for Office 29..." -ForegroundColor Yellow

        if ($roomId) {
            $result = Send-RevitCommand -Method "createRoomBoundaryFilledRegion" -Params @{
                roomId = $roomId.ToString()
                fillPatternName = "Solid fill"
                transparency = 50
            }
        } else {
            Write-Host "ERROR: Could not find room ID" -ForegroundColor Red
            $result = @{ success = $false; error = "Room ID not found" }
        }

        if ($result.success) {
            Write-Host "SUCCESS! Created filled region" -ForegroundColor Green
        } else {
            Write-Host "FAILED: $($result.error)" -ForegroundColor Red
            if ($result.offsetInfo) {
                Write-Host "`nOffset Info:" -ForegroundColor Cyan
                $result.offsetInfo | ForEach-Object {
                    Write-Host "  Wall $($_.wallId): $($_.classification)" -ForegroundColor Gray
                }
            }
            if ($result.stackTrace) {
                Write-Host "`nStack Trace:" -ForegroundColor Yellow
                Write-Host $result.stackTrace -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "Office 29 not found!" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR getting rooms: $($rooms.error)" -ForegroundColor Red
}
