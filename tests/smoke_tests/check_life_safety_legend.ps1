# Check Life Safety Legend views for occupant load
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
Write-Host "Checking Life Safety Legend views for occupant load" -ForegroundColor Cyan
Write-Host "=" * 60

# Life Safety Legend IDs from earlier scan
$legendIds = @(
    @{ id = "2570000"; name = "LIFE SAFETY LEGENDS" }
    @{ id = "2570051"; name = "LIFE SAFETY LEGENDS 2" }
)

foreach ($legend in $legendIds) {
    Write-Host "`n--- $($legend.name) (ID: $($legend.id)) ---" -ForegroundColor Yellow

    # Get all text in this view
    $result = Send-MCPRequest -Method "getTextNotesInView" -Params @{
        viewId = $legend.id
    }

    if ($result -and $result.success) {
        $notes = $result.result.textNotes
        Write-Host "Found $($notes.Count) text notes:" -ForegroundColor Green

        foreach ($note in $notes) {
            $text = $note.text
            # Highlight if contains "10" or "OCCUPANT"
            $highlight = ($text -match "10" -or $text -match "OCCUPANT")
            $color = if ($highlight) { "White" } else { "Gray" }

            if ($text.Length -gt 60) { $text = $text.Substring(0, 57) + "..." }
            Write-Host "  ID $($note.textNoteId): $text" -ForegroundColor $color
        }
    } else {
        Write-Host "Could not get text notes" -ForegroundColor Red
    }
}

# Also search for any "10" in occupancy-related text across all views
Write-Host "`n" + ("=" * 60)
Write-Host "Searching all text for occupancy-related '10'..." -ForegroundColor Cyan

$searches = @("LOAD: 10", "10 OCCUPANT", "10 PERSON", "= 10")
foreach ($term in $searches) {
    $result = Send-MCPRequest -Method "getTextElements" -Params @{
        searchText = $term
    }

    if ($result -and $result.success -and $result.result.textElements.Count -gt 0) {
        Write-Host "`nFound '$term':" -ForegroundColor Yellow
        foreach ($elem in $result.result.textElements) {
            $text = $elem.text
            if ($text.Length -gt 80) { $text = $text.Substring(0, 77) + "..." }
            Write-Host "  ID $($elem.id): $text" -ForegroundColor White
        }
    }
}
