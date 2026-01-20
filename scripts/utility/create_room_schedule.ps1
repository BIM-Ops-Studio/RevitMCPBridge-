# Create Room Schedule for Proposed Floor Plan
$pipeName = "\\.\pipe\RevitMCPBridge2026"

function Send-MCPRequest {
    param([string]$Method, [hashtable]$Params = @{})

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)

        $request = @{
            method = $Method
            parameters = $Params
        } | ConvertTo-Json -Compress

        $writer = New-Object System.IO.StreamWriter($pipe)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)

        $reader = New-Object System.IO.StreamReader($pipe)
        $response = $reader.ReadLine()

        $reader.Close()
        $writer.Close()
        $pipe.Close()

        return $response | ConvertFrom-Json
    } catch {
        Write-Host "[ERROR] $_" -ForegroundColor Red
        return $null
    }
}

Write-Host "Creating Room Schedule..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Get all rooms to see what we have
Write-Host "1. Getting all rooms in project..." -ForegroundColor Yellow
$rooms = Send-MCPRequest -Method "getRooms"
if ($rooms.success) {
    $roomCount = ($rooms.rooms | Measure-Object).Count
    Write-Host "   Found $roomCount rooms" -ForegroundColor Green
} else {
    Write-Host "   Failed: $($rooms.error)" -ForegroundColor Red
    exit
}

# Step 2: Create the room schedule
Write-Host "2. Creating room schedule..." -ForegroundColor Yellow
$schedule = Send-MCPRequest -Method "createSchedule" -Params @{
    scheduleName = "Room Schedule - Created by MCP"
    categoryName = "Rooms"
}
if ($schedule.success) {
    $scheduleId = $schedule.scheduleId
    Write-Host "   Schedule created! ID: $scheduleId" -ForegroundColor Green
} else {
    Write-Host "   Failed: $($schedule.error)" -ForegroundColor Red
    exit
}

# Step 3: Add fields to the schedule
Write-Host "3. Adding fields to schedule..." -ForegroundColor Yellow
$fields = @("Number", "Name", "Level", "Area", "Comments")

foreach ($field in $fields) {
    Write-Host "   Adding field: $field..." -ForegroundColor Gray
    $result = Send-MCPRequest -Method "addScheduleField" -Params @{
        scheduleId = $scheduleId
        fieldName = $field
    }
    if ($result.success) {
        Write-Host "      SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "      Failed: $($result.error)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "DONE! Room schedule created in Revit." -ForegroundColor Green
Write-Host "Check your Project Browser under 'Schedules/Quantities'" -ForegroundColor Cyan
