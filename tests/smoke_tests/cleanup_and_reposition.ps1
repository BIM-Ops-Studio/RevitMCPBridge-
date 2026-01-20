# Clean up duplicate labels and get coordinate info
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CLEANUP AND ANALYSIS ===" -ForegroundColor Cyan

# Navigate to legend
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

# Get ALL text notes in this view via a different method - get elements on sheet
# Try getting annotation elements
$json = '{"method":"getAnnotationsInView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Annotations found: $($result.result)"
} else {
    Write-Host "getAnnotationsInView: $($result.error)" -ForegroundColor Yellow
}

# Use element collector approach
$json = '{"method":"getViewElements","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nView elements:" -ForegroundColor Yellow
    foreach ($elem in $result.result.elements) {
        Write-Host "  $($elem.id): $($elem.category) - $($elem.name)"
    }
} else {
    Write-Host "getViewElements: $($result.error)" -ForegroundColor Yellow
}

# Since API text note retrieval isn't working as expected,
# Let me try getting elements by filtering
$json = '{"method":"getTextNotes","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nAll text notes in model:" -ForegroundColor Yellow
    foreach ($note in $result.result.textNotes) {
        $preview = $note.text -replace "`r`n", " " -replace "`n", " "
        if ($preview.Length -gt 40) { $preview = $preview.Substring(0,40) + "..." }
        # Check if it's one we might have added
        if ($note.text -like "*TYPE D*" -or $note.text -like "*TYPE E*" -or $note.text -like "*TYPE F*" -or $note.text -like "*SLIDING*" -or $note.text -like "*BYPASS*" -or $note.text -like "*FIRE-RATED*") {
            Write-Host "  ID: $($note.id) - Loc: ($($note.location.x), $($note.location.y)) - $preview" -ForegroundColor Cyan
        }
    }
} else {
    Write-Host "getTextNotes: $($result.error)" -ForegroundColor Yellow
}

$pipe.Close()
