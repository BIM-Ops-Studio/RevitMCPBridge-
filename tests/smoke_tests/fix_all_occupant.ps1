# Fix ALL occupant load values in Life Safety Legends 2
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
Write-Host "Fixing occupant load values in Life Safety Legends 2" -ForegroundColor Cyan
Write-Host "=" * 60

$updates = @(
    @{ id = "2570236"; oldText = "24 OCCUPANTS (100 SF/PERSON)"; newText = "12 OCCUPANTS (100 SF/PERSON)" }
    @{ id = "2570290"; oldText = "24 PERSONS"; newText = "12 PERSONS" }
    @{ id = "2574305"; oldText = "10"; newText = "12" }
    @{ id = "2574312"; oldText = "10"; newText = "12" }
)

foreach ($update in $updates) {
    Write-Host "`nUpdating ID $($update.id):" -ForegroundColor Yellow
    Write-Host "  '$($update.oldText)' -> '$($update.newText)'" -ForegroundColor Gray

    $result = Send-MCPRequest -Method "modifyTextNote" -Params @{
        elementId = $update.id
        text = $update.newText
    }

    if ($result -and $result.success) {
        Write-Host "  SUCCESS" -ForegroundColor Green
    } else {
        $errorMsg = if ($result) { $result.error } else { "Connection failed" }
        Write-Host "  FAILED: $errorMsg" -ForegroundColor Red
    }

    Start-Sleep -Milliseconds 300
}

Write-Host "`n" + ("=" * 60)
Write-Host "Verifying changes..." -ForegroundColor Cyan

# Verify no more "24" or standalone "10" in occupant context
$verify = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "24 OCCUPANTS"
}

if ($verify -and $verify.success -and $verify.result.textElements.Count -eq 0) {
    Write-Host "Good - no '24 OCCUPANTS' remaining" -ForegroundColor Green
} else {
    Write-Host "WARNING: Still found '24 OCCUPANTS'" -ForegroundColor Yellow
}

Write-Host "`nDone! Occupant load should now show 12." -ForegroundColor Cyan
