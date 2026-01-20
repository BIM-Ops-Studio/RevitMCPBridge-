# Add fire/life safety annotations
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

# Function to place text note
function Place-TextNote {
    param($viewId, $x, $y, $text)

    $json = @{
        method = "placeTextNote"
        params = @{
            viewId = $viewId
            location = @($x, $y, 0.0)
            text = $text
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json

    if ($result.success) {
        Write-Host "Added to view $viewId : $($text.Substring(0, [Math]::Min(40, $text.Length)))..."
        return $result.result.textNoteId
    } else {
        Write-Host "Failed: $($result.error)"
        return $null
    }
}

Write-Host "=== ADDING FIRE/LIFE SAFETY ANNOTATIONS ===" -ForegroundColor Cyan

# Life Safety 1st Floor (viewId 1551343)
$id1 = Place-TextNote -viewId 1551343 -x -25 -y 70 -text "BUILDING PROTECTED THROUGHOUT`rBY AUTOMATIC SPRINKLER SYSTEM`rPER NFPA 101 SEC. 30.3.5.1"

$id2 = Place-TextNote -viewId 1551343 -x -25 -y 60 -text "FIRE ALARM SYSTEM PROVIDED`rPER NFPA 101 SEC. 30.3.4.1.1`r(4+ STORIES OR 11+ UNITS)"

$id3 = Place-TextNote -viewId 1551343 -x -25 -y 50 -text "SINGLE EXIT PERMITTED PER`rNFPA 101 SEC. 30.2.4.2`r(4 STORIES MAX, SPRINKLERED)"

# Life Safety 2nd-3rd Floor (viewId 1551353) - 20-min doors note
$id4 = Place-TextNote -viewId 1551353 -x -25 -y 70 -text "ALL DOORS TO CORRIDOR:`r20-MINUTE FIRE RATING`rPER NFPA 101 SEC. 30.3.6.2.1"

$id5 = Place-TextNote -viewId 1551353 -x -25 -y 60 -text "OCCUPANT LOAD:`r6 UNITS x 2 PERSONS = 12 MAX`rPER NFPA 101 SEC. 7.3.1.2"

# Note about 4th floor on the sheet view
$id6 = Place-TextNote -viewId 1551353 -x 30 -y 30 -text "NOTE: 4TH FLOOR LIFE SAFETY`rIS TYPICAL TO 2ND & 3RD FLOORS"

# Add to site plan - fire features note
$id7 = Place-TextNote -viewId 29237 -x -30 -y 10 -text "FDC LOCATION: FRONT OF BLDG`rNEAR MAIN ENTRANCE`rFIRE HYDRANT PER CITY STD"

$pipe.Close()

Write-Host "`n=== FIRE ANNOTATIONS COMPLETE ===" -ForegroundColor Green
