# Place Tubs Script
# Transfers tub family and places 3 tubs from source data

$pipeName = '\\.\pipe\RevitMCPBridge2026'

function Invoke-MCPMethod {
    param(
        [string]$Method,
        [hashtable]$Params = @{}
    )

    $request = @{
        jsonrpc = '2.0'
        id = [guid]::NewGuid().ToString()
        method = $Method
        params = $Params
    } | ConvertTo-Json -Depth 10

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'RevitMCPBridge2026', [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(10000)

        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)

        $writer.WriteLine($request)
        $writer.Flush()

        $response = $reader.ReadLine()
        $pipe.Close()

        $result = $response | ConvertFrom-Json
        return $result.result
    }
    catch {
        return @{ success = $false; error = $_.Exception.Message }
    }
}

Write-Host "=== Tub Placement Script ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Transfer tub family from source to target
Write-Host "Step 1: Transferring Tub-Rectangular-3D family..." -ForegroundColor Yellow

$transferResult = Invoke-MCPMethod -Method "transferFamilyBetweenDocuments" -Params @{
    sourceDocumentName = "1700 West Sheffield Road"
    targetDocumentName = "SF-project-test-2"
    familyName = "Tub-Rectangular-3D"
}

if ($transferResult.success) {
    Write-Host "  SUCCESS: Transferred $($transferResult.transferredCount) types" -ForegroundColor Green
} elseif ($transferResult.error -match "already exists") {
    Write-Host "  Family already exists in target" -ForegroundColor Gray
} else {
    Write-Host "  Result: $($transferResult.error)" -ForegroundColor Yellow
}

Start-Sleep -Milliseconds 500

# Step 2: Switch to target document
Write-Host ""
Write-Host "Step 2: Switching to target document..." -ForegroundColor Yellow

$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{
    documentName = "SF-project-test-2"
}

if ($switchResult.result.activatedDocument) {
    Write-Host "  Active: $($switchResult.result.activatedDocument)" -ForegroundColor Green
}

Start-Sleep -Milliseconds 500

# Step 3: Get tub type ID
Write-Host ""
Write-Host "Step 3: Getting tub type ID..." -ForegroundColor Yellow

$typesResult = Invoke-MCPMethod -Method "getFamilyInstanceTypes" -Params @{
    familyName = "Tub-Rectangular-3D"
}

$tubTypeId = $null
if ($typesResult.types -and $typesResult.types.Count -gt 0) {
    $tubTypeId = $typesResult.types[0].typeId
    Write-Host "  Found type: $($typesResult.types[0].typeName) (ID: $tubTypeId)" -ForegroundColor Green
} else {
    # Try getting by category
    Write-Host "  No types found by family name, trying by category..." -ForegroundColor Yellow

    $catResult = Invoke-MCPMethod -Method "getFamiliesByCategory" -Params @{
        categoryName = "Plumbing Fixtures"
    }

    if ($catResult.families) {
        foreach ($family in $catResult.families) {
            if ($family.familyName -eq "Tub-Rectangular-3D") {
                if ($family.types -and $family.types.Count -gt 0) {
                    $tubTypeId = $family.types[0].typeId
                    Write-Host "  Found type: $($family.types[0].typeName) (ID: $tubTypeId)" -ForegroundColor Green
                }
                break
            }
        }
    }
}

if (-not $tubTypeId) {
    Write-Host "  ERROR: Could not find tub type ID" -ForegroundColor Red
    Write-Host "  Available plumbing families:" -ForegroundColor Yellow
    if ($catResult.families) {
        foreach ($family in $catResult.families) {
            Write-Host "    - $($family.familyName)" -ForegroundColor Gray
        }
    }
    exit 1
}

# Step 4: Place tubs at source locations
Write-Host ""
Write-Host "Step 4: Placing tubs..." -ForegroundColor Yellow

# Tub data from source:
$tubs = @(
    @{ x = 1.52; y = -19.65; z = 0; rotation = 1.5708 },    # 90 degrees
    @{ x = -8.27; y = 8.82; z = 0; rotation = 4.7124 },     # 270 degrees
    @{ x = -24.73; y = 8.82; z = 0; rotation = 4.7124 }     # 270 degrees
)

$successCount = 0
$failCount = 0

foreach ($tub in $tubs) {
    $location = "($([math]::Round($tub.x, 2)), $([math]::Round($tub.y, 2)))"
    Write-Host "  Placing tub at $location..." -ForegroundColor White

    $placeResult = Invoke-MCPMethod -Method "placeFamilyInstance" -Params @{
        familyTypeId = $tubTypeId
        x = $tub.x
        y = $tub.y
        z = $tub.z
        rotation = $tub.rotation
    }

    if ($placeResult.success) {
        Write-Host "    SUCCESS: Element ID $($placeResult.elementId)" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "    FAILED: $($placeResult.error)" -ForegroundColor Red
        $failCount++
    }

    Start-Sleep -Milliseconds 300
}

# Summary
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "  Placed: $successCount tubs" -ForegroundColor Green
if ($failCount -gt 0) {
    Write-Host "  Failed: $failCount tubs" -ForegroundColor Red
}
Write-Host ""
