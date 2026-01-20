$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

# Try getViews
$writer.WriteLine('{"method":"getViews","params":{}}')
$response = $reader.ReadLine()
Write-Host "getViews: $($response.Substring(0, [Math]::Min(200, $response.Length)))..."

$pipe.Close()
