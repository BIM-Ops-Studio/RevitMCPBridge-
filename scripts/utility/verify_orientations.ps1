# Verify Element Orientations - Compare source and target
# Checks if mirrored elements are facing the correct direction

# MCP helper function
function Invoke-MCPMethod {
    param(
        [string]$Method,
        [hashtable]$Params = @{}
    )

    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Depth 10 -Compress

    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    return $response | ConvertFrom-Json
}

Write-Host "=== Verify Element Orientations ===" -ForegroundColor Cyan
Write-Host ""

# Load source data (extracted from Avon Park)
$sourceData = Get-Content "D:\RevitMCPBridge2026\avon_park_family_instances.json" | ConvertFrom-Json

# Get beds from source
$sourceBeds = @()
$sourceBeds += $sourceData.furniture | Where-Object { $_.familyName -like "*BED*" }

Write-Host "=== Source Beds (Avon Park) ===" -ForegroundColor Yellow
foreach ($bed in $sourceBeds) {
    $facing = $bed.facingOrientation
    $facingStr = "($([math]::Round($facing.x, 2)), $([math]::Round($facing.y, 2)))"
    $mirStr = if ($bed.mirrored) { "[M]" } else { "" }
    Write-Host "  $($bed.typeName) $mirStr" -ForegroundColor White
    Write-Host "    Facing: $facingStr" -ForegroundColor Gray
    Write-Host "    Location: ($([math]::Round($bed.location.x, 2)), $([math]::Round($bed.location.y, 2)))" -ForegroundColor Gray
}

Write-Host ""

# Switch to target and get beds
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }

# Get bed instances from target
$targetBedsResult = Invoke-MCPMethod -Method "getFamilyInstances" -Params @{
    familyName = "FN-BED-RESIDENTIAL"
}

Write-Host "=== Target Beds (SF-project-test-2) ===" -ForegroundColor Yellow
if ($targetBedsResult.success) {
    foreach ($bed in $targetBedsResult.instances) {
        $facing = $bed.facingOrientation
        $facingStr = "($([math]::Round($facing.x, 2)), $([math]::Round($facing.y, 2)))"
        $mirStr = if ($bed.mirrored) { "[M]" } else { "" }
        Write-Host "  $($bed.typeName) $mirStr" -ForegroundColor White
        Write-Host "    Facing: $facingStr" -ForegroundColor Gray
        Write-Host "    Location: ($([math]::Round($bed.location.x, 2)), $([math]::Round($bed.location.y, 2)))" -ForegroundColor Gray
    }
} else {
    Write-Host "  Error: $($targetBedsResult.error)" -ForegroundColor Red
}

Write-Host ""

# Compare orientations
Write-Host "=== Orientation Comparison ===" -ForegroundColor Cyan
$matched = 0
$mismatched = 0

foreach ($sourceBed in $sourceBeds) {
    $srcLoc = $sourceBed.location

    # Find matching target bed by approximate location
    $targetBed = $null
    if ($targetBedsResult.success) {
        $targetBed = $targetBedsResult.instances | Where-Object {
            $dist = [math]::Sqrt(
                [math]::Pow($_.location.x - $srcLoc.x, 2) +
                [math]::Pow($_.location.y - $srcLoc.y, 2)
            )
            $dist -lt 1.0
        } | Select-Object -First 1
    }

    if ($targetBed) {
        $srcFacing = "($([math]::Round($sourceBed.facingOrientation.x, 1)), $([math]::Round($sourceBed.facingOrientation.y, 1)))"
        $tgtFacing = "($([math]::Round($targetBed.facingOrientation.x, 1)), $([math]::Round($targetBed.facingOrientation.y, 1)))"

        # Check if facing directions match
        $xMatch = [math]::Abs($sourceBed.facingOrientation.x - $targetBed.facingOrientation.x) -lt 0.1
        $yMatch = [math]::Abs($sourceBed.facingOrientation.y - $targetBed.facingOrientation.y) -lt 0.1

        if ($xMatch -and $yMatch) {
            Write-Host "  $($sourceBed.typeName): MATCH" -ForegroundColor Green
            Write-Host "    Source: $srcFacing -> Target: $tgtFacing" -ForegroundColor Gray
            $matched++
        } else {
            Write-Host "  $($sourceBed.typeName): MISMATCH" -ForegroundColor Red
            Write-Host "    Source: $srcFacing vs Target: $tgtFacing" -ForegroundColor Yellow
            $mismatched++
        }
    } else {
        Write-Host "  $($sourceBed.typeName): NOT FOUND in target" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "Matched: $matched" -ForegroundColor Green
Write-Host "Mismatched: $mismatched" -ForegroundColor $(if ($mismatched -gt 0) { "Red" } else { "Gray" })
