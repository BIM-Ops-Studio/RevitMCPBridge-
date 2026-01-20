# Check method registry count
$pipeName = "RevitMCPBridge2026"

$json = '{"method":"getMethodRegistry","params":{}}'

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(10000)

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($pipe, $utf8)
    $writer.AutoFlush = $true
    $reader = New-Object System.IO.StreamReader($pipe, $utf8)

    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $pipe.Close()

    $obj = $response | ConvertFrom-Json

    if ($obj.success) {
        Write-Host "Method Registry Count: $($obj.methodCount)" -ForegroundColor Green

        # Check if our methods are listed
        $methods = $obj.methods
        Write-Host ""
        Write-Host "Checking for BatchText methods:" -ForegroundColor Yellow

        $batchMethods = @("getTextTypes", "createStandardTextType", "getTextNotes",
                          "standardizeDocumentText", "processDetailFile",
                          "getDetailLibraryFiles", "getNextFileToProcess", "markFileProcessed")

        foreach ($m in $batchMethods) {
            if ($methods -contains $m) {
                Write-Host "  [OK] $m" -ForegroundColor Green
            } else {
                Write-Host "  [MISSING] $m" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "Error: $($obj.error)" -ForegroundColor Red
    }
}
catch {
    Write-Host "Connection failed: $_" -ForegroundColor Red
}
