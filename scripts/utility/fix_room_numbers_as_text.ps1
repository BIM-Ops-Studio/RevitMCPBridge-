# Fix room numbers to be text with leading zeros

$excelPath = "D:\RevitMCPBridge2026\Level_7_Filled_Region_Areas.xlsx"

Write-Host "`nFormatting room numbers as text with leading zeros" -ForegroundColor Yellow

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($excelPath)
    $worksheet = $workbook.Worksheets.Item(1)

    # Find the last row with data
    $lastRow = $worksheet.UsedRange.Rows.Count

    Write-Host "Processing $($lastRow - 4) rooms...`n" -ForegroundColor Yellow

    # Format Column B as text and add leading zeros
    for ($row = 5; $row -le $lastRow; $row++) {
        # Get current value
        $cellValue = $worksheet.Cells.Item($row, 2).Value2

        # Convert to integer then format with leading zero
        $roomNumber = [int]$cellValue
        $formattedNumber = "{0:D2}" -f $roomNumber

        # Format cell as text (xlTextFormat = 2)
        $worksheet.Cells.Item($row, 2).NumberFormat = "@"

        # Set the value as text with leading zero
        $worksheet.Cells.Item($row, 2).Value2 = $formattedNumber

        if ($row % 10 -eq 5) {
            Write-Host "  Row ${row}: Set to '$formattedNumber'" -ForegroundColor Gray
        }
    }

    Write-Host ""
    Write-Host "Sample of formatted data:" -ForegroundColor Cyan
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
    Write-Host "Room numbers formatted as text with leading zeros" -ForegroundColor Green
    Write-Host ""
    Write-Host "Column A: Room Name" -ForegroundColor Cyan
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
