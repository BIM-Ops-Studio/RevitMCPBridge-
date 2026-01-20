param(
    [string]$ViewId = ""
)

$pipeName = "RevitMCPBridge2026"
$request = '{"method":"openView","params":{"viewId":' + $ViewId + '}}'

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(15000)

    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)

    $writer.WriteLine($request)
    $writer.Flush()

    $response = $reader.ReadLine()
    Write-Output $response

    $pipe.Close()
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
}
