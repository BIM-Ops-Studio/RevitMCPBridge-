$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    # Import a detail
    $json = '{"method":"importDetailToDocument","params":{"detailPath":"D:\\Revit Detail Libraries\\Revit Details\\01 - Roof Details\\ROOF ANCHOR DETAIL.rvt"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output $response
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
