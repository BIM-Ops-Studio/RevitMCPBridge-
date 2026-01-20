# Edit the existing Excel file to separate room numbers and names

$excelPath = "D:\RevitMCPBridge2026\Level_7_Filled_Region_Areas.xlsx"

Write-Host "`nEditing Excel file: $excelPath" -ForegroundColor Yellow
Write-Host "Separating room numbers into dedicated column`n" -ForegroundColor Cyan

# Open existing Excel file
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($excelPath)
    $worksheet = $workbook.Worksheets.Item(1)

    # Find the last row with data
    $lastRow = $worksheet.UsedRange.Rows.Count

    Write-Host "Processing $($lastRow - 4) rooms..." -ForegroundColor Yellow

    # Process each data row (starting from row 5, after headers)
    for ($row = 5; $row -le $lastRow; $row++) {
        $roomName = $worksheet.Cells.Item($row, 2).Text

        # Remove room number from room name if it exists
        # Example: "OFFICE 01" becomes "OFFICE"
        $cleanedName = $roomName -replace '\s+\d{2,3}$', ''

        # Update the room name cell
        $worksheet.Cells.Item($row, 2) = $cleanedName
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
    Write-Host "Column A: Room Number (01, 02, 03...)" -ForegroundColor Cyan
    Write-Host "Column B: Room Name (OFFICE, not OFFICE 01)" -ForegroundColor Cyan
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
