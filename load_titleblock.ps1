$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(60000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    # Transfer title block from 512 Clematis to TEST-500
    $json = '{"method":"transferFamilyBetweenDocuments","params":{"sourceDocumentName":"512_CLEMATIS-2","targetDocumentName":"TEST-500","familyName":"TITLEBLOCK_SOP_36x24_2018","familyCategory":"TitleBlocks"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output $response
    
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
