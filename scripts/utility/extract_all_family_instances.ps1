# Extract All Family Instances from Avon Park
# Gets all Casework, Furniture, and Plumbing Fixtures with locations

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

Write-Host "=== Extract All Family Instances from Avon Park ===" -ForegroundColor Cyan
Write-Host ""

# Make sure we're on Avon Park
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "1700 West Sheffield Road" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray
Write-Host ""

$allInstances = @{
    extractedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    casework = @()
    furniture = @()
    plumbingFixtures = @()
    specialtyEquipment = @()
    electricalEquipment = @()
}

# Categories to extract
$categories = @(
    @{ name = "Casework"; key = "casework" },
    @{ name = "Furniture"; key = "furniture" },
    @{ name = "Plumbing Fixtures"; key = "plumbingFixtures" },
    @{ name = "Specialty Equipment"; key = "specialtyEquipment" },
    @{ name = "Electrical Equipment"; key = "electricalEquipment" }
)

foreach ($category in $categories) {
    Write-Host "=== Extracting $($category.name) ===" -ForegroundColor Yellow

    # Get all families in this category
    $familiesResult = Invoke-MCPMethod -Method "getFamiliesByCategory" -Params @{
        categoryName = $category.name
    }

    if (-not $familiesResult.success) {
        Write-Host "  Error getting families: $($familiesResult.error)" -ForegroundColor Red
        continue
    }

    $families = $familiesResult.families
    Write-Host "  Found $($families.Count) families" -ForegroundColor Gray

    $categoryInstances = @()

    foreach ($family in $families) {
        $familyName = $family.name
        Write-Host "  Getting instances of: $familyName" -ForegroundColor White

        # Get all instances of this family
        $instancesResult = Invoke-MCPMethod -Method "getFamilyInstances" -Params @{
            familyName = $familyName
        }

        if ($instancesResult.success -and $instancesResult.instanceCount -gt 0) {
            Write-Host "    Found: $($instancesResult.instanceCount) instances" -ForegroundColor Green

            foreach ($instance in $instancesResult.instances) {
                $categoryInstances += @{
                    instanceId = $instance.instanceId
                    familyName = $instance.familyName
                    typeName = $instance.typeName
                    typeId = $instance.typeId
                    level = $instance.level
                    location = $instance.location
                    rotation = $instance.rotation
                    facingOrientation = $instance.facingOrientation
                    handOrientation = $instance.handOrientation
                    mirrored = $instance.mirrored
                    category = $category.name
                }
            }
        } else {
            Write-Host "    No instances found" -ForegroundColor Gray
        }

        Start-Sleep -Milliseconds 100
    }

    $allInstances[$category.key] = $categoryInstances
    Write-Host "  Total instances: $($categoryInstances.Count)" -ForegroundColor Cyan
    Write-Host ""
}

# Save to JSON
$jsonPath = "D:\RevitMCPBridge2026\avon_park_family_instances.json"
$allInstances | ConvertTo-Json -Depth 10 | Out-File $jsonPath -Encoding UTF8
Write-Host "Saved to: $jsonPath" -ForegroundColor Cyan

# Summary
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Casework: $($allInstances.casework.Count)" -ForegroundColor White
Write-Host "Furniture: $($allInstances.furniture.Count)" -ForegroundColor White
Write-Host "Plumbing Fixtures: $($allInstances.plumbingFixtures.Count)" -ForegroundColor White
Write-Host "Specialty Equipment: $($allInstances.specialtyEquipment.Count)" -ForegroundColor White
Write-Host "Electrical Equipment: $($allInstances.electricalEquipment.Count)" -ForegroundColor White
$total = $allInstances.casework.Count + $allInstances.furniture.Count + $allInstances.plumbingFixtures.Count + $allInstances.specialtyEquipment.Count + $allInstances.electricalEquipment.Count
Write-Host "Total: $total" -ForegroundColor Yellow
