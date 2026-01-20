# Text Standardization Test - Current Document
$pipeName = "RevitMCPBridge2026"

function Send-MCP {
    param([string]$Method, [hashtable]$Params = @{})

    $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Depth 10

    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(10000)

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($pipe, $utf8)
    $writer.AutoFlush = $true
    $reader = New-Object System.IO.StreamReader($pipe, $utf8)

    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    return $response | ConvertFrom-Json
}

Write-Host "=== Text Standardization Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get text types
Write-Host "Step 1: Getting text types..." -ForegroundColor Yellow
$result = Send-MCP -Method "getTextTypes"

if ($result.success) {
    Write-Host "  Found $($result.count) text types:" -ForegroundColor Green
    foreach ($tt in $result.textTypes) {
        Write-Host "    - $($tt.name): $($tt.font), $($tt.sizeInches)`"" -ForegroundColor White
    }
} else {
    Write-Host "  Error: $($result.error)" -ForegroundColor Red
    exit
}

Write-Host ""

# Step 2: Get text notes
Write-Host "Step 2: Getting text notes..." -ForegroundColor Yellow
$result = Send-MCP -Method "getTextNotes"

if ($result.success) {
    Write-Host "  Found $($result.count) text notes" -ForegroundColor Green
    if ($result.count -gt 0) {
        $sample = $result.textNotes | Select-Object -First 3
        foreach ($tn in $sample) {
            $preview = if ($tn.text.Length -gt 50) { $tn.text.Substring(0,50) + "..." } else { $tn.text }
            Write-Host "    [$($tn.typeName)] $preview" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  Error: $($result.error)" -ForegroundColor Red
}

Write-Host ""

# Step 3: Standardize
Write-Host "Step 3: Standardizing text..." -ForegroundColor Yellow
Write-Host "  Target: 3/32`" ARIAL NOTES, UPPERCASE" -ForegroundColor White

$params = @{
    typeName = '3/32" ARIAL NOTES'
    fontName = "Arial"
    sizeInches = 0.09375
    bold = $false
    toUppercase = $true
}

$result = Send-MCP -Method "standardizeDocumentText" -Params $params

if ($result.success) {
    Write-Host ""
    Write-Host "  SUCCESS!" -ForegroundColor Green
    Write-Host "  Total text notes: $($result.totalTextNotes)" -ForegroundColor White
    Write-Host "  Types changed: $($result.typeChanges)" -ForegroundColor White
    Write-Host "  Uppercase conversions: $($result.uppercaseChanges)" -ForegroundColor White
    Write-Host ""
    Write-Host "Changes are in memory. Save the document to keep them." -ForegroundColor Yellow
} else {
    Write-Host "  FAILED: $($result.error)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
