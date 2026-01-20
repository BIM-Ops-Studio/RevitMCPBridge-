param([string]$FilePath)

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($FilePath)
    $sheet = $workbook.Sheets.Item(1)

    $usedRange = $sheet.UsedRange
    $rows = $usedRange.Rows.Count
    $cols = $usedRange.Columns.Count

    Write-Host "Rows: $rows, Columns: $cols"
    Write-Host "---"

    for ($r = 1; $r -le [Math]::Min($rows, 100); $r++) {
        $rowData = @()
        for ($c = 1; $c -le $cols; $c++) {
            $cell = $sheet.Cells.Item($r, $c)
            $value = $cell.Text
            if ($value) {
                $rowData += "$c`:$value"
            }
        }
        if ($rowData.Count -gt 0) {
            Write-Host "R$r | $($rowData -join ' | ')"
        }
    }

    $workbook.Close($false)
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
