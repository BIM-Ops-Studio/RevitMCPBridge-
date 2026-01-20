$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(15000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Create 16 interior walls using Generic - 5" (ID: 441454)
    # These are the corrected coordinates from the user's manual fix
    $request = '{"method":"createWallBatch","params":{"walls":[{"startPoint":[0,24.58,0],"endPoint":[22.70,24.58,0]},{"startPoint":[33.25,28.59,0],"endPoint":[48.33,28.59,0]},{"startPoint":[0,9.75,0],"endPoint":[21.83,9.75,0]},{"startPoint":[7.17,24.58,0],"endPoint":[7.17,35.67,0]},{"startPoint":[14.83,24.58,0],"endPoint":[14.83,35.67,0]},{"startPoint":[42.67,28.59,0],"endPoint":[42.67,35.67,0]},{"startPoint":[10.33,9.75,0],"endPoint":[10.33,24.58,0]},{"startPoint":[22.70,24.58,0],"endPoint":[22.70,28.71,0]},{"startPoint":[33.25,18.92,0],"endPoint":[33.25,28.71,0]},{"startPoint":[40.33,18.92,0],"endPoint":[40.33,28.59,0]},{"startPoint":[29.33,9.75,0],"endPoint":[48.33,9.75,0]},{"startPoint":[15.08,9.75,0],"endPoint":[15.08,0,0]},{"startPoint":[31.25,9.75,0],"endPoint":[31.25,0,0]},{"startPoint":[33.25,20.92,0],"endPoint":[40.33,20.92,0]},{"startPoint":[10.33,19.71,0],"endPoint":[22.83,19.71,0]},{"startPoint":[19.83,9.75,0],"endPoint":[19.83,19.71,0]}],"levelId":30,"height":10.0,"wallTypeId":441454}}'
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output $response

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
