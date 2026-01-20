param([string]$FilePath)

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($FilePath)

    Write-Host "Workbook has $($workbook.Sheets.Count) sheets"
    Write-Host "=========================="

    foreach ($sheet in $workbook.Sheets) {
        Write-Host "`nSHEET: $($sheet.Name)"
        Write-Host "---"

        $usedRange = $sheet.UsedRange
        $rows = $usedRange.Rows.Count
        $cols = $usedRange.Columns.Count

        Write-Host "Rows: $rows, Columns: $cols"

        for ($r = 1; $r -le [Math]::Min($rows, 200); $r++) {
            $rowData = @()
            for ($c = 1; $c -le [Math]::Min($cols, 10); $c++) {
                $cell = $sheet.Cells.Item($r, $c)
                $value = $cell.Text
                if ($value -and $value.Trim() -ne "") {
                    $rowData += $value.Trim()
                }
            }
            if ($rowData.Count -gt 0) {
                Write-Host "R$r | $($rowData -join ' | ')"
            }
        }
    }

    $workbook.Close($false)
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
