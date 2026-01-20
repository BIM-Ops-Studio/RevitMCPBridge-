$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    # Get elements in the HIGH ROOF SECTION view (ID 1245552)
    $json = '{"method":"getElementsInView","params":{"viewId":1245552}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output $response
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
