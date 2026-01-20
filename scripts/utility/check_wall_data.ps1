# Check wall data for issues
$walls = Get-Content "D:\RevitMCPBridge2026\avon_park_walls.json" | ConvertFrom-Json

Write-Host "Total walls: $($walls.Count)"
Write-Host ""

$nullPoints = 0
$validPoints = 0

foreach ($wall in $walls) {
    if ($null -eq $wall.startPoint -or $null -eq $wall.endPoint) {
        $nullPoints++
    } else {
        $validPoints++
    }
}

Write-Host "Walls with valid geometry: $validPoints"
Write-Host "Walls with NULL geometry: $nullPoints"
Write-Host ""

# Show first 3 with null points
Write-Host "Sample walls with issues:"
$walls | Where-Object { $null -eq $_.startPoint } | Select-Object -First 3 | ForEach-Object {
    Write-Host "  $($_.wallType) - ID: $($_.wallId)"
}
