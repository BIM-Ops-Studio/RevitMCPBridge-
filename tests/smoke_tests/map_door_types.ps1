# Map doors to TYPE letters based on room name and door characteristics
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== MAPPING DOORS TO TYPE LETTERS ===" -ForegroundColor Cyan

# Get door schedule data
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nDoor Type Mapping Rules:" -ForegroundColor Yellow
    Write-Host "  TYPE A = Entry door with sidelite (wider entry doors)"
    Write-Host "  TYPE B = Entry door single (unit entries)"
    Write-Host "  TYPE C = Interior Pocket door"
    Write-Host "  TYPE D = Interior swing door"

    Write-Host "`n--- PROPOSED TYPE ASSIGNMENTS ---" -ForegroundColor Cyan

    $typeA = @()
    $typeB = @()
    $typeC = @()
    $typeD = @()

    foreach ($row in $result.result.data) {
        # Skip header rows
        if ($row[0] -match "^\d+" -and $row[2] -ne "") {
            $doorNum = $row[0]
            $roomName = $row[1]
            $width = $row[2]
            $currentType = $row[5]

            # Determine type based on room name and width
            $assignedType = ""

            # Entry doors (wider doors at ENTRY rooms)
            if ($roomName -like "*ENTRY*") {
                if ($width -like "*4'-6*" -or $width -like "*5'-*") {
                    $assignedType = "A"  # Entry with sidelite (wider)
                } else {
                    $assignedType = "B"  # Entry single
                }
            }
            # Closet/storage areas typically have pocket doors
            elseif ($roomName -like "*CLOSET*" -or $width -like "*2'-10*") {
                $assignedType = "C"  # Pocket door
            }
            # Standard interior doors
            else {
                $assignedType = "D"  # Interior
            }

            switch ($assignedType) {
                "A" { $typeA += $doorNum }
                "B" { $typeB += $doorNum }
                "C" { $typeC += $doorNum }
                "D" { $typeD += $doorNum }
            }
        }
    }

    Write-Host "`nTYPE A (Entry w/sidelite): $($typeA.Count) doors"
    Write-Host "  Doors: $($typeA -join ', ')"

    Write-Host "`nTYPE B (Entry single): $($typeB.Count) doors"
    Write-Host "  Doors: $($typeB -join ', ')"

    Write-Host "`nTYPE C (Interior Pocket): $($typeC.Count) doors"
    Write-Host "  Doors: $($typeC -join ', ')"

    Write-Host "`nTYPE D (Interior): $($typeD.Count) doors"
    Write-Host "  Doors: $($typeD -join ', ')"

    Write-Host "`nTotal: $($typeA.Count + $typeB.Count + $typeC.Count + $typeD.Count) doors"
}

$pipe.Close()
