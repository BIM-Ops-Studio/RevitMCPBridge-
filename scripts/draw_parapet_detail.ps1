# Draw Parapet Detail - Complete Assembly
# Shows roof/wall intersection with all components

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 70,
    [float]$BaseY = 0        # Roof deck level (not grade)
)

Write-Host "=== Parapet Detail ===" -ForegroundColor Cyan

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
    param([float]$X1, [float]$Y1, [float]$X2, [float]$Y2, [string]$Style = "1")
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
$Lumber_2x6 = 1389320
$Rebar_5 = 1748194
$BreakLine = 1748208
$MetalChannel = 1389035
$MetalStud = 1748396

# === Dimensions (feet) ===
$cmuWidth = 8/12             # 8" CMU
$courseHeight = 8/12         # 8" course
$parapetHeight = 3.0         # 3'-0" parapet above roof
$roofStructDepth = 9.5/12    # 2x10 joist = 9.25" + sheathing
$roofInsulThick = 4/12       # 4" rigid insulation
$roofMembraneThick = 0.5/12  # Roofing membrane
$copingWidth = 12/12         # 12" metal coping
$copingHeight = 2/12         # 2" coping height
$flashingHeight = 8/12       # 8" base flashing
$counterFlashHeight = 4/12   # 4" counter flashing
$ceilingDepth = 1.5/12       # Ceiling space

# === Coordinate System ===
# BaseY = roof deck level (top of structure)
# CMU insertion at bottom-left corner

$cmuLeft = $BaseX
$cmuRight = $BaseX + $cmuWidth

# Roof extends to left of CMU
$roofExtent = 4.0  # Roof extends 4' to left

Write-Host "`n=== CMU Parapet Wall ===" -ForegroundColor Yellow
# CMU courses from roof deck up
$numCourses = [Math]::Ceiling($parapetHeight / $courseHeight)
for ($course = 0; $course -lt $numCourses; $course++) {
    $y = $BaseY + ($course * $courseHeight)
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU Course $($course+1)" -X $cmuLeft -Y $y
}

Write-Host "`n=== Bond Beam at Top ===" -ForegroundColor Yellow
$bondBeamY = $BaseY + (($numCourses - 1) * $courseHeight)
Place-Component -TypeId $BondBeam -Label "Bond Beam" -X $cmuLeft -Y $bondBeamY

Write-Host "`n=== Rebar ===" -ForegroundColor Yellow
$rebarX = $cmuLeft + ($cmuWidth / 2)
Place-Component -TypeId $Rebar_5 -Label "Vert Rebar" -X $rebarX -Y ($BaseY + 1.5)

Write-Host "`n=== Metal Coping ===" -ForegroundColor Yellow
$copingTop = $BaseY + $parapetHeight + $copingHeight
$copingLeft = $cmuLeft - 2/12  # 2" overhang exterior
$copingRight = $cmuRight + 2/12  # 2" overhang interior
# Draw coping profile
Draw-Rect -X1 $copingLeft -Y1 ($copingTop - $copingHeight) -X2 $copingRight -Y2 $copingTop -Style "3"
# Drip edges
Draw-Line -X1 $copingLeft -Y1 ($copingTop - $copingHeight) -X2 ($copingLeft - 0.5/12) -Y2 ($copingTop - $copingHeight - 1/12) -Style "1"
Draw-Line -X1 $copingRight -Y1 ($copingTop - $copingHeight) -X2 ($copingRight + 0.5/12) -Y2 ($copingTop - $copingHeight - 1/12) -Style "1"
Write-Host "  + Metal coping" -ForegroundColor Green

Write-Host "`n=== Roof Structure ===" -ForegroundColor Yellow
# Roof joists (horizontal, below roof deck)
$joistTop = $BaseY
$joistBottom = $BaseY - $roofStructDepth
$joistSpacing = 16/12  # 16" o.c.
for ($x = $cmuLeft - $joistSpacing; $x -gt ($cmuLeft - $roofExtent); $x -= $joistSpacing) {
    Place-Component -TypeId $Lumber_2x6 -Label "Roof Joist" -X $x -Y $joistBottom -Rotation 0
}
# Draw joist outline (simplified)
Draw-Rect -X1 ($cmuLeft - $roofExtent) -Y1 $joistBottom -X2 $cmuLeft -Y2 $joistTop -Style "1"
Write-Host "  + Roof structure" -ForegroundColor Green

Write-Host "`n=== Roof Insulation ===" -ForegroundColor Yellow
$insulTop = $joistTop + $roofInsulThick
$insulLeft = $cmuLeft - $roofExtent
$insulRight = $cmuLeft  # Stops at CMU
Draw-Rect -X1 $insulLeft -Y1 $joistTop -X2 $insulRight -Y2 $insulTop -Style "1"
# Diagonal hatch for insulation
for ($x = $insulLeft + 0.25; $x -lt $insulRight; $x += 0.25) {
    Draw-Line -X1 $x -Y1 $joistTop -X2 ($x - $roofInsulThick) -Y2 $insulTop -Style "1"
}
Write-Host "  + Rigid insulation" -ForegroundColor Green

Write-Host "`n=== Roofing Membrane ===" -ForegroundColor Yellow
$membraneTop = $insulTop + $roofMembraneThick
# Membrane on field
Draw-Line -X1 $insulLeft -Y1 $insulTop -X2 $cmuLeft -Y2 $insulTop -Style "3"
Draw-Line -X1 $insulLeft -Y1 $membraneTop -X2 $cmuLeft -Y2 $membraneTop -Style "3"
# Membrane turns up at parapet (base flashing)
Draw-Line -X1 $cmuLeft -Y1 $insulTop -X2 $cmuLeft -Y2 ($insulTop + $flashingHeight) -Style "3"
Write-Host "  + Roofing membrane" -ForegroundColor Green

Write-Host "`n=== Flashing ===" -ForegroundColor Yellow
# Base flashing (membrane turn-up)
$flashingTop = $insulTop + $flashingHeight
Draw-Line -X1 ($cmuLeft - 1/12) -Y1 $insulTop -X2 ($cmuLeft - 1/12) -Y2 $flashingTop -Style "1"
# Counter flashing (reglet in CMU)
$counterTop = $flashingTop + 1/12
$counterBottom = $counterTop - $counterFlashHeight
Draw-Line -X1 $cmuLeft -Y1 $counterTop -X2 ($cmuLeft - 1.5/12) -Y2 $counterTop -Style "1"
Draw-Line -X1 ($cmuLeft - 1.5/12) -Y1 $counterTop -X2 ($cmuLeft - 1.5/12) -Y2 $counterBottom -Style "1"
Write-Host "  + Counter flashing" -ForegroundColor Green

Write-Host "`n=== Interior Ceiling ===" -ForegroundColor Yellow
$ceilingY = $joistBottom - $ceilingDepth
# Ceiling line
Draw-Line -X1 ($cmuRight) -Y1 $ceilingY -X2 ($cmuRight + 3) -Y2 $ceilingY -Style "1"
Draw-Line -X1 ($cmuRight) -Y1 ($ceilingY - 0.5/12) -X2 ($cmuRight + 3) -Y2 ($ceilingY - 0.5/12) -Style "1"
# Metal channel at wall
Place-Component -TypeId $MetalChannel -Label "Ceiling Channel" -X $cmuRight -Y $ceilingY
Write-Host "  + Ceiling" -ForegroundColor Green

Write-Host "`n=== Break Line ===" -ForegroundColor Yellow
Place-Component -TypeId $BreakLine -Label "Break Line" -X $rebarX -Y ($BaseY + $parapetHeight/2)

Write-Host "`n=== Section Cut Lines ===" -ForegroundColor Yellow
# Exterior face line (beyond stucco)
$extLine = $cmuLeft - 2/12
Draw-Line -X1 $extLine -Y1 ($BaseY - $roofStructDepth - 0.5) -X2 $extLine -Y2 ($copingTop + 0.2) -Style "3"
# Interior face line
$intLine = $cmuRight + 0.5/12
Draw-Line -X1 $intLine -Y1 ($ceilingY - 0.3) -X2 $intLine -Y2 ($copingTop + 0.2) -Style "3"
Write-Host "  + Section lines" -ForegroundColor Green

Write-Host "`n=== Annotations ===" -ForegroundColor Yellow
$leftTextX = $cmuLeft - 3
$rightTextX = $cmuRight + 2

Add-Text -Text "METAL COPING W/`rCONT. CLEAT" -X $leftTextX -Y ($copingTop - 0.3) -LeaderX (($copingLeft + $copingRight)/2) -LeaderY ($copingTop - $copingHeight/2)
Add-Text -Text "8`" CMU PARAPET`rW/ BOND BEAM" -X $leftTextX -Y ($BaseY + 1.5) -LeaderX $rebarX -LeaderY ($BaseY + 1.5)
Add-Text -Text "COUNTER FLASH.`rIN REGLET" -X $leftTextX -Y $counterTop -LeaderX ($cmuLeft - 0.75/12) -LeaderY ($counterTop - $counterFlashHeight/2)
Add-Text -Text "BASE FLASH." -X $leftTextX -Y ($insulTop + $flashingHeight/2) -LeaderX ($cmuLeft - 0.5/12) -LeaderY ($insulTop + $flashingHeight/2)
Add-Text -Text "4`" RIGID INSUL." -X $leftTextX -Y ($joistTop + $roofInsulThick/2) -LeaderX (($insulLeft + $insulRight)/2) -LeaderY ($joistTop + $roofInsulThick/2)
Add-Text -Text "ROOF STRUCT.`r@ 16`" O.C." -X $leftTextX -Y ($joistBottom + $roofStructDepth/2) -LeaderX ($cmuLeft - 1.5) -LeaderY ($joistBottom + $roofStructDepth/2)
Add-Text -Text "5/8`" GYP. BD.`rCEILING" -X $rightTextX -Y $ceilingY -LeaderX ($cmuRight + 1.5) -LeaderY ($ceilingY - 0.25/12)

$pipe.Close()

Write-Host "`n=== Parapet Detail Complete ===" -ForegroundColor Green
Write-Host "Location: X=$BaseX"
Write-Host "Parapet height: $parapetHeight ft above roof"
Write-Host "Components: CMU, Bond Beam, Coping, Flashing, Insulation, Structure"
