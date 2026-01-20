# Update all door MARKS to match their TYPE letter
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== UPDATING DOOR MARKS TO LETTERS ===" -ForegroundColor Cyan
Write-Host "Mark will match Type (A, B, C, D, F, G, I, J, K)"

# Get all doors
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

# Get current type from schedule to know what type each door has
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

# Build lookup from current mark to TYPE
$markToType = @{}
foreach ($row in $schedResult.result.data) {
    $mark = $row[0]
    $type = $row[5]
    if ($type -match '^[A-K]$') {
        $markToType[$mark] = $type
    }
}

Write-Host ""
Write-Host "Doors to update (mark -> type letter):" -ForegroundColor Yellow

$updates = @()
foreach ($door in $result.doors) {
    $currentMark = $door.mark
    $doorId = $door.doorId
    $level = $door.level

    # Get the TYPE for this door from schedule
    if ($markToType.ContainsKey($currentMark)) {
        $newMark = $markToType[$currentMark]
        if ($currentMark -ne $newMark) {
            $updates += @{
                id = $doorId
                oldMark = $currentMark
                newMark = $newMark
                level = $level
            }
        }
    }
}

# Group by new mark to show summary
$summary = @{}
foreach ($update in $updates) {
    $newMark = $update.newMark
    if (-not $summary.ContainsKey($newMark)) {
        $summary[$newMark] = @()
    }
    $summary[$newMark] += "$($update.oldMark) ($($update.level))"
}

Write-Host ""
Write-Host "Summary of changes:"
foreach ($type in ($summary.Keys | Sort-Object)) {
    Write-Host "  TYPE $type : $($summary[$type].Count) doors"
    Write-Host "    From marks: $($summary[$type][0..4] -join ', ')$(if($summary[$type].Count -gt 5) { '...' })"
}

# Now update all marks
Write-Host ""
Write-Host "=== UPDATING MARKS ===" -ForegroundColor Cyan

$successCount = 0
$failCount = 0

foreach ($update in $updates) {
    $updateJson = @{
        method = "setParameter"
        params = @{
            elementId = $update.id
            parameterName = "Mark"
            value = $update.newMark
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($updateJson)
    $response = $reader.ReadLine()
    $updateResult = $response | ConvertFrom-Json

    if ($updateResult.success) {
        $successCount++
        Write-Host "  $($update.oldMark) -> $($update.newMark) ($($update.level))" -ForegroundColor Green
    } else {
        $failCount++
        Write-Host "  $($update.oldMark) FAILED: $($updateResult.error)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== COMPLETE ===" -ForegroundColor Green
Write-Host "Updated: $successCount doors"
Write-Host "Failed: $failCount doors"

$pipe.Close()
