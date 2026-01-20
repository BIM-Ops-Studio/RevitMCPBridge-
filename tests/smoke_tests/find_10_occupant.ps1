# Find text showing "10" as occupant load value
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

Write-Host "Searching for text with standalone '10' or '24' in occupancy context..." -ForegroundColor Cyan

# Get ALL text elements and filter
$result = Send-MCPRequest -Method "getTextElements" -Params @{}

if ($result -and $result.success) {
    $all = $result.result.textElements
    Write-Host "Total: $($all.Count) text elements" -ForegroundColor Gray

    # Filter for IDs in the 2570xxx range (Life Safety area)
    $lifeSafetyRange = $all | Where-Object { $_.id -ge 2570000 -and $_.id -lt 2580000 }
    Write-Host "In Life Safety range (2570xxx): $($lifeSafetyRange.Count) elements" -ForegroundColor Yellow

    foreach ($elem in $lifeSafetyRange) {
        $text = $elem.text
        # Show elements that might be occupant counts
        if ($text -match "^\d+$" -or $text -match "OCCUPANT" -or $text -match "\d+\s*(PERSON|OCCUPANT|MEN|WOMEN)") {
            Write-Host "`nID: $($elem.id)" -ForegroundColor Green
            Write-Host "Text: $text" -ForegroundColor White
        }
    }

    # Also search for just "10" as standalone text
    Write-Host "`n" + ("=" * 50)
    Write-Host "Searching for standalone '10' text..." -ForegroundColor Cyan

    $tens = $all | Where-Object { $_.text -eq "10" -or $_.text -match "^10$" -or $_.text -match "^\s*10\s*$" }
    foreach ($elem in $tens) {
        Write-Host "ID: $($elem.id) - Text: '$($elem.text)'" -ForegroundColor Yellow
    }
}
