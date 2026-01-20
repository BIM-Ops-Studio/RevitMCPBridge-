$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Interior walls batch 1 - 10 walls
    $request = '{"method":"createWallBatch","params":{"walls":[{"startPoint":[0,17.67,0],"endPoint":[22.92,17.67,0]},{"startPoint":[28.5,17.67,0],"endPoint":[36.5,17.67,0]},{"startPoint":[36.5,18.17,0],"endPoint":[58,18.17,0]},{"startPoint":[0,29.42,0],"endPoint":[20.33,29.42,0]},{"startPoint":[0,24.59,0],"endPoint":[20.33,24.59,0]},{"startPoint":[28.5,24.59,0],"endPoint":[36.5,24.59,0]},{"startPoint":[29.66,13.5,0],"endPoint":[36.5,13.5,0]},{"startPoint":[22.92,17.67,0],"endPoint":[22.92,35.67,0]},{"startPoint":[36.5,17.67,0],"endPoint":[36.5,35.67,0]},{"startPoint":[13.08,24.59,0],"endPoint":[13.08,29.42,0]}],"levelId":30,"height":10.0,"wallTypeId":441454}}'

    Write-Output "Creating interior walls batch 1..."
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output "Batch 1: $response"

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
