# Consolidate door types: E→D, H→G, and update overhead door to I
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CONSOLIDATING DOOR TYPES ===" -ForegroundColor Cyan
Write-Host "Changes:"
Write-Host "  TYPE E (bifold 3'-0) -> TYPE D (consolidate bifolds)"
Write-Host "  TYPE H (sliding 48) -> TYPE G (consolidate sliding)"
Write-Host "  Overhead door -> TYPE I"

# Get all doors
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

$updates = @{
    "E_to_D" = @()
    "H_to_G" = @()
    "Overhead" = @()
}

foreach ($door in $result.doors) {
    # Check for TYPE-E in type name -> change to D
    if ($door.typeName -match "TYPE-E") {
        $updates["E_to_D"] += @{
            id = $door.doorId
            mark = $door.mark
        }
    }
    # Check for TYPE-H in type name -> change to G
    elseif ($door.typeName -match "TYPE-H") {
        $updates["H_to_G"] += @{
            id = $door.doorId
            mark = $door.mark
        }
    }
    # Overhead door
    elseif ($door.familyName -like "*Overhead*") {
        $updates["Overhead"] += @{
            id = $door.doorId
            mark = $door.mark
        }
    }
}

Write-Host ""
Write-Host "Doors to update:" -ForegroundColor Yellow
Write-Host "  E -> D: $($updates['E_to_D'].Count) doors"
Write-Host "  H -> G: $($updates['H_to_G'].Count) doors"
Write-Host "  Overhead -> I: $($updates['Overhead'].Count) doors"

# Update TYPE E doors to TYPE D
Write-Host ""
Write-Host "=== Updating TYPE E -> TYPE D ===" -ForegroundColor Cyan
foreach ($door in $updates["E_to_D"]) {
    $updateJson = @{
        method = "setParameter"
        params = @{
            elementId = $door.id
            parameterName = "Dr Panel Type"
            value = "D"
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($updateJson)
    $response = $reader.ReadLine()
    $updateResult = $response | ConvertFrom-Json

    if ($updateResult.success) {
        Write-Host "  Door $($door.mark) (ID $($door.id)) -> TYPE D" -ForegroundColor Green
    } else {
        Write-Host "  Door $($door.mark) FAILED: $($updateResult.error)" -ForegroundColor Red
    }
}

# Update TYPE H doors to TYPE G
Write-Host ""
Write-Host "=== Updating TYPE H -> TYPE G ===" -ForegroundColor Cyan
foreach ($door in $updates["H_to_G"]) {
    $updateJson = @{
        method = "setParameter"
        params = @{
            elementId = $door.id
            parameterName = "Dr Panel Type"
            value = "G"
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($updateJson)
    $response = $reader.ReadLine()
    $updateResult = $response | ConvertFrom-Json

    if ($updateResult.success) {
        Write-Host "  Door $($door.mark) (ID $($door.id)) -> TYPE G" -ForegroundColor Green
    } else {
        Write-Host "  Door $($door.mark) FAILED: $($updateResult.error)" -ForegroundColor Red
    }
}

# Update Overhead door to TYPE I
Write-Host ""
Write-Host "=== Updating Overhead -> TYPE I ===" -ForegroundColor Cyan
foreach ($door in $updates["Overhead"]) {
    $updateJson = @{
        method = "setParameter"
        params = @{
            elementId = $door.id
            parameterName = "Dr Panel Type"
            value = "I"
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($updateJson)
    $response = $reader.ReadLine()
    $updateResult = $response | ConvertFrom-Json

    if ($updateResult.success) {
        Write-Host "  Overhead Door $($door.mark) (ID $($door.id)) -> TYPE I" -ForegroundColor Green
    } else {
        Write-Host "  Overhead Door $($door.mark) FAILED: $($updateResult.error)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== COMPLETE ===" -ForegroundColor Green

$pipe.Close()
