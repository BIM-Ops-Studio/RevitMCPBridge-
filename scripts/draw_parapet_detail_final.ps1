# Clean Parapet Detail - FINAL VERSION
# Properly stacked annotations with consistent spacing

param(
    [int]$ViewId = 2239996,
    [float]$BaseX = 15,
    [float]$BaseY = 0
)

Write-Host "=== Clean Parapet Detail - FINAL ===" -ForegroundColor Cyan

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
    param([int]$TypeId, [string]$Label, [float]$X, [float]$Y, [float]$Rotation = 0)
    $result = Invoke-MCP -Method "placeDetailComponent" -Params @{
        viewId = $ViewId
        componentTypeId = $TypeId
        location = @{x = $X; y = $Y; z = 0}
        rotation = $Rotation
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

# === Dimensions (feet) ===
$cmuWidth = 8/12              # 8" CMU
$courseHeight = 8/12          # 8" course
$parapetCourses = 5           # 5 courses
$parapetHeight = $parapetCourses * $courseHeight

$stuccoThick = 1/12           # 1" stucco
$roofStructDepth = 9.5/12     # 2x10 joist
$roofInsulThick = 4/12        # 4" rigid insulation
$copingHeight = 2/12          # 2" height
$flashingHeight = 8/12        # 8" base flashing

# === Coordinate System ===
$cmuLeft = $BaseX
$cmuRight = $cmuLeft + $cmuWidth
$cmuCenterX = $cmuLeft + ($cmuWidth / 2)
$roofExtent = 4.0
$stuccoRight = $cmuLeft
$stuccoLeft = $stuccoRight - $stuccoThick

# Key Y positions for leaders
$copingBottom = $BaseY + $parapetHeight
$copingTop = $copingBottom + $copingHeight
$copingLeft = $stuccoLeft - 2/12
$copingRight = $cmuRight + 2/12
$joistTop = $BaseY
$joistBottom = $BaseY - $roofStructDepth
$roofLeft = $cmuLeft - $roofExtent
$insulBottom = $joistTop
$insulTop = $insulBottom + $roofInsulThick
$membraneTop = $insulTop + 0.5/12
$flashTop = $insulTop + $flashingHeight + 1/12

# =============================================
# DRAW ALL DETAIL COMPONENTS
# =============================================

Write-Host "`n=== CMU Parapet ===" -ForegroundColor Yellow
for ($course = 0; $course -lt $parapetCourses; $course++) {
    $y = $BaseY + ($course * $courseHeight)
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU $($course+1)" -X $cmuLeft -Y $y
}
$bondBeamY = $BaseY + (($parapetCourses - 1) * $courseHeight)
Place-Component -TypeId $BondBeam -Label "Bond Beam" -X $cmuLeft -Y $bondBeamY
Place-Component -TypeId $Rebar_5 -Label "Rebar" -X $cmuCenterX -Y ($BaseY + 1.5)

Write-Host "`n=== Finishes ===" -ForegroundColor Yellow
Draw-Rect -X1 $stuccoLeft -Y1 $BaseY -X2 $stuccoRight -Y2 ($BaseY + $parapetHeight) -Style "Thin Lines"
Write-Host "  + Stucco" -ForegroundColor Green

Write-Host "`n=== Metal Coping ===" -ForegroundColor Yellow
Draw-Rect -X1 $copingLeft -Y1 $copingBottom -X2 $copingRight -Y2 $copingTop -Style "Medium Lines"
Draw-Line -X1 $copingLeft -Y1 $copingBottom -X2 ($copingLeft - 0.5/12) -Y2 ($copingBottom - 1/12) -Style "Thin Lines"
Draw-Line -X1 $copingRight -Y1 $copingBottom -X2 ($copingRight + 0.5/12) -Y2 ($copingBottom - 1/12) -Style "Thin Lines"
Write-Host "  + Coping" -ForegroundColor Green

Write-Host "`n=== Roof Assembly ===" -ForegroundColor Yellow
Draw-Rect -X1 $roofLeft -Y1 $joistBottom -X2 $cmuLeft -Y2 $joistTop -Style "Medium Lines"
$joistSpacing = 16/12
for ($x = $cmuLeft - $joistSpacing; $x -gt $roofLeft + 0.2; $x -= $joistSpacing) {
    Draw-Line -X1 ($x - 0.1) -Y1 ($joistBottom + 0.1) -X2 ($x + 0.1) -Y2 ($joistTop - 0.1) -Style "Thin Lines"
    Draw-Line -X1 ($x + 0.1) -Y1 ($joistBottom + 0.1) -X2 ($x - 0.1) -Y2 ($joistTop - 0.1) -Style "Thin Lines"
}
Write-Host "  + Roof joists" -ForegroundColor Green

Draw-Rect -X1 $roofLeft -Y1 $insulBottom -X2 $cmuLeft -Y2 $insulTop -Style "Thin Lines"
for ($x = $roofLeft + 0.3; $x -lt $cmuLeft; $x += 0.3) {
    Draw-Line -X1 $x -Y1 $insulBottom -X2 ($x - $roofInsulThick) -Y2 $insulTop -Style "Thin Lines"
}
Write-Host "  + Insulation" -ForegroundColor Green

Draw-Line -X1 $roofLeft -Y1 $insulTop -X2 $cmuLeft -Y2 $insulTop -Style "Wide Lines"
Draw-Line -X1 $roofLeft -Y1 $membraneTop -X2 $cmuLeft -Y2 $membraneTop -Style "Wide Lines"
Draw-Line -X1 $cmuLeft -Y1 $insulTop -X2 $cmuLeft -Y2 ($insulTop + $flashingHeight) -Style "Wide Lines"
Draw-Line -X1 ($cmuLeft - 0.5/12) -Y1 $insulTop -X2 ($cmuLeft - 0.5/12) -Y2 ($insulTop + $flashingHeight) -Style "Wide Lines"
Write-Host "  + Membrane & flashing" -ForegroundColor Green

Draw-Line -X1 $cmuLeft -Y1 $flashTop -X2 ($cmuLeft - 1.5/12) -Y2 $flashTop -Style "Medium Lines"
Draw-Line -X1 ($cmuLeft - 1.5/12) -Y1 $flashTop -X2 ($cmuLeft - 1.5/12) -Y2 ($flashTop - 4/12) -Style "Medium Lines"
Write-Host "  + Counter flash" -ForegroundColor Green

Write-Host "`n=== Section Lines ===" -ForegroundColor Yellow
$extFace = $stuccoLeft - 0.5/12
$intFace = $cmuRight + 0.5/12
Draw-Line -X1 $extFace -Y1 ($joistBottom - 0.3) -X2 $extFace -Y2 ($copingTop + 0.3) -Style "Wide Lines"
Draw-Line -X1 $intFace -Y1 ($joistBottom - 0.3) -X2 $intFace -Y2 ($copingTop + 0.3) -Style "Wide Lines"
Write-Host "  + Cut lines" -ForegroundColor Green

Place-Component -TypeId $BreakLine -Label "Break" -X $cmuCenterX -Y ($BaseY + $parapetHeight/2)

# =============================================
# ANNOTATIONS - Stacked vertically with fixed spacing
# =============================================
Write-Host "`n=== Annotations ===" -ForegroundColor Yellow

# All text at same X, spaced 0.6' apart vertically
$textX = $roofLeft - 5
$spacing = 0.55

# Start from top of detail and work down
$topY = $copingTop + 0.5
$annNum = 0

# 1. METAL COPING (at top)
Add-Text -Text "METAL COPING W/ CONT. CLEAT" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($copingLeft + $copingRight)/2) -LeaderY ($copingTop - $copingHeight/2)
$annNum++

# 2. BOND BEAM
Add-Text -Text "BOND BEAM W/ (2) #5 CONT." -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX $cmuCenterX -LeaderY ($BaseY + $parapetHeight - $courseHeight/2)
$annNum++

# 3. CMU PARAPET
Add-Text -Text "8`" CMU PARAPET W/ #5 @ 48`" O.C." -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX $cmuCenterX -LeaderY ($BaseY + $parapetHeight * 0.5)
$annNum++

# 4. COUNTER FLASHING
Add-Text -Text "COUNTER FLASHING IN REGLET" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX ($cmuLeft - 0.75/12) -LeaderY ($flashTop - 2/12)
$annNum++

# 5. BASE FLASHING
Add-Text -Text "BASE FLASHING" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX ($cmuLeft - 0.25/12) -LeaderY ($insulTop + $flashingHeight/2)
$annNum++

# 6. ROOFING MEMBRANE
Add-Text -Text "ROOFING MEMBRANE" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY $membraneTop
$annNum++

# 7. RIGID INSULATION
Add-Text -Text "4`" RIGID INSULATION" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY ($insulBottom + $roofInsulThick/2)
$annNum++

# 8. ROOF STRUCTURE
Add-Text -Text "ROOF STRUCTURE @ 16`" O.C." -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY ($joistBottom + $roofStructDepth/2)
$annNum++

# 9. STUCCO (at bottom)
Add-Text -Text "1`" STUCCO ON MTL. LATH" -X $textX -Y ($topY - ($annNum * $spacing)) -LeaderX (($stuccoLeft + $stuccoRight)/2) -LeaderY ($BaseY + 0.5)

$pipe.Close()

Write-Host "`n=== Parapet Detail FINAL Complete ===" -ForegroundColor Green
Write-Host "View: PARAPET DETAIL - FINAL"
Write-Host "9 annotations stacked vertically"
