$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Floor Plan 02 - TRACING ACTUAL WALL LINES (not room dimensions)
    #
    # Looking at the image, I'll trace the building outline and interior walls
    # The building has an L-shape with:
    # - Upper main rectangle (Living, Kitchen, Master)
    # - Lower left bump (Bedrooms, Office)
    # - Lower right section (Garage)
    # - Porch notch in middle-bottom

    # ANALYZING THE IMAGE MORE CAREFULLY:
    #
    # MAIN BUILDING MEASUREMENTS FROM ROOM SIZES:
    # Living Room (22'11" x 18') is in top-left
    # Kitchen (13'4" x 17') is top-center
    # Master (14'10" x 17'6") is top-right
    # Total top width: ~51'
    #
    # LOWER SECTION:
    # Garage (21'5" x 20'9") is bottom-right - starts below master/bath/closet area
    # Lower bedrooms/office area - left side
    #
    # Key observation: The building is NOT a simple rectangle!
    # - The garage extends to the bottom-right
    # - The left wing has bedrooms that extend down
    # - There's a porch indentation in the middle
    # - The hallway runs through the center
    #
    # Let me trace from the IMAGE, estimating coordinates based on proportions:
    # I'll set: Bottom of building = Y=0, Left edge = X=0
    #
    # From the image, the rough proportions are:
    # - Total width: ~70' (Living + Kitchen + Master/Garage width)
    # - Living room section height: ~35' from bottom of building to top
    # - Garage section: bottom 21' of the right side
    #
    # Let me estimate more precisely from room sizes:
    # If Garage = 21.42' x 20.75', and it's at bottom-right
    # If Master = 14.83' x 17.5' and it's above garage area
    # Then right column is about 21.42' wide
    #
    # Middle column: Kitchen = 13.33', Hall = 9.25', Laundry = 6.67'
    # This suggests middle section is ~13-15' wide
    #
    # Left column: Living = 22.92' wide
    #
    # So total width: 22.92 + 13.33 + 21.42 = ~58'
    #
    # Heights:
    # From bottom-left corner going up:
    # - Bedroom2 = 13.67' tall (at very bottom-left)
    # - Bedroom1 = 11.58' tall (above that? or same row?)
    # - Living Room = 18' tall (at top)
    #
    # Looking at image - Bedroom2 (11'4" x 13'8") is bottom-left
    # Above it is Bedroom1 (13'1" x 11'7") and Bath (7'3" x 8'5")
    # Above that is Living Room
    #
    # So left side total height: 13.67 (Bedroom2) + ??? + 18 (Living)
    # But Bedroom1 seems to be on the same row as Office, not stacked above Bedroom2
    #
    # Looking again - the layout seems to be:
    # TOP ROW: Living | Kitchen | Master Bedroom
    # MIDDLE ROW: Bedroom1, Bath, Hall | Hallway, Hall, Pantry | Closet, Bath, Room
    # BOTTOM ROW: Bedroom2 | Office, Porch | Laundry | Garage
    #
    # So it's 3-4 rows depending on section

    # I'll use simpler approach - set up a grid based on major dimensions
    # and trace walls accordingly

    # COORDINATE SYSTEM:
    # X: 0 = left edge, positive = right
    # Y: 0 = bottom edge of left wing (bedroom2 bottom), positive = up
    #
    # Major X grid lines:
    # X=0: Left edge
    # X=11.33: Right edge of Bedroom2, left edge of Office
    # X=22: Approx right edge of Living area / left of Hallway
    # X=27.58: Right edge of Hallway (5.58' wide)
    # X=36: Approx Kitchen/Master boundary
    # X=57.42: Right edge (21.42' garage + some wall/offset)
    #
    # Major Y grid lines:
    # Y=0: Bottom of Bedroom2
    # Y=13.67: Top of Bedroom2 / bottom of Bedroom1 row
    # Y=13.67+4.83: Top of Hall below Bedroom1 = 18.5
    # Y=13.67+4.83+11.58: Top of Bedroom1 = 30.08
    # Y=30.08+5 (corridor): Living room starts
    #
    # Actually let me just trace what I SEE in the image

    # VISUAL TRACE OF EXTERIOR WALLS:
    # I see the building has this shape (ASCII approximation):
    #
    #  +----------------------------------+
    #  |Living    |Kitchen    |Master    |
    #  |          |           |          |
    #  +--+-------+   +-------+--+-------+
    #  |BR1|Bath|Hall|   |Clo|Bath|Room  |
    #  |   |    |    |Hall|   |    |     |
    #  +---+----+----+   +---+----+------+
    #  |BR2|    |Office  |Laundry|Garage |
    #  |   |    |  Porch |       |       |
    #  +---+----+--[]----+-------+-------+
    #
    # The Porch is a small inset notch
    # The Garage is large bottom-right box

    # Let me build coordinates based on this layout:
    # Total width estimate: 58' (from room widths)
    # Total height estimate: 36' (max)
    #
    # For the first attempt, I'll use these key points:

    # Setting coordinate values:
    $x_left = 0
    $x_br1_right = 13.08      # Bedroom1 width
    $x_bath1_right = 20.33    # + Bath width 7.25
    $x_living_right = 22.92   # Living room width
    $x_hallway_right = 28.5   # + Hallway width 5.58
    $x_kitchen_right = 36.25  # Kitchen extends ~13.33
    $x_closet_right = 41.5    # + Closet 5.25
    $x_bath2_right = 50.42    # + Bath 8.92
    $x_right = 58.0           # Right edge (adjusted)

    $y_bottom = 0
    $y_porch_top = 4          # Porch is 4' tall
    $y_garage_step = 6.83     # Laundry height
    $y_br2_top = 13.67        # Bedroom2 height
    $y_hall1_top = 18.5       # Hall below bedrooms
    $y_lower_rooms = 24       # Bottom of upper rooms
    $y_living_bottom = 17.67  # 35.67 - 18
    $y_top = 35.67            # Building top

    # EXTERIOR WALLS - tracing the perimeter
    # Format: start(x,y) to end(x,y)

    $request = '{"method":"createWallBatch","params":{"walls":[' `
        + '{"startPoint":[0,35.67,0],"endPoint":[58,35.67,0]},' `        # Top wall full width
        + '{"startPoint":[58,35.67,0],"endPoint":[58,0,0]},' `          # Right wall full height
        + '{"startPoint":[58,0,0],"endPoint":[36.5,0,0]},' `            # Garage bottom (partial)
        + '{"startPoint":[36.5,0,0],"endPoint":[36.5,6.83,0]},' `       # Garage/Laundry step up
        + '{"startPoint":[36.5,6.83,0],"endPoint":[29.66,6.83,0]},' `   # Laundry bottom
        + '{"startPoint":[29.66,6.83,0],"endPoint":[29.66,13.67,0]},' ` # Laundry/hall step up
        + '{"startPoint":[29.66,13.67,0],"endPoint":[25.83,13.67,0]},' ` # Step to porch
        + '{"startPoint":[25.83,13.67,0],"endPoint":[25.83,9.67,0]},' ` # Porch right down
        + '{"startPoint":[25.83,9.67,0],"endPoint":[22,9.67,0]},' `     # Porch bottom
        + '{"startPoint":[22,9.67,0],"endPoint":[22,13.67,0]},' `       # Porch left up
        + '{"startPoint":[22,13.67,0],"endPoint":[11.33,13.67,0]},' `   # Office top
        + '{"startPoint":[11.33,13.67,0],"endPoint":[11.33,0,0]},' `    # BR2 right
        + '{"startPoint":[11.33,0,0],"endPoint":[0,0,0]},' `            # BR2 bottom
        + '{"startPoint":[0,0,0],"endPoint":[0,35.67,0]}' `             # Left wall
        + '],"levelId":30,"height":10.0,"wallTypeId":441451}}'

    Write-Output "Creating exterior walls..."
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output "Exterior: $response"

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
