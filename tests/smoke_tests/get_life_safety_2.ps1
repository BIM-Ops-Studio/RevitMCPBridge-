# Get text from LIFE SAFETY LEGENDS 2 (ID: 2570051)
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

Write-Host "=" * 60
Write-Host "LIFE SAFETY LEGENDS 2 (ID: 2570051)" -ForegroundColor Cyan
Write-Host "=" * 60

# Try different methods to get elements from this view

# Method 1: getTextNotesInView
Write-Host "`nTrying getTextNotesInView..." -ForegroundColor Yellow
$result1 = Send-MCPRequest -Method "getTextNotesInView" -Params @{
    viewId = "2570051"
}

if ($result1 -and $result1.success) {
    $notes = $result1.result.textNotes
    Write-Host "Found $($notes.Count) text notes"
    foreach ($note in $notes) {
        Write-Host "  ID $($note.textNoteId): $($note.text)" -ForegroundColor Gray
    }
}

# Method 2: getElementsInView
Write-Host "`nTrying getElementsInView..." -ForegroundColor Yellow
$result2 = Send-MCPRequest -Method "getElementsInView" -Params @{
    viewId = "2570051"
}

if ($result2 -and $result2.success) {
    Write-Host "Found $($result2.result.elements.Count) elements"
    foreach ($elem in $result2.result.elements) {
        Write-Host "  ID $($elem.id): $($elem.name) [$($elem.category)]" -ForegroundColor Gray
    }
}

# Method 3: Get text elements and filter by view
Write-Host "`nSearching all text containing 'OCCUPANT LOAD' or '10'..." -ForegroundColor Yellow

$searches = @("OCCUPANT LOAD:", "10 OCCUPANTS", "= 10", "10 =", ": 10")
foreach ($term in $searches) {
    $result = Send-MCPRequest -Method "getTextElements" -Params @{
        searchText = $term
    }

    if ($result -and $result.success -and $result.result.textElements) {
        foreach ($elem in $result.result.textElements) {
            # Check if this is likely from Life Safety Legend
            $text = $elem.text.ToUpper()
            if ($text -match "OCCUPANT" -or ($text -match "\b10\b" -and ($text -match "PERSON" -or $text -match "MEN" -or $text -match "WOMEN"))) {
                Write-Host "`n--- Found match for '$term' ---" -ForegroundColor Yellow
                Write-Host "ID: $($elem.id)" -ForegroundColor Green
                $display = if ($elem.text.Length -gt 100) { $elem.text.Substring(0, 100) + "..." } else { $elem.text }
                Write-Host "Text: $display" -ForegroundColor White
            }
        }
    }
}

# Specifically look at IDs near 2570000 range (Life Safety Legend area)
Write-Host "`n" + ("=" * 60)
Write-Host "Checking IDs in the 2570xxx range (Life Safety)..." -ForegroundColor Cyan

$lifeSafetyIds = @(2570235, 2570236, 2570289)

foreach ($id in $lifeSafetyIds) {
    # Get element by searching for text that might match
    $result = Send-MCPRequest -Method "getTextElements" -Params @{}

    if ($result -and $result.success) {
        $elem = $result.result.textElements | Where-Object { $_.id -eq $id }
        if ($elem) {
            Write-Host "`nID $id :" -ForegroundColor Yellow
            Write-Host "$($elem.text)" -ForegroundColor White
        }
    }
}
