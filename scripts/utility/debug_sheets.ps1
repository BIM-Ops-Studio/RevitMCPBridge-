# Debug script to see raw sheet data

function Send-RevitCommand {
    param(
        [string]$PipeName,
        [string]$Method,
        [hashtable]$Params
    )

    $pipeClient = $null
    $writer = $null
    $reader = $null

    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)

        if (-not $pipeClient.IsConnected) {
            throw "Failed to connect to pipe"
        }

        $request = @{
            method = $Method
            params = $Params
        } | ConvertTo-Json -Compress

        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)

        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()

        if ([string]::IsNullOrEmpty($response)) {
            throw "Empty response from server"
        }

        return $response | ConvertFrom-Json
    }
    catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
        return @{
            success = $false
            error = $_.Exception.Message
        }
    }
    finally {
        if ($reader -ne $null) {
            try { $reader.Dispose() } catch {}
        }
        if ($writer -ne $null) {
            try { $writer.Dispose() } catch {}
        }
        if ($pipeClient -ne $null -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

$pipeName = "RevitMCPBridge2026"

Write-Host "Getting all sheets..." -ForegroundColor Yellow
$result = Send-RevitCommand -PipeName $pipeName -Method "getAllSheets" -Params @{}

if ($result.success) {
    $sheets = $result.result.sheets
    Write-Host "Found $($sheets.Count) sheets" -ForegroundColor Green

    Write-Host "`nFirst sheet raw data:" -ForegroundColor Cyan
    $firstSheet = $sheets[0]
    Write-Host ($firstSheet | ConvertTo-Json -Depth 5)

    Write-Host "`nLooking for SP sheets:" -ForegroundColor Cyan
    foreach ($sheet in $sheets) {
        if ($sheet.sheetNumber -like "*SP*") {
            Write-Host "`nSheet:" -ForegroundColor Yellow
            Write-Host "  sheetNumber: '$($sheet.sheetNumber)'" -ForegroundColor White
            Write-Host "  sheetName: '$($sheet.sheetName)'" -ForegroundColor White
            Write-Host "  sheetId: '$($sheet.sheetId)'" -ForegroundColor White
            Write-Host "  sheetId type: $($sheet.sheetId.GetType().Name)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "FAILED: $($result.error)" -ForegroundColor Red
}
