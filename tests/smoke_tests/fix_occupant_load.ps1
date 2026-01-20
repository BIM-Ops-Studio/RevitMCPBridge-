# Fix occupant load from 10 to 12
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

Write-Host "Updating occupant load from 10 to 12..." -ForegroundColor Cyan

# Update ID 2574691: "TOTAL OCCUPANT LOAD: 10 = 5 MEN AND 5 WOMEN" -> "TOTAL OCCUPANT LOAD: 12 = 6 MEN AND 6 WOMEN"
$result = Send-MCPRequest -Method "modifyTextNote" -Params @{
    elementId = "2574691"
    text = "TOTAL OCCUPANT LOAD: 12 = 6 MEN AND 6 WOMEN"
}

if ($result -and $result.success) {
    Write-Host "SUCCESS: Updated occupant load to 12 (6 men + 6 women)" -ForegroundColor Green
} else {
    $errorMsg = if ($result) { $result.error } else { "Connection failed" }
    Write-Host "FAILED: $errorMsg" -ForegroundColor Red
}

# Verify
Write-Host "`nVerifying change..." -ForegroundColor Yellow
$verify = Send-MCPRequest -Method "getTextElements" -Params @{
    searchText = "TOTAL OCCUPANT LOAD: 12"
}

if ($verify -and $verify.success -and $verify.result.textElements.Count -gt 0) {
    Write-Host "VERIFIED: Occupant load now shows 12" -ForegroundColor Green
} else {
    Write-Host "Verification pending - check Revit" -ForegroundColor Yellow
}
