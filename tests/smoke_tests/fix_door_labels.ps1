# Fix door type label positions
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== FIXING DOOR TYPE LABELS ===" -ForegroundColor Cyan

# First, get existing text notes in the legend to find the ones we added
$json = '{"method":"getTextNotesInView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Found $($result.result.textNotes.Count) text notes"

    # Find and delete the ones we just added (TYPE D, TYPE E, TYPE F)
    foreach ($note in $result.result.textNotes) {
        if ($note.text -like "*TYPE D*" -or $note.text -like "*TYPE E*" -or $note.text -like "*TYPE F*" -or $note.text -like "*SLIDING GLASS*" -or $note.text -like "*CLOSET BYPASS*" -or $note.text -like "*FIRE-RATED*") {
            Write-Host "  Deleting: $($note.text.Substring(0, [Math]::Min(30, $note.text.Length)))..." -ForegroundColor Yellow
            $deleteJson = "{`"method`":`"deleteTextNote`",`"params`":{`"elementId`":$($note.id)}}"
            $writer.WriteLine($deleteJson)
            $delResponse = $reader.ReadLine()
        }
    }
}

Start-Sleep -Milliseconds 500

Write-Host "`nAdding labels at correct positions..." -ForegroundColor Cyan

# Based on existing TYPE A, B, C positions, the doors are spaced about 1.5 feet apart
# TYPE A is around x=0.5, TYPE B around x=2.0, TYPE C around x=3.5
# 4th door should be around x=5.0, 5th door around x=6.2

# Add TYPE D label under 4th door symbol
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(5.0, 4.5, 0)
        text = "TYPE D`nSLIDING GLASS"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
if ($result.success) {
    Write-Host "Added TYPE D at (5.0, 4.5)" -ForegroundColor Green
} else {
    Write-Host "TYPE D Error: $($result.error)" -ForegroundColor Red
}

# Add TYPE E label under 5th door symbol
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(6.2, 4.5, 0)
        text = "TYPE E`nCLOSET BYPASS"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
if ($result.success) {
    Write-Host "Added TYPE E at (6.2, 4.5)" -ForegroundColor Green
} else {
    Write-Host "TYPE E Error: $($result.error)" -ForegroundColor Red
}

# Add TYPE F label in the empty frame area
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = 1760142
        location = @(1.5, 3.0, 0)
        text = "TYPE F`nFIRE-RATED"
    }
} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
if ($result.success) {
    Write-Host "Added TYPE F at (1.5, 3.0)" -ForegroundColor Green
} else {
    Write-Host "TYPE F Error: $($result.error)" -ForegroundColor Red
}

$pipe.Close()
Write-Host "`nDone fixing labels"
