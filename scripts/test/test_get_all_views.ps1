# Simple test to get ALL views without filter
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
        Write-Host "Details: $($_.Exception)" -ForegroundColor Red
        return @{
            success = $false
            error = $_.Exception.Message
        }
    }
    finally {
        if ($reader -ne $null) { try { $reader.Dispose() } catch {} }
        if ($writer -ne $null) { try { $writer.Dispose() } catch {} }
        if ($pipeClient -ne $null -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

$pipeName = "RevitMCPBridge2026"

Write-Host "`nTesting getAllViews...`n" -ForegroundColor Cyan

# Test 1: Get ALL views (no filter)
Write-Host "[Test 1] Getting ALL views (no filter)..." -ForegroundColor Yellow
$result1 = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{}

if ($result1.success) {
    Write-Host "✅ Success! Found $($result1.result.viewCount) views" -ForegroundColor Green
    Write-Host "`nFirst 10 views:" -ForegroundColor Cyan
    $result1.result.views | Select-Object -First 10 | ForEach-Object {
        Write-Host "  - $($_.viewName) (ID: $($_.viewId), Type: $($_.viewType))"
    }
} else {
    Write-Host "❌ Failed: $($result1.error)" -ForegroundColor Red
}

# Test 2: Try the old method name
Write-Host "`n[Test 2] Trying 'getViews' method..." -ForegroundColor Yellow
$result2 = Send-RevitCommand -PipeName $pipeName -Method "getViews" -Params @{}

if ($result2.success) {
    Write-Host "✅ Success!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed: $($result2.error)" -ForegroundColor Red
}

Write-Host "`n"
