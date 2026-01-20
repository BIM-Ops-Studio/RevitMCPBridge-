# Quick script to list all rooms
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
        if ($reader -ne $null) { try { $reader.Dispose() } catch {} }
        if ($writer -ne $null) { try { $writer.Dispose() } catch {} }
        if ($pipeClient -ne $null -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

Write-Host "`nQuerying RevitMCPBridge for all rooms..." -ForegroundColor Cyan

$response = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRooms" -Params @{}

if (-not $response.success) {
    Write-Host "Failed to get rooms: $($response.error)" -ForegroundColor Red
    exit 1
}

$rooms = $response.result.rooms

Write-Host "`nFound $($rooms.Count) rooms in the model:" -ForegroundColor Green
Write-Host "============================================================`n"

if ($rooms.Count -eq 0) {
    Write-Host "No rooms found! Make sure you have a floor plan view active." -ForegroundColor Yellow
} else {
    $rooms | Sort-Object number | ForEach-Object {
        $areaStr = if ($_.area -gt 0) { "$([math]::Round($_.area, 1)) sq ft" } else { "Not placed" }
        Write-Host "  Room $($_.number): $($_.name) - $areaStr (ID: $($_.roomId))"
    }

    Write-Host "`n============================================================"
    Write-Host "Looking for Office 40 or similar..." -ForegroundColor Cyan

    $office40 = $rooms | Where-Object {
        $_.number -eq "40" -or
        $_.number -eq "040" -or
        $_.name -like "*Office 40*" -or
        $_.name -like "*40*"
    }

    if ($office40) {
        Write-Host "Found matches:" -ForegroundColor Green
        $office40 | ForEach-Object {
            Write-Host "  - Room $($_.number): $($_.name) (ID: $($_.roomId))"
        }
    } else {
        Write-Host "No room found with number '40' or name containing 'Office 40'" -ForegroundColor Yellow
    }
}
