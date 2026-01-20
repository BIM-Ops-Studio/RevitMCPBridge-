# Add roof and 4th floor annotations
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

Write-Host "=== ADDING ROOF & 4TH FLOOR ANNOTATIONS ===" -ForegroundColor Cyan

# 4th Floor Plan (viewId 1801007) - F.F.E.
$id1 = Place-TextNote -viewId 1801007 -x -10 -y 60 -text "F.F.E. L4 = 39.25' NGVD`r(VERIFY W/ SURVEY)"

# Roof Plan (viewId 1200905) - Multiple notes
$id2 = Place-TextNote -viewId 1200905 -x -20 -y 50 -text "ROOF MATERIAL: LIGHT-COLORED,`rHIGH ALBEDO OR PLANTED SURFACE`rPER MIAMI 21 SEC. 5.5.5(c)`rAND ART. 3 SEC. 3.13.2"

$id3 = Place-TextNote -viewId 1200905 -x 20 -y 30 -text "(6) CONDENSING UNITS`rBEHIND PARAPET`rSCREENED FROM LATERAL VIEW`rPER MIAMI 21 SEC. 5.5.2(i)"

$id4 = Place-TextNote -viewId 1200905 -x 0 -y 55 -text "ROOF ELEV. = 49.67' NGVD`r(VERIFY W/ SURVEY)"

$pipe.Close()

Write-Host "`n=== ROOF ANNOTATIONS COMPLETE ===" -ForegroundColor Green
