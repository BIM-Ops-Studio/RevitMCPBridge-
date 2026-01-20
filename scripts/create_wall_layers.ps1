# Create wall layer filled regions based on extracted geometry
# Target view: 2238350

$viewId = 2238350

# Wall boundaries (normalized from section cut):
# Wall X range: 32.441-33.295 -> normalized: 1.161-2.015
# Wall Z range: -1.0 to 11.667 -> normalized: -3.17 to 9.497
# But we only need the portion visible in the detail view (Z = roughly 6-10)

# Wall layers from outer to inner:
# Stucco: X = 1.161 to 1.213
# CMU: X = 1.213 to 1.848
# Rigid Insulation: X = 1.848 to 1.973
# GWB: X = 1.973 to 2.015

# Z range - use portion visible in detail
$wallMinZ = 6.0   # Approximate bottom of visible wall in detail
$wallMaxZ = 9.5   # Top of wall in detail

$layers = @(
    @{name="STUCCO"; minX=1.161; maxX=1.213; typeId=1748274},       # stucco
    @{name="CMU"; minX=1.213; maxX=1.848; typeId=1748181},          # CONCRETE (for CMU)
    @{name="RIGID INSULATION"; minX=1.848; maxX=1.973; typeId=2112703},  # RIGID INSULATION
    @{name="GWB"; minX=1.973; maxX=2.015; typeId=1780021}           # MATL-GWB
)

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(5000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

Write-Host "=== Creating Wall Layers with EXACT Coordinates ===" -ForegroundColor Cyan

foreach ($layer in $layers) {
    # Build boundary loop - 4 corners of rectangle
    $points = @(
        @{x = $layer.minX; y = $wallMinZ; z = 0},
        @{x = $layer.maxX; y = $wallMinZ; z = 0},
        @{x = $layer.maxX; y = $wallMaxZ; z = 0},
        @{x = $layer.minX; y = $wallMaxZ; z = 0}
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
    Write-Host "$($layer.name) (X: $($layer.minX)-$($layer.maxX)): $($result.success) - ID: $($result.regionId)"
}

$pipe.Close()
Write-Host "=== Wall layers complete ===" -ForegroundColor Green
