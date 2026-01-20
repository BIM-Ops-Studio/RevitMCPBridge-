# Delete scattered notes and create consolidated checklist
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CONSOLIDATING SITE PLAN NOTES ===" -ForegroundColor Cyan

# IDs of notes to delete (the ones I added)
$notesToDelete = @(2027557, 2027558, 2027559, 2027560, 2027561, 2027562, 2027563, 2027564, 2027567, 2027578)

Write-Host "`nDeleting scattered notes..."
foreach ($id in $notesToDelete) {
    $json = "{`"method`":`"deleteTextNote`",`"params`":{`"elementId`":$id}}"
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json
    if ($result.success) {
        Write-Host "  Deleted note $id" -ForegroundColor Green
    } else {
        Write-Host "  Failed to delete $id : $($result.error)" -ForegroundColor Yellow
    }
}

Write-Host "`nCreating consolidated note..."

# Consolidated note text with numbered items
$noteText = @"
ZONING & CODE COMPLIANCE NOTES (REV 1):

1. BACKFLOW PREVENTER: REAR OF PROPERTY IN
   SCREENED ENCLOSURE PER MIAMI 21 SEC. 5.5.2(i)

2. VISIBILITY TRIANGLE: 10'-0" AT DRIVEWAY
   PER MIAMI 21 ART. 3 SEC. 3.8.4.1(b)
   NO OBSTRUCTIONS 2.5' TO 10' HEIGHT

3. DRIVEWAY WIDTH: 20'-0" PER SEC. 5.5.4(g)

4. DRIVE AISLE WIDTH: 24'-0"

5. PARKING SPACES: 8'-6" x 18'-0" (TYP.)
   PER CITY OF MIAMI STANDARDS

6. EV-CAPABLE PARKING: (1) SPACE DESIGNATED
   20% OF 5 SPACES = 1 REQ'D PER SEC. 3.6.1(f)

7. FENCE: 6'-0" ALUMINUM PRIVACY FENCE
   SEE DETAIL THIS SHEET

8. FIRST LAYER: 6.5' PAVED FLUSH W/ SIDEWALK
   PER ILLUSTRATION 8.4(b)

9. F.F.E. = 8.00' NGVD (VERIFY W/ SURVEY)

10. FDC: FRONT OF BLDG, NEAR MAIN ENTRANCE
    FIRE HYDRANT PER CITY STANDARDS
"@

# Place the consolidated note on site plan view
$siteViewId = 29237
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = $siteViewId
        location = @(35, 20, 0)
        text = $noteText
    }
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "  Consolidated note created (ID: $($result.result.textNoteId))" -ForegroundColor Green
} else {
    Write-Host "  Failed: $($result.error)" -ForegroundColor Red
}

$pipe.Close()

Write-Host "`n=== CONSOLIDATION COMPLETE ===" -ForegroundColor Green
