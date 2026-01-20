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
        # Use Python to parse JSON to avoid PowerShell duplicate key issues
        return $response
    } catch {
        Write-Host "Error: $_"
        return $null
    }
}

# View IDs
$garageRoof = 2136700
$parapet = 2145981
$balcony = 2145960
$bedroomBalcony = 2136787
$canopy = 2136771

$centuryGothicTypeId = 1244683

Write-Host "=== Adding Break Lines ==="

# Get break line family type
$result = Send-MCPRequest('{"method": "getFamilyInstanceTypes", "params": {"familyName": "Break Line"}}')
Write-Host "Break Line types: $result"

# For each view, add break lines at top and bottom of detail
$views = @($garageRoof, $parapet, $balcony, $bedroomBalcony, $canopy)
$viewNames = @("Garage Roof", "Parapet", "Balcony", "Bedroom Balcony", "Canopy")

# First, let's get the Break Line type ID
$result = Send-MCPRequest('{"method": "getElements", "params": {"category": "Detail Items"}}')

Write-Host "`n=== Adding Dimensions ==="

# For drafting views, we need to create dimensions using detail line references
# Let's try to add dimensions to walls by getting wall elements first

foreach ($i in 0..4) {
    $viewId = $views[$i]
    $viewName = $viewNames[$i]
    Write-Host "`nProcessing: $viewName"

    # Try to batch dimension any walls in view
    $request = '{"method": "batchDimensionWalls", "params": {"viewId": ' + $viewId + '}}'
    $result = Send-MCPRequest($request)
    Write-Host "  Wall dimensions: $result"
}

Write-Host "`n=== Adding Insulation Symbols ==="

# Get insulation detail component types
$request = '{"method": "getDetailComponentInfo", "params": {"familyName": "Insulation"}}'
$result = Send-MCPRequest($request)
Write-Host "Insulation types: $result"

# Try repeating detail for insulation
$request = '{"method": "getElements", "params": {"category": "Detail Items", "familyName": "Repeating Detail"}}'
$result = Send-MCPRequest($request)
Write-Host "Repeating details: $result"
