# Set all door types based on family type names
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== SETTING ALL DOOR TYPES ===" -ForegroundColor Cyan
Write-Host "Type Legend:"
Write-Host "  TYPE A = Entry/Passage doors"
Write-Host "  TYPE B = Interior pocket (34 inch)"
Write-Host "  TYPE C = Bifold 4-panel"
Write-Host "  TYPE D = Bifold 2-panel (consolidated D+E)"
Write-Host "  TYPE F = Interior swing (30 inch)"
Write-Host "  TYPE G = Double sliding (consolidated G+H)"
Write-Host "  TYPE I = Overhead rolling"
Write-Host "  TYPE J = Exterior two-lite"
Write-Host "  TYPE K = Passage double"

# Get all doors
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

$successCount = 0
$failCount = 0
$typeCounts = @{}

foreach ($door in $result.doors) {
    $doorId = $door.doorId
    $mark = $door.mark
    $typeName = $door.typeName
    $familyName = $door.familyName
    $assignedType = ""

    # Determine type from family/type name
    if ($typeName -match "TYPE-([A-H])") {
        $embeddedType = $matches[1]
        # Consolidate E -> D, H -> G
        switch ($embeddedType) {
            "E" { $assignedType = "D" }
            "H" { $assignedType = "G" }
            default { $assignedType = $embeddedType }
        }
    }
    elseif ($familyName -like "*Overhead*") {
        $assignedType = "I"
    }
    elseif ($familyName -like "*Exterior*Two_Lite*") {
        $assignedType = "J"
    }
    elseif ($familyName -eq "Door-Passage-Double-Flush") {
        $assignedType = "K"
    }
    elseif ($familyName -like "*Opening*") {
        # Door openings - skip or assign based on context
        # These are cased openings, might not need type
        continue
    }
    elseif ($familyName -like "*Passage-Single-Flush" -and $typeName -notmatch "TYPE") {
        $assignedType = "A"
    }
    elseif ($familyName -like "*Bifold_4-Panel*" -and $typeName -notmatch "TYPE") {
        $assignedType = "C"
    }
    else {
        # Skip doors without clear type assignment
        continue
    }

    if ($assignedType -ne "") {
        # Update Dr Panel Type
        $updateJson = @{
            method = "setParameter"
            params = @{
                elementId = $doorId
                parameterName = "Dr Panel Type"
                value = $assignedType
            }
        } | ConvertTo-Json -Compress

        $writer.WriteLine($updateJson)
        $response = $reader.ReadLine()
        $updateResult = $response | ConvertFrom-Json

        if ($updateResult.success) {
            $successCount++
            if (-not $typeCounts.ContainsKey($assignedType)) {
                $typeCounts[$assignedType] = 0
            }
            $typeCounts[$assignedType]++
            Write-Host "  Door $mark -> TYPE $assignedType" -ForegroundColor Green
        } else {
            $failCount++
            Write-Host "  Door $mark FAILED: $($updateResult.error)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Successfully updated: $successCount doors"
Write-Host "Failed: $failCount doors"
Write-Host ""
Write-Host "Type counts:"
foreach ($type in ($typeCounts.Keys | Sort-Object)) {
    Write-Host "  TYPE $type : $($typeCounts[$type]) doors"
}

$pipe.Close()
