# Check BUILDING sheet for missing responses
$excelPath = "D:\001 - PROJECTS\01 - CLIENT PROJECTS\01 - ARKY\010-20 NW 76 Street Miami - New 4 Story Building\Permit Comments\Status Report as of July 31, 2025 - Updated (2).xlsx"

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$workbook = $excel.Workbooks.Open($excelPath)

# Find BUILDING sheet
$buildingSheet = $null
foreach ($sheet in $workbook.Sheets) {
    if ($sheet.Name -like "*BUILDING*") {
        $buildingSheet = $sheet
        Write-Host "Found sheet: $($sheet.Name)"
        break
    }
}

if ($buildingSheet) {
    Write-Host "`nBUILDING Sheet - Rows 2-12:"
    for ($row = 2; $row -le 12; $row++) {
        $colB = $buildingSheet.Cells.Item($row, 2).Text  # Comment/Description
        $colF = $buildingSheet.Cells.Item($row, 6).Text  # Architect Response
        if ($colB -ne "") {
            Write-Host "Row $row :"
            Write-Host "  Comment: $colB"
            Write-Host "  Response: $colF"
            Write-Host ""
        }
    }
}

$workbook.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
