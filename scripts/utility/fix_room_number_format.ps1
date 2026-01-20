# Fix room numbers to have leading zeros (01, 02, 03...)

$excelPath = "D:\RevitMCPBridge2026\Level_7_Filled_Region_Areas.xlsx"

Write-Host "`nFixing room number format (adding leading zeros)" -ForegroundColor Yellow

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($excelPath)
    $worksheet = $workbook.Worksheets.Item(1)

    # Find the last row with data
    $lastRow = $worksheet.UsedRange.Rows.Count

    Write-Host "Processing $($lastRow - 4) rooms...`n" -ForegroundColor Yellow

    # Fix room numbers (Column B)
    for ($row = 5; $row -le $lastRow; $row++) {
        $roomNumber = $worksheet.Cells.Item($row, 2).Text

        # Convert to integer and format with leading zero
        $formattedNumber = "{0:D2}" -f [int]$roomNumber

        # Update the cell
        $worksheet.Cells.Item($row, 2) = $formattedNumber

        if (($row - 4) % 10 -eq 0) {
            Write-Host "  Fixed row ${row}: '$roomNumber' -> '$formattedNumber'" -ForegroundColor Gray
        }
    }

    Write-Host ""
    Write-Host "Sample of fixed data:" -ForegroundColor Cyan
    for ($row = 5; $row -le 9; $row++) {
        $name = $worksheet.Cells.Item($row, 1).Text
        $number = $worksheet.Cells.Item($row, 2).Text
        $sf = $worksheet.Cells.Item($row, 3).Text
        Write-Host "  Row ${row}: Name='$name', Number='$number', SF='$sf'" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "Saving changes..." -ForegroundColor Yellow
    $workbook.Save()
    $workbook.Close()

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Room numbers formatted with leading zeros" -ForegroundColor Green
    Write-Host ""
    Write-Host "Column A: Room Name (OFFICE, MECH., etc.)" -ForegroundColor Cyan
    Write-Host "Column B: Room Number (01, 02, 03...)" -ForegroundColor Cyan
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
