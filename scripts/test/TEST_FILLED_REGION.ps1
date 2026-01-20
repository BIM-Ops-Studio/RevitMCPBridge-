# Test Automated Filled Region Solution
function Send-RevitCommand {
    param([string]$PipeName, [string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        if (-not $pipeClient.IsConnected) { throw "Failed to connect" }
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        if ([string]::IsNullOrEmpty($response)) { throw "Empty response" }
        return $response | ConvertFrom-Json
    } catch {
        return @{ success = $false; error = $_.Exception.Message }
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "AUTOMATED FILLED REGION SOLUTION" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "This solution will:" -ForegroundColor Yellow
Write-Host "  1. Calculate offset boundaries for hallway walls" -ForegroundColor White
Write-Host "  2. Create a transparent filled region automatically" -ForegroundColor White
Write-Host "  3. Calculate the effective room area" -ForegroundColor White
Write-Host "  4. Show original vs effective area comparison`n" -ForegroundColor White

Write-Host "Creating filled region for Office 40..." -ForegroundColor Cyan

$result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "createRoomBoundaryFilledRegion" -Params @{
    roomId = "1314059"           # Office 40
    hallwayOffset = 0.5          # 0.5 ft offset toward office from hallway walls
    fillPatternName = "Solid fill"
    transparency = 50             # 50% transparent
}

if ($result.success) {
    Write-Host "`n✅ SUCCESS! Filled region created!" -ForegroundColor Green

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "AREA COMPARISON" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan

    Write-Host "`nRoom: $($result.roomNumber) - $($result.roomName)" -ForegroundColor White
    Write-Host "View: $($result.viewName)`n" -ForegroundColor Gray

    $original = [math]::Round($result.originalArea, 2)
    $effective = [math]::Round($result.effectiveArea, 2)
    $difference = [math]::Round($result.areaDifference, 2)
    $percentChange = [math]::Round(($difference / $original) * 100, 2)

    Write-Host "  Original Area:  $original sq ft" -ForegroundColor White
    Write-Host "  Effective Area: $effective sq ft" -ForegroundColor Green
    Write-Host "  Difference:     $difference sq ft ($percentChange%)" -ForegroundColor Yellow

    if ($result.offsetCount -gt 0) {
        Write-Host "`n  Wall Classifications & Offsets:" -ForegroundColor Cyan
        $result.offsets | ForEach-Object {
            $color = switch ($_.classification) {
                "Exterior" { "Magenta" }
                "Hallway" { "Yellow" }
                "Demising" { "Cyan" }
                default { "Gray" }
            }
            Write-Host "    • Wall $($_.wallId): $($_.classification)" -ForegroundColor $color
            Write-Host "      Type: $($_.wallType)" -ForegroundColor Gray
            Write-Host "      Thickness: $([math]::Round($_.wallThickness, 3)) ft" -ForegroundColor Gray
            Write-Host "      Offset: $([math]::Round($_.offsetDistance, 3)) ft" -ForegroundColor DarkGray
        }
    }

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "CHECK REVIT NOW!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan

    Write-Host "`nWhat you should see:" -ForegroundColor Yellow
    Write-Host "  1. A filled region around Office 40 with smart offsets" -ForegroundColor White
    Write-Host "  2. EXTERIOR walls: Boundary at EXTERIOR FACE (outside building)" -ForegroundColor Magenta
    Write-Host "  3. HALLWAY walls: Boundary at HALLWAY FACE (away from office)" -ForegroundColor Yellow
    Write-Host "  4. DEMISING walls: Boundary at CENTER of wall (no offset)" -ForegroundColor Cyan
    Write-Host "  5. The effective area reflects these intelligent boundaries`n" -ForegroundColor White

    Write-Host "Area Interpretation:" -ForegroundColor Yellow
    Write-Host "  Original: $original sq ft (Revit's calculation from wall centerlines)" -ForegroundColor Gray
    Write-Host "  Effective: $effective sq ft (Your actual usable space)" -ForegroundColor Green
    Write-Host "  This is what you'd use for lease calculations!`n" -ForegroundColor Yellow

} else {
    Write-Host "`n❌ FAILED: $($result.error)" -ForegroundColor Red

    if ($result.diagnostics) {
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "DIAGNOSTICS" -ForegroundColor Yellow
        Write-Host "============================================================" -ForegroundColor Cyan

        foreach ($diag in $result.diagnostics) {
            if ($diag.type -eq "boundary_analysis") {
                Write-Host "`nBoundary Analysis:" -ForegroundColor Cyan
                Write-Host "  Loop Count: $($diag.loopCount)" -ForegroundColor White
                Write-Host "  View Type: $($diag.viewType)" -ForegroundColor White
                Write-Host "  View Name: $($diag.viewName)" -ForegroundColor White
                Write-Host "  Level Z: $([math]::Round($diag.levelZ, 3))" -ForegroundColor White
            }
            elseif ($diag.type -eq "validation") {
                Write-Host "`nCurve Loop Validation:" -ForegroundColor Cyan
                Write-Host "  Curve Count: $($diag.curveCount)" -ForegroundColor White
                Write-Host "  Is Closed: $($diag.isClosed)" -ForegroundColor $(if ($diag.isClosed) { "Green" } else { "Red" })
                Write-Host "  Is Counterclockwise: $($diag.isCounterclockwise)" -ForegroundColor White
            }
            elseif ($diag.type -eq "curve") {
                if ($diag.index -eq 0) {
                    Write-Host "`nCurve Details:" -ForegroundColor Cyan
                }
                Write-Host "  Curve $($diag.index): Length=$([math]::Round($diag.length, 2)) ft" -ForegroundColor Gray
            }
        }
        Write-Host ""
    }

    if ($result.stackTrace) {
        Write-Host "`nStack Trace:" -ForegroundColor Yellow
        Write-Host $result.stackTrace -ForegroundColor Gray
    }

    Write-Host "`nPossible issues:" -ForegroundColor Yellow
    Write-Host "  1. Revit isn't running or project not open" -ForegroundColor White
    Write-Host "  2. Need to deploy new DLL (close Revit first)" -ForegroundColor White
    Write-Host "  3. Not in a floor plan view (switch to Level 7)" -ForegroundColor White
    Write-Host "  4. View's detail sketch plane not compatible with room level`n" -ForegroundColor White
}

Write-Host "============================================================`n" -ForegroundColor Cyan
