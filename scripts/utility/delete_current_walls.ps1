$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(15000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    $request = '{"method":"deleteElementsBatch","params":{"elementIds":[1245303,1245304,1245305,1245306,1245307,1245308,1245309,1245310,1245311,1245312,1245313,1245314,1245315,1245316,1245367,1245368,1245369,1245370,1245371,1245372,1245373,1245374,1245375,1245376,1245377]}}'
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output $response

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
