# Dump ALL text elements and filter for "10" patterns
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

Write-Host "Getting ALL text elements..." -ForegroundColor Cyan

# Get all text elements (no filter)
$result = Send-MCPRequest -Method "getTextElements" -Params @{}

if ($result -and $result.success) {
    $all = $result.result.textElements
    Write-Host "Total text elements: $($all.Count)" -ForegroundColor Green

    # Filter for those containing "10"
    Write-Host "`nFiltering for text containing '10' near occupancy terms..." -ForegroundColor Yellow

    foreach ($elem in $all) {
        $text = $elem.text.ToUpper()

        # Check if it contains "10" AND some occupancy-related term
        if ($text -match "\b10\b" -and ($text -match "OCCUPANT" -or $text -match "LOAD" -or $text -match "PERSON" -or $text -match "MEN" -or $text -match "WOMEN")) {
            Write-Host "`n--- ID: $($elem.id) ---" -ForegroundColor Red
            Write-Host "$($elem.text)" -ForegroundColor White
        }
    }

    # Also specifically look for the calculation pattern showing 10 as a result
    Write-Host "`n" + ("=" * 60)
    Write-Host "Looking for calculation patterns with = 10..." -ForegroundColor Cyan

    foreach ($elem in $all) {
        $text = $elem.text
        if ($text -match "=\s*10\b" -or $text -match "\b10\s*=" -or $text -match ":\s*10\b") {
            Write-Host "`n--- ID: $($elem.id) ---" -ForegroundColor Yellow
            $display = if ($text.Length -gt 200) { $text.Substring(0, 200) + "..." } else { $text }
            Write-Host "$display" -ForegroundColor White
        }
    }
}
