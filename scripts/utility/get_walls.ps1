$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(10000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true
    $request = '{"method":"getWalls","params":{}}'
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output $response
    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
