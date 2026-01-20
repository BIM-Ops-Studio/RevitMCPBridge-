$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipeClient.Connect(3000)
    
    $reader = New-Object System.IO.StreamReader($pipeClient)
    $writer = New-Object System.IO.StreamWriter($pipeClient)
    $writer.AutoFlush = $true

    $request = '{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}'
    $writer.WriteLine($request)
    Start-Sleep -Milliseconds 500
    $response = $reader.ReadLine()
    Write-Host "Response: $response"
    $pipeClient.Close()
}
catch {
    Write-Host "Error: $_"
}
