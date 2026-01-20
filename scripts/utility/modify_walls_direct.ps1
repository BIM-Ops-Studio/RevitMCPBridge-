# Direct wall modification script - uses exported view info
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

$pipeName = "RevitMCPBridge2026"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Direct Wall Modification for Office 40" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "This script will let you modify individual walls by Wall ID.`n" -ForegroundColor Yellow

Write-Host "From the floor plan image, I can see Office 40." -ForegroundColor Cyan
Write-Host "You'll need to identify which walls bound Office 40 in Revit.`n" -ForegroundColor Cyan

Write-Host "Settings to use:" -ForegroundColor Yellow
Write-Host "  - Exterior walls → FinishFaceExterior (option 3)" -ForegroundColor Yellow
Write-Host "  - Hallway walls → FinishFaceExterior (option 3)" -ForegroundColor Yellow
Write-Host "  - Interior/demising walls → WallCenterline (option 1)`n" -ForegroundColor Yellow

# Get wall ID from user
Write-Host "Enter the Wall ID to modify (you can find this by selecting a wall in Revit):" -ForegroundColor Cyan
$wallId = Read-Host "Wall ID"

if ([string]::IsNullOrWhiteSpace($wallId)) {
    Write-Host "❌ No Wall ID provided. Exiting." -ForegroundColor Red
    exit 1
}

# Choose location line
Write-Host "`nChoose location line for this wall:"
Write-Host "  1. WallCenterline (for interior/demising walls)" -ForegroundColor Cyan
Write-Host "  2. CoreCenterline" -ForegroundColor Cyan
Write-Host "  3. FinishFaceExterior (for exterior/hallway walls)" -ForegroundColor Cyan
Write-Host "  4. FinishFaceInterior" -ForegroundColor Cyan

$locChoice = Read-Host "`nEnter choice (1-4)"

$locationLines = @(
    "WallCenterline",
    "CoreCenterline",
    "FinishFaceExterior",
    "FinishFaceInterior"
)

if ([int]$locChoice -lt 1 -or [int]$locChoice -gt 4) {
    Write-Host "❌ Invalid choice. Exiting." -ForegroundColor Red
    exit 1
}

$locationLine = $locationLines[[int]$locChoice - 1]

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Modifying Wall $wallId..." -ForegroundColor Yellow
Write-Host "  Location Line: $locationLine" -ForegroundColor Yellow
Write-Host "  Room Bounding: Yes" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

# Modify the wall
$result = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
    wallId = $wallId
    locationLine = $locationLine
    roomBounding = $true
}

if ($result.success) {
    Write-Host "✅ SUCCESS! Wall modified." -ForegroundColor Green
    Write-Host "   Modified properties: $($result.result.modified -join ', ')`n" -ForegroundColor Green

    # Ask if user wants to modify another wall
    $another = Read-Host "Modify another wall? (y/n)"

    if ($another -eq "y") {
        Write-Host "`nRestarting script...`n" -ForegroundColor Cyan
        & $PSCommandPath
    } else {
        Write-Host "`n✅ Done! Check Office 40 in Revit to see the updated room boundaries.`n" -ForegroundColor Green
    }
} else {
    Write-Host "❌ FAILED: $($result.error)`n" -ForegroundColor Red
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "  1. The Wall ID is correct (numeric value)" -ForegroundColor Yellow
    Write-Host "  2. The wall exists in the active document`n" -ForegroundColor Yellow
}
