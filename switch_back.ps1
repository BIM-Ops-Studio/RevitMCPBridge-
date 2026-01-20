$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    # Close 512 Clematis without saving
    $json = '{"method":"closeProject","params":{"documentName":"512_CLEMATIS-2","save":false}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "Close result: $response"
    
    # Set TEST-500 as active
    $json = '{"method":"setActiveDocument","params":{"documentName":"TEST-500"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "Switch result: $response"
    
    # Verify title blocks now available
    $json = '{"method":"getTitleblockTypes","params":{}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "Title blocks in TEST-500: $response"
    
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
