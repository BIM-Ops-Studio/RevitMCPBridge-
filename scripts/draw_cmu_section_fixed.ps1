# Draw CMU Wall Section - FIXED ALIGNMENT
# Based on discovery: CMU insertion point is at LEFT EDGE of component, not center

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 30,        # Start fresh at X=30 to avoid overlap
    [float]$BaseY = 0,
    [float]$WallHeight = 8.0
)

Write-Host "=== CMU Wall Section (Fixed Alignment) ===" -ForegroundColor Cyan
Write-Host "Testing CMU insertion point assumption..."

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
    if ($result.success) { Write-Host "  + $Label at X=$([Math]::Round($X,3))" -ForegroundColor Green }
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
$courseHeight = 8/12       # 8" course
$numCourses = [Math]::Floor($WallHeight / $courseHeight)
$stuccoThick = 0.75/12     # 3/4" stucco
$gwbThick = 0.5/12         # 1/2" GWB
$furrDepth = 1.5/12        # 1.5" furring

# === COORDINATE SYSTEM (FIXED) ===
# CMU insertion point appears to be at LEFT EDGE based on visual inspection
# So when we place at X, the CMU spans from X to X+cmuWidth

$cmuLeftEdge = $BaseX                     # CMU left edge at BaseX
$cmuRightEdge = $BaseX + $cmuWidth        # CMU right edge at BaseX + 8"
$cmuPlacementX = $cmuLeftEdge + ($cmuWidth / 2)  # Place at center for centered insertion

# Actually, let me test BOTH assumptions:
# Test A: Assume insertion point is CENTER (original assumption)
# Test B: Assume insertion point is LEFT EDGE

Write-Host "`n=== Testing alignment with CENTER insertion assumption ===" -ForegroundColor Yellow
Write-Host "CMU placed at: X=$cmuPlacementX (center of CMU)"
Write-Host "CMU visual edges SHOULD be at: $cmuLeftEdge to $cmuRightEdge"

# Place one CMU for reference
Place-Component -TypeId $CMU_8x8x16 -Label "Test CMU (center)" -X $cmuPlacementX -Y ($BaseY + 0.333)

# Draw reference lines at expected edges
Write-Host "`nDrawing reference lines at expected CMU edges:" -ForegroundColor Cyan
# Left edge marker (should touch CMU)
Draw-Line -X1 $cmuLeftEdge -Y1 ($BaseY - 0.5) -X2 $cmuLeftEdge -Y2 ($BaseY + 1.5) -Style "3"
Write-Host "  Left edge at X=$([Math]::Round($cmuLeftEdge,3))" -ForegroundColor Magenta
# Right edge marker (should touch CMU)
Draw-Line -X1 $cmuRightEdge -Y1 ($BaseY - 0.5) -X2 $cmuRightEdge -Y2 ($BaseY + 1.5) -Style "3"
Write-Host "  Right edge at X=$([Math]::Round($cmuRightEdge,3))" -ForegroundColor Magenta

# Now draw COMPLETE wall section with this assumption
Write-Host "`n=== Drawing complete wall section ===" -ForegroundColor Yellow

# Stucco on exterior (left of CMU) - should touch cmuLeftEdge
$stuccoLeft = $cmuLeftEdge - $stuccoThick
$stuccoRight = $cmuLeftEdge

# Furring and GWB on interior (right of CMU) - should touch cmuRightEdge
$furrLeft = $cmuRightEdge
$furrRight = $cmuRightEdge + $furrDepth
$gwbLeft = $furrRight
$gwbRight = $furrRight + $gwbThick

Write-Host "Stucco: X=$([Math]::Round($stuccoLeft,3)) to $([Math]::Round($stuccoRight,3))"
Write-Host "CMU: X=$([Math]::Round($cmuLeftEdge,3)) to $([Math]::Round($cmuRightEdge,3))"
Write-Host "Furring: X=$([Math]::Round($furrLeft,3)) to $([Math]::Round($furrRight,3))"
Write-Host "GWB: X=$([Math]::Round($gwbLeft,3)) to $([Math]::Round($gwbRight,3))"

# === CMU Blocks ===
Write-Host "`n=== CMU Blocks ===" -ForegroundColor Yellow
for ($course = 0; $course -lt $numCourses; $course++) {
    $y = $BaseY + ($course * $courseHeight) + ($courseHeight / 2)
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU $($course+1)" -X $cmuPlacementX -Y $y
}

# === Bond Beam at top ===
Write-Host "`n=== Bond Beam ===" -ForegroundColor Yellow
$topY = $BaseY + $WallHeight - ($courseHeight / 2)
Place-Component -TypeId $BondBeam -Label "Bond Beam" -X $cmuPlacementX -Y $topY

# === Stucco Rectangle ===
Write-Host "`n=== Stucco Layer (3/4`") ===" -ForegroundColor Yellow
Draw-Line -X1 $stuccoLeft -Y1 $BaseY -X2 $stuccoRight -Y2 $BaseY -Style "1"
Draw-Line -X1 $stuccoRight -Y1 $BaseY -X2 $stuccoRight -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $stuccoRight -Y1 ($BaseY + $WallHeight) -X2 $stuccoLeft -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $stuccoLeft -Y1 ($BaseY + $WallHeight) -X2 $stuccoLeft -Y2 $BaseY -Style "1"
Write-Host "  + Stucco rectangle from $([Math]::Round($stuccoLeft,3)) to $([Math]::Round($stuccoRight,3))" -ForegroundColor Green

# === GWB Rectangle ===
Write-Host "`n=== GWB Layer (1/2`") ===" -ForegroundColor Yellow
Draw-Line -X1 $gwbLeft -Y1 $BaseY -X2 $gwbRight -Y2 $BaseY -Style "1"
Draw-Line -X1 $gwbRight -Y1 $BaseY -X2 $gwbRight -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $gwbRight -Y1 ($BaseY + $WallHeight) -X2 $gwbLeft -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $gwbLeft -Y1 ($BaseY + $WallHeight) -X2 $gwbLeft -Y2 $BaseY -Style "1"
Write-Host "  + GWB rectangle from $([Math]::Round($gwbLeft,3)) to $([Math]::Round($gwbRight,3))" -ForegroundColor Green

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
for ($y = $BaseY + 2; $y -lt ($BaseY + $WallHeight); $y += 4) {
    Place-Component -TypeId $Rebar_5 -Label "Rebar #5" -X $cmuPlacementX -Y $y
}

# === Break Line ===
Write-Host "`n=== Break Line ===" -ForegroundColor Yellow
Place-Component -TypeId $BreakLine -Label "Break Line" -X $cmuPlacementX -Y ($BaseY + $WallHeight/2)

# === Grade Line ===
Write-Host "`n=== Grade Line ===" -ForegroundColor Yellow
Draw-Line -X1 ($stuccoLeft - 1) -Y1 $BaseY -X2 ($gwbRight + 1) -Y2 $BaseY -Style "3"
Write-Host "  + Grade line" -ForegroundColor Green

# === Annotations ===
Write-Host "`n=== Annotations ===" -ForegroundColor Yellow
$leftTextX = $stuccoLeft - 2
$rightTextX = $gwbRight + 1.5

Add-Text -Text "3/4`" STUCCO" -X $leftTextX -Y ($BaseY + 6) -LeaderX (($stuccoLeft + $stuccoRight)/2) -LeaderY ($BaseY + 6)
Add-Text -Text "8`" CMU W/`r#5 @ 48`" O.C." -X $leftTextX -Y ($BaseY + 4) -LeaderX $cmuPlacementX -LeaderY ($BaseY + 4)
Add-Text -Text "FIN. GRADE" -X $leftTextX -Y ($BaseY + 0.2)
Add-Text -Text "1/2`" GWB ON`r1x3 FURR." -X $rightTextX -Y ($BaseY + 5) -LeaderX (($gwbLeft + $gwbRight)/2) -LeaderY ($BaseY + 5)

$pipe.Close()

Write-Host "`n=== Complete ===" -ForegroundColor Green
Write-Host "CMU wall section drawn at X=$BaseX"
Write-Host "If still misaligned, the CMU insertion point may be at LEFT EDGE"
Write-Host "In that case, we need to adjust cmuPlacementX = cmuLeftEdge (not center)"
