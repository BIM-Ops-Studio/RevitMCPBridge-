# Get filled region areas for Office 01 and Office 02

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

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CALCULATING FILLED REGION AREAS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get all rooms to find Office 01 and Office 02 room IDs
Write-Host "Getting rooms..." -ForegroundColor Yellow
$roomsResult = Send-RevitCommand -Method "getRooms" -Params @{}

$office01 = $roomsResult.rooms | Where-Object { $_.number -eq "01" -and $_.level -eq "L7" } | Select-Object -First 1
$office02 = $roomsResult.rooms | Where-Object { $_.number -eq "02" -and $_.level -eq "L7" } | Select-Object -First 1

if (-not $office01) {
    Write-Host "ERROR: Office 01 not found on L7" -ForegroundColor Red
    exit 1
}

if (-not $office02) {
    Write-Host "ERROR: Office 02 not found on L7" -ForegroundColor Red
    exit 1
}

Write-Host "Found Office 01: Room ID = $($office01.roomId)" -ForegroundColor Green
Write-Host "Found Office 02: Room ID = $($office02.roomId)`n" -ForegroundColor Green

# Try to get filled region info for each office
Write-Host "Attempting to get filled region areas using UpdateRoomAreaFromFilledRegion method..." -ForegroundColor Yellow
Write-Host "(This method finds the filled region and calculates area)`n" -ForegroundColor Gray

# For Office 01
Write-Host "Office 01:" -ForegroundColor Cyan
$result01 = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
    roomId = $office01.roomId.ToString()
    multiplier = 1.0
}

if ($result01.success) {
    Write-Host "  Filled Region Area: $([math]::Round($result01.filledRegionArea, 2)) SF" -ForegroundColor Green
    Write-Host "  With 1.2x multiplier: $([math]::Round($result01.filledRegionArea * 1.2, 2)) SF" -ForegroundColor Yellow
    $office01Area = $result01.filledRegionArea
} else {
    Write-Host "  ERROR: $($result01.error)" -ForegroundColor Red
    $office01Area = $null
}

Write-Host ""

# For Office 02
Write-Host "Office 02:" -ForegroundColor Cyan
$result02 = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
    roomId = $office02.roomId.ToString()
    multiplier = 1.0
}

if ($result02.success) {
    Write-Host "  Filled Region Area: $([math]::Round($result02.filledRegionArea, 2)) SF" -ForegroundColor Green
    Write-Host "  With 1.2x multiplier: $([math]::Round($result02.filledRegionArea * 1.2, 2)) SF" -ForegroundColor Yellow
    $office02Area = $result02.filledRegionArea
} else {
    Write-Host "  ERROR: $($result02.error)" -ForegroundColor Red
    $office02Area = $null
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($office01Area) {
    Write-Host "Office 01 Filled Region: $([math]::Round($office01Area, 0)) SF" -ForegroundColor White
    Write-Host "Office 01 @ 1.2x: $([math]::Round($office01Area * 1.2, 0)) SF" -ForegroundColor Yellow
} else {
    Write-Host "Office 01: Could not calculate" -ForegroundColor Red
}

Write-Host ""

if ($office02Area) {
    Write-Host "Office 02 Filled Region: $([math]::Round($office02Area, 0)) SF" -ForegroundColor White
    Write-Host "Office 02 @ 1.2x: $([math]::Round($office02Area * 1.2, 0)) SF" -ForegroundColor Yellow
} else {
    Write-Host "Office 02: Could not calculate" -ForegroundColor Red
}

Write-Host ""
