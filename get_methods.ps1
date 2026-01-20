$pipeName = 'RevitMCPBridge2026'
$request = '{"method": "getMethods"}'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(5000)
$writer = New-Object System.IO.StreamWriter($pipe)
$reader = New-Object System.IO.StreamReader($pipe)
$writer.AutoFlush = $true
$writer.WriteLine($request)
$response = $reader.ReadLine()
$pipe.Close()
$response | Out-File -FilePath "D:\RevitMCPBridge2026\methods.json" -Encoding UTF8
