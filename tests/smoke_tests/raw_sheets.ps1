$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)
$request = '{"method":"getSheets","params":{}}'
$writer.WriteLine($request)
$response = $reader.ReadLine()
$pipe.Close()

# Output raw response
Write-Host "RAW RESPONSE:"
Write-Host $response
