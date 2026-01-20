# Check ZONING sheet rows 20-25
$excelPath = "D:\001 - PROJECTS\01 - CLIENT PROJECTS\01 - ARKY\010-20 NW 76 Street Miami - New 4 Story Building\Permit Comments\Status Report as of July 31, 2025 - Updated (2).xlsx"

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$workbook = $excel.Workbooks.Open($excelPath)

# Find ZONING sheet
$zoningSheet = $null
foreach ($sheet in $workbook.Sheets) {
    if ($sheet.Name -like "*ZONING*") {
        $zoningSheet = $sheet
        Write-Host "Found sheet: $($sheet.Name)"
        break
    }
}

if ($zoningSheet) {
    Write-Host "`nZONING Sheet - Rows 20-25:"
    for ($row = 20; $row -le 25; $row++) {
        $colB = $zoningSheet.Cells.Item($row, 2).Text  # Comment/Description
        $colF = $zoningSheet.Cells.Item($row, 6).Text  # Architect Response
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
