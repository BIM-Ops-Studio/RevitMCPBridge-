# Update door parameters using schedule element mapping
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== UPDATING DOOR TYPE PARAMETERS ===" -ForegroundColor Cyan

# Get schedule with element IDs
$json = '{"method":"getScheduleDataWithIds","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if (-not $result.success) {
    Write-Host "getScheduleDataWithIds not available, trying alternative..." -ForegroundColor Yellow

    # Try to update via parameter methods
    # First, let's check available parameter update methods
    $json = '{"method":"updateScheduleCell","params":{"scheduleId":1487966,"rowIndex":4,"columnIndex":5,"value":"D"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json

    if ($result.success) {
        Write-Host "updateScheduleCell works!" -ForegroundColor Green
    } else {
        Write-Host "updateScheduleCell: $($result.error)" -ForegroundColor Yellow
    }

    # Try setScheduleFieldValue
    $json = '{"method":"setScheduleFieldValue","params":{"scheduleId":1487966,"rowIndex":4,"fieldName":"Door_Type","value":"D"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json

    if ($result.success) {
        Write-Host "setScheduleFieldValue works!" -ForegroundColor Green
    } else {
        Write-Host "setScheduleFieldValue: $($result.error)" -ForegroundColor Yellow
    }

    # Try getting doors by category
    Write-Host "`nTrying getElementsByCategory for Doors..." -ForegroundColor Cyan
    $json = '{"method":"getElementsByCategory","params":{"category":"OST_Doors"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json

    if ($result.success) {
        Write-Host "Found door elements: $($result.result.elements.Count)"
    } else {
        Write-Host "getElementsByCategory: $($result.error)" -ForegroundColor Yellow
    }

    # Try getAllDoors
    $json = '{"method":"getAllDoors","params":{}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json

    if ($result.success) {
        Write-Host "getAllDoors found: $($result.result)" -ForegroundColor Green
    } else {
        Write-Host "getAllDoors: $($result.error)" -ForegroundColor Yellow
    }
}

$pipe.Close()
Write-Host "`nDone checking available methods"
