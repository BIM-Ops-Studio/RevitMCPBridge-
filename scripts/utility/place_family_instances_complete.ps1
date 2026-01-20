# Complete Family Instance Placement Script
# Transfers required families and places instances in one session

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

Write-Host "=== Complete Family Instance Placement ===" -ForegroundColor Cyan
Write-Host ""

# Load extracted instance data
$instanceData = Get-Content "D:\RevitMCPBridge2026\avon_park_family_instances.json" | ConvertFrom-Json

$allInstances = @()
$allInstances += $instanceData.casework
$allInstances += $instanceData.furniture
$allInstances += $instanceData.plumbingFixtures
$allInstances += $instanceData.specialtyEquipment
$allInstances += $instanceData.electricalEquipment

Write-Host "Total instances to place: $($allInstances.Count)" -ForegroundColor Yellow
Write-Host ""

# Get unique family names needed
$uniqueFamilies = $allInstances | ForEach-Object { $_.familyName } | Sort-Object -Unique
Write-Host "Unique families needed: $($uniqueFamilies.Count)" -ForegroundColor Gray

# Step 1: Transfer all needed families from Avon Park
Write-Host ""
Write-Host "=== Step 1: Transferring Required Families ===" -ForegroundColor Yellow

foreach ($familyName in $uniqueFamilies) {
    Write-Host "  Transferring: $familyName" -ForegroundColor White

    $transferResult = Invoke-MCPMethod -Method "transferFamilyBetweenDocuments" -Params @{
        sourceDocumentName = "1700 West Sheffield Road"
        targetDocumentName = "SF-project-test-2"
        familyName = $familyName
    }

    if ($transferResult.success) {
        Write-Host "    Transferred $($transferResult.transferredCount) types" -ForegroundColor Green
    } else {
        Write-Host "    Skipped: $($transferResult.error)" -ForegroundColor Gray
    }

    Start-Sleep -Milliseconds 100
}

Write-Host ""
Write-Host "Family transfer complete." -ForegroundColor Cyan

# Step 2: Switch to target and build type lookup
Write-Host ""
Write-Host "=== Step 2: Building Type Lookup ===" -ForegroundColor Yellow

$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

$typeLookup = @{}

$categories = @("Casework", "Furniture", "Plumbing Fixtures", "Specialty Equipment", "Electrical Equipment")

foreach ($category in $categories) {
    Write-Host "  Getting types for $category..." -ForegroundColor Gray

    $familiesResult = Invoke-MCPMethod -Method "getFamiliesByCategory" -Params @{
        categoryName = $category
    }

    if (-not $familiesResult.success) {
        continue
    }

    foreach ($family in $familiesResult.families) {
        $familyName = $family.name

        $typesResult = Invoke-MCPMethod -Method "getFamilyTypes" -Params @{
            familyName = $familyName
        }

        if ($typesResult.success) {
            foreach ($type in $typesResult.types) {
                $key = "$familyName|$($type.typeName)"
                $typeLookup[$key] = $type.typeId
            }
        }

        Start-Sleep -Milliseconds 30
    }
}

Write-Host "Total types mapped: $($typeLookup.Count)" -ForegroundColor Cyan

# Get level info
$levelsResult = Invoke-MCPMethod -Method "getLevels" -Params @{}
$ffLevel = $levelsResult.levels | Where-Object { $_.name -like "*L1*" -or $_.name -like "*First*" } | Select-Object -First 1

if (-not $ffLevel) {
    $ffLevel = $levelsResult.levels | Select-Object -First 1
}

$levelId = $ffLevel.levelId
Write-Host "Using level: $($ffLevel.name) (ID: $levelId)" -ForegroundColor Gray

# Step 3: Place all instances
Write-Host ""
Write-Host "=== Step 3: Placing Instances ===" -ForegroundColor Yellow

$results = @{
    success = @()
    failed = @()
    skipped = @()
}

$counter = 0
foreach ($instance in $allInstances) {
    $counter++
    $familyName = $instance.familyName
    $typeName = $instance.typeName
    $location = $instance.location
    $category = $instance.category

    # Use lookup table to find type ID in target project
    # (Source typeId is from different project and won't work)
    $key = "$familyName|$typeName"
    $typeId = $typeLookup[$key]

    Write-Host "[$counter/$($allInstances.Count)] $familyName : $typeName" -ForegroundColor White

    if ($null -eq $typeId -or $typeId -eq 0) {
        Write-Host "  SKIPPED: Type not found" -ForegroundColor Yellow
        $results.skipped += @{
            familyName = $familyName
            typeName = $typeName
            category = $category
        }
        continue
    }

    $locationArray = @($location.x, $location.y, $location.z)

    # Get rotation from instance data (defaults to 0 if not present)
    $rotation = $instance.rotation
    if ($null -eq $rotation) { $rotation = 0 }

    # Get mirrored state
    $mirrored = $instance.mirrored
    if ($null -eq $mirrored) { $mirrored = $false }

    # Get hand orientation for correct mirror plane
    $handArray = $null
    if ($instance.handOrientation) {
        $handArray = @($instance.handOrientation.x, $instance.handOrientation.y, $instance.handOrientation.z)
    }

    # Get facing orientation for post-mirror correction
    $facingArray = $null
    if ($instance.facingOrientation) {
        $facingArray = @($instance.facingOrientation.x, $instance.facingOrientation.y, $instance.facingOrientation.z)
    }

    $params = @{
        familyTypeId = $typeId
        location = $locationArray
        levelId = $levelId
        rotation = $rotation
        mirrored = $mirrored
    }

    if ($handArray) {
        $params.handOrientation = $handArray
    }

    if ($facingArray) {
        $params.facingOrientation = $facingArray
    }

    $placeResult = Invoke-MCPMethod -Method "placeFamilyInstance" -Params $params

    if ($placeResult.success) {
        $rotMsg = if ($rotation -ne 0) { " @ ${rotation}°" } else { "" }
        $mirMsg = if ($mirrored) { " [M]" } else { "" }
        Write-Host "  SUCCESS: ID $($placeResult.instanceId)$rotMsg$mirMsg" -ForegroundColor Green
        $results.success += @{
            familyName = $familyName
            typeName = $typeName
            instanceId = $placeResult.instanceId
            category = $category
            rotation = $rotation
            mirrored = $mirrored
        }
    } else {
        Write-Host "  FAILED: $($placeResult.error)" -ForegroundColor Red
        $results.failed += @{
            familyName = $familyName
            typeName = $typeName
            error = $placeResult.error
            category = $category
        }
    }

    Start-Sleep -Milliseconds 150
}

# Results summary
Write-Host ""
Write-Host "=== Final Results ===" -ForegroundColor Cyan
Write-Host "Successful: $($results.success.Count)" -ForegroundColor Green
Write-Host "Failed: $($results.failed.Count)" -ForegroundColor $(if ($results.failed.Count -gt 0) { "Red" } else { "Gray" })
Write-Host "Skipped: $($results.skipped.Count)" -ForegroundColor $(if ($results.skipped.Count -gt 0) { "Yellow" } else { "Gray" })

# Save results
$results | ConvertTo-Json -Depth 10 | Out-File "D:\RevitMCPBridge2026\family_placement_results_complete.json" -Encoding UTF8
Write-Host ""
Write-Host "Results saved to: family_placement_results_complete.json" -ForegroundColor Cyan
