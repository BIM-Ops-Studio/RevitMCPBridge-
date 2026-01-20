# Office 40 Room Boundary Test Script
# Connects to RevitMCPBridge2026 and modifies wall location lines

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
        # Create named pipe client
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $PipeName, [System.IO.Pipes.PipeDirection]::InOut)

        # Connect with 5 second timeout
        $pipeClient.Connect(5000)

        if (-not $pipeClient.IsConnected) {
            throw "Failed to connect to pipe"
        }

        # Prepare request
        $request = @{
            method = $Method
            params = $Params
        } | ConvertTo-Json -Compress

        # Send request
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)

        # Read response
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
        # Cleanup in reverse order
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

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Office 40 Room Boundary Test" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$pipeName = "RevitMCPBridge2026"

# Step 1: Get all rooms
Write-Host "`n[1/5] Finding Office 40..." -ForegroundColor Yellow
$roomsResponse = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}

if (-not $roomsResponse.success) {
    Write-Host "❌ Failed to get rooms: $($roomsResponse.error)" -ForegroundColor Red
    exit 1
}

$rooms = $roomsResponse.result.rooms
$office40 = $rooms | Where-Object { $_.number -eq "40" -or $_.name -like "*40*" } | Select-Object -First 1

if (-not $office40) {
    Write-Host "❌ Office 40 not found!" -ForegroundColor Red
    Write-Host "`nAvailable rooms (first 10):" -ForegroundColor Yellow
    $rooms | Select-Object -First 10 | ForEach-Object { Write-Host "  - $($_.number): $($_.name)" }
    exit 1
}

Write-Host "✅ Found Office 40:" -ForegroundColor Green
Write-Host "   - Room ID: $($office40.id)"
Write-Host "   - Name: $($office40.name)"
Write-Host "   - Number: $($office40.number)"
Write-Host "   - Area: $($office40.area) sq ft"

# Step 2: Get room boundaries
Write-Host "`n[2/5] Getting Office 40 boundary information..." -ForegroundColor Yellow
$roomInfo = Send-RevitCommand -PipeName $pipeName -Method "getRoomInfo" -Params @{ roomId = $office40.id.ToString() }

if (-not $roomInfo.success) {
    Write-Host "❌ Failed: $($roomInfo.error)" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Room has $($roomInfo.result.boundaries.Count) boundary loops" -ForegroundColor Green

# Step 3: Get current view name
Write-Host "`n[3/5] Getting current view..." -ForegroundColor Yellow
$viewsResponse = Send-RevitCommand -PipeName $pipeName -Method "getAllViews" -Params @{}

if ($viewsResponse.success) {
    $activeView = $viewsResponse.result.views | Where-Object { $_.isActive -eq $true } | Select-Object -First 1
    if ($activeView) {
        Write-Host "✅ Current view: $($activeView.name)" -ForegroundColor Green
    }
}

# Step 4: Get walls in view
Write-Host "`n[4/5] Getting walls in current view..." -ForegroundColor Yellow
$wallsResponse = Send-RevitCommand -PipeName $pipeName -Method "getWallsInView" -Params @{}

if (-not $wallsResponse.success) {
    Write-Host "❌ Failed: $($wallsResponse.error)" -ForegroundColor Red
    exit 1
}

$walls = $wallsResponse.result.walls
Write-Host "✅ Found $($walls.Count) walls in view" -ForegroundColor Green

if ($walls.Count -eq 0) {
    Write-Host "⚠️  No walls found in current view!" -ForegroundColor Yellow
    Write-Host "Please make sure Level 7 Floor Plan Color view is active" -ForegroundColor Yellow
    exit 1
}

# Step 5: Interactive wall modification
Write-Host "`n[5/5] Wall Modification Options" -ForegroundColor Yellow
Write-Host "============================================================`n"

Write-Host "Choose modification strategy:"
Write-Host "  1. Modify FIRST 5 walls (demo mode)"
Write-Host "  2. Modify SPECIFIC wall by ID"
Write-Host "  3. Show all wall IDs and exit"
Write-Host "  4. Exit without changes"
Write-Host ""

$choice = Read-Host "Enter choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`nModifying first 5 walls..." -ForegroundColor Cyan

        $configs = @(
            @{ name = "Hallway Side"; locationLine = "FinishFaceExterior"; roomBounding = $true }
            @{ name = "Demising Wall"; locationLine = "FinishFaceInterior"; roomBounding = $true }
            @{ name = "Interior Wall"; locationLine = "CoreCenterline"; roomBounding = $true }
            @{ name = "Curtain Wall"; locationLine = "FinishFaceExterior"; roomBounding = $true }
            @{ name = "Partition"; locationLine = "WallCenterline"; roomBounding = $true }
        )

        for ($i = 0; $i -lt [Math]::Min(5, $walls.Count); $i++) {
            $wall = $walls[$i]
            $config = $configs[$i]

            Write-Host "`n  Wall $($i+1) - $($config.name) (ID: $($wall.id)):"
            Write-Host "    Type: $($wall.wallType)"
            Write-Host "    Setting locationLine = $($config.locationLine)"

            $result = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
                wallId = $wall.id.ToString()
                locationLine = $config.locationLine
                roomBounding = $config.roomBounding
            }

            if ($result.success) {
                $modified = $result.result.modified -join ", "
                Write-Host "    ✅ Success! Modified: $modified" -ForegroundColor Green
            } else {
                Write-Host "    ❌ Failed: $($result.error)" -ForegroundColor Red
            }

            Start-Sleep -Milliseconds 500
        }
    }

    "2" {
        Write-Host "`nEnter wall ID to modify:" -ForegroundColor Cyan
        $wallId = Read-Host "Wall ID"

        Write-Host "`nChoose location line:"
        Write-Host "  1. FinishFaceExterior (for hallways/exterior)"
        Write-Host "  2. FinishFaceInterior (for demising walls)"
        Write-Host "  3. CoreCenterline"
        Write-Host "  4. WallCenterline"
        Write-Host "  5. CoreExterior"
        Write-Host "  6. CoreInterior"

        $locChoice = Read-Host "Enter choice (1-6)"

        $locationLines = @(
            "FinishFaceExterior",
            "FinishFaceInterior",
            "CoreCenterline",
            "WallCenterline",
            "CoreExterior",
            "CoreInterior"
        )

        $locationLine = $locationLines[[int]$locChoice - 1]

        Write-Host "`nModifying wall $wallId with locationLine = $locationLine..." -ForegroundColor Cyan

        $result = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
            wallId = $wallId
            locationLine = $locationLine
            roomBounding = $true
        }

        if ($result.success) {
            Write-Host "✅ Success! Modified: $($result.result.modified -join ', ')" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed: $($result.error)" -ForegroundColor Red
        }
    }

    "3" {
        Write-Host "`nAll walls in view:" -ForegroundColor Cyan
        $walls | ForEach-Object {
            Write-Host "  - ID: $($_.id), Type: $($_.wallType), Length: $($_.length) ft"
        }
    }

    default {
        Write-Host "`nExiting without changes." -ForegroundColor Yellow
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Test Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Check Office 40 in Revit - room boundaries should update"
Write-Host "2. Use Room tool to verify area calculation"
Write-Host "3. Adjust more walls as needed"
