$test = @{
    method = 'createWall'
    params = @{
        startPoint = @(0, 0, 0)
        endPoint = @(10, 0, 0)
        levelId = 30
        height = 10.0
    }
}

$json = $test | ConvertTo-Json -Compress -Depth 5
Write-Host "JSON: $json"
