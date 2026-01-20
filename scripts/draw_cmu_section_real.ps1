# Draw CMU Wall Section with REAL CMU Components
# Uses actual CMU detail components placed at each course (simulating repeating detail)

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 0,
    [float]$BaseY = 0,
    [float]$WallHeight = 8.0  # 8 feet default
)

Write-Host "=== CMU Wall Section with Real Components ===" -ForegroundColor Cyan
Write-Host "Placing CMU blocks at each course (simulating repeating detail)"

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(15000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 5 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 250
    $response = $reader.ReadLine()
    return $response | ConvertFrom-Json
}

function Place-Component {
    param([int]$TypeId, [string]$Label, [float]$X, [float]$Y, [float]$Rotation = 0)

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
        Write-Host "  + $Label" -ForegroundColor Green
    } else {
        Write-Host "  ! $Label failed: $($result.error)" -ForegroundColor Red
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

# === Component TypeIds (discovered from existing details) ===
$CMU_8x8x16 = 1748270      # 04-CMU-2 Core-Section:8" x 8" x 16"
$CMU_4x8x16 = 1748434      # 04-CMU-2 Core-Section:4" x 8" x 16"
$Lumber_1x3 = 1389310      # Nominal Cut Lumber-Section:1x3
$Gypsum_3_4 = 1748191      # Gypsum Plaster-Section:3/4" (stucco)
$Gypsum_1_2 = 1748189      # Gypsum Sheathing-Section:1/2" (GWB)
$Rebar_5 = 1748194         # Reinf Bar Section:#_5
$BreakLine = 1748208       # Break Line:Break Line

# === Wall Dimensions ===
$cmuWidth = 8/12           # 8" CMU = 0.667 feet
$courseHeight = 8/12       # 8" course height
$numCourses = [Math]::Floor($WallHeight / $courseHeight)

Write-Host "`nStep 1: Placing CMU blocks at each course..." -ForegroundColor Yellow
Write-Host "  Wall height: $WallHeight ft = $numCourses courses"

# Place CMU component at each course
for ($course = 0; $course -lt $numCourses; $course++) {
    $y = ($course * $courseHeight) + ($courseHeight / 2)  # Center of each course
    Place-Component -TypeId $CMU_8x8x16 -Label "CMU Course $($course + 1) at Y=$([Math]::Round($y, 2))'" -X ($cmuWidth / 2) -Y $y
}

Write-Host "`nStep 2: Placing interior furring (1x3 @ 24`" o.c.)..." -ForegroundColor Yellow
$furrX = $cmuWidth + 0.125  # Interior side
$stripSpacing = 24/12       # 24" o.c.
for ($y = $stripSpacing; $y -lt $WallHeight; $y += $stripSpacing) {
    Place-Component -TypeId $Lumber_1x3 -Label "Furring at Y=$([Math]::Round($y, 2))'" -X $furrX -Y $y
}

Write-Host "`nStep 3: Placing exterior stucco (3/4`")..." -ForegroundColor Yellow
$stuccoX = -0.03125  # Exterior side
Place-Component -TypeId $Gypsum_3_4 -Label "Stucco at center" -X $stuccoX -Y ($WallHeight / 2)

Write-Host "`nStep 4: Placing interior GWB (1/2`")..." -ForegroundColor Yellow
$gwbX = $cmuWidth + 0.2  # On furring
Place-Component -TypeId $Gypsum_1_2 -Label "GWB at center" -X $gwbX -Y ($WallHeight / 2)

Write-Host "`nStep 5: Placing vertical rebar (#5 @ 48`" o.c.)..." -ForegroundColor Yellow
$rebarSpacing = 48/12  # 48" o.c.
for ($y = 1; $y -lt $WallHeight; $y += $rebarSpacing) {
    Place-Component -TypeId $Rebar_5 -Label "Rebar at Y=$([Math]::Round($y, 2))'" -X ($cmuWidth * 0.5) -Y $y
}

Write-Host "`nStep 6: Placing break line..." -ForegroundColor Yellow
Place-Component -TypeId $BreakLine -Label "Break line at mid-height" -X ($cmuWidth / 2) -Y ($WallHeight / 2)

Write-Host "`nStep 7: Drawing wall outline and grade..." -ForegroundColor Yellow
# Wall outline
Draw-Line -X1 -0.0625 -Y1 0 -X2 -0.0625 -Y2 $WallHeight -Style "3"  # Stucco face
Draw-Line -X1 ($gwbX + 0.04) -Y1 0 -X2 ($gwbX + 0.04) -Y2 $WallHeight -Style "3"  # GWB face
Draw-Line -X1 -0.0625 -Y1 $WallHeight -X2 ($gwbX + 0.04) -Y2 $WallHeight -Style "3"  # Top

# Grade line
Draw-Line -X1 -1 -Y1 0 -X2 1.5 -Y2 0 -Style "3"

Write-Host "`nStep 8: Adding annotations..." -ForegroundColor Yellow
$leftX = -2.5
$rightX = $gwbX + 1.5

Add-Text -Text "3/4`" STUCCO ON`rMTL. LATH" -X $leftX -Y 6 -LeaderX $stuccoX -LeaderY 6
Add-Text -Text "8`" CMU WALL W/`r#5 VERT. @ 48`" O.C.`rW/ BOND BEAM AT TOP" -X $leftX -Y 4 -LeaderX ($cmuWidth/2) -LeaderY 4
Add-Text -Text "FIN. GRADE" -X $leftX -Y 0.2
Add-Text -Text "1/2`" GYP. BD. ON`r1x3 P.T. FURR.`r@ 24`" O.C." -X $rightX -Y 5 -LeaderX $gwbX -LeaderY 5

$pipe.Close()

Write-Host "`n=== CMU Wall Section Complete ===" -ForegroundColor Green
Write-Host "Location: ($BaseX, $BaseY)"
Write-Host "Height: $WallHeight ft ($numCourses courses)"
Write-Host "Components used:"
Write-Host "  - $numCourses CMU blocks (8x8x16)"
Write-Host "  - $([Math]::Floor(($WallHeight - $stripSpacing) / $stripSpacing) + 1) Furring strips"
Write-Host "  - 1 Stucco section"
Write-Host "  - 1 GWB section"
Write-Host "  - $([Math]::Floor(($WallHeight - 1) / $rebarSpacing) + 1) Rebar sections"
Write-Host "  - 1 Break line"
