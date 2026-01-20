$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(10000)

$reader = New-Object System.IO.StreamReader($pipeClient)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$writer.AutoFlush = $true

# Get loaded families (for titleblock)
Write-Host "FAMILIES_START"
$request = '{"jsonrpc":"2.0","id":1,"method":"getLoadedFamilies","params":{}}'
$writer.WriteLine($request)
Start-Sleep -Milliseconds 2000
$response = $reader.ReadLine()
Write-Host $response
Write-Host "FAMILIES_END"

$pipeClient.Close()
