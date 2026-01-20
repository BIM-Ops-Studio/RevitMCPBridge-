# Draw CMU Wall Section v3 - Using typeIds from existing components
# First queries for component typeIds, then places them in a repeating pattern

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 0,
    [float]$BaseY = 0,
    [float]$WallHeight = 8.0  # 8 feet default
)

Write-Host "=== CMU Wall Section v3 ===" -ForegroundColor Cyan
Write-Host "Using existing component typeIds for placement"

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(15000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 5 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 300
    $response = $reader.ReadLine()
    return $response | ConvertFrom-Json
}

# Step 1: Get component typeIds from existing wall section view (1737919 has CMU components)
Write-Host "`nStep 1: Discovering component typeIds from existing details..." -ForegroundColor Yellow
$sourceView = Invoke-MCP -Method "getDetailComponentsInViewVA" -Params @{viewId = 1737919}

$typeIds = @{}
if ($sourceView.success) {
    foreach ($comp in $sourceView.result.components) {
        $key = "$($comp.familyName):$($comp.typeName)"
        if (-not $typeIds.ContainsKey($key)) {
            $typeIds[$key] = $comp.typeId
            Write-Host "  Found: $key (TypeID: $($comp.typeId))" -ForegroundColor Green
        }
    }
}

# If no typeIds found from view, we need the new DLL
if ($typeIds.Count -eq 0) {
    Write-Host "  No components found - you may need to restart Revit to load updated DLL" -ForegroundColor Red
    $pipe.Close()
    exit
}

function Place-Component {
    param([int]$TypeId, [string]$Label, [float]$X, [float]$Y, [float]$Rotation = 0)

    if ($TypeId -eq 0) {
        Write-Host "  ! $Label skipped - no typeId" -ForegroundColor Yellow
        return $null
    }

    $result = Invoke-MCP -Method "placeDetailComponent" -Params @{
        viewId = $ViewId
        componentTypeId = $TypeId
        location = @{
            x = $BaseX + $X
            y = $BaseY + $Y
            z = 0
        }
        rotation = $Rotation
    }
    if ($result.success) {
        Write-Host "  + $Label at ($X, $Y)" -ForegroundColor Green
    } else {
        Write-Host "  ! $Label failed - $($result.error)" -ForegroundColor Red
    }
    return $result
}

function Draw-Line {
    param([float]$X1, [float]$Y1, [float]$X2, [float]$Y2, [string]$Style = "Thin Lines")
    $result = Invoke-MCP -Method "createDetailLineInDraftingView" -Params @{
        viewId = $ViewId
        startX = $BaseX + $X1
        startY = $BaseY + $Y1
        endX = $BaseX + $X2
        endY = $BaseY + $Y2
        lineStyle = $Style
    }
    return $result.success
}

function Add-Text {
    param([string]$Text, [float]$X, [float]$Y, [float]$LeaderX = $null, [float]$LeaderY = $null)
    if ($null -ne $LeaderX) {
        $result = Invoke-MCP -Method "createTextNoteWithLeader" -Params @{
            viewId = $ViewId
            text = $Text
            textX = $BaseX + $X
            textY = $BaseY + $Y
            leaderEndX = $BaseX + $LeaderX
            leaderEndY = $BaseY + $LeaderY
        }
    } else {
        $result = Invoke-MCP -Method "createTextNote" -Params @{
            viewId = $ViewId
            text = $Text
            x = $BaseX + $X
            y = $BaseY + $Y
        }
    }
    return $result.success
}

# === Wall Dimensions ===
$cmuWidth = 8/12       # 8" CMU = 0.667 feet
$courseHeight = 8/12   # 8" course height
$numCourses = [Math]::Floor($WallHeight / $courseHeight)

Write-Host "`nStep 2: Looking for CMU-related typeIds..." -ForegroundColor Yellow
# Try to find CMU section component
$cmuTypeId = 0
$lumberTypeId = 0
$gypsumTypeId = 0
$rebarTypeId = 0
$breakLineTypeId = 0

foreach ($key in $typeIds.Keys) {
    if ($key -match "Lumber" -and $key -match "1x3") { $lumberTypeId = $typeIds[$key] }
    if ($key -match "Gypsum" -or $key -match "Plaster") { $gypsumTypeId = $typeIds[$key] }
    if ($key -match "Reinf|Bar|#_5") { $rebarTypeId = $typeIds[$key] }
    if ($key -match "Break") { $breakLineTypeId = $typeIds[$key] }
}

Write-Host "  Lumber 1x3 TypeId: $lumberTypeId"
Write-Host "  Gypsum TypeId: $gypsumTypeId"
Write-Host "  Rebar TypeId: $rebarTypeId"
Write-Host "  Break Line TypeId: $breakLineTypeId"

Write-Host "`nStep 3: Placing components..." -ForegroundColor Yellow

# === INTERIOR FURRING ===
if ($lumberTypeId -gt 0) {
    Write-Host "`nPlacing interior furring strips (1x3)..." -ForegroundColor Cyan
    $furrX = $cmuWidth + 0.0833  # Furring at 1" from CMU
    $stripSpacing = 24/12  # 24" o.c.
    for ($y = $stripSpacing; $y -lt $WallHeight; $y += $stripSpacing) {
        Place-Component -TypeId $lumberTypeId -Label "Furring 1x3" -X $furrX -Y $y
    }
}

# === REBAR ===
if ($rebarTypeId -gt 0) {
    Write-Host "`nPlacing reinforcement..." -ForegroundColor Cyan
    Place-Component -TypeId $rebarTypeId -Label "Rebar #5" -X ($cmuWidth * 0.3) -Y 1
    Place-Component -TypeId $rebarTypeId -Label "Rebar #5" -X ($cmuWidth * 0.7) -Y 1
    Place-Component -TypeId $rebarTypeId -Label "Rebar #5" -X ($cmuWidth * 0.3) -Y ($WallHeight - 1)
    Place-Component -TypeId $rebarTypeId -Label "Rebar #5" -X ($cmuWidth * 0.7) -Y ($WallHeight - 1)
}

# === BREAK LINE ===
if ($breakLineTypeId -gt 0) {
    Write-Host "`nPlacing break line..." -ForegroundColor Cyan
    Place-Component -TypeId $breakLineTypeId -Label "Break Line" -X ($cmuWidth / 2) -Y ($WallHeight / 2)
}

Write-Host "`nStep 4: Drawing CMU pattern with lines (simulating repeating detail)..." -ForegroundColor Yellow

# Since we may not have CMU section typeId, draw CMU pattern with lines
$stuccoX = -0.0625
$gwbX = $cmuWidth + 0.125

# Wall outline
Draw-Line -X1 0 -Y1 0 -X2 0 -Y2 $WallHeight -Style "3"
Draw-Line -X1 $cmuWidth -Y1 0 -X2 $cmuWidth -Y2 $WallHeight -Style "3"

# CMU horizontal coursing (repeating pattern)
for ($y = $courseHeight; $y -lt $WallHeight; $y += $courseHeight) {
    Draw-Line -X1 0 -Y1 $y -X2 $cmuWidth -Y2 $y -Style "1"
}

# CMU vertical cells
Draw-Line -X1 ($cmuWidth/3) -Y1 0 -X2 ($cmuWidth/3) -Y2 $WallHeight -Style "1"
Draw-Line -X1 (2*$cmuWidth/3) -Y1 0 -X2 (2*$cmuWidth/3) -Y2 $WallHeight -Style "1"

# Stucco
Draw-Line -X1 $stuccoX -Y1 0 -X2 $stuccoX -Y2 $WallHeight -Style "1"
Draw-Line -X1 $stuccoX -Y1 $WallHeight -X2 0 -Y2 $WallHeight -Style "1"

# GWB
Draw-Line -X1 $gwbX -Y1 0 -X2 $gwbX -Y2 $WallHeight -Style "1"
Draw-Line -X1 $cmuWidth -Y1 $WallHeight -X2 $gwbX -Y2 $WallHeight -Style "1"

# Grade line
Draw-Line -X1 -1 -Y1 0 -X2 1.5 -Y2 0 -Style "3"

Write-Host "`nStep 5: Adding annotations..." -ForegroundColor Yellow

$leftX = -2.5
$rightX = $gwbX + 1.5

Add-Text -Text "3/4`" STUCCO ON`rMTL. LATH" -X $leftX -Y 6 -LeaderX $stuccoX -LeaderY 6
Add-Text -Text "8`" CMU WALL W/`r#5 VERT. @ 48`" O.C.`rAND BOND BEAM AT TOP" -X $leftX -Y 4 -LeaderX ($cmuWidth/2) -LeaderY 4
Add-Text -Text "FIN. GRADE" -X $leftX -Y 0.2
Add-Text -Text "1/2`" GYP. BD. ON`r1x3 P.T. FURR.`r@ 24`" O.C." -X $rightX -Y 5 -LeaderX $gwbX -LeaderY 5

$pipe.Close()

Write-Host "`n=== CMU Wall Section Complete ===" -ForegroundColor Green
Write-Host "Location: ($BaseX, $BaseY)"
Write-Host "Height: $WallHeight ft"
Write-Host "Components placed: Lumber, Rebar, Break Line"
Write-Host "CMU pattern drawn with detail lines"
