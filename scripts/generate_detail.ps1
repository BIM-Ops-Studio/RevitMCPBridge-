# Generate architectural details from learned patterns
# Uses knowledge extracted from detail library

param(
    [Parameter(Mandatory=$true)]
    [string]$DetailType,  # wallSection, roofEave, cmuWall, doorJamb, footing, etc.

    [Parameter(Mandatory=$true)]
    [int]$ViewId,  # Target drafting view ID

    [string]$Variation = "standard",  # standard, florida, etc.
    [float]$BaseX = 0,  # Origin X
    [float]$BaseY = 0,  # Origin Y
    [int]$Scale = 16    # View scale (16 = 3/4" = 1'-0")
)

Write-Host "=== Detail Generation ===" -ForegroundColor Cyan
Write-Host "Type: $DetailType"
Write-Host "View: $ViewId"
Write-Host "Origin: ($BaseX, $BaseY)"

# Connect to MCP
$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 5 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 300
    $response = $reader.ReadLine()
    return $response | ConvertFrom-Json
}

# Scale factor for 3/4" = 1'-0" (1 foot = 0.75 inches on paper = 0.0625 feet)
$sf = 1.0 / $Scale  # Converts paper units to model units

# Common detail component placement
function Place-Component {
    param(
        [string]$Family,
        [string]$Type,
        [float]$X,
        [float]$Y
    )
    $result = Invoke-MCP -Method "placeDetailComponent" -Params @{
        viewId = $ViewId
        familyName = $Family
        typeName = $Type
        x = $BaseX + ($X * $sf)
        y = $BaseY + ($Y * $sf)
    }
    if ($result.success) {
        Write-Host "  + $Family : $Type" -ForegroundColor Green
    } else {
        Write-Host "  ! $Family failed: $($result.error)" -ForegroundColor Yellow
    }
    return $result
}

function Draw-Line {
    param(
        [float]$X1, [float]$Y1,
        [float]$X2, [float]$Y2,
        [string]$Style = "Thin Lines"
    )
    $result = Invoke-MCP -Method "createDetailLineInDraftingView" -Params @{
        viewId = $ViewId
        startX = $BaseX + ($X1 * $sf)
        startY = $BaseY + ($Y1 * $sf)
        endX = $BaseX + ($X2 * $sf)
        endY = $BaseY + ($Y2 * $sf)
        lineStyle = $Style
    }
    return $result
}

function Add-Text {
    param(
        [string]$Text,
        [float]$X, [float]$Y,
        [float]$LeaderX = $null,
        [float]$LeaderY = $null
    )
    if ($LeaderX -ne $null) {
        $result = Invoke-MCP -Method "createTextNoteWithLeader" -Params @{
            viewId = $ViewId
            text = $Text
            textX = $BaseX + ($X * $sf)
            textY = $BaseY + ($Y * $sf)
            leaderEndX = $BaseX + ($LeaderX * $sf)
            leaderEndY = $BaseY + ($LeaderY * $sf)
        }
    } else {
        $result = Invoke-MCP -Method "createTextNote" -Params @{
            viewId = $ViewId
            text = $Text
            x = $BaseX + ($X * $sf)
            y = $BaseY + ($Y * $sf)
        }
    }
    if ($result.success) {
        Write-Host "  + Text: $($Text.Substring(0, [Math]::Min(30, $Text.Length)))..." -ForegroundColor Cyan
    }
    return $result
}

# Detail Templates
switch ($DetailType) {
    "wallSection" {
        Write-Host "`nGenerating: Wall Section (CMU with Flat Roof)" -ForegroundColor Yellow

        # Wall height (8' typical)
        $wallHeight = 8.0

        # CMU Wall (8" thick)
        Place-Component -Family "04-CMU-2 Core-Section" -Type "8x8x16" -X 0 -Y ($wallHeight / 2)

        # Exterior stucco
        Place-Component -Family "Gypsum Plaster-Section" -Type "3/4`"" -X -0.375 -Y ($wallHeight / 2)

        # Interior furring and GWB
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "1x3" -X 0.5 -Y 1
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "1x3" -X 0.5 -Y 3
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "1x3" -X 0.5 -Y 5
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "1x3" -X 0.5 -Y 7
        Place-Component -Family "Gypsum Plaster-Section" -Type "1/2`"" -X 0.7 -Y ($wallHeight / 2)

        # Rebar
        Place-Component -Family "Reinf Bar Section" -Type "#_5" -X 0 -Y 0.5
        Place-Component -Family "Reinf Bar Section" -Type "#_5" -X 0 -Y 7.5

        # Foundation/footing
        Place-Component -Family "Reinf Bar Section" -Type "#_5" -X 0 -Y -0.5
        Place-Component -Family "Reinf Bar Section" -Type "#_5" -X 0.3 -Y -0.5

        # Text annotations
        Add-Text -Text "8`" CMU WALL W/`r#5 VERT. @ 48`" O.C." -X -3 -Y 4 -LeaderX 0 -LeaderY 4
        Add-Text -Text "3/4`" EXT. STUCCO" -X -3 -Y 6 -LeaderX -0.375 -LeaderY 6
        Add-Text -Text "1/2`" GYP. BD. ON`r1x3 FURR. STRIPS @ 24`" O.C." -X 3 -Y 4 -LeaderX 0.7 -LeaderY 4
        Add-Text -Text "CONC. FTG. W/ (2) #5 CONT." -X 3 -Y -1 -LeaderX 0 -LeaderY -0.5

        # Break lines
        Place-Component -Family "Break Line" -Type "Break Line" -X 0 -Y 3.5

        Write-Host "`nWall section complete!" -ForegroundColor Green
    }

    "roofEave" {
        Write-Host "`nGenerating: Roof Eave Detail" -ForegroundColor Yellow

        # Roof slope (1/4" per foot)
        $slopeHeight = 0.25

        # Roof sheathing
        Place-Component -Family "Plywood-Section" -Type "5/8`"" -X 0 -Y 8

        # Roof joists
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "2x10" -X 0 -Y 7.5
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "2x10" -X 2 -Y 7.5

        # Fascia
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "2x12" -X 3 -Y 7.5

        # Soffit
        Place-Component -Family "Plywood-Section" -Type "3/4`"" -X 2 -Y 7

        # Blocking
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "1x3" -X 2.8 -Y 8

        # Text annotations
        Add-Text -Text "19/32`" PLYWOOD SHEATHING" -X -3 -Y 8.5 -LeaderX 0 -LeaderY 8.2
        Add-Text -Text "2x10 WD. JOIST @ 16`" O.C." -X -3 -Y 7 -LeaderX 0 -LeaderY 7.5
        Add-Text -Text "2x12 P.T. WD. FASCIA" -X 5 -Y 7.5 -LeaderX 3.2 -LeaderY 7.5
        Add-Text -Text "3/4`" EXT. GRADE PLYWD. SOFFIT`rW/ VENT SCREEN @ 48`" O.C." -X 5 -Y 6.5 -LeaderX 2 -LeaderY 7
        Add-Text -Text "1/4`" SLOPE PER FT." -X 0 -Y 9

        Write-Host "`nRoof eave detail complete!" -ForegroundColor Green
    }

    "footing" {
        Write-Host "`nGenerating: Typical Footing Section" -ForegroundColor Yellow

        # Footing dimensions (16" x 12" typical)
        $footingWidth = 16/12  # in feet
        $footingHeight = 12/12  # in feet

        # Draw footing outline
        Draw-Line -X1 (-$footingWidth/2) -Y1 0 -X2 ($footingWidth/2) -Y2 0 -Style "3"
        Draw-Line -X1 (-$footingWidth/2) -Y1 0 -X2 (-$footingWidth/2) -Y2 (-$footingHeight) -Style "3"
        Draw-Line -X1 ($footingWidth/2) -Y1 0 -X2 ($footingWidth/2) -Y2 (-$footingHeight) -Style "3"
        Draw-Line -X1 (-$footingWidth/2) -Y1 (-$footingHeight) -X2 ($footingWidth/2) -Y2 (-$footingHeight) -Style "3"

        # Rebar
        Place-Component -Family "Reinf Bar Section" -Type "#_5" -X -0.3 -Y (-$footingHeight + 0.25)
        Place-Component -Family "Reinf Bar Section" -Type "#_5" -X 0.3 -Y (-$footingHeight + 0.25)

        # Wall stem above
        Draw-Line -X1 -0.33 -Y1 0 -X2 -0.33 -Y2 2 -Style "3"
        Draw-Line -X1 0.33 -Y1 0 -X2 0.33 -Y2 2 -Style "3"

        # Break line at top
        Place-Component -Family "Break Line" -Type "Break Line" -X 0 -Y 1.8

        # Gravel fill indication below
        Draw-Line -X1 (-$footingWidth/2 - 0.5) -Y1 (-$footingHeight - 0.5) -X2 ($footingWidth/2 + 0.5) -Y2 (-$footingHeight - 0.5) -Style "1"

        # Text annotations
        Add-Text -Text "16`"X12`" CONC. FTG.`rW/ (2) #5 CONT." -X 2 -Y (-$footingHeight/2) -LeaderX 0.5 -LeaderY (-$footingHeight/2)
        Add-Text -Text "8`" CMU WALL" -X 2 -Y 1 -LeaderX 0.33 -LeaderY 1
        Add-Text -Text "COMPACT FILL TO`r95% PROCTOR" -X -3 -Y (-$footingHeight - 0.3) -LeaderX 0 -LeaderY (-$footingHeight - 0.5)
        Add-Text -Text "FIN. GRADE" -X 1.5 -Y 0.2

        Write-Host "`nFooting detail complete!" -ForegroundColor Green
    }

    "doorJamb" {
        Write-Host "`nGenerating: Door Jamb Detail" -ForegroundColor Yellow

        # Door frame and jamb
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "2x4" -X 0 -Y 0

        # Wall framing
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "2x4" -X -0.2 -Y 0
        Place-Component -Family "Nominal Cut Lumber-Section" -Type "2x4" -X -0.4 -Y 0

        # GWB each side
        Place-Component -Family "Gypsum Plaster-Section" -Type "1/2`"" -X 0.3 -Y 0
        Place-Component -Family "Gypsum Plaster-Section" -Type "1/2`"" -X -0.6 -Y 0

        # Annotations
        Add-Text -Text "DOOR FRAME" -X 1.5 -Y 0 -LeaderX 0.15 -LeaderY 0
        Add-Text -Text "SHIM SPACE" -X 1.5 -Y -0.3 -LeaderX 0 -LeaderY -0.1
        Add-Text -Text "KING STUD" -X -2 -Y 0 -LeaderX -0.4 -LeaderY 0
        Add-Text -Text "1/2`" GYP. BD." -X -2 -Y -0.5 -LeaderX -0.6 -LeaderY -0.2

        Write-Host "`nDoor jamb detail complete!" -ForegroundColor Green
    }

    default {
        Write-Host "Unknown detail type: $DetailType" -ForegroundColor Red
        Write-Host "Available types: wallSection, roofEave, footing, doorJamb" -ForegroundColor Yellow
    }
}

$pipe.Close()

Write-Host "`n=== Generation Complete ===" -ForegroundColor Cyan
