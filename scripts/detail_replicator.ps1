# Detail Replicator Script
# Extracts all elements from a source view and replicates them in a target view

param(
    [int]$SourceViewId,
    [int]$TargetViewId,
    [string]$PipeName = "RevitMCPBridge2026"
)

function Send-MCPCommand {
    param([string]$Method, [hashtable]$Params = @{})

    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $PipeName, 'InOut')
    $pipe.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $paramsJson = $Params | ConvertTo-Json -Compress
    $msg = "{`"method`":`"$Method`",`"params`":$paramsJson}"
    $writer.WriteLine($msg)
    $response = $reader.ReadLine()
    $pipe.Close()

    return $response | ConvertFrom-Json
}

function Get-ViewAnalysis {
    param([int]$ViewId)

    Write-Host "=== ANALYZING VIEW $ViewId ===" -ForegroundColor Cyan

    # Get view info and crop region
    $analysis = Send-MCPCommand -Method "analyzeDetailView" -Params @{viewId = $ViewId}

    if (-not $analysis.success) {
        Write-Error "Failed to analyze view: $($analysis.error)"
        return $null
    }

    $result = @{
        ViewId = $ViewId
        ViewName = $analysis.result.viewName
        ViewType = $analysis.result.viewType
        CropRegion = $analysis.result.cropRegion
        ElementCounts = $analysis.result.elementCounts
        Components = @()
        TextNotes = @()
        FilledRegions = @()
        DetailLines = @()
    }

    Write-Host "View: $($result.ViewName) ($($result.ViewType))"
    Write-Host "Crop: $($result.CropRegion.width)' x $($result.CropRegion.height)'"
    Write-Host "Elements: Components=$($result.ElementCounts.detailComponents), Text=$($result.ElementCounts.textNotes), Regions=$($result.ElementCounts.filledRegions), Lines=$($result.ElementCounts.detailLines)"

    # Get detail components
    Write-Host "`nExtracting detail components..." -ForegroundColor Yellow
    $components = Send-MCPCommand -Method "getDetailComponentsInViewVA" -Params @{viewId = $ViewId}
    if ($components.success) {
        $result.Components = $components.result.components
        Write-Host "  Found $($result.Components.Count) components"
    }

    # Get text notes with positions
    Write-Host "Extracting text notes..." -ForegroundColor Yellow
    $textNotes = Send-MCPCommand -Method "getTextNotePositions" -Params @{viewId = $ViewId}
    if ($textNotes.success) {
        $result.TextNotes = $textNotes.result.textNotes
        Write-Host "  Found $($result.TextNotes.Count) text notes"
    }

    # Get filled regions
    Write-Host "Extracting filled regions..." -ForegroundColor Yellow
    $regions = Send-MCPCommand -Method "getFilledRegionsInView" -Params @{viewId = $ViewId}
    if ($regions.success) {
        $result.FilledRegions = $regions.result.regions
        Write-Host "  Found $($result.FilledRegions.Count) filled regions"
    }

    # Get detail lines
    Write-Host "Extracting detail lines..." -ForegroundColor Yellow
    $lines = Send-MCPCommand -Method "getDetailLinesInViewVA" -Params @{viewId = $ViewId}
    if ($lines.success) {
        $result.DetailLines = $lines.result.lines
        Write-Host "  Found $($result.DetailLines.Count) detail lines"
    }

    return $result
}

function Normalize-Coordinates {
    param(
        [hashtable]$ViewData,
        [double]$OffsetX = 0,
        [double]$OffsetZ = 0
    )

    # Calculate offset to normalize to origin
    $cropMinX = $ViewData.CropRegion.minX
    $cropMinZ = $ViewData.CropRegion.minY  # Note: Y in crop = Z in 3D

    Write-Host "`nNormalizing coordinates (offset: X=$([Math]::Round($cropMinX,2)), Z=$([Math]::Round($cropMinZ,2)))"

    # Normalize each element
    foreach ($comp in $ViewData.Components) {
        $comp.location.x = $comp.location.x - $cropMinX + $OffsetX
        $comp.location.z = $comp.location.z - $cropMinZ + $OffsetZ
    }

    foreach ($text in $ViewData.TextNotes) {
        $text.x = $text.x - $cropMinX + $OffsetX
        $text.z = $text.z - $cropMinZ + $OffsetZ
        foreach ($leader in $text.leaderEndpoints) {
            $leader.x = $leader.x - $cropMinX + $OffsetX
            $leader.z = $leader.z - $cropMinZ + $OffsetZ
        }
    }

    foreach ($region in $ViewData.FilledRegions) {
        $region.boundingBox.min.x = $region.boundingBox.min.x - $cropMinX + $OffsetX
        $region.boundingBox.min.z = $region.boundingBox.min.z - $cropMinZ + $OffsetZ
        $region.boundingBox.max.x = $region.boundingBox.max.x - $cropMinX + $OffsetX
        $region.boundingBox.max.z = $region.boundingBox.max.z - $cropMinZ + $OffsetZ
    }

    return $ViewData
}

function Replicate-ToView {
    param(
        [hashtable]$SourceData,
        [int]$TargetViewId
    )

    Write-Host "`n=== REPLICATING TO VIEW $TargetViewId ===" -ForegroundColor Cyan

    $results = @{
        ComponentsCreated = 0
        TextNotesCreated = 0
        RegionsCreated = 0
        LinesCreated = 0
        Errors = @()
    }

    # Replicate detail components
    Write-Host "`nReplicating detail components..." -ForegroundColor Yellow
    foreach ($comp in $SourceData.Components) {
        # Need to find matching type in target project
        $msg = Send-MCPCommand -Method "placeDetailComponentVA" -Params @{
            viewId = $TargetViewId
            typeId = $comp.typeId  # Assuming same project
            x = $comp.location.x
            y = $comp.location.z  # Z becomes Y in 2D view
        }
        if ($msg.success) {
            $results.ComponentsCreated++
        } else {
            $results.Errors += "Component: $($msg.error)"
        }
    }
    Write-Host "  Created $($results.ComponentsCreated) components"

    # Replicate text notes
    Write-Host "Replicating text notes..." -ForegroundColor Yellow
    foreach ($text in $SourceData.TextNotes) {
        $leaderEndX = if ($text.leaderEndpoints.Count -gt 0) { $text.leaderEndpoints[0].x } else { $text.x }
        $leaderEndY = if ($text.leaderEndpoints.Count -gt 0) { $text.leaderEndpoints[0].z } else { $text.z }

        $msg = Send-MCPCommand -Method "createTextNoteWithLeader" -Params @{
            viewId = $TargetViewId
            text = $text.text
            textX = $text.x
            textY = $text.z
            leaderEndX = $leaderEndX
            leaderEndY = $leaderEndY
        }
        if ($msg.success) {
            $results.TextNotesCreated++
        } else {
            $results.Errors += "TextNote: $($msg.error)"
        }
    }
    Write-Host "  Created $($results.TextNotesCreated) text notes"

    # Replicate filled regions (would need boundary extraction, not just bounding box)
    Write-Host "Filled regions require boundary points - skipping for now" -ForegroundColor DarkYellow

    # Replicate detail lines (would need proper endpoint data)
    Write-Host "Detail lines require proper endpoint data - skipping for now" -ForegroundColor DarkYellow

    return $results
}

# Main execution
Write-Host "============================================" -ForegroundColor Green
Write-Host "  DETAIL VIEW REPLICATOR" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

if ($SourceViewId -eq 0) {
    Write-Host "Usage: .\detail_replicator.ps1 -SourceViewId <id> -TargetViewId <id>"
    Write-Host "Example: .\detail_replicator.ps1 -SourceViewId 2136700 -TargetViewId 2238350"
    exit
}

# Analyze source view
$sourceData = Get-ViewAnalysis -ViewId $SourceViewId

if ($sourceData) {
    # Normalize coordinates to origin
    $normalizedData = Normalize-Coordinates -ViewData $sourceData

    # Output summary
    Write-Host "`n=== SUMMARY ===" -ForegroundColor Green
    Write-Host "Source: $($sourceData.ViewName)"
    Write-Host "Crop Size: $([Math]::Round($sourceData.CropRegion.width, 2))' x $([Math]::Round($sourceData.CropRegion.height, 2))'"
    Write-Host "Components: $($sourceData.Components.Count)"
    Write-Host "Text Notes: $($sourceData.TextNotes.Count)"
    Write-Host "Filled Regions: $($sourceData.FilledRegions.Count)"
    Write-Host "Detail Lines: $($sourceData.DetailLines.Count)"

    # If target specified, replicate
    if ($TargetViewId -gt 0) {
        $results = Replicate-ToView -SourceData $normalizedData -TargetViewId $TargetViewId
        Write-Host "`n=== REPLICATION RESULTS ===" -ForegroundColor Green
        Write-Host "Components: $($results.ComponentsCreated)"
        Write-Host "Text Notes: $($results.TextNotesCreated)"
        if ($results.Errors.Count -gt 0) {
            Write-Host "Errors: $($results.Errors.Count)" -ForegroundColor Red
            $results.Errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        }
    }

    # Export data for reference
    $exportPath = "D:\detail_analysis_$SourceViewId.json"
    $normalizedData | ConvertTo-Json -Depth 10 | Out-File $exportPath
    Write-Host "`nData exported to: $exportPath"
}
