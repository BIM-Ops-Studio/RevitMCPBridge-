$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Floor Plan 02 - Interior walls
    # Using room dimensions to calculate wall positions
    #
    # Key X coordinates:
    # 0 = left edge
    # 11.33 = right of Bedroom2 (11'4" = 11.33')
    # 13.08 = right of Bedroom1 (13'1" = 13.08')
    # 20.33 = right of Bath1 (13.08 + 7.25)
    # 22.92 = right of Living (22'11")
    # 28.5 = right of Hallway (22.92 + 5.58)
    # 32.67 = right of Hall2/left of Pantry
    # 36.5 = Garage/house separation (approx)
    # 41.75 = right of Closet (36.5 + 5.25)
    # 50.67 = right of Bath2 (41.75 + 8.92)
    # 58 = right edge
    #
    # Key Y coordinates:
    # 0 = bottom
    # 4 = top of Porch (4')
    # 6.83 = top of Laundry/Garage step
    # 9.67 = bottom of Porch notch
    # 13.67 = top of Bedroom2/Office row
    # 17.67 = top of lower section (Living bottom at 35.67 - 18)
    # 18.5 = top of Hall below bedrooms
    # 24 = middle corridor line
    # 29.42 = top of Bedroom1 area (13.67 + 4.83 + 10.92)
    # 35.67 = top

    # Interior walls - tracing from image
    # Living/Kitchen/Master dividers
    $interiorWalls = @()

    # HORIZONTAL WALLS:
    # Wall below Living room (separating Living from Bedroom1/Bath/Hall row)
    $interiorWalls += '{"startPoint":[0,17.67,0],"endPoint":[22.92,17.67,0]}'

    # Wall below Kitchen (partial - Hallway extends into this)
    $interiorWalls += '{"startPoint":[28.5,17.67,0],"endPoint":[36.5,17.67,0]}'

    # Wall below Master (separating Master from Closet/Bath/Room)
    $interiorWalls += '{"startPoint":[36.5,18.17,0],"endPoint":[58,18.17,0]}'

    # Wall at top of Bedroom1/Bath (separating from Living bottom)
    $interiorWalls += '{"startPoint":[0,29.42,0],"endPoint":[20.33,29.42,0]}'

    # Hall top wall (below Bedroom1)
    $interiorWalls += '{"startPoint":[0,24.59,0],"endPoint":[20.33,24.59,0]}'

    # Wall between Hallway and Hall2
    $interiorWalls += '{"startPoint":[28.5,24.59,0],"endPoint":[36.5,24.59,0]}'

    # Wall top of Laundry
    $interiorWalls += '{"startPoint":[29.66,13.5,0],"endPoint":[36.5,13.5,0]}'

    # VERTICAL WALLS:
    # Living/Kitchen divider
    $interiorWalls += '{"startPoint":[22.92,17.67,0],"endPoint":[22.92,35.67,0]}'

    # Kitchen/Master divider
    $interiorWalls += '{"startPoint":[36.5,17.67,0],"endPoint":[36.5,35.67,0]}'

    # Bedroom1/Bath divider
    $interiorWalls += '{"startPoint":[13.08,24.59,0],"endPoint":[13.08,29.42,0]}'

    # Bath/Hall divider
    $interiorWalls += '{"startPoint":[20.33,17.67,0],"endPoint":[20.33,29.42,0]}'

    # Hallway left wall
    $interiorWalls += '{"startPoint":[22.92,9.67,0],"endPoint":[22.92,17.67,0]}'

    # Hallway right wall
    $interiorWalls += '{"startPoint":[28.5,13.5,0],"endPoint":[28.5,24.59,0]}'

    # Hall2/Pantry divider
    $interiorWalls += '{"startPoint":[32.33,17.67,0],"endPoint":[32.33,24.59,0]}'

    # Pantry right wall
    $interiorWalls += '{"startPoint":[36.5,20.34,0],"endPoint":[36.5,24.59,0]}'

    # Closet/Bath2 divider
    $interiorWalls += '{"startPoint":[41.75,18.17,0],"endPoint":[41.75,29.42,0]}'

    # Bath2/Room divider
    $interiorWalls += '{"startPoint":[50.67,18.17,0],"endPoint":[50.67,29.42,0]}'

    # Closet top
    $interiorWalls += '{"startPoint":[36.5,29.42,0],"endPoint":[50.67,29.42,0]}'

    # Office/Bedroom2 divider (vertical at x=11.33, already exterior)
    # Hall under bedroom1 bottom
    $interiorWalls += '{"startPoint":[0,18.5,0],"endPoint":[13.08,18.5,0]}'

    # Laundry left wall
    $interiorWalls += '{"startPoint":[29.66,6.83,0],"endPoint":[29.66,13.5,0]}'

    # Garage wall (separating Garage from house)
    $interiorWalls += '{"startPoint":[36.5,0,0],"endPoint":[36.5,18.17,0]}'

    $wallJson = '[' + ($interiorWalls -join ',') + ']'
    $request = '{"method":"createWallBatch","params":{"walls":' + $wallJson + ',"levelId":30,"height":10.0,"wallTypeId":441454}}'

    Write-Output "Creating interior walls..."
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output "Interior: $response"

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
