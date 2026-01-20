# Check schedule filters and overhead door details
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CHECKING SCHEDULE FILTERS ===" -ForegroundColor Cyan

# Get schedule info
$json = '{"method":"getScheduleFilters","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Schedule filters:"
    $result.result | ConvertTo-Json -Depth 3
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Yellow
}

# Check overhead door details
Write-Host ""
Write-Host "=== OVERHEAD DOOR DETAILS ===" -ForegroundColor Cyan

$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$doorsResult = $response | ConvertFrom-Json

$overhead = $doorsResult.doors | Where-Object { $_.familyName -like "*Overhead*" }
if ($overhead) {
    Write-Host "Overhead Door:"
    Write-Host "  ID: $($overhead.doorId)"
    Write-Host "  Mark: $($overhead.mark)"
    Write-Host "  Level: $($overhead.level)"
    Write-Host "  Family: $($overhead.familyName)"
    Write-Host "  Type: $($overhead.typeName)"

    # Get parameters
    $paramJson = '{"method":"getParameters","params":{"elementId":' + $overhead.doorId + '}}'
    $writer.WriteLine($paramJson)
    $paramResponse = $reader.ReadLine()
    $paramResult = $paramResponse | ConvertFrom-Json

    if ($paramResult.success) {
        Write-Host ""
        Write-Host "Key parameters:"
        $paramResult.result.parameters | Where-Object {
            $_.name -in @("Mark", "Level", "Phase Created", "Dr Panel Type", "Category")
        } | ForEach-Object {
            Write-Host "  $($_.name) = '$($_.value)'"
        }
    }
}

# Check what levels are in the schedule
Write-Host ""
Write-Host "=== DOORS BY LEVEL ===" -ForegroundColor Cyan
$levelCounts = @{}
foreach ($door in $doorsResult.doors) {
    $level = $door.level
    if (-not $levelCounts.ContainsKey($level)) {
        $levelCounts[$level] = 0
    }
    $levelCounts[$level]++
}
foreach ($level in ($levelCounts.Keys | Sort-Object)) {
    Write-Host "  $level : $($levelCounts[$level]) doors"
}

$pipe.Close()
