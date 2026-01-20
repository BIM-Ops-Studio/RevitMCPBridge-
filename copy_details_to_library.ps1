$harvestPath = "D:\003 - RESOURCES\01 - REVIT LIBRARY\Harvest RVTs\100 N. MAIN"
$libraryPath = "D:\Revit Detail Libraries\Revit Details"

$copied = 0
$failed = 0

Write-Output "=== Copying Recommended Details to Library ==="
Write-Output ""

# Create Fire Protection folder if needed
$fireFolder = "$libraryPath\18 - Fire Protection"
if (-not (Test-Path $fireFolder)) {
    New-Item -ItemType Directory -Path $fireFolder | Out-Null
    Write-Output "Created folder: 18 - Fire Protection"
}

# Create Legends folder if needed
$legendsFolder = "$libraryPath\20 - Legends"
if (-not (Test-Path $legendsFolder)) {
    New-Item -ItemType Directory -Path $legendsFolder | Out-Null
    Write-Output "Created folder: 20 - Legends"
}

Write-Output ""
Write-Output "--- Bathroom/Shower Details (12 files) ---"
$bathroomFiles = @(
    "3D BATHROOM DETAIL.rvt",
    "FOLDING SHOWER GLASS DOOR DETAIL.rvt",
    "SHOWER ADJACENT TO BATHTUB DETAIL.rvt",
    "SHOWER CURB_GLAZING DETAIL.rvt",
    "SHOWER GLASS DETAIL WITH PARTIAL WALL.rvt",
    "SHOWER GLASS DOOR DETAIL.rvt",
    "TYPICAL BATH TUB DECK DETAIL.rvt",
    "TYPICAL MASTER BATH TUB DECK DETAIL-1.rvt",
    "GRABBAR.rvt",
    "KNEE WALL DETAIL.rvt",
    "RESTROOM PARTITION DETAILS.rvt",
    "RESTROOM PARTITION ELEVATION DETAILS.rvt"
)
foreach ($file in $bathroomFiles) {
    $src = "$harvestPath\Drafting Views\$file"
    $dst = "$libraryPath\12 - Bathroom Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else {
            Write-Output "  ~ $file (already exists)"
        }
    } else {
        Write-Output "  ! $file (not found)"
        $failed++
    }
}

Write-Output ""
Write-Output "--- Fire Protection Details (6 files) ---"
$fireFiles = @(
    "DETAIL OF 2 HR FIRE RATED DUCT _ WALL CONNECTION - UL U529.rvt",
    "FIRE STOPPING - PENETRATIONS.rvt",
    "FIRE STOPPING - WALL TO CEILING.rvt",
    "FIRE STOPPING - WALL TO DECK.rvt",
    "Fire Stopping FW Detail - 1054.rvt",
    "Fire Stopping HW Detail - 1049.rvt"
)
foreach ($file in $fireFiles) {
    $src = "$harvestPath\Drafting Views\$file"
    $dst = "$fireFolder\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else {
            Write-Output "  ~ $file (already exists)"
        }
    } else {
        Write-Output "  ! $file (not found)"
        $failed++
    }
}

Write-Output ""
Write-Output "--- Wall/Glazing Details (5 files) ---"
$wallFiles = @(
    "CURTAIN WALL PIPE PENETRATION DETAIL.rvt",
    "PARTIAL WALL_GLAZING DETAIL.rvt",
    "PARTITION TERMINATION AT MULLION WRAPPED.rvt",
    "UNIT_UNIT DEMISING WALL1.rvt",
    "FRAMING DETAIL @ INTERIOR GLASS POOL DECK CONDO LOBBY.rvt"
)
foreach ($file in $wallFiles) {
    $src = "$harvestPath\Drafting Views\$file"
    $dst = "$libraryPath\03 - Wall Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else {
            Write-Output "  ~ $file (already exists)"
        }
    } else {
        Write-Output "  ! $file (not found)"
        $failed++
    }
}

Write-Output ""
Write-Output "--- Site/Parking Details (2 files) ---"
$siteFiles = @(
    "WHEEL STOP DETAIL.rvt",
    "wheelchair-elevation.rvt"
)
foreach ($file in $siteFiles) {
    $src = "$harvestPath\Drafting Views\$file"
    $dst = "$libraryPath\99 - General Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else {
            Write-Output "  ~ $file (already exists)"
        }
    } else {
        Write-Output "  ! $file (not found)"
        $failed++
    }
}

Write-Output ""
Write-Output "--- Specialty Details (2 files) ---"
# Vanishing Edge -> 12 - Bathroom (pool related)
$src = "$harvestPath\Drafting Views\Vanishing Edge.rvt"
$dst = "$libraryPath\16 - Waterproofing & Insulation\Vanishing Edge.rvt"
if (Test-Path $src) {
    if (-not (Test-Path $dst)) {
        Copy-Item $src $dst
        Write-Output "  + Vanishing Edge.rvt"
        $copied++
    } else {
        Write-Output "  ~ Vanishing Edge.rvt (already exists)"
    }
}

# Scupper -> 01 - Roof Details
$src = "$harvestPath\Drafting Views\SCUPPER DETAILS.rvt"
$dst = "$libraryPath\01 - Roof Details\SCUPPER DETAILS.rvt"
if (Test-Path $src) {
    if (-not (Test-Path $dst)) {
        Copy-Item $src $dst
        Write-Output "  + SCUPPER DETAILS.rvt"
        $copied++
    } else {
        Write-Output "  ~ SCUPPER DETAILS.rvt (already exists)"
    }
}

Write-Output ""
Write-Output "--- Legends (10 files) ---"
$legendFiles = @(
    "ADA REQUIREMENTS.rvt",
    "ADA TOILETS AND BATH ACCESORIES.rvt",
    "DIMENSION CRITERIA.rvt",
    "FHA LEGEND.rvt",
    "GENERAL NOTES.rvt",
    "GRAPHIC SYMBOLS.rvt",
    "MATERIAL SYMBOL.rvt",
    "STANDARD MOUNTING HEGHTS.rvt",
    "WALL TYPES - CMU.rvt",
    "WALL TYPES - METAL FRAMING.rvt"
)
foreach ($file in $legendFiles) {
    $src = "$harvestPath\Legends\$file"
    $dst = "$legendsFolder\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else {
            Write-Output "  ~ $file (already exists)"
        }
    } else {
        Write-Output "  ! $file (not found)"
        $failed++
    }
}

Write-Output ""
Write-Output "=== SUMMARY ==="
Write-Output "Files copied: $copied"
Write-Output "Files skipped/failed: $failed"
Write-Output ""
Write-Output "New library folders created:"
Write-Output "  - 18 - Fire Protection"
Write-Output "  - 20 - Legends"
