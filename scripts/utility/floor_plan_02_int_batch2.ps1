$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Interior walls batch 2 - remaining walls
    $request = '{"method":"createWallBatch","params":{"walls":[{"startPoint":[20.33,17.67,0],"endPoint":[20.33,29.42,0]},{"startPoint":[22.92,9.67,0],"endPoint":[22.92,17.67,0]},{"startPoint":[28.5,13.5,0],"endPoint":[28.5,24.59,0]},{"startPoint":[32.33,17.67,0],"endPoint":[32.33,24.59,0]},{"startPoint":[36.5,20.34,0],"endPoint":[36.5,24.59,0]},{"startPoint":[41.75,18.17,0],"endPoint":[41.75,29.42,0]},{"startPoint":[50.67,18.17,0],"endPoint":[50.67,29.42,0]},{"startPoint":[36.5,29.42,0],"endPoint":[50.67,29.42,0]},{"startPoint":[0,18.5,0],"endPoint":[13.08,18.5,0]},{"startPoint":[29.66,6.83,0],"endPoint":[29.66,13.5,0]},{"startPoint":[36.5,0,0],"endPoint":[36.5,18.17,0]}],"levelId":30,"height":10.0,"wallTypeId":441454}}'

    Write-Output "Creating interior walls batch 2..."
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output "Batch 2: $response"

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
