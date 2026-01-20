# Create all 19 sheets matching Sheffield Road - with individual connections
$sheets = @(
    @{ number = "A-0.0"; name = "GENERAL NOTES / SITE DATA" },
    @{ number = "A-1.0"; name = "COVER SHEET" },
    @{ number = "A-1.1"; name = "FLOOR PLAN, SCHEDULES, DETAILS & LEGEND" },
    @{ number = "A-2.0"; name = "BUILDING ELEVATIONS" },
    @{ number = "A-2.1"; name = "BUILDING ELEVATIONS" },
    @{ number = "A-3.0"; name = "ROOF PLAN & DETAILS" },
    @{ number = "A-4.0"; name = "BUILDING SECTIONS & DETAILS" },
    @{ number = "A-5.0"; name = "ENLARGED PLANS, ELEVATION AND DETAILS" },
    @{ number = "S-1.0"; name = "FOUNDATION PLAN AND DETAILS" },
    @{ number = "S-2.0"; name = "ROOF FRAMING PLAN AND DETAILS" },
    @{ number = "S-3.0"; name = "COLUMN & BOND BEAM PLAN" },
    @{ number = "M-1.0"; name = "MECHANICAL" },
    @{ number = "E-1.0"; name = "ELECTRICAL" },
    @{ number = "E-2.0"; name = "ELECTRICAL" },
    @{ number = "P-1.0"; name = "PLUMBING" },
    @{ number = "P-2.0"; name = "PLUMBING" },
    @{ number = "C-1.0"; name = "TYPICAL SITE PLAN" },
    @{ number = "L-1.0"; name = "LANDSCAPE PLAN / NOTES & DETAILS" },
    @{ number = "L-2.0"; name = "IRRIGATION PLAN / NOTES & DETAILS" }
)

$created = 0
$failed = 0
$results = @()

foreach ($sheet in $sheets) {
    try {
        # Fresh connection for each sheet
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(10000)
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $reader = New-Object System.IO.StreamReader($pipeClient)

        $json = '{"method":"createSheet","params":{"number":"' + $sheet.number + '","name":"' + $sheet.name + '"}}'
        $writer.WriteLine($json)
        $writer.Flush()
        $response = $reader.ReadLine()

        $pipeClient.Close()
        $pipeClient.Dispose()

        $result = $response | ConvertFrom-Json
        if ($result.success) {
            Write-Host "[OK] $($sheet.number) - $($sheet.name)" -ForegroundColor Green
            $created++
            $results += @{ number = $sheet.number; name = $sheet.name; id = $result.sheetId; status = "created" }
        } else {
            Write-Host "[FAIL] $($sheet.number) - $($result.error)" -ForegroundColor Red
            $failed++
            $results += @{ number = $sheet.number; name = $sheet.name; error = $result.error; status = "failed" }
        }

        # Small delay between creations
        Start-Sleep -Milliseconds 500
    }
    catch {
        Write-Host "[ERROR] $($sheet.number) - $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Created: $created / $($sheets.Count) sheets" -ForegroundColor $(if ($created -eq $sheets.Count) { "Green" } else { "Yellow" })
Write-Host "Failed: $failed sheets" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "========================================" -ForegroundColor Cyan
