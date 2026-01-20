param(
    [string]$FilePath = "D:/001 - PROJECTS/01 - CLIENT PROJECTS/01 - ARKY/010-20 NW 76 Street Miami - New 4 Story Building/Permit Comments/Status Report as of July 31, 2025 - Updated (2).xlsx"
)

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($FilePath)

    Write-Host "=== WRITING RESPONSES TO EXCEL ===" -ForegroundColor Cyan

    # Column F is typically for responses (column 6), G for sheet references (column 7)
    # Adjust based on actual structure

    # --- ZONING SHEET ---
    $zoning = $workbook.Sheets.Item("ZONING")
    Write-Host "`nZONING RESPONSES:" -ForegroundColor Yellow

    # Row 3: BBL comment
    $zoning.Cells.Item(3, 7).Value = "Noted. BBL to be provided by Public Works."
    $zoning.Cells.Item(3, 8).Value = "SP-1.0"

    # Row 4: Zoning legend
    $zoning.Cells.Item(4, 7).Value = "Refer to zoning legend on SP-1.0"
    $zoning.Cells.Item(4, 8).Value = "SP-1.0"

    # Row 5: Parking - IMPORTANT
    $zoning.Cells.Item(5, 7).Value = "Project qualifies for Affordable Housing parking reduction per Miami 21 Article 4. 5 spaces provided including 1 HC."
    $zoning.Cells.Item(5, 8).Value = "SP-1.0"

    # Row 6: Lot coverage
    $zoning.Cells.Item(6, 7).Value = "Lot coverage diagram added to SP-1.0. Clouded."
    $zoning.Cells.Item(6, 8).Value = "SP-1.0"

    # Row 7: Section 5.5.1(e)
    $zoning.Cells.Item(7, 7).Value = "Compliance verified. See site plan."
    $zoning.Cells.Item(7, 8).Value = "SP-1.0"

    # Row 8: Section 5.5.1(f)
    $zoning.Cells.Item(8, 7).Value = "Compliance verified. See site plan."
    $zoning.Cells.Item(8, 8).Value = "SP-1.0"

    # Row 9: Condensing units
    $zoning.Cells.Item(9, 7).Value = "Condensing units located on roof, behind parapet, screened from lateral view. See roof plan."
    $zoning.Cells.Item(9, 8).Value = "A-2.1"

    # Row 10: Backflow preventer
    $zoning.Cells.Item(10, 7).Value = "Backflow preventer located at rear of property in screened enclosure per Miami 21 Sec. 5.5.2(i). See site plan."
    $zoning.Cells.Item(10, 8).Value = "SP-1.0"

    # Row 11: Parking location
    $zoning.Cells.Item(11, 7).Value = "Parking in third layer, no parking in first layer. Compliance verified."
    $zoning.Cells.Item(11, 8).Value = "SP-1.0"

    # Row 12: Driveway width
    $zoning.Cells.Item(12, 7).Value = "Driveway width: 20'-0\" shown on site plan."
    $zoning.Cells.Item(12, 8).Value = "SP-1.0"

    # Row 13: Drive aisle
    $zoning.Cells.Item(13, 7).Value = "Drive aisle: 24'-0\" noted on site plan."
    $zoning.Cells.Item(13, 8).Value = "SP-1.0"

    # Row 14: Roof materials
    $zoning.Cells.Item(14, 7).Value = "Note added: Roof material to be light-colored, high albedo per Miami 21 Sec. 5.5.5(c)."
    $zoning.Cells.Item(14, 8).Value = "A-2.1"

    # Row 15: Visibility triangles
    $zoning.Cells.Item(15, 7).Value = "10' visibility triangles noted at driveway intersection per Art. 3 Sec. 3.8.4.1(b)."
    $zoning.Cells.Item(15, 8).Value = "SP-1.0"

    # Row 16: Parking space width
    $zoning.Cells.Item(16, 7).Value = "Parking spaces: 8'-6\" x 18'-0\" per City standards. Noted on site plan."
    $zoning.Cells.Item(16, 8).Value = "SP-1.0"

    # Row 17: EV parking
    $zoning.Cells.Item(17, 7).Value = "1 EV-Capable parking space designated (20% of 5 = 1 required)."
    $zoning.Cells.Item(17, 8).Value = "SP-1.0"

    # Row 18: Landscape
    $zoning.Cells.Item(18, 7).Value = "Landscape plans by registered LA to be provided."
    $zoning.Cells.Item(18, 8).Value = "By LA"

    # Row 19: Irrigation
    $zoning.Cells.Item(19, 7).Value = "Irrigation plan to be provided with landscape plans."
    $zoning.Cells.Item(19, 8).Value = "By LA"

    # Row 20: Shrubs
    $zoning.Cells.Item(20, 7).Value = "Shrub requirements per Sec. 9.5.6(a) to be addressed in landscape plans."
    $zoning.Cells.Item(20, 8).Value = "By LA"

    # Row 21: First layer paving
    $zoning.Cells.Item(21, 7).Value = "First layer: 6.5' paved flush with sidewalk per Illustration 8.4(b). Noted."
    $zoning.Cells.Item(21, 8).Value = "SP-1.0"

    Write-Host "  Zoning responses written (19 items)"

    # --- FIRE SHEET ---
    $fire = $workbook.Sheets.Item("FIRE")
    Write-Host "`nFIRE RESPONSES:" -ForegroundColor Yellow

    # Row 3: 20-min doors
    $fire.Cells.Item(3, 7).Value = "Note added: All doors to corridor 20-minute fire rated per NFPA 101 Sec. 30.3.6.2.1."
    $fire.Cells.Item(3, 8).Value = "ALS-0.6"

    # Row 4: EV parking
    $fire.Cells.Item(4, 7).Value = "1 EV-Capable space provided per Zoning. See site plan."
    $fire.Cells.Item(4, 8).Value = "SP-1.0"

    # Row 5: 4th floor life safety
    $fire.Cells.Item(5, 7).Value = "Note added: 4th floor life safety is typical to 2nd & 3rd floors. See ALS-0.6."
    $fire.Cells.Item(5, 8).Value = "ALS-0.6"

    # Row 6: Site plan fire features
    $fire.Cells.Item(6, 7).Value = "FDC location added to site plan. Fire hydrant per City standards."
    $fire.Cells.Item(6, 8).Value = "SP-1.0"

    # Row 7: Sprinkler
    $fire.Cells.Item(7, 7).Value = "Note added: Building protected throughout by automatic sprinkler per NFPA 101 Sec. 30.3.5.1."
    $fire.Cells.Item(7, 8).Value = "ALS-0.6"

    # Row 8: EV (duplicate)
    $fire.Cells.Item(8, 7).Value = "See response to comment 4."
    $fire.Cells.Item(8, 8).Value = "SP-1.0"

    # Row 9: 4th floor (duplicate)
    $fire.Cells.Item(9, 7).Value = "See response to comment 5."
    $fire.Cells.Item(9, 8).Value = "ALS-0.6"

    # Row 10: Site plan fire (duplicate)
    $fire.Cells.Item(10, 7).Value = "See response to comment 6."
    $fire.Cells.Item(10, 8).Value = "SP-1.0"

    # Row 11: Fire alarm
    $fire.Cells.Item(11, 7).Value = "Note added: Fire alarm system provided per NFPA 101 Sec. 30.3.4.1.1."
    $fire.Cells.Item(11, 8).Value = "ALS-0.6"

    # Row 12: 20-min doors (duplicate)
    $fire.Cells.Item(12, 7).Value = "See response to comment 3."
    $fire.Cells.Item(12, 8).Value = "ALS-0.6"

    # Row 13: Fire protection pages
    $fire.Cells.Item(13, 7).Value = "Fire Protection and Fire Alarm pages to be provided by MEP."
    $fire.Cells.Item(13, 8).Value = "By MEP"

    # Row 14: Occupant load
    $fire.Cells.Item(14, 7).Value = "Occupant load calculation added: 6 units x 2 persons = 12 max per NFPA 101 Sec. 7.3.1.2."
    $fire.Cells.Item(14, 8).Value = "ALS-0.6"

    # Row 15: Single exit code
    $fire.Cells.Item(15, 7).Value = "Single exit permitted per NFPA 101 Sec. 30.2.4.2 (4 stories max, sprinklered). Note added."
    $fire.Cells.Item(15, 8).Value = "ALS-0.6"

    Write-Host "  Fire responses written (13 items)"

    # --- FLOOD PLAIN SHEET ---
    $flood = $workbook.Sheets.Item("FLOOD PLAIN")
    Write-Host "`nFLOOD PLAIN RESPONSES:" -ForegroundColor Yellow

    # Row 3: F.F.E. in NGVD
    $flood.Cells.Item(3, 7).Value = "F.F.E. in NGVD added to A-1.1 and SP-1.0. Values to be verified with survey."
    $flood.Cells.Item(3, 8).Value = "A-1.1, SP-1.0"

    # Row 4: Structural drawings
    $flood.Cells.Item(4, 7).Value = "Structural drawings to be provided by Structural Engineer."
    $flood.Cells.Item(4, 8).Value = "By SE"

    # Row 5: Drainage plan
    $flood.Cells.Item(5, 7).Value = "Drainage plan with 100-year storm calculations to be provided by Civil Engineer."
    $flood.Cells.Item(5, 8).Value = "By CE"

    Write-Host "  Flood Plain responses written (3 items)"

    # --- BUILDING SHEET ---
    $building = $workbook.Sheets.Item("BUILDING")
    Write-Host "`nBUILDING RESPONSES:" -ForegroundColor Yellow

    # Row 3: Demolition
    $building.Cells.Item(3, 7).Value = "Demolition permit application to be filed by Owner."
    $building.Cells.Item(3, 8).Value = "Owner"

    # Row 4: Fence
    $building.Cells.Item(4, 7).Value = "6'-0\" aluminum privacy fence. See site plan and detail."
    $building.Cells.Item(4, 8).Value = "SP-1.0"

    # Row 5: FL Architect seal
    $building.Cells.Item(5, 7).Value = "All architectural drawings signed and sealed by FL Licensed Architect."
    $building.Cells.Item(5, 8).Value = "All A-sheets"

    # Row 6: Complete permit
    $building.Cells.Item(6, 7).Value = "Complete documents resubmitted."
    $building.Cells.Item(6, 8).Value = "All sheets"

    # Row 7: FBC 1021.4
    $building.Cells.Item(7, 7).Value = "Exit location complies with FBC 1021.4. Single exit per NFPA 101 Sec. 30.2.4.2."
    $building.Cells.Item(7, 8).Value = "ALS-0.6"

    Write-Host "  Building responses written (5 items)"

    # Save the workbook
    $workbook.Save()
    $workbook.Close($true)

    Write-Host "`n=== EXCEL RESPONSES COMPLETE ===" -ForegroundColor Green
    Write-Host "File saved: $FilePath"
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
