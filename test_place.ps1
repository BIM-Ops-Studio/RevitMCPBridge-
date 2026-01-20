$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    # Place view 1245544 on sheet - use a sheet we know exists
    # Try placing at center of sheet (1 foot from origin)
    $json = '{"method":"placeViewOnSheet","params":{"viewId":1245544,"sheetId":1240478,"x":1.0,"y":0.75}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output $response
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
