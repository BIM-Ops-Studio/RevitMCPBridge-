# Draw CMU Wall Section - ALIGNED VERSION
# Fixed coordinate system: CMU center is the reference point

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 0,
    [float]$BaseY = 0,
    [float]$WallHeight = 8.0
)

Write-Host "=== CMU Wall Section (Aligned) ===" -ForegroundColor Cyan

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
$cmuWidth = 8/12           # 8" CMU
$cmuHalf = $cmuWidth / 2   # 4" half-width
$courseHeight = 8/12       # 8" course
$numCourses = [Math]::Floor($WallHeight / $courseHeight)
$stuccoThick = 0.75/12     # 3/4" stucco
$gwbThick = 0.5/12         # 1/2" GWB
$furrDepth = 1.5/12        # 1.5" furring

# === COORDINATE SYSTEM ===
# CMU center is at BaseX. Left edge = BaseX - cmuHalf, Right edge = BaseX + cmuHalf
$cmuCenterX = $BaseX
$cmuLeftEdge = $cmuCenterX - $cmuHalf
$cmuRightEdge = $cmuCenterX + $cmuHalf

# Stucco on exterior (left of CMU)
$stuccoLeft = $cmuLeftEdge - $stuccoThick
$stuccoRight = $cmuLeftEdge

# Furring and GWB on interior (right of CMU)
$furrLeft = $cmuRightEdge
$furrRight = $cmuRightEdge + $furrDepth
$gwbLeft = $furrRight
$gwbRight = $furrRight + $gwbThick

Write-Host "Coordinate reference:"
Write-Host "  CMU: $([Math]::Round($cmuLeftEdge,3)) to $([Math]::Round($cmuRightEdge,3)) (center at $cmuCenterX)"
Write-Host "  Stucco: $([Math]::Round($stuccoLeft,3)) to $([Math]::Round($stuccoRight,3))"
Write-Host "  GWB: $([Math]::Round($gwbLeft,3)) to $([Math]::Round($gwbRight,3))"

# === Step 1: CMU Blocks ===
Write-Host "`n=== CMU Blocks ===" -ForegroundColor Yellow
for ($course = 0; $course -lt $numCourses; $course++) {
    $y = $BaseY + ($course * $courseHeight) + ($courseHeight / 2)
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU $($course+1)" -X $cmuCenterX -Y $y
}

# === Step 2: Bond Beam ===
Write-Host "`n=== Bond Beam ===" -ForegroundColor Yellow
$topY = $BaseY + $WallHeight - ($courseHeight / 2)
Place-Component -TypeId $BondBeam -Label "Bond Beam" -X $cmuCenterX -Y $topY

# === Step 3: Stucco (3/4") ===
Write-Host "`n=== Stucco Layer ===" -ForegroundColor Yellow
# Rectangle for stucco
Draw-Line -X1 $stuccoLeft -Y1 $BaseY -X2 $stuccoRight -Y2 $BaseY -Style "1"
Draw-Line -X1 $stuccoRight -Y1 $BaseY -X2 $stuccoRight -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $stuccoRight -Y1 ($BaseY + $WallHeight) -X2 $stuccoLeft -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $stuccoLeft -Y1 ($BaseY + $WallHeight) -X2 $stuccoLeft -Y2 $BaseY -Style "1"
Write-Host "  + Stucco rectangle" -ForegroundColor Green

# === Step 4: GWB (1/2") ===
Write-Host "`n=== GWB Layer ===" -ForegroundColor Yellow
Draw-Line -X1 $gwbLeft -Y1 $BaseY -X2 $gwbRight -Y2 $BaseY -Style "1"
Draw-Line -X1 $gwbRight -Y1 $BaseY -X2 $gwbRight -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $gwbRight -Y1 ($BaseY + $WallHeight) -X2 $gwbLeft -Y2 ($BaseY + $WallHeight) -Style "1"
Draw-Line -X1 $gwbLeft -Y1 ($BaseY + $WallHeight) -X2 $gwbLeft -Y2 $BaseY -Style "1"
Write-Host "  + GWB rectangle" -ForegroundColor Green

# === Step 5: Furring strips ===
Write-Host "`n=== Furring Strips ===" -ForegroundColor Yellow
$furrSpacing = 24/12
for ($y = $BaseY + $furrSpacing; $y -lt ($BaseY + $WallHeight); $y += $furrSpacing) {
    # Draw small rectangle for each furring strip
    Draw-Line -X1 $furrLeft -Y1 ($y - 0.04) -X2 $furrRight -Y2 ($y - 0.04) -Style "1"
    Draw-Line -X1 $furrLeft -Y1 ($y + 0.04) -X2 $furrRight -Y2 ($y + 0.04) -Style "1"
}
Write-Host "  + Furring at 24`" o.c." -ForegroundColor Green

# === Step 6: Rebar ===
Write-Host "`n=== Rebar ===" -ForegroundColor Yellow
for ($y = $BaseY + 2; $y -lt ($BaseY + $WallHeight); $y += 4) {
    Place-Component -TypeId $Rebar_5 -Label "Rebar #5" -X $cmuCenterX -Y $y
}

# === Step 7: Break Line ===
Write-Host "`n=== Break Line ===" -ForegroundColor Yellow
Place-Component -TypeId $BreakLine -Label "Break Line" -X $cmuCenterX -Y ($BaseY + $WallHeight/2)

# === Step 8: Grade Line ===
Write-Host "`n=== Grade Line ===" -ForegroundColor Yellow
Draw-Line -X1 ($stuccoLeft - 1) -Y1 $BaseY -X2 ($gwbRight + 1) -Y2 $BaseY -Style "3"
Write-Host "  + Grade line" -ForegroundColor Green

# === Step 9: Annotations ===
Write-Host "`n=== Annotations ===" -ForegroundColor Yellow
$leftTextX = $stuccoLeft - 2
$rightTextX = $gwbRight + 1.5

Add-Text -Text "3/4`" STUCCO" -X $leftTextX -Y ($BaseY + 6) -LeaderX (($stuccoLeft + $stuccoRight)/2) -LeaderY ($BaseY + 6)
Add-Text -Text "8`" CMU W/`r#5 @ 48`" O.C." -X $leftTextX -Y ($BaseY + 4) -LeaderX $cmuCenterX -LeaderY ($BaseY + 4)
Add-Text -Text "FIN. GRADE" -X $leftTextX -Y ($BaseY + 0.2)
Add-Text -Text "1/2`" GWB ON`r1x3 FURR." -X $rightTextX -Y ($BaseY + 5) -LeaderX (($gwbLeft + $gwbRight)/2) -LeaderY ($BaseY + 5)

$pipe.Close()

Write-Host "`n=== Complete ===" -ForegroundColor Green
Write-Host "CMU center at X=$BaseX, $numCourses courses"
