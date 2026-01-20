$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(15000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Delete all 24 walls from Floor Plan 01
    $request = '{"method":"deleteElementsBatch","params":{"elementIds":[1245279,1245280,1245281,1245282,1245283,1245284,1245285,1245286,1245287,1245288,1245289,1245290,1245291,1245292,1245293,1245294,1245295,1245296,1245297,1245298,1245299,1245300,1245301,1245302]}}'
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output $response

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
