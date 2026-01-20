# Create sheets one at a time with fresh connections
param([string]$number, [string]$name)

$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(5000)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$reader = New-Object System.IO.StreamReader($pipeClient)

$json = '{"method":"createSheet","params":{"number":"' + $number + '","name":"' + $name + '"}}'
$writer.WriteLine($json)
$writer.Flush()
$response = $reader.ReadLine()
$pipeClient.Close()

Write-Output $response
