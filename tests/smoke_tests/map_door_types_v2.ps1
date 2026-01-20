# Refined door type mapping based on size and room
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== REFINED DOOR TYPE MAPPING ===" -ForegroundColor Cyan

# Get door schedule data
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nDoor Type Definitions from Legend:" -ForegroundColor Yellow
    Write-Host "  TYPE A = Entry door with sidelite"
    Write-Host "  TYPE B = Entry door single with vision panel"
    Write-Host "  TYPE C = Interior Pocket door"
    Write-Host "  TYPE D = Interior swing door"

    $assignments = @{}

    foreach ($row in $result.result.data) {
        if ($row[0] -match "^\d+" -and $row[2] -ne "") {
            $doorNum = $row[0]
            $roomName = $row[1]
            $width = $row[2]

            # Parse width for comparison
            $widthInches = 0
            if ($width -match "(\d+)'") {
                $feet = [int]$Matches[1]
                $widthInches = $feet * 12
            }
            if ($width -match "(\d+)""") {
                $inches = [int]$Matches[1]
                $widthInches += $inches
            }

            $assignedType = ""

            # Entry doors - doors at ENTRY rooms
            if ($roomName -like "*ENTRY*") {
                if ($widthInches -ge 54) {  # 4'-6" or wider
                    $assignedType = "A"  # Entry with sidelite
                } else {
                    $assignedType = "B"  # Entry single
                }
            }
            # Pocket doors - 2'-10" (34") doors in bedrooms are closet pockets
            elseif ($width -like "*2' - 10*" -and ($roomName -like "*BEDROOM*" -or $roomName -like "*MASTER*")) {
                $assignedType = "C"  # Pocket door
            }
            # All other interior doors
            else {
                $assignedType = "D"  # Interior
            }

            $assignments[$doorNum] = @{
                room = $roomName
                width = $width
                type = $assignedType
            }
        }
    }

    # Group by type
    $typeGroups = @{
        "A" = @()
        "B" = @()
        "C" = @()
        "D" = @()
    }

    foreach ($door in $assignments.Keys) {
        $type = $assignments[$door].type
        $typeGroups[$type] += "$door ($($assignments[$door].width))"
    }

    Write-Host "`n--- TYPE ASSIGNMENTS ---" -ForegroundColor Cyan

    Write-Host "`nTYPE A - Entry w/sidelite ($($typeGroups['A'].Count) doors):" -ForegroundColor Green
    $typeGroups['A'] | ForEach-Object { Write-Host "  $_" }

    Write-Host "`nTYPE B - Entry single ($($typeGroups['B'].Count) doors):" -ForegroundColor Green
    $typeGroups['B'] | ForEach-Object { Write-Host "  $_" }

    Write-Host "`nTYPE C - Pocket ($($typeGroups['C'].Count) doors):" -ForegroundColor Green
    $typeGroups['C'] | ForEach-Object { Write-Host "  $_" }

    Write-Host "`nTYPE D - Interior ($($typeGroups['D'].Count) doors):" -ForegroundColor Green
    Write-Host "  $($typeGroups['D'].Count) doors (standard interior)"

    $total = $typeGroups['A'].Count + $typeGroups['B'].Count + $typeGroups['C'].Count + $typeGroups['D'].Count
    Write-Host "`nTotal assigned: $total doors"
}

$pipe.Close()
