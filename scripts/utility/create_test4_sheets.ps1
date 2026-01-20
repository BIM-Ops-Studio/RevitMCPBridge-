# Create sheets matching Sheffield Road project in TEST-4
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

$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(5000)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$reader = New-Object System.IO.StreamReader($pipeClient)

$created = 0
$failed = 0

foreach ($sheet in $sheets) {
    $json = '{"method":"createSheet","params":{"number":"' + $sheet.number + '","name":"' + $sheet.name + '"}}'
    $writer.WriteLine($json)
    $writer.Flush()
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json

    if ($result.success) {
        Write-Host "Created: $($sheet.number) - $($sheet.name)" -ForegroundColor Green
        $created++
    } else {
        Write-Host "FAILED: $($sheet.number) - $($result.error)" -ForegroundColor Red
        $failed++
    }
}

$pipeClient.Close()

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Created: $created sheets" -ForegroundColor Green
Write-Host "Failed: $failed sheets" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
