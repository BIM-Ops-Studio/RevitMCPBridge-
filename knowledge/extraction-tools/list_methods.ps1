$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(5000)

$reader = New-Object System.IO.StreamReader($pipeClient)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$writer.AutoFlush = $true

$request = '{"jsonrpc":"2.0","id":1,"method":"listMethods","params":{}}'
$writer.WriteLine($request)
Start-Sleep -Milliseconds 1000
$response = $reader.ReadLine()
Write-Host $response

$pipeClient.Close()
