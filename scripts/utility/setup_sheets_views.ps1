# Setup TEST-4 views and sheets to match Sheffield Road
# Part 1: Rename views to match Sheffield naming convention

function Send-RevitCommand {
    param([string]$json)
    $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
    $pipeClient.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipeClient)
    $reader = New-Object System.IO.StreamReader($pipeClient)
    $writer.WriteLine($json)
    $writer.Flush()
    $response = $reader.ReadLine()
    $pipeClient.Close()
    $pipeClient.Dispose()
    return $response | ConvertFrom-Json
}

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "PART 1: Renaming Views" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# View renames - TEST-4 IDs to Sheffield names
$viewRenames = @(
    @{ viewId = 32; newName = "FLOOR PLAN" },
    @{ viewId = 29154; newName = "RIGHT-SIDE EXTERIOR ELEVATION" },
    @{ viewId = 29181; newName = "REAR EXTERIOR ELEVATION" },
    @{ viewId = 29191; newName = "LEFT-SIDE EXTERIOR ELEVATION" },
    @{ viewId = 29201; newName = "FRONT EXTERIOR ELEVATION" },
    @{ viewId = 916524; newName = "BUILDING SECTION - AA" },
    @{ viewId = 950761; newName = "FOUNDATION PLAN" },
    @{ viewId = 950771; newName = "ROOF FRAMING PLAN" },
    @{ viewId = 828646; newName = "L1 - MECHANICAL" },
    @{ viewId = 828718; newName = "L1 - ELECTRICAL POWER" },
    @{ viewId = 829237; newName = "L1 - ELECTRICAL LIGHTING" },
    @{ viewId = 828790; newName = "L1 - PLUMBING" },
    @{ viewId = 828827; newName = "L2 - PLUMBING" },
    @{ viewId = 29237; newName = "SITE PLAN" }
)

foreach ($v in $viewRenames) {
    $json = '{"method":"renameView","params":{"viewId":' + $v.viewId + ',"newName":"' + $v.newName + '"}}'
    $result = Send-RevitCommand $json
    if ($result.success) {
        Write-Host "[OK] Renamed to: $($v.newName)" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] $($v.newName) - $($result.error)" -ForegroundColor Yellow
    }
    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "PART 2: Placing Views on Sheets" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Sheet IDs from creation
$sheetIds = @{
    "A-0.0" = 1294574   # GENERAL NOTES / SITE DATA
    "A-1.0" = 1294580   # COVER SHEET
    "A-1.1" = 1294586   # FLOOR PLAN, SCHEDULES, DETAILS & LEGEND
    "A-2.0" = 1294592   # BUILDING ELEVATIONS
    "A-2.1" = 1294598   # BUILDING ELEVATIONS
    "A-3.0" = 1294604   # ROOF PLAN & DETAILS
    "A-4.0" = 1294610   # BUILDING SECTIONS & DETAILS
    "A-5.0" = 1294616   # ENLARGED PLANS, ELEVATION AND DETAILS
    "S-1.0" = 1294622   # FOUNDATION PLAN AND DETAILS
    "S-2.0" = 1294628   # ROOF FRAMING PLAN AND DETAILS
    "S-3.0" = 1294634   # COLUMN & BOND BEAM PLAN
    "M-1.0" = 1294640   # MECHANICAL
    "E-1.0" = 1294646   # ELECTRICAL
    "E-2.0" = 1294652   # ELECTRICAL
    "P-1.0" = 1294658   # PLUMBING
    "P-2.0" = 1294664   # PLUMBING
    "C-1.0" = 1294670   # TYPICAL SITE PLAN
    "L-1.0" = 1294676   # LANDSCAPE PLAN / NOTES & DETAILS
    "L-2.0" = 1294682   # IRRIGATION PLAN / NOTES & DETAILS
}

# View placements: [sheetNumber, viewId, X, Y]
# Coordinates in feet from sheet origin (0,0 is bottom-left)
$viewPlacements = @(
    # A-1.0: COVER SHEET - 3D view
    @{ sheet = "A-1.0"; viewId = 410135; x = 1.25; y = 1.0 },

    # A-1.1: FLOOR PLAN - Floor plan + schedules
    @{ sheet = "A-1.1"; viewId = 32; x = 1.0; y = 1.2 },

    # A-2.0: ELEVATIONS - Front and Right
    @{ sheet = "A-2.0"; viewId = 29201; x = 0.75; y = 1.5 },   # Front
    @{ sheet = "A-2.0"; viewId = 29154; x = 0.75; y = 0.5 },   # Right

    # A-2.1: ELEVATIONS - Rear and Left
    @{ sheet = "A-2.1"; viewId = 29181; x = 0.75; y = 1.5 },   # Rear
    @{ sheet = "A-2.1"; viewId = 29191; x = 0.75; y = 0.5 },   # Left

    # A-4.0: BUILDING SECTIONS - Section AA
    @{ sheet = "A-4.0"; viewId = 916524; x = 1.0; y = 1.0 },

    # S-1.0: FOUNDATION PLAN
    @{ sheet = "S-1.0"; viewId = 950761; x = 1.0; y = 1.0 },

    # S-2.0: ROOF FRAMING
    @{ sheet = "S-2.0"; viewId = 950771; x = 1.0; y = 1.0 },

    # M-1.0: MECHANICAL
    @{ sheet = "M-1.0"; viewId = 828646; x = 1.0; y = 1.0 },

    # E-1.0: ELECTRICAL POWER
    @{ sheet = "E-1.0"; viewId = 828718; x = 1.0; y = 1.0 },

    # E-2.0: ELECTRICAL LIGHTING
    @{ sheet = "E-2.0"; viewId = 829237; x = 1.0; y = 1.0 },

    # P-1.0: PLUMBING L1
    @{ sheet = "P-1.0"; viewId = 828790; x = 1.0; y = 1.0 },

    # P-2.0: PLUMBING L2
    @{ sheet = "P-2.0"; viewId = 828827; x = 1.0; y = 1.0 },

    # C-1.0: SITE PLAN
    @{ sheet = "C-1.0"; viewId = 29237; x = 1.0; y = 1.0 }
)

$placed = 0
$failed = 0

foreach ($p in $viewPlacements) {
    $sheetId = $sheetIds[$p.sheet]
    $json = '{"method":"placeViewOnSheet","params":{"sheetId":' + $sheetId + ',"viewId":' + $p.viewId + ',"location":[' + $p.x + ',' + $p.y + ']}}'
    $result = Send-RevitCommand $json
    if ($result.success) {
        Write-Host "[OK] $($p.sheet): Placed view $($p.viewId)" -ForegroundColor Green
        $placed++
    } else {
        Write-Host "[FAIL] $($p.sheet): $($result.error)" -ForegroundColor Red
        $failed++
    }
    Start-Sleep -Milliseconds 300
}

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Views placed: $placed" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "Views failed: $failed" -ForegroundColor Red
}
Write-Host "=======================================" -ForegroundColor Cyan
