# Draw CMU Wall Section using detail lines
# Creates a complete wall section without needing component type IDs

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 0,
    [float]$BaseY = 0
)

Write-Host "=== Drawing CMU Wall Section ===" -ForegroundColor Cyan

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 5 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 150
    $response = $reader.ReadLine()
    return $response | ConvertFrom-Json
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

# Wall dimensions
$wallHeight = 8.0      # 8 feet
$cmuWidth = 8/12       # 8" CMU = 0.667 feet
$stuccoWidth = 0.0625  # 3/4" stucco
$furrWidth = 0.0833    # 1" furring + 1/2" GWB
$footingWidth = 16/12  # 16" footing
$footingDepth = 12/12  # 12" deep

Write-Host "Drawing wall outline..." -ForegroundColor Yellow

# === CMU WALL (8" wide, 8' tall) ===
# Exterior face (left side)
Draw-Line -X1 0 -Y1 0 -X2 0 -Y2 $wallHeight -Style "3"
# Interior face (right side)
Draw-Line -X1 $cmuWidth -Y1 0 -X2 $cmuWidth -Y2 $wallHeight -Style "3"

# CMU horizontal coursing lines (every 8")
$courseHeight = 8/12  # 8 inches
for ($y = $courseHeight; $y -lt $wallHeight; $y += $courseHeight) {
    Draw-Line -X1 0 -Y1 $y -X2 $cmuWidth -Y2 $y -Style "1"
}

# CMU cell vertical lines (cells at 16" o.c.)
$cellSpacing = 16/12
Draw-Line -X1 ($cmuWidth/3) -Y1 0 -X2 ($cmuWidth/3) -Y2 $wallHeight -Style "1"
Draw-Line -X1 (2*$cmuWidth/3) -Y1 0 -X2 (2*$cmuWidth/3) -Y2 $wallHeight -Style "1"

Write-Host "Drawing stucco layer..." -ForegroundColor Yellow

# === EXTERIOR STUCCO (3/4") ===
$stuccoX = -$stuccoWidth
Draw-Line -X1 $stuccoX -Y1 0 -X2 $stuccoX -Y2 $wallHeight -Style "1"
# Top of stucco
Draw-Line -X1 $stuccoX -Y1 $wallHeight -X2 0 -Y2 $wallHeight -Style "1"

Write-Host "Drawing interior furring..." -ForegroundColor Yellow

# === INTERIOR FURRING + GWB ===
$furrX = $cmuWidth + $furrWidth
Draw-Line -X1 $furrX -Y1 0 -X2 $furrX -Y2 $wallHeight -Style "1"
# Furring strips (horizontal lines at 24" o.c.)
$stripSpacing = 24/12
for ($y = $stripSpacing; $y -lt $wallHeight; $y += $stripSpacing) {
    Draw-Line -X1 $cmuWidth -Y1 $y -X2 $furrX -Y2 $y -Style "1"
}
# Top of GWB
Draw-Line -X1 $cmuWidth -Y1 $wallHeight -X2 $furrX -Y2 $wallHeight -Style "1"

Write-Host "Drawing footing..." -ForegroundColor Yellow

# === FOOTING (16"W x 12"D) ===
$footingLeft = -($footingWidth - $cmuWidth)/2
$footingRight = $footingLeft + $footingWidth
$footingBottom = -$footingDepth

# Footing outline (heavy lines)
Draw-Line -X1 $footingLeft -Y1 0 -X2 $footingLeft -Y2 $footingBottom -Style "3"
Draw-Line -X1 $footingRight -Y1 0 -X2 $footingRight -Y2 $footingBottom -Style "3"
Draw-Line -X1 $footingLeft -Y1 $footingBottom -X2 $footingRight -Y2 $footingBottom -Style "3"

# Rebar in footing (circles represented as small X marks)
$rebarY = $footingBottom + 0.25
$rebarX1 = $footingLeft + 0.25
$rebarX2 = $footingRight - 0.25
# Draw small + for rebar
Draw-Line -X1 ($rebarX1 - 0.03) -Y1 $rebarY -X2 ($rebarX1 + 0.03) -Y2 $rebarY -Style "1"
Draw-Line -X1 $rebarX1 -Y1 ($rebarY - 0.03) -X2 $rebarX1 -Y2 ($rebarY + 0.03) -Style "1"
Draw-Line -X1 ($rebarX2 - 0.03) -Y1 $rebarY -X2 ($rebarX2 + 0.03) -Y2 $rebarY -Style "1"
Draw-Line -X1 $rebarX2 -Y1 ($rebarY - 0.03) -X2 $rebarX2 -Y2 ($rebarY + 0.03) -Style "1"

Write-Host "Drawing grade line..." -ForegroundColor Yellow

# === GRADE LINE ===
Draw-Line -X1 ($footingLeft - 1) -Y1 0 -X2 ($footingRight + 1) -Y2 0 -Style "3"

# Hatch marks for grade (diagonal lines)
for ($x = $footingLeft - 0.8; $x -lt $footingRight + 0.8; $x += 0.25) {
    Draw-Line -X1 $x -Y1 0 -X2 ($x - 0.15) -Y2 -0.15 -Style "1"
}

Write-Host "Drawing break line..." -ForegroundColor Yellow

# === BREAK LINE (zigzag at mid-height) ===
$breakY = $wallHeight / 2
$zigWidth = 0.1
# Simple zigzag pattern
Draw-Line -X1 $stuccoX -Y1 $breakY -X2 ($stuccoX + $zigWidth) -Y2 ($breakY + 0.08) -Style "1"
Draw-Line -X1 ($stuccoX + $zigWidth) -Y1 ($breakY + 0.08) -X2 ($stuccoX + 2*$zigWidth) -Y2 ($breakY - 0.08) -Style "1"
Draw-Line -X1 ($stuccoX + 2*$zigWidth) -Y1 ($breakY - 0.08) -X2 0 -Y2 $breakY -Style "1"

Draw-Line -X1 $furrX -Y1 $breakY -X2 ($furrX - $zigWidth) -Y2 ($breakY + 0.08) -Style "1"
Draw-Line -X1 ($furrX - $zigWidth) -Y1 ($breakY + 0.08) -X2 ($furrX - 2*$zigWidth) -Y2 ($breakY - 0.08) -Style "1"
Draw-Line -X1 ($furrX - 2*$zigWidth) -Y1 ($breakY - 0.08) -X2 $cmuWidth -Y2 $breakY -Style "1"

Write-Host "Adding annotations..." -ForegroundColor Yellow

# === TEXT ANNOTATIONS ===
$textX = -2.5  # Left side annotations
$rightTextX = $furrX + 1.5  # Right side annotations

# Left side annotations (exterior)
Add-Text -Text "3/4`" STUCCO ON`rMTL. LATH" -X $textX -Y 6 -LeaderX $stuccoX -LeaderY 6
Add-Text -Text "8`" CMU WALL W/`r#5 VERT. @ 48`" O.C." -X $textX -Y 4 -LeaderX ($cmuWidth/2) -LeaderY 4
Add-Text -Text "FIN. GRADE" -X $textX -Y 0.2

# Right side annotations (interior)
Add-Text -Text "1/2`" GYP. BD. ON`r1x3 P.T. FURR.`r@ 24`" O.C." -X $rightTextX -Y 6 -LeaderX $furrX -LeaderY 6
Add-Text -Text "R-4.1 RIGID INSUL." -X $rightTextX -Y 4 -LeaderX ($cmuWidth + $furrWidth/2) -LeaderY 4

# Footing annotation
Add-Text -Text "16`"x12`" CONC. FTG.`rW/ (2) #5 CONT." -X $rightTextX -Y (-$footingDepth/2) -LeaderX ($cmuWidth/2) -LeaderY (-$footingDepth/2)

# Top annotation
Add-Text -Text "SEE ROOF DETAIL" -X ($cmuWidth/2 - 0.5) -Y ($wallHeight + 0.3)

$pipe.Close()

Write-Host "`n=== CMU Wall Section Complete ===" -ForegroundColor Green
Write-Host "Location: ($BaseX, $BaseY)"
Write-Host "View ID: $ViewId"
