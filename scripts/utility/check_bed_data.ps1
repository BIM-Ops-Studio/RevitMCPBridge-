# Check bed orientation data
$data = Get-Content "D:\RevitMCPBridge2026\avon_park_family_instances.json" | ConvertFrom-Json
$beds = $data.furniture | Where-Object { $_.familyName -like "*BED*" }

foreach ($bed in $beds) {
    Write-Host "Type: $($bed.typeName)"
    Write-Host "  Location: ($([math]::Round($bed.location.x, 2)), $([math]::Round($bed.location.y, 2)))"
    Write-Host "  Facing: ($([math]::Round($bed.facingOrientation.x, 2)), $([math]::Round($bed.facingOrientation.y, 2)))"
    Write-Host "  Hand: ($([math]::Round($bed.handOrientation.x, 2)), $([math]::Round($bed.handOrientation.y, 2)))"
    Write-Host "  Rotation: $([math]::Round($bed.rotation, 1)) deg"
    Write-Host "  Mirrored: $($bed.mirrored)"
    Write-Host ""
}
