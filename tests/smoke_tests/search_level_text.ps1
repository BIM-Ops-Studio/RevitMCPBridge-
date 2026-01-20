# Search for various text patterns
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

$searches = @("ALTERATION", "Level 2", "LEVEL 2", "ALTER", "level")

foreach ($term in $searches) {
    Write-Host "`nSearching for '$term'..." -ForegroundColor Cyan

    $result = Send-MCPRequest -Method "getTextElements" -Params @{
        searchText = $term
    }

    if ($result -and $result.success) {
        $elements = $result.result.textElements
        if ($elements -and $elements.Count -gt 0) {
            Write-Host "Found $($elements.Count) elements:" -ForegroundColor Green
            foreach ($elem in $elements) {
                $text = $elem.text
                if ($text.Length -gt 60) { $text = $text.Substring(0, 57) + "..." }
                Write-Host "  ID $($elem.id): $text" -ForegroundColor White
            }
        }
    }
}

# Also get text from Life Safety Legends 2 view (ID: 2570051)
Write-Host "`n" + ("=" * 50)
Write-Host "Getting text from Life Safety Legends 2 (2570051)..." -ForegroundColor Cyan

$result = Send-MCPRequest -Method "getTextNotesInView" -Params @{
    viewId = "2570051"
}

if ($result -and $result.success) {
    $notes = $result.result.textNotes
    Write-Host "Found $($notes.Count) text notes in view"
    foreach ($note in $notes) {
        Write-Host "  ID $($note.textNoteId): $($note.text)" -ForegroundColor Gray
    }
}
