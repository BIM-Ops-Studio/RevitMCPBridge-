$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(10000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true
    $request = '{"method":"getWalls","params":{"includeAllLevels":true}}'
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    # Parse JSON and count
    $data = $response | ConvertFrom-Json
    Write-Output "Total walls: $($data.wallCount)"
    Write-Output "Wall Types:"
    $data.walls | Group-Object wallType | ForEach-Object { Write-Output "  $($_.Name): $($_.Count)" }
    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
