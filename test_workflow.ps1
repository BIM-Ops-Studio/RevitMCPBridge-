$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(15000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    # Import second detail
    Write-Output "=== Importing ROOF DRAIN DETAIL ==="
    $json = '{"method":"importDetailToDocument","params":{"detailPath":"D:\\Revit Detail Libraries\\Revit Details\\01 - Roof Details\\ROOF DRAIN DETAIL.rvt"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output $response
    
    # Parse viewId from response
    $data = $response | ConvertFrom-Json
    $viewId = $data.viewId
    
    # Place on sheet at different location
    Write-Output "`n=== Placing on sheet AD-001 ==="
    $json = '{"method":"placeViewOnSheet","params":{"viewId":' + $viewId + ',"sheetId":1240478,"x":2.5,"y":0.75}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output $response
    
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
