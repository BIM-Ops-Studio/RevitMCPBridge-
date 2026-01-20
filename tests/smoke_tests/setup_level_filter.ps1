# Setup Level field and filter
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== GETTING AVAILABLE FIELDS ===" -ForegroundColor Cyan

# Get available fields that can be added
$json = '{"method":"getAvailableSchedulableFields","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success -and $result.result.fields) {
    Write-Host "Available fields (showing Level-related):"
    $result.result.fields | Where-Object { $_.name -like "*Level*" } | ForEach-Object {
        Write-Host "  Field: $($_.name), ID: $($_.fieldId)"
    }
}

# First, let's add the Level field to the schedule
Write-Host ""
Write-Host "=== ADDING LEVEL FIELD ===" -ForegroundColor Cyan

# Find Level field ID
$levelField = $null
if ($result.success -and $result.result.fields) {
    $levelField = $result.result.fields | Where-Object { $_.name -eq "Level" } | Select-Object -First 1
}

if ($levelField) {
    Write-Host "Found Level field with ID: $($levelField.fieldId)"

    # Add Level field
    $addJson = @{
        method = "addScheduleField"
        params = @{
            scheduleId = 1487966
            fieldId = $levelField.fieldId
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($addJson)
    $response = $reader.ReadLine()
    $addResult = $response | ConvertFrom-Json

    if ($addResult.success) {
        Write-Host "Level field added successfully" -ForegroundColor Green
        Write-Host "Field index: $($addResult.result.fieldIndex)"

        # Now add filter for L3
        Write-Host ""
        Write-Host "Adding filter: Level != L3"
        $filterJson = @{
            method = "addScheduleFilter"
            params = @{
                scheduleId = 1487966
                fieldIndex = $addResult.result.fieldIndex
                filterType = "notequals"
                value = "L3"
            }
        } | ConvertTo-Json -Compress

        $writer.WriteLine($filterJson)
        $response = $reader.ReadLine()
        $filterResult = $response | ConvertFrom-Json

        if ($filterResult.success) {
            Write-Host "Filter L3 added" -ForegroundColor Green
        } else {
            Write-Host "Filter error: $($filterResult.error)" -ForegroundColor Red
        }

        # Add filter for L4
        Write-Host "Adding filter: Level != L4"
        $filterJson = @{
            method = "addScheduleFilter"
            params = @{
                scheduleId = 1487966
                fieldIndex = $addResult.result.fieldIndex
                filterType = "notequals"
                value = "L4"
            }
        } | ConvertTo-Json -Compress

        $writer.WriteLine($filterJson)
        $response = $reader.ReadLine()
        $filterResult = $response | ConvertFrom-Json

        if ($filterResult.success) {
            Write-Host "Filter L4 added" -ForegroundColor Green
        } else {
            Write-Host "Filter error: $($filterResult.error)" -ForegroundColor Red
        }
    } else {
        Write-Host "Error adding Level field: $($addResult.error)" -ForegroundColor Red
    }
} else {
    Write-Host "Level field not found in available fields" -ForegroundColor Red
}

# Verify final schedule
Write-Host ""
Write-Host "=== FINAL SCHEDULE CHECK ===" -ForegroundColor Cyan
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

$doorCount = 0
$marks = @{}
foreach ($row in $schedResult.result.data) {
    if ($row[0] -match '^[A-Z]$') {
        $doorCount++
        $mark = $row[0]
        if (-not $marks.ContainsKey($mark)) {
            $marks[$mark] = 0
        }
        $marks[$mark]++
    }
}

Write-Host "Total doors in schedule: $doorCount"
Write-Host "By type:"
foreach ($mark in ($marks.Keys | Sort-Object)) {
    Write-Host "  TYPE $mark : $($marks[$mark])"
}

$pipe.Close()
