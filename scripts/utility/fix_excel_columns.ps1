# Fix Excel file to properly separate room numbers and names

$excelPath = "D:\RevitMCPBridge2026\Level_7_Filled_Region_Areas.xlsx"

Write-Host "`nOpening Excel file: $excelPath" -ForegroundColor Yellow

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($excelPath)
    $worksheet = $workbook.Worksheets.Item(1)

    # Find the last row with data
    $lastRow = $worksheet.UsedRange.Rows.Count

    Write-Host "Processing $($lastRow - 4) rooms..." -ForegroundColor Yellow
    Write-Host ""

    # Process each data row (starting from row 5, after headers)
    for ($row = 5; $row -le $lastRow; $row++) {
        # Get current values
        $roomNumberCell = $worksheet.Cells.Item($row, 1).Text
        $roomNameCell = $worksheet.Cells.Item($row, 2).Text

        Write-Host "Row $row - Before:" -ForegroundColor Cyan
        Write-Host "  Col A (Room Number): '$roomNumberCell'" -ForegroundColor Gray
        Write-Host "  Col B (Room Name): '$roomNameCell'" -ForegroundColor Gray

        # Extract room number from room name if it exists
        # Match patterns like "OFFICE 01", "CONFERENCE 02", etc.
        if ($roomNameCell -match '^(.+?)\s+(\d{2,3})$') {
            $cleanName = $matches[1].Trim()
            $number = $matches[2]

            # Update cells
            $worksheet.Cells.Item($row, 1) = $number
            $worksheet.Cells.Item($row, 2) = $cleanName

            Write-Host "  After:" -ForegroundColor Green
            Write-Host "  Col A (Room Number): '$number'" -ForegroundColor Green
            Write-Host "  Col B (Room Name): '$cleanName'" -ForegroundColor Green
        } else {
            # No number found in name, just clean up any trailing spaces
            $cleanName = $roomNameCell.Trim()
            $worksheet.Cells.Item($row, 2) = $cleanName

            Write-Host "  After: No changes needed" -ForegroundColor Yellow
        }
        Write-Host ""
    }

    Write-Host "Saving changes..." -ForegroundColor Yellow
    $workbook.Save()
    $workbook.Close()

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Excel file updated" -ForegroundColor Green
    Write-Host ""
    Write-Host "Column A: Room Number only (01, 02, 03...)" -ForegroundColor Cyan
    Write-Host "Column B: Room Name only (OFFICE, CONFERENCE...)" -ForegroundColor Cyan
    Write-Host "Column C: Square Footage" -ForegroundColor Cyan
    Write-Host ""
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($worksheet) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($workbook) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
