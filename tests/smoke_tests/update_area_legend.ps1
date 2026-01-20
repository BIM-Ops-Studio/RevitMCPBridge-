# Update AREA CALCULATION Legend for 6365 West Semple Road
# Scaling areas from face-of-wall (963 SF) to center-of-wall (1,197 SF)
# Scale factor: 1,197 / 963 = 1.243

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

# Text note ID to new value mapping
# Original values scaled by 1.243 (from 963 SF to 1,197 SF)
$updates = @(
    @{ id = 2575537; text = "271 SF" }   # Storage (was 218 SF)
    @{ id = 2575539; text = "63 SF" }    # Restroom (was 51 SF)
    @{ id = 2575541; text = "92 SF" }    # Physician's Office (was 74 SF)
    @{ id = 2575543; text = "160 SF" }   # Client Lounge (was 129 SF)
    @{ id = 2575545; text = "138 SF" }   # Waiting Area (was 111 SF)
    @{ id = 2575547; text = "93 SF" }    # Reception (was 75 SF)
    @{ id = 2575549; text = "88 SF" }    # Consultation Room (was 71 SF)
    @{ id = 2575551; text = "97 SF" }    # Treatment Room #1 (was 78 SF)
    @{ id = 2575553; text = "97 SF" }    # Treatment Room #2 (was 78 SF)
    @{ id = 2575555; text = "97 SF" }    # Treatment Room #3 (was 78 SF)
    @{ id = 2575557; text = "1,197 SF" } # TOTAL (was 963 SF)
)

Write-Host "=" * 60
Write-Host "AREA CALCULATION Legend Update - 6365 West Semple Road" -ForegroundColor Cyan
Write-Host "Scaling from 963 SF (face of wall) to 1,197 SF (center of wall)" -ForegroundColor Gray
Write-Host "=" * 60

$successCount = 0
$failCount = 0

foreach ($update in $updates) {
    Write-Host "`nUpdating element $($update.id) to '$($update.text)'..." -NoNewline

    $result = Send-MCPRequest -Method "modifyTextNote" -Params @{
        elementId = $update.id.ToString()
        text = $update.text
    }

    if ($result -and $result.success) {
        Write-Host " OK" -ForegroundColor Green
        $successCount++
    }
    else {
        $errorMsg = if ($result) { $result.error } else { "Connection failed" }
        Write-Host " FAILED: $errorMsg" -ForegroundColor Red
        $failCount++
    }

    Start-Sleep -Milliseconds 500  # Brief pause between updates
}

Write-Host "`n" + ("=" * 60)
Write-Host "Summary: $successCount succeeded, $failCount failed" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "=" * 60
