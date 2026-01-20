# Find ALL text containing "10" that might be occupancy related
$pipeName = "RevitMCPBridge2026"

function Send-MCPRequest {
    param(
        [string]$Method,
        [hashtable]$Params
    )

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Compress

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
Write-Host "Finding ALL text with '10' (filtering for occupancy-related)" -ForegroundColor Cyan
Write-Host "=" * 70

# Get elements from sheet A0.3 (ID: 2548220)
Write-Host "`nGetting elements from sheet A0.3..." -ForegroundColor Yellow
$elements = Send-MCPRequest -Method "getElementsInView" -Params @{
    viewId = "2548220"
}

if ($elements -and $elements.success) {
    Write-Host "Found $($elements.result.elements.Count) elements on sheet" -ForegroundColor Green
}

# Search for specific patterns
$patterns = @(
    "OCCUPANT LOAD: 10",
    "10 OCCUPANTS",
    "10 PERSONS",
    "LOAD: 10",
    "= 10 =",
    ": 10 PERSON",
    "10 = 5 MEN"
)

Write-Host "`nSearching for occupancy patterns..." -ForegroundColor Yellow

foreach ($pattern in $patterns) {
    $result = Send-MCPRequest -Method "getTextElements" -Params @{
        searchText = $pattern
    }

    if ($result -and $result.success) {
        $count = 0
        if ($result.result.textElements) {
            $count = $result.result.textElements.Count
        }

        if ($count -gt 0) {
            Write-Host "`nFOUND '$pattern' in $count elements:" -ForegroundColor Red
            foreach ($elem in $result.result.textElements) {
                Write-Host "  ID: $($elem.id)" -ForegroundColor Yellow
                # Show context around the match
                $text = $elem.text
                if ($text.Length -gt 100) {
                    # Find the pattern in text and show context
                    $idx = $text.ToLower().IndexOf($pattern.ToLower())
                    if ($idx -ge 0) {
                        $start = [Math]::Max(0, $idx - 20)
                        $end = [Math]::Min($text.Length, $idx + $pattern.Length + 30)
                        $context = "..." + $text.Substring($start, $end - $start) + "..."
                        Write-Host "  Context: $context" -ForegroundColor White
                    }
                } else {
                    Write-Host "  Text: $text" -ForegroundColor White
                }
            }
        }
    }
}

# Also get text notes from the sheet view itself
Write-Host "`n" + ("=" * 70)
Write-Host "Getting text notes directly from sheet A0.3..." -ForegroundColor Cyan

$sheetText = Send-MCPRequest -Method "getTextNotesInView" -Params @{
    viewId = "2548220"
}

if ($sheetText -and $sheetText.success) {
    $notes = $sheetText.result.textNotes
    Write-Host "Found $($notes.Count) text notes on sheet"

    # Filter for those containing "10" and occupancy-related terms
    $occupancyNotes = $notes | Where-Object {
        $_.text -match "OCCUPANT" -or $_.text -match "LOAD.*10" -or $_.text -match "10.*PERSON"
    }

    if ($occupancyNotes) {
        Write-Host "`nOccupancy-related notes:" -ForegroundColor Yellow
        foreach ($note in $occupancyNotes) {
            Write-Host "  ID $($note.textNoteId): $($note.text.Substring(0, [Math]::Min(80, $note.text.Length)))..." -ForegroundColor White
        }
    }
}

# Check IDs we found earlier that have OCCUPANT text
Write-Host "`n" + ("=" * 70)
Write-Host "Checking specific occupancy-related text note IDs..." -ForegroundColor Cyan

$occupancyIds = @(2570235, 2570236, 2570289, 2574297, 2574298)

foreach ($id in $occupancyIds) {
    # Get the full text of this element
    $search = Send-MCPRequest -Method "getTextElements" -Params @{
        searchText = "OCCUPANT"
    }

    if ($search -and $search.success) {
        $elem = $search.result.textElements | Where-Object { $_.id -eq $id }
        if ($elem) {
            Write-Host "`nID $id :" -ForegroundColor Yellow
            Write-Host "  $($elem.text)" -ForegroundColor White
        }
    }
}
