# Create roof layer filled regions based on extracted geometry
# Target view: 2238350
# Uses correct boundaryLoops format

$viewId = 2238350

# Get appropriate filled region types
# EPDM/Roofing: Dark (Solid Black 23064)
# Rigid Insulation: Crosshatch (2112703 RIGID INSULATION)
# Concrete: Concrete pattern (1748181 CONCRETE)
# Metal Deck: Metal pattern (2141004 MATL-STEEL)

# Roof layers (normalized Z coordinates)
# Top of roof at Z = 9.497 (11.667 - 2.17 offset)
$roofMinX = 0
$roofMaxX = 1.16  # Where wall starts

$layers = @(
    @{name="EPDM"; minZ=9.476; maxZ=9.497; typeId=23064},           # Solid Black
    @{name="RIGID INSULATION (ROOF)"; minZ=9.351; maxZ=9.476; typeId=2112703},  # RIGID INSULATION
    @{name="CONCRETE DECK"; minZ=9.101; maxZ=9.351; typeId=1748181},  # CONCRETE
    @{name="METAL DECK"; minZ=8.976; maxZ=9.101; typeId=2141004}     # MATL-STEEL
)

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(5000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

Write-Host "=== Creating Roof Layers with EXACT Coordinates ===" -ForegroundColor Cyan

foreach ($layer in $layers) {
    # Build boundary loop - 4 corners of rectangle
    $points = @(
        @{x = $roofMinX; y = $layer.minZ; z = 0},
        @{x = $roofMaxX; y = $layer.minZ; z = 0},
        @{x = $roofMaxX; y = $layer.maxZ; z = 0},
        @{x = $roofMinX; y = $layer.maxZ; z = 0}
    )

    $params = @{
        viewId = $viewId
        filledRegionTypeId = $layer.typeId
        boundaryLoops = @(,$points)  # Array of one loop
    }

    $json = @{
        method = "createFilledRegion"
        params = $params
    } | ConvertTo-Json -Depth 5 -Compress

    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 800
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json
    Write-Host "$($layer.name) (Z: $($layer.minZ)-$($layer.maxZ)): $($result.success) - ID: $($result.regionId)"
}

$pipe.Close()
Write-Host "=== Roof layers complete ===" -ForegroundColor Green
