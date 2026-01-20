$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Floor Plan 02 - Tracing wall segments from room dimensions
    # Coordinate system: Origin (0,0) at bottom-left of building
    # X increases to the right, Y increases upward

    # Room dimensions converted to decimal feet:
    # Living Room: 22.92' x 18'
    # Kitchen: 13.33' x 17'
    # Master Bedroom: 14.83' x 17.5'
    # Garage: 21.42' x 20.75'
    # Bedroom1 (top-left): 13.08' x 11.58'
    # Bedroom2 (bottom-left): 11.33' x 13.67'
    # Bath1: 7.25' x 8.42'
    # Bath2: 8.92' x 11.25'
    # Office: 10.33' x 9.83'
    # Hallway: 5.58' x 19.75'
    # Hall1: 12.08' x 4.83'
    # Hall2: 9.25' x 4.25'
    # Pantry: 4.17' x 4.33'
    # Laundry: 6.67' x 6.83'
    # Closet: 5.25' x 11.25'
    # Room: 3.17' x 5.08'
    # Porch: 3.83' x 4'

    # Building layout analysis:
    # - Left wing has L-shape (Living on top, Bedrooms/Office below)
    # - Right wing has Garage below, Master suite above
    # - Central hallway connects the wings

    # Key coordinates based on room sizes:
    # Total top width: ~51' (Living + Kitchen + Master)
    # Left wing bottom: Bedroom2 + Office + Porch area
    # Garage area: bottom-right

    # Let me trace the EXTERIOR walls first (8" thick)
    # Starting from room dimensions and visible wall positions

    # Y coordinates (from bottom to top):
    # Y=0: Bottom of garage, bottom of left wing bump-out
    # Y=20.75: Top of garage
    # Y=~13.67: Top of lower bedroom area (bottom bedroom is 13.67' tall)
    # Y=~32: Top of building (Living room is 18' tall above the lower area)

    # X coordinates (from left to right):
    # X=0: Left edge
    # X=11.33: Right of bottom bedroom
    # X=~22.92: Right of living room
    # X=~36: Right of kitchen area
    # X=~51: Right edge (Master bedroom)

    # Calculated building extents:
    # The left wing extends down with bedroom/office
    # The bump-out at bottom-left contains: Bedroom2 (11.33'), Office (10.33'), Porch (3.83')

    # Main building rectangle appears to be:
    # Width: Living(22.92) + Kitchen(13.33) + Master(14.83) = 51.08'
    # But Kitchen + Master share some space with Garage below

    # Let me use the garage as anchor:
    # Garage is 21.42' x 20.75'
    # Master above garage is 14.83' x 17.5'
    # So right portion is about 21.42' wide

    # Left portion (Living room area): 22.92' wide
    # That leaves Kitchen connecting them: 51.08 - 22.92 - 14.83 = 13.33' (matches Kitchen width)

    # Building height calculation:
    # Looking at left side: Living room is 18' tall
    # Below living room: Bedroom1 area + Hall area
    # Bedroom1 is 11.58' tall, so total left height = 18 + lower section

    # Let's set the coordinate system with:
    # Y=0 at bottom of building (lowest point - garage/bedroom2 bottom)
    # The left wing bump-out is lower than the main rectangle

    # I'll trace each visible wall segment individually

    # EXTERIOR WALLS (Generic - 8")
    $exteriorWalls = @(
        # TOP EDGE - going left to right
        @{start=@(0,35.67); end=@(22.92,35.67)},      # Living room top
        @{start=@(22.92,35.67); end=@(36.25,35.67)},  # Kitchen top
        @{start=@(36.25,35.67); end=@(51.08,35.67)},  # Master bedroom top

        # RIGHT EDGE - top to bottom
        @{start=@(51.08,35.67); end=@(51.08,18.17)},  # Master right (17.5')
        @{start=@(51.08,18.17); end=@(51.08,0)},      # Garage right (18.17')

        # BOTTOM - right to left
        @{start=@(51.08,0); end=@(29.66,0)},          # Garage bottom (21.42')
        @{start=@(29.66,0); end=@(29.66,13.67)},      # Garage/house transition up
        @{start=@(29.66,13.67); end=@(25.83,13.67)},  # Step in (porch area)
        @{start=@(25.83,13.67); end=@(25.83,9.67)},   # Porch right side down
        @{start=@(25.83,9.67); end=@(22,9.67)},       # Porch bottom
        @{start=@(22,9.67); end=@(22,13.67)},         # Porch left side up
        @{start=@(22,13.67); end=@(11.33,13.67)},     # Office bottom/top of lower bedroom
        @{start=@(11.33,13.67); end=@(11.33,0)},      # Lower bedroom right (13.67')
        @{start=@(11.33,0); end=@(0,0)},              # Lower bedroom bottom (11.33')

        # LEFT EDGE - bottom to top
        @{start=@(0,0); end=@(0,35.67)}               # Full left side
    )

    # Convert to JSON format for createWallBatch
    $wallsJson = @()
    foreach ($wall in $exteriorWalls) {
        $wallsJson += @{
            startPoint = @($wall.start[0], $wall.start[1], 0)
            endPoint = @($wall.end[0], $wall.end[1], 0)
        }
    }

    $jsonWalls = $wallsJson | ConvertTo-Json -Compress
    $request = '{"method":"createWallBatch","params":{"walls":' + $jsonWalls + ',"levelId":30,"height":10.0,"wallTypeId":441451}}'

    Write-Output "Creating exterior walls..."
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output "Exterior: $response"

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
