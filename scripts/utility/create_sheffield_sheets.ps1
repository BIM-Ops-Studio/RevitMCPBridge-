# Create all 19 sheets matching Sheffield Road with ARKY titleblock
$titleblockId = 1246190  # ARKY - Title Block

$sheets = @(
    @{ sheetNumber = "A-0.0"; sheetName = "GENERAL NOTES / SITE DATA" },
    @{ sheetNumber = "A-1.0"; sheetName = "COVER SHEET" },
    @{ sheetNumber = "A-1.1"; sheetName = "FLOOR PLAN, SCHEDULES, DETAILS & LEGEND" },
    @{ sheetNumber = "A-2.0"; sheetName = "BUILDING ELEVATIONS" },
    @{ sheetNumber = "A-2.1"; sheetName = "BUILDING ELEVATIONS" },
    @{ sheetNumber = "A-3.0"; sheetName = "ROOF PLAN & DETAILS" },
    @{ sheetNumber = "A-4.0"; sheetName = "BUILDING SECTIONS & DETAILS" },
    @{ sheetNumber = "A-5.0"; sheetName = "ENLARGED PLANS, ELEVATION AND DETAILS" },
    @{ sheetNumber = "S-1.0"; sheetName = "FOUNDATION PLAN AND DETAILS" },
    @{ sheetNumber = "S-2.0"; sheetName = "ROOF FRAMING PLAN AND DETAILS" },
    @{ sheetNumber = "S-3.0"; sheetName = "COLUMN & BOND BEAM PLAN" },
    @{ sheetNumber = "M-1.0"; sheetName = "MECHANICAL" },
    @{ sheetNumber = "E-1.0"; sheetName = "ELECTRICAL" },
    @{ sheetNumber = "E-2.0"; sheetName = "ELECTRICAL" },
    @{ sheetNumber = "P-1.0"; sheetName = "PLUMBING" },
    @{ sheetNumber = "P-2.0"; sheetName = "PLUMBING" },
    @{ sheetNumber = "C-1.0"; sheetName = "TYPICAL SITE PLAN" },
    @{ sheetNumber = "L-1.0"; sheetName = "LANDSCAPE PLAN / NOTES & DETAILS" },
    @{ sheetNumber = "L-2.0"; sheetName = "IRRIGATION PLAN / NOTES & DETAILS" }
)

$created = 0
$failed = 0
$createdSheets = @()

Write-Host "Creating 19 sheets with ARKY titleblock..." -ForegroundColor Cyan
Write-Host ""

foreach ($sheet in $sheets) {
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(10000)
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $reader = New-Object System.IO.StreamReader($pipeClient)

        $json = '{"method":"createSheet","params":{"sheetNumber":"' + $sheet.sheetNumber + '","sheetName":"' + $sheet.sheetName + '","titleblockId":' + $titleblockId + '}}'
        $writer.WriteLine($json)
        $writer.Flush()
        $response = $reader.ReadLine()

        $pipeClient.Close()
        $pipeClient.Dispose()

        $result = $response | ConvertFrom-Json
        if ($result.success) {
            Write-Host "[OK] $($sheet.sheetNumber) - $($sheet.sheetName)" -ForegroundColor Green
            $created++
            $createdSheets += @{ id = $result.sheetId; number = $sheet.sheetNumber; name = $sheet.sheetName }
        } else {
            Write-Host "[FAIL] $($sheet.sheetNumber) - $($result.error)" -ForegroundColor Red
            $failed++
        }

        Start-Sleep -Milliseconds 300
    }
    catch {
        Write-Host "[ERROR] $($sheet.sheetNumber) - $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Created: $created / $($sheets.Count) sheets" -ForegroundColor $(if ($created -eq $sheets.Count) { "Green" } else { "Yellow" })
if ($failed -gt 0) {
    Write-Host "Failed: $failed sheets" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan

# Output created sheet IDs for reference
if ($createdSheets.Count -gt 0) {
    Write-Host ""
    Write-Host "Created Sheet IDs:" -ForegroundColor Yellow
    foreach ($s in $createdSheets) {
        Write-Host "  $($s.number): ID $($s.id)" -ForegroundColor Gray
    }
}
