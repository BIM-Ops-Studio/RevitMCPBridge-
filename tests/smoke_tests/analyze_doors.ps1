# Analyze all doors from schedule to determine types needed
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== ANALYZING DOOR SCHEDULE DATA ===" -ForegroundColor Cyan

# Get full schedule data
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    # Group by door size and room type to determine door types needed
    $doorGroups = @{}
    $roomTypes = @{}

    foreach ($row in $result.result.data) {
        # Skip header rows and empty rows
        if ($row[0] -match "^\d+" -and $row[2] -ne "") {
            $doorNum = $row[0]
            $roomName = $row[1]
            $width = $row[2]
            $height = $row[3]
            $thickness = $row[4]
            $doorType = $row[5]
            $doorMatl = $row[6]
            $frameMatl = $row[7]
            $rating = $row[8]
            $hdwr = $row[9]

            $sizeKey = "$width x $height"

            if (-not $doorGroups.ContainsKey($sizeKey)) {
                $doorGroups[$sizeKey] = @{
                    count = 0
                    doors = @()
                    rooms = @()
                }
            }
            $doorGroups[$sizeKey].count++
            $doorGroups[$sizeKey].doors += $doorNum
            if ($roomName -and $roomName -notin $doorGroups[$sizeKey].rooms) {
                $doorGroups[$sizeKey].rooms += $roomName
            }

            # Track room types
            if ($roomName) {
                if (-not $roomTypes.ContainsKey($roomName)) {
                    $roomTypes[$roomName] = 0
                }
                $roomTypes[$roomName]++
            }
        }
    }

    Write-Host "`nDOOR SIZES (grouped):" -ForegroundColor Yellow
    foreach ($size in $doorGroups.Keys | Sort-Object) {
        $info = $doorGroups[$size]
        Write-Host "`n  $size - Count: $($info.count)"
        $roomList = ($info.rooms | Select-Object -First 5) -join ", "
        if ($info.rooms.Count -gt 5) { $roomList += "..." }
        Write-Host "    Rooms: $roomList"
    }

    Write-Host "`n`nROOM TYPES with doors:" -ForegroundColor Yellow
    foreach ($room in $roomTypes.Keys | Sort-Object) {
        Write-Host "  $room : $($roomTypes[$room]) doors"
    }

    Write-Host "`n`nTotal unique door sizes: $($doorGroups.Count)"
}

$pipe.Close()
