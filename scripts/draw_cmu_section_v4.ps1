# Draw CMU Wall Section v4 - CORRECT Y ALIGNMENT
# CMU insertion: X at LEFT EDGE, Y at BOTTOM EDGE
# First CMU at Y=0 (grade), subsequent courses stacked above

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 60,        # Fresh position
    [float]$BaseY = 0,         # Grade level
    [float]$WallHeight = 8.0
)

Write-Host "=== CMU Wall Section v4 (Bottom Y Insertion) ===" -ForegroundColor Cyan

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(15000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 5 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 200
    $response = $reader.ReadLine()
    return $response | ConvertFrom-Json
}

function Place-Component {
    param([int]$TypeId, [string]$Label, [float]$X, [float]$Y)
    $result = Invoke-MCP -Method "placeDetailComponent" -Params @{
        viewId = $ViewId
        componentTypeId = $TypeId
        location = @{x = $X; y = $Y; z = 0}
        rotation = 0
    }
    if ($result.success) { Write-Host "  + $Label" -ForegroundColor Green }
    else { Write-Host "  ! $Label - $($result.error)" -ForegroundColor Red }
    return $result
}

function Draw-Line {
    param([float]$X1, [float]$Y1, [float]$X2, [float]$Y2, [string]$Style = "Thin Lines")
    $result = Invoke-MCP -Method "createDetailLineInDraftingView" -Params @{
        viewId = $ViewId
        startX = $X1; startY = $Y1; endX = $X2; endY = $Y2
        lineStyle = $Style
    }
    return $result.success
}

function Add-Text {
    param([string]$Text, [float]$X, [float]$Y, [float]$LeaderX = $null, [float]$LeaderY = $null)
    if ($null -ne $LeaderX) {
        Invoke-MCP -Method "createTextNoteWithLeader" -Params @{
            viewId = $ViewId; text = $Text
            textX = $X; textY = $Y; leaderEndX = $LeaderX; leaderEndY = $LeaderY
        }
    } else {
        Invoke-MCP -Method "createTextNote" -Params @{viewId = $ViewId; text = $Text; x = $X; y = $Y}
    }
}

# === Component TypeIds ===
$CMU_8x8x16 = 1748270
$BondBeam = 1748430
$Rebar_5 = 1748194
$BreakLine = 1748208

# === Dimensions (in feet) ===
$cmuWidth = 8/12           # 8" CMU = 0.667'
$courseHeight = 8/12       # 8" course = 0.667'
$numCourses = [Math]::Floor($WallHeight / $courseHeight)
$stuccoThick = 0.75/12     # 3/4" stucco = 0.0625'
$insulThick = 1.0/12       # 1" rigid insulation = 0.0833'
$furrDepth = 1.5/12        # 1.5" furring = 0.125'
$gwbThick = 0.5/12         # 1/2" GWB = 0.0417'

# === COORDINATE SYSTEM ===
# CMU insertion: X at LEFT EDGE, Y at BOTTOM EDGE
# Place at (X, Y) = CMU left-bottom corner

$cmuLeftEdge = $BaseX
$cmuRightEdge = $BaseX + $cmuWidth
$cmuPlacementX = $BaseX

# EXTERIOR
$stuccoRight = $cmuLeftEdge
$stuccoLeft = $stuccoRight - $stuccoThick

# INTERIOR (with insulation)
$insulLeft = $cmuRightEdge
$insulRight = $insulLeft + $insulThick
$furrLeft = $insulRight
$furrRight = $furrLeft + $furrDepth
$gwbLeft = $furrRight
$gwbRight = $gwbLeft + $gwbThick

Write-Host "`nCMU insertion: LEFT-BOTTOM corner"
Write-Host "First CMU at Y=$BaseY (bottom at grade)"

# === CMU Blocks (BOTTOM insertion - place at course bottom, not center) ===
Write-Host "`n=== CMU Blocks ===" -ForegroundColor Yellow
for ($course = 0; $course -lt $numCourses; $course++) {
    # Y = bottom of each course (not center!)
    $y = $BaseY + ($course * $courseHeight)
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU Course $($course+1) bottom at Y=$([Math]::Round($y,2))'" -X $cmuPlacementX -Y $y
}

# === Bond Beam at top (last course) ===
Write-Host "`n=== Bond Beam ===" -ForegroundColor Yellow
$topCourseY = $BaseY + (($numCourses - 1) * $courseHeight)
Place-Component -TypeId $BondBeam -Label "Bond Beam" -X $cmuPlacementX -Y $topCourseY

# === Stucco Rectangle ===
Write-Host "`n=== Stucco Layer (3/4`") ===" -ForegroundColor Yellow
Draw-Line -X1 $stuccoLeft -Y1 $BaseY -X2 $stuccoRight -Y2 $BaseY -Style "1"
Draw-Line -X1 $stuccoRight -Y1 $BaseY -X2 $stuccoRight -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $stuccoRight -Y1 ($BaseY + $WallHeight) -X2 $stuccoLeft -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $stuccoLeft -Y1 ($BaseY + $WallHeight) -X2 $stuccoLeft -Y2 $BaseY -Style "1"
Write-Host "  + Stucco rectangle" -ForegroundColor Green

# === Insulation Rectangle ===
Write-Host "`n=== Insulation Layer (1`") ===" -ForegroundColor Yellow
Draw-Line -X1 $insulLeft -Y1 $BaseY -X2 $insulRight -Y2 $BaseY -Style "1"
Draw-Line -X1 $insulRight -Y1 $BaseY -X2 $insulRight -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $insulRight -Y1 ($BaseY + $WallHeight) -X2 $insulLeft -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $insulLeft -Y1 ($BaseY + $WallHeight) -X2 $insulLeft -Y2 $BaseY -Style "1"
# Hatch
for ($y = $BaseY + 0.25; $y -lt ($BaseY + $WallHeight); $y += 0.25) {
    Draw-Line -X1 $insulLeft -Y1 $y -X2 $insulRight -Y2 ($y - $insulThick) -Style "1"
}
Write-Host "  + Insulation with hatch" -ForegroundColor Green

# === GWB Rectangle ===
Write-Host "`n=== GWB Layer (1/2`") ===" -ForegroundColor Yellow
Draw-Line -X1 $gwbLeft -Y1 $BaseY -X2 $gwbRight -Y2 $BaseY -Style "1"
Draw-Line -X1 $gwbRight -Y1 $BaseY -X2 $gwbRight -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $gwbRight -Y1 ($BaseY + $WallHeight) -X2 $gwbLeft -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $gwbLeft -Y1 ($BaseY + $WallHeight) -X2 $gwbLeft -Y2 $BaseY -Style "1"
Write-Host "  + GWB rectangle" -ForegroundColor Green

# === Furring strips ===
Write-Host "`n=== Furring Strips ===" -ForegroundColor Yellow
$furrSpacing = 24/12
for ($y = $BaseY + $furrSpacing; $y -lt ($BaseY + $WallHeight); $y += $furrSpacing) {
    Draw-Line -X1 $furrLeft -Y1 ($y - 0.04) -X2 $furrRight -Y2 ($y - 0.04) -Style "1"
    Draw-Line -X1 $furrLeft -Y1 ($y + 0.04) -X2 $furrRight -Y2 ($y + 0.04) -Style "1"
}
Write-Host "  + Furring at 24`" o.c." -ForegroundColor Green

# === Rebar ===
Write-Host "`n=== Rebar ===" -ForegroundColor Yellow
$rebarX = $cmuLeftEdge + ($cmuWidth / 2)
for ($y = $BaseY + 2; $y -lt ($BaseY + $WallHeight); $y += 4) {
    Place-Component -TypeId $Rebar_5 -Label "Rebar #5" -X $rebarX -Y $y
}

# === Break Line ===
Write-Host "`n=== Break Line ===" -ForegroundColor Yellow
Place-Component -TypeId $BreakLine -Label "Break Line" -X $rebarX -Y ($BaseY + $WallHeight/2)

# === Grade Line ===
Write-Host "`n=== Grade Line ===" -ForegroundColor Yellow
Draw-Line -X1 ($stuccoLeft - 1) -Y1 $BaseY -X2 ($gwbRight + 1) -Y2 $BaseY -Style "3"
for ($x = $stuccoLeft - 0.8; $x -lt ($gwbRight + 0.8); $x += 0.2) {
    Draw-Line -X1 $x -Y1 $BaseY -X2 ($x - 0.1) -Y2 ($BaseY - 0.1) -Style "1"
}
Write-Host "  + Grade line with hatch" -ForegroundColor Green

# === Annotations ===
Write-Host "`n=== Annotations ===" -ForegroundColor Yellow
$leftTextX = $stuccoLeft - 2.5
$rightTextX = $gwbRight + 1.5

Add-Text -Text "3/4`" STUCCO ON`rMTL. LATH" -X $leftTextX -Y ($BaseY + 6) -LeaderX (($stuccoLeft + $stuccoRight)/2) -LeaderY ($BaseY + 6)
Add-Text -Text "8`" CMU WALL W/`r#5 VERT. @ 48`" O.C." -X $leftTextX -Y ($BaseY + 4) -LeaderX $rebarX -LeaderY ($BaseY + 4)
Add-Text -Text "BOND BEAM W/`r(2) #5 CONT." -X $leftTextX -Y ($BaseY + $WallHeight - 0.5) -LeaderX $rebarX -LeaderY ($BaseY + $WallHeight - $courseHeight/2)
Add-Text -Text "FIN. GRADE" -X $leftTextX -Y ($BaseY + 0.3)

Add-Text -Text "1`" RIGID INSUL." -X $rightTextX -Y ($BaseY + 6) -LeaderX (($insulLeft + $insulRight)/2) -LeaderY ($BaseY + 6)
Add-Text -Text "1/2`" GYP. BD. ON`r1x3 P.T. FURR.`r@ 24`" O.C." -X $rightTextX -Y ($BaseY + 4) -LeaderX (($gwbLeft + $gwbRight)/2) -LeaderY ($BaseY + 4)

$pipe.Close()

Write-Host "`n=== CMU Wall Section Complete ===" -ForegroundColor Green
Write-Host "Location: X=$BaseX"
Write-Host "CMU BOTTOM at grade (Y=$BaseY) - insertion at left-bottom corner"
