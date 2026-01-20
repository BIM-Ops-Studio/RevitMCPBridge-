# Extract Family Instances from Avon Park
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

Write-Host "=== Extract Family Instances from Avon Park ===" -ForegroundColor Cyan
Write-Host ""

# Make sure we're on Avon Park
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "1700 West Sheffield Road" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray

# Get a floor plan view for extracting elements
$viewsResult = Invoke-MCPMethod -Method "getViews" -Params @{}
$floorPlan = $viewsResult.views | Where-Object { $_.viewType -eq "FloorPlan" -and $_.name -like "*F.F.*" } | Select-Object -First 1

if (-not $floorPlan) {
    $floorPlan = $viewsResult.views | Where-Object { $_.viewType -eq "FloorPlan" } | Select-Object -First 1
}

Write-Host "Using view: $($floorPlan.name) (ID: $($floorPlan.viewId))" -ForegroundColor Gray
Write-Host ""

$allElements = @{
    extractedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    casework = @()
    furniture = @()
    plumbingFixtures = @()
}

# Categories to extract
$categories = @(
    @{ name = "Casework"; key = "casework" },
    @{ name = "Furniture"; key = "furniture" },
    @{ name = "Plumbing Fixtures"; key = "plumbingFixtures" }
)

foreach ($category in $categories) {
    Write-Host "Extracting $($category.name)..." -ForegroundColor Yellow

    $result = Invoke-MCPMethod -Method "getElementsByCategory" -Params @{
        categoryName = $category.name
        viewId = $floorPlan.viewId
    }

    if ($result.success) {
        $elements = @()
        foreach ($elem in $result.elements) {
            # Get element location
            $locResult = Invoke-MCPMethod -Method "getElementLocation" -Params @{
                elementId = $elem.elementId
            }

            if ($locResult.success) {
                $elements += @{
                    elementId = $elem.elementId
                    familyName = $elem.familyName
                    typeName = $elem.typeName
                    typeId = $elem.typeId
                    location = $locResult.location
                    rotation = $locResult.rotation
                    levelId = $elem.levelId
                    levelName = $elem.levelName
                }
            }
        }

        $allElements[$category.key] = $elements
        Write-Host "  Found: $($elements.Count) instances" -ForegroundColor Green
    } else {
        Write-Host "  Error: $($result.error)" -ForegroundColor Red
    }

    Start-Sleep -Milliseconds 200
}

# Save to JSON
$jsonPath = "D:\RevitMCPBridge2026\avon_park_family_instances.json"
$allElements | ConvertTo-Json -Depth 10 | Out-File $jsonPath -Encoding UTF8
Write-Host ""
Write-Host "Saved to: $jsonPath" -ForegroundColor Cyan

# Summary
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Casework: $($allElements.casework.Count)" -ForegroundColor White
Write-Host "Furniture: $($allElements.furniture.Count)" -ForegroundColor White
Write-Host "Plumbing Fixtures: $($allElements.plumbingFixtures.Count)" -ForegroundColor White
Write-Host "Total: $($allElements.casework.Count + $allElements.furniture.Count + $allElements.plumbingFixtures.Count)" -ForegroundColor Yellow
