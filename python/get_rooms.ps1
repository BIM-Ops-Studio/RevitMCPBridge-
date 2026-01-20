$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(5000)
$reader = New-Object System.IO.StreamReader($pipe)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true

$request = '{"method": "getRooms", "params": {}}'
$writer.WriteLine($request)
$response = $reader.ReadLine()
$pipe.Close()

Write-Output $response
