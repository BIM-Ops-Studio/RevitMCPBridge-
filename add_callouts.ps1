$pipeName = 'RevitMCPBridge2026'

function Send-MCPRequest($request) {
    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)
        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $response = $reader.ReadLine()
        $pipe.Close()
        return $response
    } catch {
        Write-Host "Error: $_"
        return $null
    }
}

$centuryGothicTypeId = 1244683

# Material callouts for each detail - positioned based on typical detail layout
# These are common construction materials that need callouts

Write-Host "=== Adding Material Callouts ==="

# Detail 4 - Garage Roof (2136700)
# Typical roof assembly materials
$garageRoofCallouts = @(
    @{text="ROOFING MEMBRANE"; x=-0.5; y=0.8; z=0},
    @{text="SLOPE TO DRAIN"; x=-0.3; y=0.6; z=0},
    @{text="RIGID INSUL."; x=-0.4; y=0.4; z=0},
    @{text="CONC. DECK"; x=-0.5; y=0.2; z=0},
    @{text="8 IN CMU WALL"; x=0.3; y=-0.3; z=0}
)

foreach ($callout in $garageRoofCallouts) {
    $request = '{"method": "placeTextNote", "params": {"viewId": 2136700, "text": "' + $callout.text + '", "location": [' + $callout.x + ',' + $callout.y + ',' + $callout.z + '], "textTypeId": ' + $centuryGothicTypeId + '}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success) {
        Write-Host "  Placed: $($callout.text)"
    } else {
        Write-Host "  Failed: $($callout.text) - $($result.error)"
    }
}

# Detail 5 - Parapet (2145981)
$parapetCallouts = @(
    @{text="COPING"; x=-0.3; y=1.0; z=0},
    @{text="CANT STRIP"; x=-0.4; y=0.8; z=0},
    @{text="FLASHING"; x=-0.5; y=0.6; z=0},
    @{text="TERMINATION BAR"; x=-0.4; y=0.4; z=0}
)

foreach ($callout in $parapetCallouts) {
    $request = '{"method": "placeTextNote", "params": {"viewId": 2145981, "text": "' + $callout.text + '", "location": [' + $callout.x + ',' + $callout.y + ',' + $callout.z + '], "textTypeId": ' + $centuryGothicTypeId + '}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success) {
        Write-Host "  Placed: $($callout.text)"
    } else {
        Write-Host "  Failed: $($callout.text) - $($result.error)"
    }
}

# Detail 1 & 2 - Balcony/Bedroom Balcony (2145960, 2136787)
$balconyCallouts = @(
    @{text="GUARDRAIL"; x=-0.3; y=0.8; z=0},
    @{text="WATERPROOF MEMBRANE"; x=-0.4; y=0.3; z=0},
    @{text="SLOPE"; x=-0.2; y=0.1; z=0}
)

foreach ($callout in $balconyCallouts) {
    # Balcony
    $request = '{"method": "placeTextNote", "params": {"viewId": 2145960, "text": "' + $callout.text + '", "location": [' + $callout.x + ',' + $callout.y + ',' + $callout.z + '], "textTypeId": ' + $centuryGothicTypeId + '}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success) { Write-Host "  Placed (Balcony): $($callout.text)" }

    # Bedroom Balcony
    $request = '{"method": "placeTextNote", "params": {"viewId": 2136787, "text": "' + $callout.text + '", "location": [' + $callout.x + ',' + $callout.y + ',' + $callout.z + '], "textTypeId": ' + $centuryGothicTypeId + '}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success) { Write-Host "  Placed (Bedroom Balcony): $($callout.text)" }
}

# Detail 3 - Canopy (2136771)
$canopyCallouts = @(
    @{text="STEEL ANGLE SUPPORT"; x=-0.3; y=0.5; z=0},
    @{text="DRIP EDGE"; x=-0.2; y=0.3; z=0},
    @{text="ATTACHMENT TO WALL"; x=-0.4; y=-0.2; z=0}
)

foreach ($callout in $canopyCallouts) {
    $request = '{"method": "placeTextNote", "params": {"viewId": 2136771, "text": "' + $callout.text + '", "location": [' + $callout.x + ',' + $callout.y + ',' + $callout.z + '], "textTypeId": ' + $centuryGothicTypeId + '}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success) {
        Write-Host "  Placed: $($callout.text)"
    } else {
        Write-Host "  Failed: $($callout.text) - $($result.error)"
    }
}

Write-Host "`n=== Done adding callouts ==="
