# Add F.F.E. notes to floor plans
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
        Write-Host "Added to view $viewId : $text"
        return $result.result.textNoteId
    } else {
        Write-Host "Failed: $($result.error)"
        return $null
    }
}

Write-Host "=== ADDING F.F.E. NOTES ===" -ForegroundColor Cyan

# First Floor Plan (viewId 32)
$id1 = Place-TextNote -viewId 32 -x -10 -y 60 -text "F.F.E. = 8.00' NGVD`r(VERIFY W/ SURVEY)"

# Typical 2nd-3rd Floor (viewId 9948)
$id2 = Place-TextNote -viewId 9948 -x -10 -y 60 -text "F.F.E. L2 = 18.42' NGVD`rF.F.E. L3 = 28.83' NGVD`r(VERIFY W/ SURVEY)"

# Also add to Site Plan view for completeness
$id3 = Place-TextNote -viewId 29237 -x -30 -y 20 -text "GROUND FLOOR F.F.E. = 8.00' NGVD`r(VERIFY W/ SURVEY)`rPER FLOOD PLAIN COMMENT"

$pipe.Close()

Write-Host "`n=== F.F.E. NOTES COMPLETE ===" -ForegroundColor Green
