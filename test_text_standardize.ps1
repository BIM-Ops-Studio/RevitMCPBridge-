# Test Text Standardization on Single File
# ==========================================
# Tests the text standardization on the currently open document in Revit
# before running the batch process on all files.

$pipeName = "RevitMCPBridge2026"

function Send-MCPRequest {
    param(
        [string]$Method,
        [hashtable]$Params = @{}
    )

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Depth 10

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)

        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)

        $writer.WriteLine($request)
        $writer.Flush()

        $response = $reader.ReadLine()

        $pipe.Close()

        return $response | ConvertFrom-Json
    }
    catch {
        Write-Host "ERROR: MCP request failed - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

Write-Host "=== Text Standardization Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get current text types
Write-Host "Step 1: Getting current text types..." -ForegroundColor Yellow
$result = Send-MCPRequest -Method "getTextTypes"

if ($result -and $result.success) {
    Write-Host "  Found $($result.count) text types:" -ForegroundColor Green
    foreach ($tt in $result.textTypes) {
        Write-Host "    - $($tt.name): $($tt.font), $($tt.sizeInches)"" $(if ($tt.bold) { '[BOLD]' })"
    }
}
else {
    Write-Host "  FAILED to get text types" -ForegroundColor Red
    if ($result) { Write-Host "  Error: $($result.error)" }
    exit
}

Write-Host ""

# Step 2: Get current text notes
Write-Host "Step 2: Getting current text notes..." -ForegroundColor Yellow
$result = Send-MCPRequest -Method "getTextNotes"

if ($result -and $result.success) {
    Write-Host "  Found $($result.count) text notes" -ForegroundColor Green

    # Show first 5 as sample
    $sample = $result.textNotes | Select-Object -First 5
    foreach ($tn in $sample) {
        $textPreview = if ($tn.text.Length -gt 40) { $tn.text.Substring(0, 40) + "..." } else { $tn.text }
        Write-Host "    - [$($tn.typeName)] $textPreview"
    }
    if ($result.count -gt 5) {
        Write-Host "    ... and $($result.count - 5) more"
    }
}
else {
    Write-Host "  FAILED to get text notes" -ForegroundColor Red
}

Write-Host ""

# Step 3: Ask to proceed
Write-Host "Step 3: Ready to standardize text in current document" -ForegroundColor Yellow
Write-Host "  Target type: 3/32"" ARIAL NOTES" -ForegroundColor White
Write-Host "  Font: Arial" -ForegroundColor White
Write-Host "  Size: 0.09375"" (3/32"")" -ForegroundColor White
Write-Host "  Convert to UPPERCASE: Yes" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Proceed with standardization? (y/n)"

if ($confirm -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit
}

# Step 4: Standardize
Write-Host ""
Write-Host "Step 4: Standardizing text..." -ForegroundColor Yellow

$params = @{
    typeName = '3/32" ARIAL NOTES'
    fontName = "Arial"
    sizeInches = 0.09375
    bold = $false
    toUppercase = $true
}

$result = Send-MCPRequest -Method "standardizeDocumentText" -Params $params

if ($result -and $result.success) {
    Write-Host "  SUCCESS!" -ForegroundColor Green
    Write-Host "  Total text notes: $($result.totalTextNotes)"
    Write-Host "  Types changed: $($result.typeChanges)"
    Write-Host "  Uppercase changes: $($result.uppercaseChanges)"
    Write-Host "  Target type: $($result.targetTypeName)"
}
else {
    Write-Host "  FAILED!" -ForegroundColor Red
    if ($result) { Write-Host "  Error: $($result.error)" }
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host "NOTE: Changes are in memory. Save the document to keep them."
