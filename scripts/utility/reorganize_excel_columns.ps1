# Completely reorganize Excel file to proper column structure

$excelPath = "D:\RevitMCPBridge2026\Level_7_Filled_Region_Areas.xlsx"

Write-Host "`nReorganizing Excel file: $excelPath" -ForegroundColor Yellow

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($excelPath)
    $worksheet = $workbook.Worksheets.Item(1)

    # Find the last row with data
    $lastRow = $worksheet.UsedRange.Rows.Count

    Write-Host "Found $($lastRow - 4) data rows" -ForegroundColor Cyan
    Write-Host "Reading current data..." -ForegroundColor Yellow
    Write-Host ""

    # Collect all data first
    $allData = @()
    for ($row = 5; $row -le $lastRow; $row++) {
        $colA = $worksheet.Cells.Item($row, 1).Text
        $colB = $worksheet.Cells.Item($row, 2).Text
        $colC = $worksheet.Cells.Item($row, 3).Text

        # Current structure seems to be:
        # Col A: "OFFICE 01", Col B: "810", Col C: might be empty or something else

        # Extract room number and name from Col A
        if ($colA -match '^(.+?)\s+(\d{2,3})$') {
            $roomName = $matches[1].Trim()
            $roomNumber = $matches[2]
        } else {
            # Fallback if pattern doesn't match
            $roomName = $colA
            $roomNumber = "??"
        }

        # Square footage is in Col B
        $squareFeet = $colB

        $allData += [PSCustomObject]@{
            Number = $roomNumber
            Name = $roomName
            SF = $squareFeet
        }

        Write-Host "Row ${row}: Number='$roomNumber', Name='$roomName', SF='$squareFeet'" -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "Reorganizing columns..." -ForegroundColor Yellow
    Write-Host ""

    # Now write back in correct structure
    $row = 5
    foreach ($data in $allData) {
        $worksheet.Cells.Item($row, 1) = $data.Number
        $worksheet.Cells.Item($row, 2) = $data.Name
        $worksheet.Cells.Item($row, 3) = $data.SF

        Write-Host "Row ${row}:" -ForegroundColor Cyan
        Write-Host "  Col A: $($data.Number)" -ForegroundColor Green
        Write-Host "  Col B: $($data.Name)" -ForegroundColor Green
        Write-Host "  Col C: $($data.SF)" -ForegroundColor Green

        $row++
    }

    Write-Host ""
    Write-Host "Saving changes..." -ForegroundColor Yellow
    $workbook.Save()
    $workbook.Close()

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Excel file reorganized correctly" -ForegroundColor Green
    Write-Host ""
    Write-Host "Column A: Room Number (01, 02, 03...)" -ForegroundColor Cyan
    Write-Host "Column B: Room Name (OFFICE, MECH., etc.)" -ForegroundColor Cyan
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
