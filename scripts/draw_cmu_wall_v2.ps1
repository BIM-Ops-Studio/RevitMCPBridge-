# Draw CMU Wall Section v2 - Using detail components by name
# Uses placeDetailComponentByName for proper component placement

param(
    [int]$ViewId = 2238350,
    [float]$BaseX = 0,
    [float]$BaseY = 0,
    [float]$WallHeight = 8.0  # 8 feet default
)

Write-Host "=== CMU Wall Section v2 ===" -ForegroundColor Cyan
Write-Host "Using placeDetailComponentByName for components"

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
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
    param([string]$Family, [string]$Type, [float]$X, [float]$Y, [float]$Rotation = 0)
    $result = Invoke-MCP -Method "placeDetailComponentByName" -Params @{
        viewId = $ViewId
        familyName = $Family
        typeName = $Type
        x = $BaseX + $X
        y = $BaseY + $Y
        z = 0
        rotation = $Rotation
    }
    if ($result.success) {
        Write-Host "  + $Family : $Type at ($X, $Y)" -ForegroundColor Green
    } else {
        Write-Host "  ! $Family : $Type failed - $($result.error)" -ForegroundColor Yellow
        if ($result.availableTypes) {
            Write-Host "    Available types:" -ForegroundColor Gray
            $result.availableTypes | Select-Object -First 10 | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
        }
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

# === Wall Dimensions ===
$cmuWidth = 8/12       # 8" CMU = 0.667 feet
$courseHeight = 8/12   # 8" course height
$numCourses = [Math]::Floor($WallHeight / $courseHeight)

Write-Host "`nPlacing CMU section components..." -ForegroundColor Yellow

# === CMU BLOCKS (stack vertically) ===
# Place CMU sections at each course
for ($course = 0; $course -lt $numCourses; $course++) {
    $y = ($course * $courseHeight) + ($courseHeight / 2)
    # Place at center of CMU wall
    Place-Component -Family "04-CMU-2 Core-Section" -Type "8x8x16" -X ($cmuWidth / 2) -Y $y
}

Write-Host "`nPlacing bond beam..." -ForegroundColor Yellow

# === BOND BEAM at top ===
$topY = $WallHeight - ($courseHeight / 2)
Place-Component -Family "Bond Beam - 001" -Type "Bond Beam - 001" -X ($cmuWidth / 2) -Y $topY

Write-Host "`nPlacing interior finish components..." -ForegroundColor Yellow

# === INTERIOR FURRING + GWB ===
$furrX = $cmuWidth + 0.0833  # Furring at 1" from CMU
# Place furring strips at 24" o.c.
$stripSpacing = 24/12
for ($y = $stripSpacing; $y -lt $WallHeight; $y += $stripSpacing) {
    Place-Component -Family "Nominal Cut Lumber-Section" -Type "1x3" -X $furrX -Y $y
}

# GWB on furring
$gwbX = $cmuWidth + 0.125  # 1.5" from CMU face
Place-Component -Family "Gypsum Plaster-Section" -Type "1/2`"" -X $gwbX -Y ($WallHeight / 2)

Write-Host "`nPlacing exterior stucco..." -ForegroundColor Yellow

# === EXTERIOR STUCCO ===
$stuccoX = -0.0625  # 3/4" from CMU face (exterior side)
Place-Component -Family "Gypsum Plaster-Section" -Type "3/4`"" -X $stuccoX -Y ($WallHeight / 2)

Write-Host "`nPlacing reinforcement..." -ForegroundColor Yellow

# === REBAR in CMU ===
# Vertical rebar at cells
Place-Component -Family "Reinf Bar Section" -Type "#_5" -X ($cmuWidth * 0.3) -Y 1
Place-Component -Family "Reinf Bar Section" -Type "#_5" -X ($cmuWidth * 0.7) -Y 1
Place-Component -Family "Reinf Bar Section" -Type "#_5" -X ($cmuWidth * 0.3) -Y ($WallHeight - 1)
Place-Component -Family "Reinf Bar Section" -Type "#_5" -X ($cmuWidth * 0.7) -Y ($WallHeight - 1)

Write-Host "`nPlacing break lines..." -ForegroundColor Yellow

# === BREAK LINES ===
Place-Component -Family "Break Line" -Type "Break Line" -X ($cmuWidth / 2) -Y ($WallHeight / 2)

Write-Host "`nDrawing outline and grade..." -ForegroundColor Yellow

# === WALL OUTLINE (heavy lines) ===
Draw-Line -X1 $stuccoX -Y1 0 -X2 $stuccoX -Y2 $WallHeight -Style "3"
Draw-Line -X1 ($gwbX + 0.05) -Y1 0 -X2 ($gwbX + 0.05) -Y2 $WallHeight -Style "3"
Draw-Line -X1 $stuccoX -Y1 $WallHeight -X2 ($gwbX + 0.05) -Y2 $WallHeight -Style "3"

# === GRADE LINE ===
Draw-Line -X1 -1 -Y1 0 -X2 1.5 -Y2 0 -Style "3"

Write-Host "`nAdding annotations..." -ForegroundColor Yellow

# === ANNOTATIONS ===
$leftX = -2.5
$rightX = $gwbX + 1.5

Add-Text -Text "3/4`" STUCCO ON`rMTL. LATH" -X $leftX -Y 6 -LeaderX $stuccoX -LeaderY 6
Add-Text -Text "8`" CMU WALL W/`r#5 VERT. @ 48`" O.C.`rAND BOND BEAM AT TOP" -X $leftX -Y 4 -LeaderX ($cmuWidth/2) -LeaderY 4
Add-Text -Text "FIN. GRADE" -X $leftX -Y 0.2
Add-Text -Text "1/2`" GYP. BD. ON`r1x3 P.T. FURR.`r@ 24`" O.C." -X $rightX -Y 5 -LeaderX $gwbX -LeaderY 5

$pipe.Close()

Write-Host "`n=== CMU Wall Section Complete ===" -ForegroundColor Green
Write-Host "Location: ($BaseX, $BaseY)"
Write-Host "Height: $WallHeight ft"
