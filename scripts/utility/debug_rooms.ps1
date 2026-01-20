# Debug script to see what getRooms returns

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

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Room Debugging Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get current view
Write-Host "`n[1] Getting current view..." -ForegroundColor Yellow
$viewsResponse = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{}

if ($viewsResponse.success) {
    $activeView = $viewsResponse.result.views | Where-Object { $_.isActive -eq $true } | Select-Object -First 1
    if ($activeView) {
        Write-Host "✅ Current view: $($activeView.name) (ID: $($activeView.id))" -ForegroundColor Green
        Write-Host "   View Type: $($activeView.viewType)" -ForegroundColor Gray
        $currentViewId = $activeView.id
    } else {
        Write-Host "⚠️  No active view found" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Failed to get views: $($viewsResponse.error)" -ForegroundColor Red
}

# Try getRooms with no parameters
Write-Host "`n[2] Getting rooms (no parameters)..." -ForegroundColor Yellow
$roomsResponse1 = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}

Write-Host "Raw response:" -ForegroundColor Gray
Write-Host ($roomsResponse1 | ConvertTo-Json -Depth 5) -ForegroundColor DarkGray

if ($roomsResponse1.success) {
    $rooms = $roomsResponse1.result.rooms
    Write-Host "✅ Success! Found $($rooms.Count) rooms" -ForegroundColor Green

    if ($rooms.Count -gt 0) {
        Write-Host "`nFirst 10 rooms:" -ForegroundColor Cyan
        $rooms | Select-Object -First 10 | ForEach-Object {
            Write-Host "  - Number: $($_.number), Name: $($_.name), ID: $($_.id), Level: $($_.level)" -ForegroundColor White
        }

        # Search for Office 40
        Write-Host "`n[3] Searching for Office 40..." -ForegroundColor Yellow
        $office40Candidates = $rooms | Where-Object {
            $_.number -like "*40*" -or
            $_.name -like "*40*" -or
            $_.name -like "*Office*40*"
        }

        if ($office40Candidates.Count -gt 0) {
            Write-Host "✅ Found $($office40Candidates.Count) candidate(s) for Office 40:" -ForegroundColor Green
            $office40Candidates | ForEach-Object {
                Write-Host "  - Number: $($_.number), Name: $($_.name), ID: $($_.id)" -ForegroundColor Cyan
            }
        } else {
            Write-Host "❌ No rooms matching 'Office 40' pattern found" -ForegroundColor Red
            Write-Host "`nAll room names:" -ForegroundColor Yellow
            $rooms | ForEach-Object {
                Write-Host "  - $($_.number): $($_.name)" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "⚠️  No rooms returned!" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Failed: $($roomsResponse1.error)" -ForegroundColor Red
}

# Try with current view ID if we have one
if ($currentViewId) {
    Write-Host "`n[4] Getting rooms in current view (ID: $currentViewId)..." -ForegroundColor Yellow
    $roomsResponse2 = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{ viewId = $currentViewId.ToString() }

    if ($roomsResponse2.success) {
        $roomsInView = $roomsResponse2.result.rooms
        Write-Host "✅ Found $($roomsInView.Count) rooms in current view" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed: $($roomsResponse2.error)" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Debug Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
