# Place consolidated checklist note on sheet SP-1.0
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== PLACING CONSOLIDATED NOTE ON SHEET ===" -ForegroundColor Cyan

# Sheet ID for SP-1.0 (SITE PLAN / PROPERTY DATA)
$sheetId = 1544935

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

# Place at the right side of sheet (typical note location)
# Sheet coordinates are in feet from sheet origin
$json = @{
    method = "placeTextNote"
    params = @{
        viewId = $sheetId
        location = @(2.0, 1.5, 0)  # Right side of 24x36 sheet
        text = $noteText
    }
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Consolidated note placed on sheet!" -ForegroundColor Green
    Write-Host "  Note ID: $($result.result.textNoteId)"
} else {
    Write-Host "Failed: $($result.error)" -ForegroundColor Red
}

$pipe.Close()

Write-Host "`n=== COMPLETE ===" -ForegroundColor Green
