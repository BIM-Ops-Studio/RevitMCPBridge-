# Check MEANS OF EGRESS legend text notes
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

# Get all legends on the current sheet
Write-Host "Getting legends..." -ForegroundColor Cyan
$legends = Send-MCPRequest -Method "getLegends" -Params @{}

if ($legends -and $legends.success) {
    $legendList = $legends.result.legends
    Write-Host "Found $($legendList.Count) legends:" -ForegroundColor Green

    foreach ($legend in $legendList) {
        Write-Host "`n--- $($legend.name) (ID: $($legend.id)) ---" -ForegroundColor Yellow

        # Get text notes in this legend
        $textNotes = Send-MCPRequest -Method "getTextNotesInView" -Params @{
            viewId = $legend.id.ToString()
        }

        if ($textNotes -and $textNotes.success) {
            $notes = $textNotes.result.textNotes
            Write-Host "  Text notes: $($notes.Count)"

            foreach ($note in $notes) {
                $text = $note.text
                if ($text.Length -gt 50) { $text = $text.Substring(0, 47) + "..." }
                Write-Host "    ID $($note.textNoteId): $text" -ForegroundColor Gray
            }
        }
    }
}
else {
    Write-Host "Failed to get legends" -ForegroundColor Red
}
