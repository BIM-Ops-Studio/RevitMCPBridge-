$FilePath = "D:\001 - PROJECTS\01 - CLIENT PROJECTS\01 - ARKY\010-20 NW 76 Street Miami - New 4 Story Building\Permit Comments\Status Report as of July 31, 2025 - Updated (2).xlsx"

Write-Host "Opening Excel..." -ForegroundColor Cyan
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

Write-Host "Opening workbook: $FilePath"
$workbook = $excel.Workbooks.Open($FilePath)

Write-Host "Sheets in workbook:"
foreach ($sheet in $workbook.Sheets) {
    Write-Host "  - $($sheet.Name)"
}

# Try ZONING sheet
Write-Host "`nWriting to ZONING sheet..."
$zoning = $workbook.Sheets.Item("ZONING")

# The structure shows: No.# (col 1), Reviewer's Comments (col 2), Date (col 3), Days (col 4), Owner (col 5), Architect (col 6), Retriving (col 7)
# We need to add response columns. Let's check column 8 and 9

# Add headers for response columns if not present
$zoning.Cells.Item(2, 8).Value = "Response"
$zoning.Cells.Item(2, 9).Value = "Sheet Reference"

# Row 3 - Comment 1: BBL
$zoning.Cells.Item(3, 8).Value = "Noted. BBL to be provided by Public Works."
$zoning.Cells.Item(3, 9).Value = "SP-1.0"

# Row 4 - Comment 2: Zoning legend
$zoning.Cells.Item(4, 8).Value = "Refer to zoning legend on SP-1.0"
$zoning.Cells.Item(4, 9).Value = "SP-1.0"

# Row 5 - Comment 3: Parking
$zoning.Cells.Item(5, 8).Value = "Affordable housing parking reduction. 5 spaces incl. 1 HC provided."
$zoning.Cells.Item(5, 9).Value = "SP-1.0"

# Row 6 - Comment 4: Lot coverage
$zoning.Cells.Item(6, 8).Value = "Lot coverage diagram added. Clouded Rev 1."
$zoning.Cells.Item(6, 9).Value = "SP-1.0"

# Row 7 - Comment 5: Sec 5.5.1(e)
$zoning.Cells.Item(7, 8).Value = "Compliance verified."
$zoning.Cells.Item(7, 9).Value = "SP-1.0"

# Row 8 - Comment 6: Sec 5.5.1(f)
$zoning.Cells.Item(8, 8).Value = "Compliance verified."
$zoning.Cells.Item(8, 9).Value = "SP-1.0"

# Row 9 - Comment 7: Condensing units
$zoning.Cells.Item(9, 8).Value = "Located on roof, behind parapet, screened. Clouded Rev 1."
$zoning.Cells.Item(9, 9).Value = "A-2.1"

# Row 10 - Comment 8: Backflow
$zoning.Cells.Item(10, 8).Value = "Rear of property in screened enclosure per Sec. 5.5.2(i). Clouded Rev 1."
$zoning.Cells.Item(10, 9).Value = "SP-1.0"

# Row 11 - Comment 9: Parking layers
$zoning.Cells.Item(11, 8).Value = "Parking in third layer, none in first layer."
$zoning.Cells.Item(11, 9).Value = "SP-1.0"

# Row 12 - Comment 10: Driveway width
$zoning.Cells.Item(12, 8).Value = "20'-0"" shown. Clouded Rev 1."
$zoning.Cells.Item(12, 9).Value = "SP-1.0"

# Row 13 - Comment 11: Drive aisle
$zoning.Cells.Item(13, 8).Value = "24'-0"" noted. Clouded Rev 1."
$zoning.Cells.Item(13, 9).Value = "SP-1.0"

# Row 14 - Comment 12: Roof materials
$zoning.Cells.Item(14, 8).Value = "Light-colored/high albedo note added. Clouded Rev 1."
$zoning.Cells.Item(14, 9).Value = "A-2.1"

# Row 15 - Comment 13: Visibility triangles
$zoning.Cells.Item(15, 8).Value = "10' triangles noted per 3.8.4.1(b). Clouded Rev 1."
$zoning.Cells.Item(15, 9).Value = "SP-1.0"

# Row 16 - Comment 14: Parking dimensions
$zoning.Cells.Item(16, 8).Value = "8'-6"" x 18'-0"" noted. Clouded Rev 1."
$zoning.Cells.Item(16, 9).Value = "SP-1.0"

# Row 17 - Comment 15: EV parking
$zoning.Cells.Item(17, 8).Value = "1 EV-Capable space designated (20% of 5). Clouded Rev 1."
$zoning.Cells.Item(17, 9).Value = "SP-1.0"

# Rows 18-20: Landscape (By LA)
$zoning.Cells.Item(18, 8).Value = "By Landscape Architect"
$zoning.Cells.Item(18, 9).Value = "LA"
$zoning.Cells.Item(19, 8).Value = "By Landscape Architect"
$zoning.Cells.Item(19, 9).Value = "LA"
$zoning.Cells.Item(20, 8).Value = "By Landscape Architect"
$zoning.Cells.Item(20, 9).Value = "LA"

# Row 21 - Comment 19: First layer
$zoning.Cells.Item(21, 8).Value = "6.5' paved flush with sidewalk noted. Clouded Rev 1."
$zoning.Cells.Item(21, 9).Value = "SP-1.0"

# Row 22-23: Remaining
$zoning.Cells.Item(22, 8).Value = "Certificate to be provided by Owner"
$zoning.Cells.Item(22, 9).Value = "Owner"
$zoning.Cells.Item(23, 8).Value = "Acknowledged"
$zoning.Cells.Item(23, 9).Value = "-"

Write-Host "  ZONING complete"

# FIRE sheet
Write-Host "Writing to FIRE sheet..."
$fire = $workbook.Sheets.Item("FIRE")
$fire.Cells.Item(2, 8).Value = "Response"
$fire.Cells.Item(2, 9).Value = "Sheet Reference"

$fire.Cells.Item(3, 8).Value = "20-min doors noted per NFPA 101 30.3.6.2.1. Clouded Rev 1."
$fire.Cells.Item(3, 9).Value = "ALS-0.6"
$fire.Cells.Item(4, 8).Value = "1 EV-Capable space provided."
$fire.Cells.Item(4, 9).Value = "SP-1.0"
$fire.Cells.Item(5, 8).Value = "4th floor typical to 2nd/3rd noted. Clouded Rev 1."
$fire.Cells.Item(5, 9).Value = "ALS-0.6"
$fire.Cells.Item(6, 8).Value = "FDC location added. Clouded Rev 1."
$fire.Cells.Item(6, 9).Value = "SP-1.0"
$fire.Cells.Item(7, 8).Value = "Sprinkler note added per NFPA 101 30.3.5.1. Clouded Rev 1."
$fire.Cells.Item(7, 9).Value = "ALS-0.6"
$fire.Cells.Item(8, 8).Value = "See comment 4"
$fire.Cells.Item(8, 9).Value = "SP-1.0"
$fire.Cells.Item(9, 8).Value = "See comment 5"
$fire.Cells.Item(9, 9).Value = "ALS-0.6"
$fire.Cells.Item(10, 8).Value = "See comment 6"
$fire.Cells.Item(10, 9).Value = "SP-1.0"
$fire.Cells.Item(11, 8).Value = "Fire alarm note added per NFPA 101 30.3.4.1.1. Clouded Rev 1."
$fire.Cells.Item(11, 9).Value = "ALS-0.6"
$fire.Cells.Item(12, 8).Value = "See comment 3"
$fire.Cells.Item(12, 9).Value = "ALS-0.6"
$fire.Cells.Item(13, 8).Value = "By MEP Engineer"
$fire.Cells.Item(13, 9).Value = "MEP"
$fire.Cells.Item(14, 8).Value = "Occupant load: 6 units x 2 = 12. Clouded Rev 1."
$fire.Cells.Item(14, 9).Value = "ALS-0.6"
$fire.Cells.Item(15, 8).Value = "Single exit per NFPA 101 30.2.4.2 (sprinklered). Clouded Rev 1."
$fire.Cells.Item(15, 9).Value = "ALS-0.6"

Write-Host "  FIRE complete"

# FLOOD PLAIN sheet
Write-Host "Writing to FLOOD PLAIN sheet..."
$flood = $workbook.Sheets.Item("FLOOD PLAIN")
$flood.Cells.Item(2, 8).Value = "Response"
$flood.Cells.Item(2, 9).Value = "Sheet Reference"

$flood.Cells.Item(3, 8).Value = "F.F.E. in NGVD added. Verify w/ survey. Clouded Rev 1."
$flood.Cells.Item(3, 9).Value = "A-1.1, SP-1.0"
$flood.Cells.Item(4, 8).Value = "By Structural Engineer"
$flood.Cells.Item(4, 9).Value = "SE"
$flood.Cells.Item(5, 8).Value = "By Civil Engineer (100-year storm)"
$flood.Cells.Item(5, 9).Value = "CE"

Write-Host "  FLOOD PLAIN complete"

# BUILDING sheet
Write-Host "Writing to BUILDING sheet..."
$building = $workbook.Sheets.Item("BUILDING")
$building.Cells.Item(2, 8).Value = "Response"
$building.Cells.Item(2, 9).Value = "Sheet Reference"

$building.Cells.Item(3, 8).Value = "Demolition permit to be filed by Owner"
$building.Cells.Item(3, 9).Value = "Owner"
$building.Cells.Item(4, 8).Value = "6'-0"" aluminum privacy fence. See detail."
$building.Cells.Item(4, 9).Value = "SP-1.0"
$building.Cells.Item(5, 8).Value = "All A-sheets signed/sealed by FL Architect"
$building.Cells.Item(5, 9).Value = "All A-sheets"
$building.Cells.Item(6, 8).Value = "Complete resubmittal provided"
$building.Cells.Item(6, 9).Value = "All sheets"
$building.Cells.Item(7, 8).Value = "Exit per FBC 1021.4 / NFPA 101 30.2.4.2"
$building.Cells.Item(7, 9).Value = "ALS-0.6"

Write-Host "  BUILDING complete"

# Save and close
Write-Host "`nSaving workbook..."
$workbook.Save()
$workbook.Close($true)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

Write-Host "`n=== EXCEL RESPONSES COMPLETE ===" -ForegroundColor Green
