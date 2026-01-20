param([int]$SheetId)

$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$request = "{`"method`":`"setActiveView`",`"params`":{`"viewId`":$SheetId}}"
$writer.WriteLine($request)
$response = $reader.ReadLine()
$pipe.Close()

Write-Host $response
