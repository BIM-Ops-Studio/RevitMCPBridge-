# Extract detail patterns from drafting views
# Saves to knowledge base for future detail creation

param(
    [int]$MaxDetails = 20,  # Limit for testing
    [string]$OutputDir = "D:/RevitMCPBridge2026/knowledge/details"
)

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 5 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 1500
    $response = $reader.ReadLine()
    return $response | ConvertFrom-Json
}

Write-Host "=== Detail Library Extraction ===" -ForegroundColor Cyan
Write-Host "Output: $OutputDir"

# Get all drafting views
$viewsResult = Invoke-MCP -Method "getViews"
$draftingViews = $viewsResult.result.views | Where-Object { $_.viewType -eq 'DraftingView' }
Write-Host "Found $($draftingViews.Count) drafting views"

$extracted = 0
$details = @()

foreach ($view in $draftingViews | Select-Object -First $MaxDetails) {
    Write-Host "`nExtracting: $($view.name) (ID: $($view.id))..." -ForegroundColor Yellow

    # Analyze the view
    $analysis = Invoke-MCP -Method "analyzeDetailView" -Params @{viewId = $view.id}

    if (-not $analysis.success) {
        Write-Host "  Skipped - analysis failed" -ForegroundColor Red
        continue
    }

    $detail = @{
        id = $view.id
        name = $view.name
        scale = $view.scale
        elements = @{
            detailLines = @()
            filledRegions = @()
            textNotes = @()
            detailComponents = @()
        }
        metadata = @{
            extractedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            lineCount = $analysis.result.elementCounts.detailLines
            regionCount = $analysis.result.elementCounts.filledRegions
            textCount = $analysis.result.elementCounts.textNotes
            componentCount = $analysis.result.elementCounts.detailComponents
        }
    }

    # Extract detail lines
    if ($analysis.result.elementCounts.detailLines -gt 0) {
        $lines = Invoke-MCP -Method "getDetailLinesInViewVA" -Params @{viewId = $view.id}
        if ($lines.success -and $lines.result.lines) {
            $detail.elements.detailLines = $lines.result.lines | ForEach-Object {
                @{
                    style = $_.lineStyle
                    start = @{x = [Math]::Round($_.start.x, 4); y = [Math]::Round($_.start.z, 4)}
                    end = @{x = [Math]::Round($_.end.x, 4); y = [Math]::Round($_.end.z, 4)}
                    length = [Math]::Round($_.length, 4)
                }
            }
        }
    }

    # Extract text notes
    if ($analysis.result.elementCounts.textNotes -gt 0) {
        $texts = Invoke-MCP -Method "getTextNotePositions" -Params @{viewId = $view.id}
        if ($texts.success -and $texts.result.textNotes) {
            $detail.elements.textNotes = $texts.result.textNotes | ForEach-Object {
                @{
                    text = $_.text
                    position = @{x = [Math]::Round($_.x, 4); y = [Math]::Round($_.z, 4)}
                    hasLeader = $_.hasLeader
                    leaderEnd = if ($_.leaderEndpoints -and $_.leaderEndpoints.Count -gt 0) {
                        @{x = [Math]::Round($_.leaderEndpoints[0].x, 4); y = [Math]::Round($_.leaderEndpoints[0].z, 4)}
                    } else { $null }
                }
            }
        }
    }

    # Extract filled regions
    if ($analysis.result.elementCounts.filledRegions -gt 0) {
        $regions = Invoke-MCP -Method "getFilledRegionsInView" -Params @{viewId = $view.id}
        if ($regions.success -and $regions.result.regions) {
            $detail.elements.filledRegions = $regions.result.regions | ForEach-Object {
                @{
                    typeName = $_.regionTypeName
                    pattern = $_.fillPatternName
                    bounds = @{
                        minX = [Math]::Round($_.boundingBox.min.x, 4)
                        minY = [Math]::Round($_.boundingBox.min.z, 4)
                        maxX = [Math]::Round($_.boundingBox.max.x, 4)
                        maxY = [Math]::Round($_.boundingBox.max.z, 4)
                    }
                }
            }
        }
    }

    # Extract detail components
    if ($analysis.result.elementCounts.detailComponents -gt 0) {
        $components = Invoke-MCP -Method "getDetailComponentsInViewVA" -Params @{viewId = $view.id}
        if ($components.success -and $components.result.components) {
            $detail.elements.detailComponents = $components.result.components | ForEach-Object {
                @{
                    family = $_.familyName
                    type = $_.typeName
                    typeId = $_.typeId
                    location = @{x = [Math]::Round($_.location.x, 4); y = [Math]::Round($_.location.z, 4)}
                }
            }
        }
    }

    $details += $detail
    $extracted++

    # Categorize and save
    $category = "99-general"
    $nameLower = $view.name.ToLower()
    if ($nameLower -match "roof|eave|parapet|flashing") { $category = "01-roof" }
    elseif ($nameLower -match "cabinet|millwork|sink") { $category = "02-cabinetry" }
    elseif ($nameLower -match "wall|cmu|stud|section") { $category = "03-wall" }
    elseif ($nameLower -match "floor|slab|footing|foundation") { $category = "04-floor" }
    elseif ($nameLower -match "door|jamb") { $category = "05-door" }
    elseif ($nameLower -match "window|buck|sill") { $category = "06-window" }
    elseif ($nameLower -match "stair|railing|handrail") { $category = "07-stair" }
    elseif ($nameLower -match "ceiling|soffit") { $category = "08-ceiling" }

    $safeName = ($view.name -replace '[^\w\-]', '_').Substring(0, [Math]::Min(50, $view.name.Length))
    $outPath = "$OutputDir/$category/$safeName.json"

    # Ensure directory exists
    $outDir = Split-Path $outPath -Parent
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

    $detail | ConvertTo-Json -Depth 10 | Out-File -FilePath $outPath -Encoding UTF8

    $lineCount = $detail.elements.detailLines.Count
    $textCount = $detail.elements.textNotes.Count
    $regionCount = $detail.elements.filledRegions.Count
    Write-Host "  Saved: $lineCount lines, $textCount texts, $regionCount regions -> $category" -ForegroundColor Green
}

$pipe.Close()

Write-Host "`n=== Extraction Complete ===" -ForegroundColor Cyan
Write-Host "Extracted: $extracted details"
Write-Host "Saved to: $OutputDir"

# Create summary index
$summary = @{
    extractedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    totalDetails = $extracted
    details = $details | ForEach-Object {
        @{
            name = $_.name
            id = $_.id
            lines = $_.metadata.lineCount
            texts = $_.metadata.textCount
            regions = $_.metadata.regionCount
            components = $_.metadata.componentCount
        }
    }
}

$summary | ConvertTo-Json -Depth 5 | Out-File -FilePath "$OutputDir/_extraction_summary.json" -Encoding UTF8
Write-Host "Summary saved to: $OutputDir/_extraction_summary.json"
