# View full window schedule data
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== WINDOW SCHEDULE FULL VIEW ===" -ForegroundColor Cyan

$json = '{"method":"getScheduleData","params":{"scheduleId":510941}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    # Show all column headers
    Write-Host "Column headers:"
    for ($i = 0; $i -lt $result.result.data[0].Count; $i++) {
        $h0 = $result.result.data[0][$i]
        $h1 = $result.result.data[1][$i]
        Write-Host "  Col $i : '$h0' / '$h1'"
    }

    # Show unique type marks
    Write-Host ""
    Write-Host "Unique window types:" -ForegroundColor Yellow
    $types = @{}
    foreach ($row in $result.result.data) {
        $typeMark = $row[0]
        if ($typeMark -match '^[A-Z]+$') {
            if (-not $types.ContainsKey($typeMark)) {
                $types[$typeMark] = @{
                    count = 0
                    width = $row[1]
                    height = $row[2]
                }
            }
            $types[$typeMark].count++
        }
    }

    foreach ($type in ($types.Keys | Sort-Object)) {
        $info = $types[$type]
        Write-Host "  TYPE $type : $($info.count) windows, Size: $($info.width) x $($info.height)"
    }

    # Check what columns have data
    Write-Host ""
    Write-Host "Sample complete row (Type A):" -ForegroundColor Yellow
    $sampleRow = $result.result.data | Where-Object { $_[0] -eq "A" } | Select-Object -First 1
    if ($sampleRow) {
        for ($i = 0; $i -lt $sampleRow.Count; $i++) {
            $val = $sampleRow[$i]
            Write-Host "  Col $i : '$val'"
        }
    }
}

$pipe.Close()
