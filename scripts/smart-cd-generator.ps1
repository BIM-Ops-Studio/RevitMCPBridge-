# Smart CD Sheet Generator
# Creates construction document sheets based on learned patterns and project type
# Uses SheetPatternMethods and intelligent organization

param(
    [string]$PipeName = 'RevitMCPBridge2026',
    [string]$ProjectType = "multi-family",  # single-family, multi-family, office, healthcare, retail
    [string]$SheetSet = "full",             # full, sd, dd, cd, permit
    [switch]$Preview,                       # Preview only, don't create
    [switch]$LearnFromExisting              # Learn pattern from current project first
)

# Helper function to call MCP
function Invoke-RevitMCP {
    param(
        [string]$Method,
        [hashtable]$Params = @{}
    )

    try {
        $cmd = @{method=$Method; params=$Params} | ConvertTo-Json -Compress -Depth 10
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(10000)
        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)
        $writer.WriteLine($cmd)
        $writer.Flush()
        $result = $reader.ReadLine()
        $pipe.Close()
        return $result | ConvertFrom-Json
    }
    catch {
        return @{success=$false; error=$_.Exception.Message}
    }
}

# Define standard sheet sets by project type
$sheetTemplates = @{
    "single-family" = @{
        full = @(
            @{number="G-001"; name="COVER SHEET"; discipline="General"},
            @{number="G-002"; name="CODE ANALYSIS"; discipline="General"},
            @{number="A-101"; name="SITE PLAN"; discipline="Architectural"},
            @{number="A-102"; name="FLOOR PLAN"; discipline="Architectural"},
            @{number="A-103"; name="ROOF PLAN"; discipline="Architectural"},
            @{number="A-201"; name="ELEVATIONS"; discipline="Architectural"},
            @{number="A-301"; name="BUILDING SECTIONS"; discipline="Architectural"},
            @{number="A-401"; name="WALL SECTIONS"; discipline="Architectural"},
            @{number="A-501"; name="DETAILS"; discipline="Architectural"},
            @{number="A-601"; name="DOOR & WINDOW SCHEDULE"; discipline="Architectural"},
            @{number="A-701"; name="FINISH SCHEDULE"; discipline="Architectural"},
            @{number="S-101"; name="FOUNDATION PLAN"; discipline="Structural"},
            @{number="S-201"; name="FRAMING PLAN"; discipline="Structural"},
            @{number="E-101"; name="ELECTRICAL PLAN"; discipline="Electrical"},
            @{number="M-101"; name="MECHANICAL PLAN"; discipline="Mechanical"},
            @{number="P-101"; name="PLUMBING PLAN"; discipline="Plumbing"}
        )
        permit = @(
            @{number="G-001"; name="COVER SHEET"; discipline="General"},
            @{number="A-101"; name="SITE PLAN"; discipline="Architectural"},
            @{number="A-102"; name="FLOOR PLAN"; discipline="Architectural"},
            @{number="A-201"; name="ELEVATIONS"; discipline="Architectural"},
            @{number="A-301"; name="BUILDING SECTIONS"; discipline="Architectural"},
            @{number="S-101"; name="FOUNDATION PLAN"; discipline="Structural"}
        )
    }
    "multi-family" = @{
        full = @(
            @{number="G-001"; name="COVER SHEET & INDEX"; discipline="General"},
            @{number="G-002"; name="LIFE SAFETY PLAN"; discipline="General"},
            @{number="G-003"; name="CODE ANALYSIS"; discipline="General"},
            @{number="A-001"; name="SITE PLAN"; discipline="Architectural"},
            @{number="A-101"; name="LEVEL 1 - FLOOR PLAN"; discipline="Architectural"},
            @{number="A-102"; name="LEVEL 2 - FLOOR PLAN"; discipline="Architectural"},
            @{number="A-103"; name="LEVEL 3 - FLOOR PLAN"; discipline="Architectural"},
            @{number="A-104"; name="ROOF PLAN"; discipline="Architectural"},
            @{number="A-201"; name="EXTERIOR ELEVATIONS"; discipline="Architectural"},
            @{number="A-301"; name="BUILDING SECTIONS"; discipline="Architectural"},
            @{number="A-401"; name="WALL SECTIONS"; discipline="Architectural"},
            @{number="A-501"; name="EXTERIOR DETAILS"; discipline="Architectural"},
            @{number="A-502"; name="INTERIOR DETAILS"; discipline="Architectural"},
            @{number="A-503"; name="STAIR DETAILS"; discipline="Architectural"},
            @{number="A-601"; name="DOOR SCHEDULE"; discipline="Architectural"},
            @{number="A-602"; name="WINDOW SCHEDULE"; discipline="Architectural"},
            @{number="A-701"; name="FINISH SCHEDULE"; discipline="Architectural"},
            @{number="A-801"; name="UNIT TYPE A - ENLARGED PLAN"; discipline="Architectural"},
            @{number="A-802"; name="UNIT TYPE B - ENLARGED PLAN"; discipline="Architectural"},
            @{number="A-901"; name="REFLECTED CEILING PLANS"; discipline="Architectural"}
        )
        permit = @(
            @{number="G-001"; name="COVER SHEET"; discipline="General"},
            @{number="G-002"; name="LIFE SAFETY PLAN"; discipline="General"},
            @{number="A-001"; name="SITE PLAN"; discipline="Architectural"},
            @{number="A-101"; name="LEVEL 1 - FLOOR PLAN"; discipline="Architectural"},
            @{number="A-102"; name="TYPICAL FLOOR PLAN"; discipline="Architectural"},
            @{number="A-201"; name="EXTERIOR ELEVATIONS"; discipline="Architectural"},
            @{number="A-301"; name="BUILDING SECTIONS"; discipline="Architectural"}
        )
    }
    "office" = @{
        full = @(
            @{number="G-001"; name="COVER SHEET & INDEX"; discipline="General"},
            @{number="G-002"; name="CODE ANALYSIS"; discipline="General"},
            @{number="G-003"; name="LIFE SAFETY PLAN"; discipline="General"},
            @{number="A-001"; name="SITE PLAN"; discipline="Architectural"},
            @{number="A-101"; name="FLOOR PLAN - LEVEL 1"; discipline="Architectural"},
            @{number="A-102"; name="FLOOR PLAN - TYPICAL"; discipline="Architectural"},
            @{number="A-103"; name="ROOF PLAN"; discipline="Architectural"},
            @{number="A-201"; name="EXTERIOR ELEVATIONS"; discipline="Architectural"},
            @{number="A-301"; name="BUILDING SECTIONS"; discipline="Architectural"},
            @{number="A-401"; name="WALL SECTIONS"; discipline="Architectural"},
            @{number="A-501"; name="EXTERIOR DETAILS"; discipline="Architectural"},
            @{number="A-502"; name="INTERIOR DETAILS"; discipline="Architectural"},
            @{number="A-601"; name="DOOR SCHEDULE"; discipline="Architectural"},
            @{number="A-602"; name="WINDOW SCHEDULE"; discipline="Architectural"},
            @{number="A-701"; name="FINISH SCHEDULE"; discipline="Architectural"},
            @{number="A-801"; name="INTERIOR ELEVATIONS"; discipline="Architectural"},
            @{number="A-901"; name="REFLECTED CEILING PLAN"; discipline="Architectural"},
            @{number="I-101"; name="FURNITURE PLAN"; discipline="Interiors"}
        )
    }
    "healthcare" = @{
        full = @(
            @{number="G-001"; name="COVER SHEET & INDEX"; discipline="General"},
            @{number="G-002"; name="CODE ANALYSIS & FGI COMPLIANCE"; discipline="General"},
            @{number="G-003"; name="LIFE SAFETY PLAN"; discipline="General"},
            @{number="G-004"; name="EGRESS PLAN"; discipline="General"},
            @{number="A-001"; name="SITE PLAN"; discipline="Architectural"},
            @{number="A-101"; name="FLOOR PLAN - LEVEL 1"; discipline="Architectural"},
            @{number="A-102"; name="FLOOR PLAN - LEVEL 2"; discipline="Architectural"},
            @{number="A-103"; name="ROOF PLAN"; discipline="Architectural"},
            @{number="A-201"; name="EXTERIOR ELEVATIONS"; discipline="Architectural"},
            @{number="A-301"; name="BUILDING SECTIONS"; discipline="Architectural"},
            @{number="A-401"; name="WALL SECTIONS"; discipline="Architectural"},
            @{number="A-501"; name="EXTERIOR DETAILS"; discipline="Architectural"},
            @{number="A-502"; name="INTERIOR DETAILS"; discipline="Architectural"},
            @{number="A-601"; name="DOOR SCHEDULE"; discipline="Architectural"},
            @{number="A-602"; name="DOOR TYPE DETAILS"; discipline="Architectural"},
            @{number="A-603"; name="WINDOW SCHEDULE"; discipline="Architectural"},
            @{number="A-701"; name="FINISH SCHEDULE"; discipline="Architectural"},
            @{number="A-702"; name="EQUIPMENT SCHEDULE"; discipline="Architectural"},
            @{number="A-801"; name="INTERIOR ELEVATIONS - PATIENT"; discipline="Architectural"},
            @{number="A-802"; name="INTERIOR ELEVATIONS - NURSING"; discipline="Architectural"},
            @{number="A-901"; name="REFLECTED CEILING PLAN"; discipline="Architectural"},
            @{number="A-902"; name="CEILING DETAILS"; discipline="Architectural"}
        )
    }
}

# Get project info
Write-Host "Smart CD Sheet Generator" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

$projectInfo = Invoke-RevitMCP -Method "getProjectInfo"
if ($projectInfo.success) {
    Write-Host "Project: $($projectInfo.data.projectName)"
} else {
    Write-Host "Warning: Could not get project info" -ForegroundColor Yellow
}

# Learn from existing if requested
if ($LearnFromExisting) {
    Write-Host "`nLearning sheet pattern from existing project..." -ForegroundColor Yellow
    $learnResult = Invoke-RevitMCP -Method "learnSheetPattern"
    if ($learnResult.success) {
        Write-Host "Learned pattern: $($learnResult.data.pattern)" -ForegroundColor Green
        Write-Host "Total sheets: $($learnResult.data.sheetCount)"
    }
}

# Get template for project type
$template = $sheetTemplates[$ProjectType]
if (-not $template) {
    Write-Host "Unknown project type: $ProjectType" -ForegroundColor Red
    Write-Host "Available: $($sheetTemplates.Keys -join ', ')"
    return
}

# Get sheet set
$sheets = $template[$SheetSet]
if (-not $sheets) {
    Write-Host "Unknown sheet set: $SheetSet" -ForegroundColor Red
    Write-Host "Available: $($template.Keys -join ', ')"
    return
}

Write-Host "`nProject Type: $ProjectType"
Write-Host "Sheet Set: $SheetSet"
Write-Host "Sheets to create: $($sheets.Count)"
Write-Host ""

# Preview mode
if ($Preview) {
    Write-Host "PREVIEW MODE - No sheets will be created" -ForegroundColor Yellow
    Write-Host ("-" * 50)

    foreach ($sheet in $sheets) {
        Write-Host "$($sheet.number)`t$($sheet.name)" -ForegroundColor White
    }

    Write-Host ("-" * 50)
    Write-Host "Total: $($sheets.Count) sheets"
    return $sheets
}

# Get existing sheets to avoid duplicates
Write-Host "Checking existing sheets..." -ForegroundColor Yellow
$existingSheets = Invoke-RevitMCP -Method "getSheets"
$existingNumbers = @()
if ($existingSheets.success -and $existingSheets.data) {
    $existingNumbers = $existingSheets.data | ForEach-Object { $_.SheetNumber }
    Write-Host "Found $($existingNumbers.Count) existing sheets"
}

# Get titleblock type
$titleblocks = Invoke-RevitMCP -Method "getTitleblocks"
$titleblockId = $null
if ($titleblocks.success -and $titleblocks.data.Count -gt 0) {
    $titleblockId = $titleblocks.data[0].Id
    Write-Host "Using titleblock: $($titleblocks.data[0].Name)"
} else {
    Write-Host "Warning: No titleblock found, sheets may not display correctly" -ForegroundColor Yellow
}

# Create sheets
Write-Host "`nCreating sheets..." -ForegroundColor Cyan
$created = 0
$skipped = 0

foreach ($sheet in $sheets) {
    if ($existingNumbers -contains $sheet.number) {
        Write-Host "  SKIP: $($sheet.number) - already exists" -ForegroundColor Yellow
        $skipped++
        continue
    }

    $createParams = @{
        sheetNumber = $sheet.number
        sheetName = $sheet.name
    }
    if ($titleblockId) {
        $createParams.titleblockTypeId = $titleblockId
    }

    $result = Invoke-RevitMCP -Method "createSheet" -Params $createParams

    if ($result.success) {
        Write-Host "  OK: $($sheet.number) - $($sheet.name)" -ForegroundColor Green
        $created++
    } else {
        Write-Host "  FAIL: $($sheet.number) - $($result.error)" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n" + ("-" * 50)
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "  Created: $created"
Write-Host "  Skipped: $skipped (already existed)"
Write-Host "  Total in set: $($sheets.Count)"

# Return results
return @{
    created = $created
    skipped = $skipped
    total = $sheets.Count
    projectType = $ProjectType
    sheetSet = $SheetSet
}
