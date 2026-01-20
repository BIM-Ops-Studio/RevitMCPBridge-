# Swap Column A and Column B (Name first, then Number)

$excelPath = "D:\RevitMCPBridge2026\Level_7_Filled_Region_Areas.xlsx"

Write-Host "`nSwapping columns A and B in Excel file" -ForegroundColor Yellow
Write-Host "New order: Room Name, Room Number, Square Footage`n" -ForegroundColor Cyan

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($excelPath)
    $worksheet = $workbook.Worksheets.Item(1)

    # Find the last row with data
    $lastRow = $worksheet.UsedRange.Rows.Count

    Write-Host "Swapping data for $($lastRow - 4) rooms..." -ForegroundColor Yellow
    Write-Host ""

    # First, update headers (row 4)
    $worksheet.Cells.Item(4, 1) = "Room Name"
    $worksheet.Cells.Item(4, 2) = "Room Number"
    # Column 3 stays as "Square Footage"

    # Now swap the data in all rows
    for ($row = 5; $row -le $lastRow; $row++) {
        # Read current values
        $colA = $worksheet.Cells.Item($row, 1).Text  # Currently has Number
        $colB = $worksheet.Cells.Item($row, 2).Text  # Currently has Name

        # Swap them
        $worksheet.Cells.Item($row, 1) = $colB  # Name goes to Column A
        $worksheet.Cells.Item($row, 2) = $colA  # Number goes to Column B

        if (($row - 4) % 10 -eq 0) {
            Write-Host "  Swapped row $row" -ForegroundColor Gray
        }
    }

    Write-Host ""
    Write-Host "Sample of swapped data:" -ForegroundColor Cyan
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
    Write-Host "Columns swapped" -ForegroundColor Green
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
