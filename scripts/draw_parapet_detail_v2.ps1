# Clean Parapet Detail v2 - Professional Quality
# FIXED: Properly spaced annotations

param(
    [int]$ViewId = 2239924,
    [float]$BaseX = 15,     # Offset from annotations
    [float]$BaseY = 0       # Roof deck level
)

Write-Host "=== Clean Parapet Detail v2 ===" -ForegroundColor Cyan

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
$parapetCourses = 5           # 5 courses = 3'-4" parapet
$parapetHeight = $parapetCourses * $courseHeight

$stuccoThick = 1/12           # 1" stucco
$roofStructDepth = 9.5/12     # 2x10 joist
$roofInsulThick = 4/12        # 4" rigid insulation
$roofMembraneThick = 0.5/12   # Roofing membrane
$copingWidth = 12/12          # 12" coping
$copingHeight = 2/12          # 2" height
$flashingHeight = 8/12        # 8" base flashing

# === Coordinate System ===
$cmuLeft = $BaseX
$cmuRight = $cmuLeft + $cmuWidth
$cmuCenterX = $cmuLeft + ($cmuWidth / 2)

# Roof extends left
$roofExtent = 4.0

# Exterior (left of CMU)
$stuccoRight = $cmuLeft
$stuccoLeft = $stuccoRight - $stuccoThick

# =============================================
# SECTION 1: CMU PARAPET WALL
# =============================================
Write-Host "`n=== CMU Parapet Wall ===" -ForegroundColor Yellow

# CMU courses (bottom-left insertion)
for ($course = 0; $course -lt $parapetCourses; $course++) {
    $y = $BaseY + ($course * $courseHeight)
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU Course $($course+1)" -X $cmuLeft -Y $y
}

# Bond beam at top course
$bondBeamY = $BaseY + (($parapetCourses - 1) * $courseHeight)
Place-Component -TypeId $BondBeam -Label "Bond Beam" -X $cmuLeft -Y $bondBeamY

# Vertical rebar
Place-Component -TypeId $Rebar_5 -Label "Vert Rebar" -X $cmuCenterX -Y ($BaseY + 1.5)

# =============================================
# SECTION 2: STUCCO FINISH (EXTERIOR)
# =============================================
Write-Host "`n=== Stucco Finish ===" -ForegroundColor Yellow

$stuccoTop = $BaseY + $parapetHeight
Draw-Rect -X1 $stuccoLeft -Y1 $BaseY -X2 $stuccoRight -Y2 $stuccoTop -Style "Thin Lines"
Write-Host "  + Stucco layer" -ForegroundColor Green

# =============================================
# SECTION 3: METAL COPING
# =============================================
Write-Host "`n=== Metal Coping ===" -ForegroundColor Yellow

$copingBottom = $BaseY + $parapetHeight
$copingTop = $copingBottom + $copingHeight
$copingLeft = $stuccoLeft - 2/12    # 2" overhang exterior
$copingRight = $cmuRight + 2/12     # 2" overhang interior

# Coping rectangle (medium line)
Draw-Rect -X1 $copingLeft -Y1 $copingBottom -X2 $copingRight -Y2 $copingTop -Style "Medium Lines"

# Drip edges
Draw-Line -X1 $copingLeft -Y1 $copingBottom -X2 ($copingLeft - 0.5/12) -Y2 ($copingBottom - 1/12) -Style "Thin Lines"
Draw-Line -X1 $copingRight -Y1 $copingBottom -X2 ($copingRight + 0.5/12) -Y2 ($copingBottom - 1/12) -Style "Thin Lines"
Write-Host "  + Metal coping with drips" -ForegroundColor Green

# =============================================
# SECTION 4: ROOF STRUCTURE
# =============================================
Write-Host "`n=== Roof Structure ===" -ForegroundColor Yellow

$joistTop = $BaseY
$joistBottom = $BaseY - $roofStructDepth
$roofLeft = $cmuLeft - $roofExtent

# Roof deck outline
Draw-Rect -X1 $roofLeft -Y1 $joistBottom -X2 $cmuLeft -Y2 $joistTop -Style "Medium Lines"

# Joist symbols at 16" o.c.
$joistSpacing = 16/12
for ($x = $cmuLeft - $joistSpacing; $x -gt $roofLeft + 0.2; $x -= $joistSpacing) {
    # Draw joist cut symbol (X)
    Draw-Line -X1 ($x - 0.1) -Y1 ($joistBottom + 0.1) -X2 ($x + 0.1) -Y2 ($joistTop - 0.1) -Style "Thin Lines"
    Draw-Line -X1 ($x + 0.1) -Y1 ($joistBottom + 0.1) -X2 ($x - 0.1) -Y2 ($joistTop - 0.1) -Style "Thin Lines"
}
Write-Host "  + Roof joists" -ForegroundColor Green

# =============================================
# SECTION 5: RIGID INSULATION
# =============================================
Write-Host "`n=== Rigid Insulation ===" -ForegroundColor Yellow

$insulBottom = $joistTop
$insulTop = $insulBottom + $roofInsulThick

# Insulation rectangle
Draw-Rect -X1 $roofLeft -Y1 $insulBottom -X2 $cmuLeft -Y2 $insulTop -Style "Thin Lines"

# Diagonal hatch (insulation symbol)
for ($x = $roofLeft + 0.3; $x -lt $cmuLeft; $x += 0.3) {
    Draw-Line -X1 $x -Y1 $insulBottom -X2 ($x - $roofInsulThick) -Y2 $insulTop -Style "Thin Lines"
}
Write-Host "  + Rigid insulation" -ForegroundColor Green

# =============================================
# SECTION 6: ROOFING MEMBRANE
# =============================================
Write-Host "`n=== Roofing Membrane ===" -ForegroundColor Yellow

$membraneTop = $insulTop + $roofMembraneThick

# Membrane on roof field (bold line)
Draw-Line -X1 $roofLeft -Y1 $insulTop -X2 $cmuLeft -Y2 $insulTop -Style "Wide Lines"
Draw-Line -X1 $roofLeft -Y1 $membraneTop -X2 $cmuLeft -Y2 $membraneTop -Style "Wide Lines"

# Membrane turns up at parapet (base flashing)
Draw-Line -X1 $cmuLeft -Y1 $insulTop -X2 $cmuLeft -Y2 ($insulTop + $flashingHeight) -Style "Wide Lines"
Draw-Line -X1 ($cmuLeft - $roofMembraneThick) -Y1 $insulTop -X2 ($cmuLeft - $roofMembraneThick) -Y2 ($insulTop + $flashingHeight) -Style "Wide Lines"
Write-Host "  + Roofing membrane" -ForegroundColor Green

# =============================================
# SECTION 7: COUNTER FLASHING
# =============================================
Write-Host "`n=== Counter Flashing ===" -ForegroundColor Yellow

$flashTop = $insulTop + $flashingHeight + 1/12
$counterBottom = $flashTop - 4/12

# Counter flashing profile
Draw-Line -X1 $cmuLeft -Y1 $flashTop -X2 ($cmuLeft - 1.5/12) -Y2 $flashTop -Style "Medium Lines"
Draw-Line -X1 ($cmuLeft - 1.5/12) -Y1 $flashTop -X2 ($cmuLeft - 1.5/12) -Y2 $counterBottom -Style "Medium Lines"
Write-Host "  + Counter flashing" -ForegroundColor Green

# =============================================
# SECTION 8: BREAK LINE
# =============================================
Write-Host "`n=== Break Line ===" -ForegroundColor Yellow
Place-Component -TypeId $BreakLine -Label "Break Line" -X $cmuCenterX -Y ($BaseY + $parapetHeight/2)

# =============================================
# SECTION 9: SECTION CUT LINES
# =============================================
Write-Host "`n=== Section Lines ===" -ForegroundColor Yellow

# Exterior face line
$extFace = $stuccoLeft - 0.5/12
Draw-Line -X1 $extFace -Y1 ($joistBottom - 0.3) -X2 $extFace -Y2 ($copingTop + 0.3) -Style "Wide Lines"

# Interior face line
$intFace = $cmuRight + 0.5/12
Draw-Line -X1 $intFace -Y1 ($joistBottom - 0.3) -X2 $intFace -Y2 ($copingTop + 0.3) -Style "Wide Lines"
Write-Host "  + Section cut lines" -ForegroundColor Green

# =============================================
# SECTION 10: ANNOTATIONS (PROPERLY SPACED)
# =============================================
Write-Host "`n=== Annotations ===" -ForegroundColor Yellow

# Text starts far left and each annotation has DIFFERENT Y position
$textX = $roofLeft - 4   # Plenty of room for text

# Work from top to bottom with consistent spacing
$annY = @{}
$annY['coping'] = $copingTop + 0.5
$annY['bondbeam'] = $BaseY + $parapetHeight - 0.3
$annY['parapet'] = $BaseY + ($parapetHeight * 0.5)
$annY['counter'] = $insulTop + $flashingHeight - 0.2
$annY['base'] = $insulTop + ($flashingHeight * 0.3)
$annY['membrane'] = $insulTop + 0.2
$annY['insul'] = $insulBottom + ($roofInsulThick / 2)
$annY['struct'] = $joistBottom + ($roofStructDepth / 2)
$annY['stucco'] = $BaseY + 0.5

# Draw annotations with proper spacing
Add-Text -Text "METAL COPING W/ CONT. CLEAT" -X $textX -Y $annY['coping'] -LeaderX (($copingLeft + $copingRight)/2) -LeaderY ($copingTop - $copingHeight/2)

Add-Text -Text "BOND BEAM W/ (2) #5 CONT." -X $textX -Y $annY['bondbeam'] -LeaderX $cmuCenterX -LeaderY ($BaseY + $parapetHeight - $courseHeight/2)

Add-Text -Text "8`" CMU PARAPET W/ #5 @ 48`" O.C." -X $textX -Y $annY['parapet'] -LeaderX $cmuCenterX -LeaderY ($BaseY + $parapetHeight * 0.5)

Add-Text -Text "COUNTER FLASH. IN REGLET" -X $textX -Y $annY['counter'] -LeaderX ($cmuLeft - 0.75/12) -LeaderY ($flashTop - 2/12)

Add-Text -Text "BASE FLASHING" -X $textX -Y $annY['base'] -LeaderX ($cmuLeft - 0.25/12) -LeaderY ($insulTop + $flashingHeight * 0.3)

Add-Text -Text "ROOFING MEMBRANE" -X $textX -Y $annY['membrane'] -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY $membraneTop

Add-Text -Text "4`" RIGID INSULATION" -X $textX -Y $annY['insul'] -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY ($insulBottom + $roofInsulThick/2)

Add-Text -Text "ROOF STRUCTURE @ 16`" O.C." -X $textX -Y $annY['struct'] -LeaderX (($roofLeft + $cmuLeft)/2) -LeaderY ($joistBottom + $roofStructDepth/2)

Add-Text -Text "1`" STUCCO ON MTL. LATH" -X $textX -Y $annY['stucco'] -LeaderX (($stuccoLeft + $stuccoRight)/2) -LeaderY ($BaseY + 0.5)

$pipe.Close()

Write-Host "`n=== Clean Parapet Detail v2 Complete ===" -ForegroundColor Green
Write-Host "Location: X=$BaseX"
Write-Host "Parapet: $parapetCourses courses ($([Math]::Round($parapetHeight, 2)) ft)"
Write-Host "Annotations: Vertically stacked on LEFT side"
