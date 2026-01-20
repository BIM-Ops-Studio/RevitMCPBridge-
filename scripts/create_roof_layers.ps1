# Create roof layer filled regions based on extracted geometry
# Target view: 2238350

$viewId = 2238350

# Roof layers (from top to bottom, normalized Z coordinates)
# Top of roof at Z = 9.497 (11.667 - 2.17 offset)
$roofMinX = 0
$roofMaxX = 1.16  # Where wall starts

$layers = @(
    @{name="EPDM"; minZ=9.476; maxZ=9.497},
    @{name="RIGID INSULATION (ROOF)"; minZ=9.351; maxZ=9.476},
    @{name="CONCRETE DECK"; minZ=9.101; maxZ=9.351},
    @{name="METAL DECK"; minZ=8.976; maxZ=9.101}
)

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(5000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

Write-Host "=== Creating Roof Layers with EXACT Coordinates ===" -ForegroundColor Cyan

foreach ($layer in $layers) {
    $json = @{
        method = "createFilledRegion"
        params = @{
            viewId = $viewId
            regionTypeName = "Solid Black"
            points = @(
                @{x = $roofMinX; y = $layer.minZ},
                @{x = $roofMaxX; y = $layer.minZ},
                @{x = $roofMaxX; y = $layer.maxZ},
                @{x = $roofMinX; y = $layer.maxZ}
            )
        }
    } | ConvertTo-Json -Depth 5 -Compress

    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 500
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json
    Write-Host "$($layer.name) (Z: $($layer.minZ)-$($layer.maxZ)): $($result.success)"
}

$pipe.Close()
Write-Host "=== Roof layers complete ===" -ForegroundColor Green
