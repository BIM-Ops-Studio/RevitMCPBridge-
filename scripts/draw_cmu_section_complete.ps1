# Draw Complete CMU Wall Section with Real Components
# CMU blocks as components, finishes as detail line rectangles

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 0,
    [float]$BaseY = 0,
    [float]$WallHeight = 8.0
)

Write-Host "=== Complete CMU Wall Section ===" -ForegroundColor Cyan

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
    param([int]$TypeId, [string]$Label, [float]$X, [float]$Y, [float]$Rotation = 0)
    $result = Invoke-MCP -Method "placeDetailComponent" -Params @{
        viewId = $ViewId
        componentTypeId = $TypeId
        location = @{x = $BaseX + $X; y = $BaseY + $Y; z = 0}
        rotation = $Rotation
    }
    if ($result.success) { Write-Host "  + $Label" -ForegroundColor Green }
    else { Write-Host "  ! $Label - $($result.error)" -ForegroundColor Red }
    return $result
}

function Draw-Line {
    param([float]$X1, [float]$Y1, [float]$X2, [float]$Y2, [string]$Style = "Thin Lines")
    $result = Invoke-MCP -Method "createDetailLineInDraftingView" -Params @{
        viewId = $ViewId
        startX = $BaseX + $X1; startY = $BaseY + $Y1
        endX = $BaseX + $X2; endY = $BaseY + $Y2
        lineStyle = $Style
    }
    return $result.success
}

function Draw-Rectangle {
    param([float]$X1, [float]$Y1, [float]$X2, [float]$Y2, [string]$Style = "Thin Lines")
    Draw-Line -X1 $X1 -Y1 $Y1 -X2 $X2 -Y2 $Y1 -Style $Style  # Bottom
    Draw-Line -X1 $X2 -Y1 $Y1 -X2 $X2 -Y2 $Y2 -Style $Style  # Right
    Draw-Line -X1 $X2 -Y1 $Y2 -X2 $X1 -Y2 $Y2 -Style $Style  # Top
    Draw-Line -X1 $X1 -Y1 $Y2 -X2 $X1 -Y2 $Y1 -Style $Style  # Left
}

function Add-Text {
    param([string]$Text, [float]$X, [float]$Y, [float]$LeaderX = $null, [float]$LeaderY = $null)
    if ($null -ne $LeaderX) {
        $result = Invoke-MCP -Method "createTextNoteWithLeader" -Params @{
            viewId = $ViewId; text = $Text
            textX = $BaseX + $X; textY = $BaseY + $Y
            leaderEndX = $BaseX + $LeaderX; leaderEndY = $BaseY + $LeaderY
        }
    } else {
        $result = Invoke-MCP -Method "createTextNote" -Params @{
            viewId = $ViewId; text = $Text; x = $BaseX + $X; y = $BaseY + $Y
        }
    }
    return $result.success
}

# === Component TypeIds ===
$CMU_8x8x16 = 1748270      # 04-CMU-2 Core-Section:8" x 8" x 16"
$BondBeam = 1748430        # Bond Beam - 001:8" x 8" x 16"
$Lumber_2x6 = 1389320      # Nominal Cut Lumber-Section:2x6
$Rebar_5 = 1748194         # Reinf Bar Section:#_5
$BreakLine = 1748208       # Break Line

# === Dimensions ===
$cmuWidth = 8/12           # 8" = 0.667'
$courseHeight = 8/12       # 8" courses
$numCourses = [Math]::Floor($WallHeight / $courseHeight)
$stuccoThick = 0.75/12     # 3/4"
$gwbThick = 0.5/12         # 1/2"
$furrDepth = 1.5/12        # 1.5" furring space

# X positions
$stuccoLeft = -$stuccoThick
$cmuLeft = 0
$cmuRight = $cmuWidth
$furrRight = $cmuRight + $furrDepth
$gwbRight = $furrRight + $gwbThick

Write-Host "`n=== Step 1: CMU Blocks (Real Components) ===" -ForegroundColor Yellow
for ($course = 0; $course -lt $numCourses; $course++) {
    $y = ($course * $courseHeight) + ($courseHeight / 2)
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU Course $($course + 1)" -X ($cmuWidth / 2) -Y $y
}

Write-Host "`n=== Step 2: Bond Beam at Top ===" -ForegroundColor Yellow
Place-Component -TypeId $BondBeam -Label "Bond Beam" -X ($cmuWidth / 2) -Y ($WallHeight - $courseHeight/2)

Write-Host "`n=== Step 3: Stucco Layer (3/4`" - Lines) ===" -ForegroundColor Yellow
Write-Host "  Drawing stucco rectangle..." -ForegroundColor Cyan
Draw-Rectangle -X1 $stuccoLeft -Y1 0 -X2 0 -Y2 $WallHeight -Style "1"
# Add diagonal hatch lines for stucco pattern
for ($y = 0.5; $y -lt $WallHeight; $y += 0.5) {
    Draw-Line -X1 $stuccoLeft -Y1 $y -X2 0 -Y2 ($y - $stuccoThick * 2) -Style "1"
}
Write-Host "  + Stucco layer complete" -ForegroundColor Green

Write-Host "`n=== Step 4: Furring & GWB (1/2`" - Lines) ===" -ForegroundColor Yellow
Write-Host "  Drawing GWB rectangle..." -ForegroundColor Cyan
Draw-Rectangle -X1 $furrRight -Y1 0 -X2 $gwbRight -Y2 $WallHeight -Style "1"
Write-Host "  + GWB layer complete" -ForegroundColor Green

# Furring strips at 24" o.c.
Write-Host "  Adding furring strip lines..." -ForegroundColor Cyan
$furrSpacing = 24/12
for ($y = $furrSpacing; $y -lt $WallHeight; $y += $furrSpacing) {
    Draw-Line -X1 $cmuRight -Y1 ($y - 0.125) -X2 $furrRight -Y2 ($y - 0.125) -Style "1"
    Draw-Line -X1 $cmuRight -Y1 ($y + 0.125) -X2 $furrRight -Y2 ($y + 0.125) -Style "1"
}
Write-Host "  + Furring strips complete" -ForegroundColor Green

Write-Host "`n=== Step 5: Rebar ===" -ForegroundColor Yellow
$rebarSpacing = 48/12
for ($y = 2; $y -lt $WallHeight; $y += $rebarSpacing) {
    Place-Component -TypeId $Rebar_5 -Label "Rebar #5 at Y=$([Math]::Round($y,1))'" -X ($cmuWidth * 0.5) -Y $y
}

Write-Host "`n=== Step 6: Break Line ===" -ForegroundColor Yellow
Place-Component -TypeId $BreakLine -Label "Break Line" -X ($cmuWidth / 2) -Y ($WallHeight / 2)

Write-Host "`n=== Step 7: Grade Line ===" -ForegroundColor Yellow
Draw-Line -X1 ($stuccoLeft - 1) -Y1 0 -X2 ($gwbRight + 1) -Y2 0 -Style "3"
# Grade hatch
for ($x = $stuccoLeft - 0.8; $x -lt $gwbRight + 0.8; $x += 0.2) {
    Draw-Line -X1 $x -Y1 0 -X2 ($x - 0.1) -Y2 -0.1 -Style "1"
}
Write-Host "  + Grade line complete" -ForegroundColor Green

Write-Host "`n=== Step 8: Annotations ===" -ForegroundColor Yellow
$leftX = -2.5
$rightX = $gwbRight + 1.5

Add-Text -Text "3/4`" STUCCO ON`rMTL. LATH" -X $leftX -Y 6 -LeaderX ($stuccoLeft/2) -LeaderY 6
Add-Text -Text "8`" CMU WALL W/`r#5 VERT. @ 48`" O.C." -X $leftX -Y 4 -LeaderX ($cmuWidth/2) -LeaderY 4
Add-Text -Text "BOND BEAM W/`r(2) #5 CONT." -X $leftX -Y ($WallHeight - 0.5) -LeaderX ($cmuWidth/2) -LeaderY ($WallHeight - $courseHeight/2)
Add-Text -Text "FIN. GRADE" -X $leftX -Y 0.2
Add-Text -Text "1/2`" GYP. BD. ON`r1x3 P.T. FURR.`r@ 24`" O.C." -X $rightX -Y 5 -LeaderX $gwbRight -LeaderY 5

$pipe.Close()

Write-Host "`n=== CMU Wall Section Complete ===" -ForegroundColor Green
Write-Host "Location: ($BaseX, $BaseY) | Height: $WallHeight'"
Write-Host "Components: $numCourses CMU + Bond Beam + Rebar + Break Line"
Write-Host "Lines: Stucco rect + GWB rect + Furring + Grade"
