$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    # Place the view on sheet AD-001 (ID 1240478)
    $json = '{"method":"placeViewOnSheet","params":{"viewId":1245656,"sheetId":1240478,"x":1.0,"y":1.0}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "Place view result:"
    Write-Output $response
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
