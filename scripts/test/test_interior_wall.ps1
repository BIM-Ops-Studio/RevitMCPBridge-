$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(15000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Test: Create a single interior wall in the middle of the building
    $request = '{"method":"createWallBatch","params":{"walls":[{"startPoint":[20,10,0],"endPoint":[20,30,0]}],"levelId":30,"height":10.0,"wallTypeId":441454}}'

    Write-Output "Creating test interior wall..."
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output "Response: $response"

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
