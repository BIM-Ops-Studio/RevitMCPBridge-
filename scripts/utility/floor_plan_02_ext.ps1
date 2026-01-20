$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Floor Plan 02 - Exterior walls
    # Tracing the perimeter clockwise from top-left
    # Based on room dimensions and visual analysis

    $request = '{"method":"createWallBatch","params":{"walls":[{"startPoint":[0,35.67,0],"endPoint":[58,35.67,0]},{"startPoint":[58,35.67,0],"endPoint":[58,0,0]},{"startPoint":[58,0,0],"endPoint":[36.5,0,0]},{"startPoint":[36.5,0,0],"endPoint":[36.5,6.83,0]},{"startPoint":[36.5,6.83,0],"endPoint":[29.66,6.83,0]},{"startPoint":[29.66,6.83,0],"endPoint":[29.66,13.67,0]},{"startPoint":[29.66,13.67,0],"endPoint":[25.83,13.67,0]},{"startPoint":[25.83,13.67,0],"endPoint":[25.83,9.67,0]},{"startPoint":[25.83,9.67,0],"endPoint":[22,9.67,0]},{"startPoint":[22,9.67,0],"endPoint":[22,13.67,0]},{"startPoint":[22,13.67,0],"endPoint":[11.33,13.67,0]},{"startPoint":[11.33,13.67,0],"endPoint":[11.33,0,0]},{"startPoint":[11.33,0,0],"endPoint":[0,0,0]},{"startPoint":[0,0,0],"endPoint":[0,35.67,0]}],"levelId":30,"height":10.0,"wallTypeId":441451}}'

    Write-Output "Creating exterior walls..."
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output "Exterior: $response"

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
