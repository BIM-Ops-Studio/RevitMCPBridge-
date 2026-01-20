$sklarPath = "D:\003 - RESOURCES\01 - REVIT LIBRARY\MISC REVIT LIBRARY\SKLAR REVIT 2D DETAILS"
$libraryPath = "D:\Revit Detail Libraries\Revit Details"

$copied = 0
$skipped = 0

Write-Output "=== Copying SKLAR Details to Library ==="
Write-Output ""

# Create new folders if needed
$siteFolder = "$libraryPath\19 - Site Details"
$ulFolder = "$libraryPath\18 - Fire Protection"
$legendsFolder = "$libraryPath\20 - Legends"

if (-not (Test-Path $siteFolder)) {
    New-Item -ItemType Directory -Path $siteFolder | Out-Null
    Write-Output "Created folder: 19 - Site Details"
}

# === ROOF/DRAINAGE DETAILS ===
Write-Output ""
Write-Output "--- Roof/Drainage Details ---"
$roofFiles = @(
    "DRAINAGE SCUPPER @ BUILT-UP ROOF.rvt",
    "DRAINAGE SCUPPER @ BUILT-UP ROOF_WITH STUCCO.rvt",
    "DRAINAGE SCUPPER.rvt",
    "OVERFLOW DRAINAGE SCUPPER.rvt",
    "PARAPET STUCCO CAP DETAIL.rvt",
    "PARAPET WALL DETAIL @ BUILT-UP ROOF.rvt",
    "PARAPET WALL DETAIL W_STUCCO @ BUILT-UP ROOF.rvt",
    "ROOF ACCESS HATCH DETAIL.rvt",
    "ROOF DECK DETAIL @ CMU W STUCCO.rvt",
    "ROOF DECK DETAIL @ CMU.rvt",
    "ROOF EVE @ TOWER.rvt",
    "TYP ROOF PENETRATION DETAIL.rvt",
    "TYP. PARAPET FLASHING DETAL.rvt",
    "TYP. PARAPET WALL DETAIL W-INSULATION.rvt",
    "TYP. PARAPET WALL DETAIL.rvt",
    "SKLAR TYP. PARAPET DETAIL.rvt",
    "DETAIL OF SLOPED EAVE @ FLAT ROOF.rvt"
)
foreach ($file in $roofFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\01 - Roof Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === DOOR DETAILS ===
Write-Output ""
Write-Output "--- Door Details ---"
$doorFiles = @(
    "ELEVATOR DOOR HEAD DETAIL.rvt",
    "ELEVATOR DOOR JAMB DETAIL.rvt",
    "ELEVATOR DOOR SILL DETAIL.rvt",
    "ENTRY DOUBLE DOOR.rvt",
    "FRENCH DOOR.rvt",
    "HEAD_SILL BIFOLD DETAIL.rvt",
    "METAL DOOR - EXTERIOR JAMB_HEADER_SILL.rvt",
    "METAL DOOR - INTERIOR JAMB_HEADER.rvt",
    "SINGLE DOOR @ TYP. OFFICE ENTRY CONDITION.rvt",
    "WOOD DOOR DETAIL (INTERIOR).rvt",
    "WOOD DOOR JAMB.rvt",
    "SKLAR DOOR-WINDOW DETAILS.rvt"
)
foreach ($file in $doorFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\05 - Door Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === WINDOW DETAILS ===
Write-Output ""
Write-Output "--- Window Details ---"
$windowFiles = @(
    "FIXED PANEL.rvt",
    "SINGLE HUNG WINDOW.rvt",
    "SLIDING GLASS DOOR.rvt",
    "PYRAMID SKYLIGHT.rvt",
    "SKYLIGHT SILL.rvt",
    "SLOPED SKYLIGHT.rvt",
    "TYP STOREFRONT DETAILS @ EXTG WALL - DOOR.rvt",
    "TYP STOREFRONT DETAILS @ EXTG WALL.rvt",
    "TYP STOREFRONT DETAILS.rvt",
    "TYP STOREFRONT HEADER_JAMB & SILL DETAILS.rvt",
    "DETAIL ELEVATION & SECTION @ WINDOW CORNICE.rvt"
)
foreach ($file in $windowFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\06 - Window Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === WALL DETAILS ===
Write-Output ""
Write-Output "--- Wall Details ---"
$wallFiles = @(
    "BLOCK-UP DETAIL.rvt",
    "DETAIL @ STUCCO CORNERS.rvt",
    "DETAIL @ STUCCO MOULDING.rvt",
    "FLAT STUCCO BAND.rvt",
    "STUCCO EXPANSION JOINT.rvt",
    "STUCCO REVEAL DETAIL.rvt",
    "PRIVACY WALL.rvt",
    "PIPE PENETRATION DETAIL.rvt"
)
foreach ($file in $wallFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\03 - Wall Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === STAIR/RAILING DETAILS ===
Write-Output ""
Write-Output "--- Stair/Railing Details ---"
$stairFiles = @(
    "STAIR & RAMP RAILING DETAILS.rvt",
    "STAIR TREAD @ PLATFORM.rvt",
    "TYP. HANDRAIL_GUARDRAIL_RISER DETAILS.rvt",
    "SECTION @ ADA RAMP.rvt",
    "GLASS GUARD_BAFFLE.rvt"
)
foreach ($file in $stairFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\07 - Stair & Railing\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === CEILING DETAILS ===
Write-Output ""
Write-Output "--- Ceiling Details ---"
$ceilingFiles = @(
    "COVE LIGHT SOFFIT @ BEAM.rvt",
    "SOFFIT DETAIL.rvt",
    "TYP COVE LIGHT.rvt",
    "TYP. CEILING DETAIL.rvt",
    "TYP. GWB CEILING DETAIL.rvt",
    "TYP. SOFFIT DETAIL.rvt"
)
foreach ($file in $ceilingFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\08 - Ceiling Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === BATHROOM DETAILS ===
Write-Output ""
Write-Output "--- Bathroom Details ---"
$bathFiles = @(
    "SHOWER PAN DETAIL (TYPICAL).rvt",
    "TYP. ADA VANITY DETAIL.rvt",
    "LOCATION OF GRAB BARS (FOR ALL RESIDENTIAL UNITS).rvt",
    "Toilet_Accessories_Elevation_4020.rvt"
)
foreach ($file in $bathFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\12 - Bathroom Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === FIRE PROTECTION / UL DETAILS ===
Write-Output ""
Write-Output "--- Fire Protection / UL Details ---"
$fireFiles = @(
    "FIRE STOPPING DETAILS.rvt",
    "INSUL MTL PIPE _ CONC FLOOR - UL# C-AJ-5138.rvt",
    "INSUL MTL PIPE _ CONC FLOOR - UL# C-AJ-5155.rvt",
    "INSUL MTL PIPE _ CONC FLOOR - UL# W-L-5121.rvt",
    "INSUL MTL PIPE _ CONC FLOOR - UL# W-L-5122.rvt",
    "METALIC PIPES_TUBING UL# W-L-1028.rvt",
    "MTL PIPE _ CONC FLOOR - UL# C-AJ-1353.rvt",
    "MTL PIPE _ CONC FLOOR - UL# C-AJ-2297.rvt",
    "NON MTL PIPE _ CONC FLOOR - UL# C-AJ-2137.rvt",
    "NON MTL PIPE _ CONC FLOOR - UL# C-AJ-2362.rvt",
    "NON MTL PIPE _ CONC FLOOR - UL#CAJ2031.rvt",
    "NON-METALIC PIPES_TUBING UL# W-L-2046.rvt",
    "NON-METALIC PIPES_TUBING UL# W-L-2243.rvt",
    "NON-METALIC PIPES_TUBING UL# W-L-2288.rvt",
    "NON-METALIC PIPES_TUBING UL# W-L-2497.rvt",
    "NON-METALIC PIPES_TUBING UL# W-L-2498.rvt",
    "TYP. STEEL COLUMN AND BEAM FIREPROOFING.rvt",
    "TYP. EPICORE SLAB UL DESIGN NO. D938.rvt",
    "SKLAR UL DETAIL.rvt"
)
foreach ($file in $fireFiles) {
    $src = "$sklarPath\$file"
    $dst = "$ulFolder\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === SITE DETAILS ===
Write-Output ""
Write-Output "--- Site Details ---"
$siteFiles = @(
    "DOUBLE GATE DETAIL.rvt",
    "DUMPSTER FRONT ELEVATION.rvt",
    "DUMPSTER PLAN.rvt",
    "DUMPSTER SIDE ELEVATION (TYP).rvt",
    "DUMPSTER WALL SECTION.rvt",
    "GREEN SCREEN DETAIL- FREESTANDING FENCE_SCREEN.rvt",
    "PAVERS DETAIL.rvt",
    "TYP BOLLARD DETAIL.rvt",
    "TYP PAVER EDGE DETAIL @ DRIVEWAYS & PATIO.rvt",
    "TYP PAVER EDGE DETAIL @ WALKWAYS.rvt",
    "TYP PROPERTY FENCE DETAIL.rvt",
    "WOOD FENCE DETAIL.rvt",
    "DRINKING FOUNTAIN DETAILS.rvt",
    "MAIL BOXES.rvt",
    "TRASH CHUTE & VENT DETAILS.rvt"
)
foreach ($file in $siteFiles) {
    $src = "$sklarPath\$file"
    $dst = "$siteFolder\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === MEP DETAILS ===
Write-Output ""
Write-Output "--- MEP Details ---"
$mepFiles = @(
    "BACKFLOW PREVENTER DETAIL.rvt",
    "BACKFLOW PREVENTER ELEVATION.rvt",
    "BACKFLOW PREVENTER PLAN.rvt"
)
foreach ($file in $mepFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\14 - MEP Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === CABINETRY/MILLWORK ===
Write-Output ""
Write-Output "--- Cabinetry/Millwork Details ---"
$cabinetFiles = @(
    "BANQUETTE_ BENCH SECTION.rvt",
    "BAR SECTION.rvt",
    "TYP. CLEARANCE BETWEEN KITCHEN COUNTERS.rvt",
    "TYP. MIN. CLEARANCE IN U-SHAPED KITCHEN.rvt"
)
foreach ($file in $cabinetFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\02 - Cabinetry & Millwork\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === GENERAL/MISC DETAILS ===
Write-Output ""
Write-Output "--- General/Misc Details ---"
$generalFiles = @(
    "ADA SIGN DETAIL.rvt",
    "BALCONY EDGE DETAIL W_ TILE.rvt",
    "BALCONY EDGE DETAIL.rvt",
    "DETAIL @ DECORATIVE BRACKET.rvt",
    "DETAIL @ ELEVATOR ROOF.rvt",
    "MOUNTING HEIGHTS.rvt",
    "TYP. MOUNTING HEIGHTS.rvt"
)
foreach ($file in $generalFiles) {
    $src = "$sklarPath\$file"
    $dst = "$libraryPath\99 - General Details\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

# === LEGENDS/WALL TYPES ===
Write-Output ""
Write-Output "--- Legends/Wall Types ---"
$legendFiles = @(
    "WALL TYPE - 1 HR RATED PARTITION.rvt",
    "WALL TYPE - 1 HR RATED PARTITIONS.rvt",
    "WALL TYPE - 2 HR RATED PARTITION.rvt",
    "WALL TYPE - 2 HR RATED SHAFT WALL.rvt",
    "WALL TYPE - CMU W_ CHASE WALL.rvt",
    "WALL TYPE - CMU.rvt",
    "WALL TYPE - CONCRETE SHEAR WALL.rvt",
    "WALL TYPE - CONCRETE WALL W_ STL STUD FURR OUT.rvt",
    "WALL TYPE - EXISTING RATED PARTITIONS.rvt",
    "WALL TYPE - EXTG EXTERIOR CMU.rvt",
    "WALL TYPE - INTERIOR CMU.rvt",
    "WALL TYPE - INTERIOR FULL STOREFRONT PARTITION.rvt",
    "WALL TYPE - INTERIOR_EXTERIOR CMU.rvt",
    "WALL TYPE - NON RATED PARTITION.rvt",
    "HANDICAP ACCESSIBILITY GENERAL NOTES.rvt"
)
foreach ($file in $legendFiles) {
    $src = "$sklarPath\$file"
    $dst = "$legendsFolder\$file"
    if (Test-Path $src) {
        if (-not (Test-Path $dst)) {
            Copy-Item $src $dst
            Write-Output "  + $file"
            $copied++
        } else { $skipped++ }
    }
}

Write-Output ""
Write-Output "=== SUMMARY ==="
Write-Output "Files copied: $copied"
Write-Output "Files skipped (already exist): $skipped"
Write-Output ""
Write-Output "New library folder created:"
Write-Output "  - 19 - Site Details"
