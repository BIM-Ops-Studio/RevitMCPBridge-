$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    Write-Output "=== Arranging viewports on 36x24 sheets ==="
    Write-Output ""

    # AD-001: 4 viewports in 2x2 grid
    # Sheet is 3ft wide x 2ft tall
    # Position viewports in a nice 2x2 arrangement
    Write-Output "--- AD-001 ROOF DETAILS (4 viewports in 2x2 grid) ---"

    # Top row: ROOF CRICKET DIAGRAM and OVERFLOW SCUPPER
    # Bottom row: ROOF ANCHOR DETAIL and ROOF DRAIN DETAIL
    $ad001_moves = @(
        @{ id = 1249192; name = "ROOF CRICKET DIAGRAM"; x = 0.85; y = 1.4 },   # Top left
        @{ id = 1250522; name = "OVERFLOW SCUPPER"; x = 2.15; y = 1.4 },        # Top right
        @{ id = 1246691; name = "ROOF ANCHOR DETAIL"; x = 0.85; y = 0.6 },      # Bottom left
        @{ id = 1247622; name = "ROOF DRAIN DETAIL"; x = 2.15; y = 0.6 }        # Bottom right
    )

    foreach ($move in $ad001_moves) {
        $json = '{"method":"moveViewport","params":{"viewportId":' + $move.id + ',"newLocation":[' + $move.x + ',' + $move.y + ']}}'
        $writer.WriteLine($json)
        $response = $reader.ReadLine()
        $result = $response | ConvertFrom-Json
        if ($result.success) {
            Write-Output ("  " + $move.name + " -> (" + $move.x + ", " + $move.y + ") OK")
        } else {
            Write-Output ("  " + $move.name + " FAILED: " + $result.error)
        }
    }

    Write-Output ""
    Write-Output "--- AD-002 WALL DETAILS (3 viewports in row) ---"

    # 3 viewports spaced horizontally
    $ad002_moves = @(
        @{ id = 1253128; name = "PARAPET WALL DTL"; x = 0.75; y = 1.0 },         # Left
        @{ id = 1247647; name = "1HR BOTTOM WALL DETAIL"; x = 1.5; y = 1.0 },    # Center
        @{ id = 1253594; name = "STUCCO BAND DETAIL"; x = 2.25; y = 1.0 }        # Right
    )

    foreach ($move in $ad002_moves) {
        $json = '{"method":"moveViewport","params":{"viewportId":' + $move.id + ',"newLocation":[' + $move.x + ',' + $move.y + ']}}'
        $writer.WriteLine($json)
        $response = $reader.ReadLine()
        $result = $response | ConvertFrom-Json
        if ($result.success) {
            Write-Output ("  " + $move.name + " -> (" + $move.x + ", " + $move.y + ") OK")
        } else {
            Write-Output ("  " + $move.name + " FAILED: " + $result.error)
        }
    }

    Write-Output ""
    Write-Output "=== All viewports repositioned! ==="

} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
