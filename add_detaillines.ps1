$pipeName = 'RevitMCPBridge2026'

function Send-MCPRequest($request) {
    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)
        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $response = $reader.ReadLine()
        $pipe.Close()
        return $response
    } catch {
        Write-Host "Error: $_"
        return $null
    }
}

Write-Host "=== Adding Detail Lines as Leaders ==="

$views = @(
    @{id=2136700; name="Garage Roof"},
    @{id=2145981; name="Parapet"},
    @{id=2145960; name="Balcony"},
    @{id=2136787; name="Bedroom Balcony"},
    @{id=2136771; name="Canopy"}
)

$linesAdded = 0

foreach ($view in $views) {
    Write-Host "`nAdding leaders to $($view.name)..."

    # Add a few leader lines pointing to key areas
    # Using startPoint and endPoint parameters
    $leaders = @(
        @{sx=-0.3; sy=0.6; ex=-0.1; ey=0.5},
        @{sx=-0.3; sy=0.4; ex=-0.1; ey=0.3},
        @{sx=-0.3; sy=0.2; ex=-0.1; ey=0.1}
    )

    foreach ($leader in $leaders) {
        $request = '{"method": "createDetailLine", "params": {"viewId": ' + $view.id + ', "startPoint": [' + $leader.sx + ',' + $leader.sy + ',0], "endPoint": [' + $leader.ex + ',' + $leader.ey + ',0]}}'
        $result = Send-MCPRequest($request) | ConvertFrom-Json
        if ($result.success) {
            $linesAdded++
            Write-Host "  Added leader line"
        } else {
            Write-Host "  Failed: $($result.error)"
            break
        }
    }
}

Write-Host "`n=== Total leader lines added: $linesAdded ==="
