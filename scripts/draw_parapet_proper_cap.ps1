# Clean Parapet Detail with PROPER CAP PROFILE
# Cap drawn with lines (not rectangle)
# Section lines trimmed to proper length

param(
    [int]$ViewId = 2240191,
    [float]$BaseX = 15,
    [float]$BaseY = 0
)

Write-Host "=== Parapet Detail with Proper Cap ===" -ForegroundColor Cyan

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(15000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 5 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 150
    return ($reader.ReadLine() | ConvertFrom-Json)
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
}

function Draw-Line {
    param([float]$X1, [float]$Y1, [float]$X2, [float]$Y2, [string]$Style = "Thin Lines")
    Invoke-MCP -Method "createDetailLineInDraftingView" -Params @{
        viewId = $ViewId
        startX = $X1; startY = $Y1; endX = $X2; endY = $Y2
        lineStyle = $Style
    } | Out-Null
}

function Draw-Rect {
    param([float]$X1, [float]$Y1, [float]$X2, [float]$Y2, [string]$Style = "Thin Lines")
    Draw-Line -X1 $X1 -Y1 $Y1 -X2 $X2 -Y2 $Y1 -Style $Style
    Draw-Line -X1 $X2 -Y1 $Y1 -X2 $X2 -Y2 $Y2 -Style $Style
    Draw-Line -X1 $X2 -Y1 $Y2 -X2 $X1 -Y2 $Y2 -Style $Style
    Draw-Line -X1 $X1 -Y1 $Y2 -X2 $X1 -Y2 $Y1 -Style $Style
}

function Add-Text {
    param([string]$Text, [float]$X, [float]$Y, [float]$LeaderX, [float]$LeaderY)
    Invoke-MCP -Method "createTextNoteWithLeader" -Params @{
        viewId = $ViewId; text = $Text
        textX = $X; textY = $Y; leaderEndX = $LeaderX; leaderEndY = $LeaderY
    }
}

# === Component TypeIds ===
$CMU_8x8x16 = 1748270
$BondBeam = 1748430
$Rebar_5 = 1748194
$BreakLine = 1748208

# === Dimensions (feet) ===
$cmuWidth = 8/12              # 8" CMU
$courseHeight = 8/12          # 8" course
$parapetCourses = 5
$parapetHeight = $parapetCourses * $courseHeight

$stuccoThick = 1/12           # 1" stucco
$roofStructDepth = 9.5/12     # 2x10 joist
$roofInsulThick = 4/12        # 4" rigid insulation
$flashingHeight = 8/12        # 8" base flashing

# Cap dimensions (matching the reference)
$capTopWidth = 14/12          # 14" total width at top
$capHeight = 3/12             # 3" height
$capDripDrop = 1.5/12         # 1.5" drip drop
$capDripWidth = 0.5/12        # 0.5" drip width

# === Coordinate System ===
$cmuLeft = $BaseX
$cmuRight = $cmuLeft + $cmuWidth
$cmuCenterX = $cmuLeft + ($cmuWidth / 2)
$roofExtent = 4.0
$stuccoRight = $cmuLeft
$stuccoLeft = $stuccoRight - $stuccoThick

# Key Y positions
$parapetTop = $BaseY + $parapetHeight
$joistTop = $BaseY
$joistBottom = $BaseY - $roofStructDepth
$roofLeft = $cmuLeft - $roofExtent
$insulBottom = $joistTop
$insulTop = $insulBottom + $roofInsulThick
$membraneTop = $insulTop + 0.5/12
$flashTop = $insulTop + $flashingHeight + 1/12

# Cap positions
$capCenterX = $cmuCenterX
$capLeft = $capCenterX - ($capTopWidth / 2)
$capRight = $capCenterX + ($capTopWidth / 2)
$capBottom = $parapetTop
$capTop = $capBottom + $capHeight

# =============================================
# CMU PARAPET WALL
# =============================================
Write-Host "`n=== CMU Parapet ===" -ForegroundColor Yellow
for ($course = 0; $course -lt $parapetCourses; $course++) {
    $y = $BaseY + ($course * $courseHeight)
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU $($course+1)" -X $cmuLeft -Y $y
}
$bondBeamY = $BaseY + (($parapetCourses - 1) * $courseHeight)
Place-Component -TypeId $BondBeam -Label "Bond Beam" -X $cmuLeft -Y $bondBeamY
Place-Component -TypeId $Rebar_5 -Label "Rebar" -X $cmuCenterX -Y ($BaseY + 1.5)

# =============================================
# STUCCO FINISH
# =============================================
Write-Host "`n=== Stucco ===" -ForegroundColor Yellow
Draw-Rect -X1 $stuccoLeft -Y1 $BaseY -X2 $stuccoRight -Y2 $parapetTop -Style "Thin Lines"
Write-Host "  + Stucco" -ForegroundColor Green

# =============================================
# PROPER METAL CAP PROFILE (drawn with lines)
# =============================================
Write-Host "`n=== Metal Cap Profile ===" -ForegroundColor Yellow

# Cap shape: flat top with angled sides and drip edges
# Interior drip (right side)
$dripRightX = $capRight + $capDripWidth
$dripRightBottom = $capBottom - $capDripDrop

# Exterior drip (left side)
$dripLeftX = $capLeft - $capDripWidth
$dripLeftBottom = $capBottom - $capDripDrop

# Draw cap outline (medium lines for visibility)
# Top surface
Draw-Line -X1 $capLeft -Y1 $capTop -X2 $capRight -Y2 $capTop -Style "Medium Lines"

# Left side (exterior) - angled
Draw-Line -X1 $capLeft -Y1 $capTop -X2 ($stuccoLeft - 1/12) -Y2 $capBottom -Style "Medium Lines"

# Right side (interior) - angled
Draw-Line -X1 $capRight -Y1 $capTop -X2 ($cmuRight + 1/12) -Y2 $capBottom -Style "Medium Lines"

# Bottom edges
Draw-Line -X1 ($stuccoLeft - 1/12) -Y1 $capBottom -X2 $dripLeftX -Y2 $capBottom -Style "Medium Lines"
Draw-Line -X1 ($cmuRight + 1/12) -Y1 $capBottom -X2 $dripRightX -Y2 $capBottom -Style "Medium Lines"

# Drip edges (exterior)
Draw-Line -X1 $dripLeftX -Y1 $capBottom -X2 $dripLeftX -Y2 $dripLeftBottom -Style "Medium Lines"
Draw-Line -X1 $dripLeftX -Y1 $dripLeftBottom -X2 ($dripLeftX + 0.25/12) -Y2 ($dripLeftBottom + 0.25/12) -Style "Medium Lines"

# Drip edges (interior)
Draw-Line -X1 $dripRightX -Y1 $capBottom -X2 $dripRightX -Y2 $dripRightBottom -Style "Medium Lines"
Draw-Line -X1 $dripRightX -Y1 $dripRightBottom -X2 ($dripRightX - 0.25/12) -Y2 ($dripRightBottom + 0.25/12) -Style "Medium Lines"

# Cap center support/cleat line
Draw-Line -X1 $cmuCenterX -Y1 $capTop -X2 $cmuCenterX -Y2 $capBottom -Style "Thin Lines"

Write-Host "  + Metal cap with drip edges" -ForegroundColor Green

# =============================================
# ROOF ASSEMBLY
# =============================================
Write-Host "`n=== Roof Assembly ===" -ForegroundColor Yellow

# Roof structure
Draw-Rect -X1 $roofLeft -Y1 $joistBottom -X2 $cmuLeft -Y2 $joistTop -Style "Medium Lines"
$joistSpacing = 16/12
for ($x = $cmuLeft - $joistSpacing; $x -gt $roofLeft + 0.2; $x -= $joistSpacing) {
    Draw-Line -X1 ($x - 0.1) -Y1 ($joistBottom + 0.1) -X2 ($x + 0.1) -Y2 ($joistTop - 0.1) -Style "Thin Lines"
    Draw-Line -X1 ($x + 0.1) -Y1 ($joistBottom + 0.1) -X2 ($x - 0.1) -Y2 ($joistTop - 0.1) -Style "Thin Lines"
}
Write-Host "  + Roof joists" -ForegroundColor Green

# Insulation
Draw-Rect -X1 $roofLeft -Y1 $insulBottom -X2 $cmuLeft -Y2 $insulTop -Style "Thin Lines"
for ($x = $roofLeft + 0.3; $x -lt $cmuLeft; $x += 0.3) {
    Draw-Line -X1 $x -Y1 $insulBottom -X2 ($x - $roofInsulThick) -Y2 $insulTop -Style "Thin Lines"
}
Write-Host "  + Insulation" -ForegroundColor Green

# Roofing membrane
Draw-Line -X1 $roofLeft -Y1 $insulTop -X2 $cmuLeft -Y2 $insulTop -Style "Wide Lines"
Draw-Line -X1 $roofLeft -Y1 $membraneTop -X2 $cmuLeft -Y2 $membraneTop -Style "Wide Lines"

# Base flashing turn-up
Draw-Line -X1 $cmuLeft -Y1 $insulTop -X2 $cmuLeft -Y2 ($insulTop + $flashingHeight) -Style "Wide Lines"
Draw-Line -X1 ($cmuLeft - 0.5/12) -Y1 $insulTop -X2 ($cmuLeft - 0.5/12) -Y2 ($insulTop + $flashingHeight) -Style "Wide Lines"
Write-Host "  + Membrane & flashing" -ForegroundColor Green

# Counter flashing
Draw-Line -X1 $cmuLeft -Y1 $flashTop -X2 ($cmuLeft - 1.5/12) -Y2 $flashTop -Style "Medium Lines"
Draw-Line -X1 ($cmuLeft - 1.5/12) -Y1 $flashTop -X2 ($cmuLeft - 1.5/12) -Y2 ($flashTop - 4/12) -Style "Medium Lines"
Write-Host "  + Counter flash" -ForegroundColor Green

# =============================================
# SECTION CUT LINES (TRIMMED PROPERLY)
# =============================================
Write-Host "`n=== Section Lines (trimmed) ===" -ForegroundColor Yellow

# Exterior cut line - from drip bottom to roof bottom only
$extCutX = $stuccoLeft - 1/12
Draw-Line -X1 $extCutX -Y1 $joistBottom -X2 $extCutX -Y2 $dripLeftBottom -Style "Wide Lines"

# Interior cut line - from roof bottom to cap bottom only
$intCutX = $cmuRight + 0.5/12
Draw-Line -X1 $intCutX -Y1 $joistBottom -X2 $intCutX -Y2 $dripRightBottom -Style "Wide Lines"

Write-Host "  + Section lines (properly trimmed)" -ForegroundColor Green

# Break line
Place-Component -TypeId $BreakLine -Label "Break" -X $cmuCenterX -Y ($BaseY + $parapetHeight/2)

# =============================================
# ANNOTATIONS
# =============================================
Write-Host "`n=== Annotations ===" -ForegroundColor Yellow

$textX = $roofLeft - 5
$spacing = 0.55
$topY = $capTop + 0.3
$annNum = 0

Add-Text -Text "METAL COPING W/ CONT. CLEAT" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX $capCenterX -LeaderY ($capTop - $capHeight/2)
$annNum++

Add-Text -Text "BOND BEAM W/ (2) #5 CONT." -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX $cmuCenterX -LeaderY ($parapetTop - $courseHeight/2)
$annNum++

Add-Text -Text "8`" CMU PARAPET W/ #5 @ 48`" O.C." -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX $cmuCenterX -LeaderY ($BaseY + $parapetHeight * 0.5)
$annNum++

Add-Text -Text "COUNTER FLASHING IN REGLET" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX ($cmuLeft - 0.75/12) -LeaderY ($flashTop - 2/12)
$annNum++

Add-Text -Text "BASE FLASHING" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX ($cmuLeft - 0.25/12) -LeaderY ($insulTop + $flashingHeight/2)
$annNum++

Add-Text -Text "ROOFING MEMBRANE" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY $membraneTop
$annNum++

Add-Text -Text "4`" RIGID INSULATION" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY ($insulBottom + $roofInsulThick/2)
$annNum++

Add-Text -Text "ROOF STRUCTURE @ 16`" O.C." -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY ($joistBottom + $roofStructDepth/2)
$annNum++

Add-Text -Text "1`" STUCCO ON MTL. LATH" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($stuccoLeft + $stuccoRight)/2) -LeaderY ($BaseY + 0.5)

$pipe.Close()

Write-Host "`n=== Parapet Detail with Proper Cap Complete ===" -ForegroundColor Green
Write-Host "Cap: Proper profile with drip edges"
Write-Host "Section lines: Trimmed to detail bounds"
