# Place Family Instances from Avon Park to SF-project-test-2
# Version 2: Uses type ID lookup by family name and type name

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

Write-Host "=== Place Family Instances from Avon Park ===" -ForegroundColor Cyan
Write-Host ""

# Load extracted instance data
$instanceData = Get-Content "D:\RevitMCPBridge2026\avon_park_family_instances.json" | ConvertFrom-Json

Write-Host "Loaded instance data:" -ForegroundColor Gray
Write-Host "  Casework: $($instanceData.casework.Count)" -ForegroundColor White
Write-Host "  Furniture: $($instanceData.furniture.Count)" -ForegroundColor White
Write-Host "  Plumbing Fixtures: $($instanceData.plumbingFixtures.Count)" -ForegroundColor White
Write-Host ""

# Switch to target document
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray
Write-Host ""

# Build type lookup map
Write-Host "Building type lookup map..." -ForegroundColor Yellow
$typeLookup = @{}

$categories = @("Casework", "Furniture", "Plumbing Fixtures")

foreach ($category in $categories) {
    Write-Host "  Getting types for $category..." -ForegroundColor Gray

    # Get all families in the category
    $familiesResult = Invoke-MCPMethod -Method "getFamiliesByCategory" -Params @{
        categoryName = $category
    }

    if (-not $familiesResult.success) {
        Write-Host "    Error: $($familiesResult.error)" -ForegroundColor Red
        continue
    }

    # For each family, get all its types
    foreach ($family in $familiesResult.families) {
        $familyName = $family.name

        # Get types for this family
        $typesResult = Invoke-MCPMethod -Method "getFamilyTypes" -Params @{
            familyName = $familyName
        }

        if ($typesResult.success) {
            foreach ($type in $typesResult.types) {
                $key = "$familyName|$($type.typeName)"
                $typeLookup[$key] = $type.typeId
            }
        }

        Start-Sleep -Milliseconds 50
    }

    Write-Host "    Found types for $($familiesResult.families.Count) families" -ForegroundColor Green
}

Write-Host "Total types mapped: $($typeLookup.Count)" -ForegroundColor Cyan
Write-Host ""

# Get level info for the target
$levelsResult = Invoke-MCPMethod -Method "getLevels" -Params @{}
$ffLevel = $levelsResult.levels | Where-Object { $_.name -like "*L1*" -or $_.name -like "*First*" -or $_.name -eq "Level 1" } | Select-Object -First 1

if (-not $ffLevel) {
    $ffLevel = $levelsResult.levels | Select-Object -First 1
}

$levelId = $ffLevel.levelId
Write-Host "Using level: $($ffLevel.name) (ID: $levelId)" -ForegroundColor Gray
Write-Host ""

# Results tracking
$results = @{
    success = @()
    failed = @()
    skipped = @()
}

# Process each category
$allInstances = @()
$allInstances += $instanceData.casework
$allInstances += $instanceData.furniture
$allInstances += $instanceData.plumbingFixtures

Write-Host "Total instances to place: $($allInstances.Count)" -ForegroundColor Yellow
Write-Host ""

$counter = 0
foreach ($instance in $allInstances) {
    $counter++
    $familyName = $instance.familyName
    $typeName = $instance.typeName
    $location = $instance.location
    $category = $instance.category

    # Look up the type ID
    $key = "$familyName|$typeName"
    $typeId = $typeLookup[$key]

    Write-Host "[$counter/$($allInstances.Count)] $familyName : $typeName" -ForegroundColor White

    if ($null -eq $typeId) {
        Write-Host "  SKIPPED: Type not found in target project" -ForegroundColor Yellow
        $results.skipped += @{
            familyName = $familyName
            typeName = $typeName
            category = $category
            reason = "Type not found"
        }
        continue
    }

    # Build location array
    $locationArray = @($location.x, $location.y, $location.z)

    # Place the instance
    $placeResult = Invoke-MCPMethod -Method "placeFamilyInstance" -Params @{
        familyTypeId = $typeId
        location = $locationArray
        levelId = $levelId
    }

    if ($placeResult.success) {
        Write-Host "  SUCCESS: ID $($placeResult.instanceId)" -ForegroundColor Green
        $results.success += @{
            familyName = $familyName
            typeName = $typeName
            instanceId = $placeResult.instanceId
            category = $category
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

    Start-Sleep -Milliseconds 200  # Give Revit time to process
}

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "Successful: $($results.success.Count)" -ForegroundColor Green
Write-Host "Failed: $($results.failed.Count)" -ForegroundColor $(if ($results.failed.Count -gt 0) { "Red" } else { "Gray" })
Write-Host "Skipped: $($results.skipped.Count)" -ForegroundColor $(if ($results.skipped.Count -gt 0) { "Yellow" } else { "Gray" })
Write-Host ""

# Summary by category
$caseworkSuccess = ($results.success | Where-Object { $_.category -eq "Casework" }).Count
$furnitureSuccess = ($results.success | Where-Object { $_.category -eq "Furniture" }).Count
$plumbingSuccess = ($results.success | Where-Object { $_.category -eq "Plumbing Fixtures" }).Count

Write-Host "By Category:" -ForegroundColor Yellow
Write-Host "  Casework: $caseworkSuccess / $($instanceData.casework.Count)" -ForegroundColor White
Write-Host "  Furniture: $furnitureSuccess / $($instanceData.furniture.Count)" -ForegroundColor White
Write-Host "  Plumbing Fixtures: $plumbingSuccess / $($instanceData.plumbingFixtures.Count)" -ForegroundColor White

# Save results
$resultsPath = "D:\RevitMCPBridge2026\family_placement_results.json"
$results | ConvertTo-Json -Depth 10 | Out-File $resultsPath -Encoding UTF8
Write-Host ""
Write-Host "Results saved to: $resultsPath" -ForegroundColor Cyan

# Show failed items for debugging
if ($results.failed.Count -gt 0) {
    Write-Host ""
    Write-Host "=== Failed Items ===" -ForegroundColor Red
    foreach ($failed in $results.failed | Select-Object -First 10) {
        Write-Host "  $($failed.familyName) : $($failed.typeName)" -ForegroundColor Yellow
        Write-Host "    Error: $($failed.error)" -ForegroundColor Gray
    }
    if ($results.failed.Count -gt 10) {
        Write-Host "  ... and $($results.failed.Count - 10) more" -ForegroundColor Gray
    }
}

# Show skipped items for debugging
if ($results.skipped.Count -gt 0) {
    Write-Host ""
    Write-Host "=== Skipped Items ===" -ForegroundColor Yellow
    foreach ($skipped in $results.skipped | Select-Object -First 10) {
        Write-Host "  $($skipped.familyName) : $($skipped.typeName)" -ForegroundColor White
        Write-Host "    Reason: $($skipped.reason)" -ForegroundColor Gray
    }
    if ($results.skipped.Count -gt 10) {
        Write-Host "  ... and $($results.skipped.Count - 10) more" -ForegroundColor Gray
    }
}
