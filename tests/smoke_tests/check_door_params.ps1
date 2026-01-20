# Check parameters on a door element
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CHECKING DOOR PARAMETERS ===" -ForegroundColor Cyan

# Get parameters for door 248 (ID 1672936)
$json = '{"method":"getParameters","params":{"elementId":1672936}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Parameters for door 248 (ID 1672936):" -ForegroundColor Green

    # Look for TYPE-related parameters
    $typeParams = @()
    foreach ($param in $result.result.parameters) {
        if ($param.name -like "*type*" -or $param.name -like "*TYPE*" -or $param.name -eq "Door_Type") {
            $typeParams += $param
        }
    }

    Write-Host "`nTYPE-related parameters:"
    $typeParams | ForEach-Object {
        Write-Host "  Name: $($_.name), Value: $($_.value), ReadOnly: $($_.isReadOnly)"
    }

    Write-Host "`nAll parameter names containing interesting terms:"
    $result.result.parameters | Where-Object {
        $_.name -like "*Door*" -or
        $_.name -like "*MATL*" -or
        $_.name -like "*HDWR*" -or
        $_.name -like "*Hardware*" -or
        $_.name -like "*Material*"
    } | ForEach-Object {
        Write-Host "  $($_.name) = '$($_.value)' (ReadOnly: $($_.isReadOnly))"
    }

    Write-Host "`n--- Full parameter list (first 30) ---"
    $result.result.parameters | Select-Object -First 30 | ForEach-Object {
        Write-Host "  $($_.name) = '$($_.value)'"
    }
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

$pipe.Close()
