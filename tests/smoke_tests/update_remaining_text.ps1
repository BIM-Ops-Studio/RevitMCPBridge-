# Update remaining text notes with 963 SF references
# Change 963 to 1,197 and occupant load from 10 to 12
$pipeName = "RevitMCPBridge2026"

function Send-MCPRequest {
    param(
        [string]$Method,
        [hashtable]$Params
    )

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Compress -Depth 10

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)

        $writer = New-Object System.IO.StreamWriter($pipe)
        $writer.AutoFlush = $true
        $reader = New-Object System.IO.StreamReader($pipe)

        $writer.WriteLine($request)
        $response = $reader.ReadLine()

        $pipe.Close()
        return $response | ConvertFrom-Json
    }
    catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

Write-Host "=" * 70
Write-Host "Updating remaining text notes: 963 -> 1,197 SF" -ForegroundColor Cyan
Write-Host "Occupant Load: 10 -> 12 persons" -ForegroundColor Cyan
Write-Host "=" * 70

# Update the simple text notes first
$simpleUpdates = @(
    @{ id = 2574303; text = "1,197 S.F." }  # Was 963 S.F.
    @{ id = 2574310; text = "1,197 S.F." }  # Was 963 S.F.
    @{ id = 2575588; text = "1,197 SF" }    # Was 963 SF
)

Write-Host "`nUpdating simple text notes..." -ForegroundColor Yellow

foreach ($update in $simpleUpdates) {
    Write-Host "  Updating ID $($update.id) to '$($update.text)'..." -NoNewline

    $result = Send-MCPRequest -Method "modifyTextNote" -Params @{
        elementId = $update.id.ToString()
        text = $update.text
    }

    if ($result -and $result.success) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        $errorMsg = if ($result) { $result.error } else { "Connection failed" }
        Write-Host " FAILED: $errorMsg" -ForegroundColor Red
    }

    Start-Sleep -Milliseconds 300
}

# Now update the large Life Safety Notes text (ID 2548296)
Write-Host "`nUpdating Life Safety Notes (ID 2548296)..." -ForegroundColor Yellow

$lifeSafetyNotesUpdated = @"
1. CORRIDOR PARTITIONS, SMOKESTOP PARTITIONS, HORIZONTAL EXIT PARTITIONS, EXIT ENCLOSURES AND FIRE RATED WALLS REQUIRED TO HAVE PROTECTED OPENINGS SHALL BE EFFECTIVELY AND PERMANENTLY IDENTIFIED WITH SIGNS OR STENCILED IN A MANNER ACCEPTABLE TO THE AUTHORITY HAVING JURISDICTION. SUCH IDENTIFICATION SHALL BE ABOVE ANY DECORATIVE CEILING AND IN CONCEALED SPACES. SUGGESTED WORDING: "FIRE AND SMOKE BARRIER PROTECT ALL OPENINGS".
2. ALL DOORS SHALL COMPLY WITH NFPA 101-7.2.1.5
3. EXIT DOORS SHALL BE EQUIPPED WITH DOOR HARDWARE THAT ALLOWS FOR IMMEDIATE EGRESS. NOTE: PANIC HARDWARE IS NOT REQUIRED FOR GROUP B OCCUPANCIES WITH OCCUPANT LOADS LESS THAN 50 PERSONS PER NFPA 101 - 7.2.1.7. DOORS THAT ARE REQUIRED TO BE AUTOMATIC-CLOSING SHALL BE PROVIDED WITH APPROVED DOOR HOLDING DEVICES OF THE FAIL-SAFE TYPE WHICH WILL RELEASE THE DOOR UPON ACTIVATION BY SMOKE DETECTORS.
4. PORTABLE FIRE EXTINGUISHER MULTIPURPOSE DRY-CHEMICAL TYPE, UL-RATED, 10 LB. NOMINAL CAPACITY IN ENAMELED-STEEL CONTAINER PER NFPA 10.
5. FIRE EXTINGUISHER REQUIREMENTS FOR #6365:
5.1. ONE (1) FIRE EXTINGUISHER TYPE ABC IN CUSTOMER/SERVICE AREAS.
5.1.1. REQUIREMENT IS MIN 1 PER EACH 3,000 SQ. FT. OF FLOOR AREA OR WITHIN A TRAVEL DISTANCE OF 75 FEET.
1 FIRE EXTINGUISHER (F.E.) REQUIRED, 1 FIRE EXTINGUISHER PROVIDED FOR #6365.
F.E. LOCATION IS NOTED ON LIFE SAFETY PLAN.
6. FIRE SPRINKLER SYSTEM:
THIS IS A NON-SPRINKLERED BUILDING. PER FBC 2023 SECTION 903.2, AN AUTOMATIC SPRINKLER SYSTEM IS NOT REQUIRED FOR GROUP B OCCUPANCIES WITH A FIRE AREA LESS THAN 12,000 SQ. FT. THIS BUILDING HAS A TOTAL AREA OF 1,197 SQ. FT. AND DOES NOT EXCEED THE THRESHOLD. NO FIRE SPRINKLER SUBPERMIT IS REQUIRED.
7. ALL EXITS & EXIT ACCESS SHALL HAVE CLASS "A" INTERIOR FINISHES. FLAME-SPREAD 0-25, SMOKE DEVELOPED 0-450 AS PER FBC 803.3 AND N.F.P.A. 101. ALL CORRIDORS SHALL HAVE CLASS 'A' OR 'B' INTERIOR FINISHES. ALL OTHER SPACES SHALL HAVE CLASS 'A', 'B' OR 'C' INTERIOR FINISHES.
8. THE FOLLOWING LIFE-SAFETY CRITERIA SHALL BE FOLLOWED:
-MINIMUM CORRIDOR WIDTH: 36"
-MINIMUM CLEAR OPENING OF EXIT DOORS: 32"
-COMMON PATH OF TRAVEL LIMIT: 75'
-MAXIMUM TRAVEL DISTANCE TO EXIT (NON-SPRINKLERED): 200'
9. OCCUPANT LOAD: 12 PERSONS (1,197 SQ. FT. / 100 SQ. FT. PER PERSON = 12)
10. PROVIDE 6" ADDRESS NUMBERS ON ALL EXTERIOR DOORS.
11. THE AUTHORITY HAVING JURISDICTION (AHJ) SHALL BE NOTIFIED WHEN ANY FIRE PROTECTION SYSTEM IS OUT OF SERVICE OR ON RESTORATION OF SERVICE.
CEILINGS
1. REFER TO REFLECTED CEILING PLAN FOR CEILING TYPES.
FINISHES:
1. ALL PLYWOOD / MDF / MILLWORK SHALL BE FIRE RETARDANT. ALL MILLWORK SHALL HAVE NEVAMAR LAMINATE FINISH TO MEET MINIMUM CODE REQUIREMENTS.
2. ALL WALLS SHALL BE PAINTED TO MEET MINIMUM REQUIREMENT OF CLASS B OR C AS PER CODE ANALYSIS.
"@

$result = Send-MCPRequest -Method "modifyTextNote" -Params @{
    elementId = "2548296"
    text = $lifeSafetyNotesUpdated
}

if ($result -and $result.success) {
    Write-Host "  Life Safety Notes updated successfully!" -ForegroundColor Green
} else {
    $errorMsg = if ($result) { $result.error } else { "Connection failed" }
    Write-Host "  FAILED: $errorMsg" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 70)
Write-Host "Update complete!" -ForegroundColor Green
Write-Host "Changes made:" -ForegroundColor Cyan
Write-Host "  - Area: 963 SF -> 1,197 SF (center of wall calculation)" -ForegroundColor White
Write-Host "  - Occupant Load: 10 -> 12 persons (1,197 / 100 = 12)" -ForegroundColor White
Write-Host "=" * 70
