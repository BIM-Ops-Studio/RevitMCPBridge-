# Create revision clouds for all changes
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$revisionId = 75715  # Existing Revision 1

# Function to create revision cloud using raw JSON
function Create-Cloud {
    param($viewId, $viewName, $x, $y, $width, $height)

    $x2 = $x + $width
    $y2 = $y + $height

    $json = "{`"method`":`"createRevisionCloud`",`"params`":{`"viewId`":$viewId,`"revisionId`":$revisionId,`"boundaryPoints`":[[$x,$y,0],[$x2,$y,0],[$x2,$y2,0],[$x,$y2,0]]}}"

    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json

    if ($result.success) {
        Write-Host "Cloud created in $viewName" -ForegroundColor Green
        return $result.result.cloudId
    } else {
        Write-Host "Failed in $viewName : $($result.error)" -ForegroundColor Red
        return $null
    }
}

Write-Host "=== CREATING REVISION CLOUDS ===" -ForegroundColor Cyan
Write-Host "Using Revision ID: $revisionId" -ForegroundColor Yellow

# Site Plan (viewId 29237)
Create-Cloud -viewId 29237 -viewName "Site Plan" -x -35 -y 5 -width 70 -height 45

# First Floor Plan (viewId 32)
Create-Cloud -viewId 32 -viewName "First Floor" -x -15 -y 55 -width 20 -height 10

# 2nd-3rd Floor (viewId 9948)
Create-Cloud -viewId 9948 -viewName "2nd-3rd Floor" -x -15 -y 55 -width 25 -height 12

# 4th Floor (viewId 1801007)
Create-Cloud -viewId 1801007 -viewName "4th Floor" -x -15 -y 55 -width 20 -height 10

# Roof Plan (viewId 1200905)
Create-Cloud -viewId 1200905 -viewName "Roof Plan" -x -25 -y 25 -width 55 -height 35

# Life Safety 1st (viewId 1551343)
Create-Cloud -viewId 1551343 -viewName "Life Safety 1st" -x -30 -y 45 -width 30 -height 30

# Life Safety 2nd-3rd (viewId 1551353)
Create-Cloud -viewId 1551353 -viewName "Life Safety 2nd-3rd" -x -30 -y 25 -width 65 -height 50

$pipe.Close()

Write-Host "`n=== REVISION CLOUDS COMPLETE ===" -ForegroundColor Green
