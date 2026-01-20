# Add site plan annotations for permit response
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

# Site Plan view ID
$siteViewId = 29237

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
        Write-Host "Added: $text"
        return $result.result.textNoteId
    } else {
        Write-Host "Failed: $($result.error)"
        return $null
    }
}

Write-Host "=== ADDING SITE PLAN ANNOTATIONS ===" -ForegroundColor Cyan

# 1. Backflow Preventer Note (rear of property, screened)
$id1 = Place-TextNote -viewId $siteViewId -x -20 -y 30 -text "BACKFLOW PREVENTER`rIN SCREENED ENCLOSURE`rPER MIAMI 21 SEC. 5.5.2(i)"

# 2. Visibility Triangle Note
$id2 = Place-TextNote -viewId $siteViewId -x 0 -y -5 -text "10'-0"" VISIBILITY TRIANGLE`rPER MIAMI 21 ART. 3 SEC. 3.8.4.1(b)`rNO OBSTRUCTIONS 2.5' TO 10' HEIGHT"

# 3. Driveway Width
$id3 = Place-TextNote -viewId $siteViewId -x 10 -y -2 -text "DRIVEWAY WIDTH: 20'-0""`rPER MIAMI 21 SEC. 5.5.4(g)"

# 4. Parking Space Dimensions
$id4 = Place-TextNote -viewId $siteViewId -x 25 -y 15 -text "TYP. PARKING SPACE`r8'-6"" x 18'-0""`rPER CITY OF MIAMI STANDARDS"

# 5. EV Parking Designation
$id5 = Place-TextNote -viewId $siteViewId -x 25 -y 25 -text "EV-CAPABLE PARKING (1)`r20% OF 5 SPACES = 1 REQ'D`rPER MIAMI 21 ART. 3 SEC. 3.6.1(f)"

# 6. Drive Aisle Width
$id6 = Place-TextNote -viewId $siteViewId -x 15 -y 20 -text "DRIVE AISLE: 24'-0"""

# 7. Fence Note
$id7 = Place-TextNote -viewId $siteViewId -x -25 -y 40 -text "6'-0"" ALUMINUM PRIVACY FENCE`rSEE DETAIL THIS SHEET"

# 8. First Layer Paving Note
$id8 = Place-TextNote -viewId $siteViewId -x 5 -y -8 -text "FIRST LAYER: 6.5' PAVED`rFLUSH W/ SIDEWALK`rPER ILLUSTRATION 8.4(b)"

$pipe.Close()

Write-Host "`n=== SITE ANNOTATIONS COMPLETE ===" -ForegroundColor Green
