# Create comprehensive office area schedule and export to CSV
function Send-RevitCommand {
    param([string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        return $response | ConvertFrom-Json
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient) { try { $pipeClient.Dispose() } catch {} }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CREATE OFFICE AREA SCHEDULE" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Create the schedule
Write-Host "Step 1: Creating room schedule..." -ForegroundColor Cyan
$createResult = Send-RevitCommand -Method "createSchedule" -Params @{
    scheduleName = "Office Areas - Adjusted"
    category = "Rooms"
}

if (-not $createResult.success) {
    Write-Host "ERROR: Could not create schedule - $($createResult.error)" -ForegroundColor Red
    exit
}

$scheduleId = $createResult.scheduleId
Write-Host "  SUCCESS: Schedule created (ID: $scheduleId)" -ForegroundColor Green

# Step 2: Add fields
Write-Host "`nStep 2: Adding schedule fields..." -ForegroundColor Cyan

$fields = @(
    @{ name = "Number"; displayName = "Room Number" },
    @{ name = "Name"; displayName = "Room Name" },
    @{ name = "Level"; displayName = "Level" },
    @{ name = "Area"; displayName = "Revit Area (SF)" },
    @{ name = "Comments"; displayName = "Adjusted Area (1.2x)" }
)

foreach ($field in $fields) {
    Write-Host "  Adding field: $($field.displayName)..." -ForegroundColor White
    $fieldResult = Send-RevitCommand -Method "addScheduleField" -Params @{
        scheduleId = $scheduleId.ToString()
        fieldName = $field.name
    }

    if ($fieldResult.success) {
        Write-Host "    SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "    WARNING: $($fieldResult.error)" -ForegroundColor Yellow
    }
}

# Step 3: Add filter for offices only
Write-Host "`nStep 3: Adding filter (offices only)..." -ForegroundColor Cyan
$filterResult = Send-RevitCommand -Method "addScheduleFilter" -Params @{
    scheduleId = $scheduleId.ToString()
    fieldName = "Name"
    filterType = "contains"
    value = "OFFICE"
}

if ($filterResult.success) {
    Write-Host "  SUCCESS: Filter added" -ForegroundColor Green
} else {
    Write-Host "  WARNING: $($filterResult.error)" -ForegroundColor Yellow
}

# Step 4: Add sorting by room number
Write-Host "`nStep 4: Adding sorting (by room number)..." -ForegroundColor Cyan
$sortResult = Send-RevitCommand -Method "addScheduleSorting" -Params @{
    scheduleId = $scheduleId.ToString()
    fieldName = "Number"
    sortOrder = "ascending"
}

if ($sortResult.success) {
    Write-Host "  SUCCESS: Sorting added" -ForegroundColor Green
} else {
    Write-Host "  WARNING: $($sortResult.error)" -ForegroundColor Yellow
}

# Step 5: Format appearance
Write-Host "`nStep 5: Formatting schedule appearance..." -ForegroundColor Cyan
$formatResult = Send-RevitCommand -Method "formatScheduleAppearance" -Params @{
    scheduleId = $scheduleId.ToString()
    showTitle = $true
    showHeaders = $true
    showGridLines = $true
}

if ($formatResult.success) {
    Write-Host "  SUCCESS: Formatting applied" -ForegroundColor Green
} else {
    Write-Host "  WARNING: $($formatResult.error)" -ForegroundColor Yellow
}

# Step 6: Get schedule data preview
Write-Host "`nStep 6: Getting schedule data..." -ForegroundColor Cyan
$dataResult = Send-RevitCommand -Method "getScheduleData" -Params @{
    scheduleId = $scheduleId.ToString()
}

if ($dataResult.success) {
    Write-Host "  SUCCESS: Retrieved $($dataResult.rowCount) rows" -ForegroundColor Green

    # Show first 5 rows as preview
    if ($dataResult.rows -and $dataResult.rows.Count -gt 0) {
        Write-Host "`n  Preview (first 5 rows):" -ForegroundColor Cyan
        $dataResult.rows | Select-Object -First 5 | ForEach-Object {
            Write-Host "    $($_)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  WARNING: $($dataResult.error)" -ForegroundColor Yellow
}

# Step 7: Export to CSV
Write-Host "`nStep 7: Exporting to CSV..." -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$csvPath = "D:\RevitMCPBridge2026\Office_Areas_Adjusted_$timestamp.csv"

$exportResult = Send-RevitCommand -Method "exportScheduleToCSV" -Params @{
    scheduleId = $scheduleId.ToString()
    filePath = $csvPath
}

if ($exportResult.success) {
    Write-Host "  SUCCESS: Exported to CSV" -ForegroundColor Green
    Write-Host "  File: $csvPath" -ForegroundColor White
} else {
    Write-Host "  ERROR: $($exportResult.error)" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Schedule Name: Office Areas - Adjusted" -ForegroundColor White
Write-Host "Schedule ID: $scheduleId" -ForegroundColor White
Write-Host "Total Rows: $($dataResult.rowCount)" -ForegroundColor White
Write-Host "CSV Export: $csvPath" -ForegroundColor White
Write-Host "`nDone!" -ForegroundColor Green
