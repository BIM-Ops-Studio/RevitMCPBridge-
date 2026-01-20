# Filter schedule to L1 and L2, and update marks to letters
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== STEP 1: CHECK CURRENT SCHEDULE FIELDS ===" -ForegroundColor Cyan

# Get schedule fields to find Level field
$json = '{"method":"getScheduleFields","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success -and $result.result.fields) {
    Write-Host "Schedule fields:"
    $result.result.fields | ForEach-Object {
        Write-Host "  Index $($_.fieldIndex): $($_.name)"
    }
}

# Check available schedulable fields for Level
Write-Host ""
Write-Host "=== CHECKING FOR LEVEL FIELD ===" -ForegroundColor Cyan
$json = '{"method":"getAvailableSchedulableFields","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    $levelField = $result.result.fields | Where-Object { $_.name -like "*Level*" }
    if ($levelField) {
        Write-Host "Level fields available:"
        $levelField | ForEach-Object {
            Write-Host "  $($_.name) (ID: $($_.fieldId))"
        }
    }
}

# Get current doors by level
Write-Host ""
Write-Host "=== DOORS BY LEVEL ===" -ForegroundColor Cyan
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$doorsResult = $response | ConvertFrom-Json

$levelCounts = @{}
foreach ($door in $doorsResult.doors) {
    $level = $door.level
    if (-not $levelCounts.ContainsKey($level)) {
        $levelCounts[$level] = @()
    }
    $levelCounts[$level] += $door.mark
}

foreach ($level in ($levelCounts.Keys | Sort-Object)) {
    Write-Host "  $level : $($levelCounts[$level].Count) doors"
}

$pipe.Close()
