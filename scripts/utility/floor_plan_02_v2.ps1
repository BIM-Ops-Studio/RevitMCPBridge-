$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true

    # Floor Plan 02 - Version 2 - More careful analysis
    #
    # ROOM DIMENSIONS (converted to decimal feet):
    # Living Room: 22'11" x 18'0" = 22.92 x 18
    # Kitchen: 13'4" x 17'0" = 13.33 x 17
    # Master Bedroom: 14'10" x 17'6" = 14.83 x 17.5
    # Bedroom (upper-mid-left): 13'1" x 11'7" = 13.08 x 11.58
    # Bedroom (lower-left bump): 11'4" x 13'8" = 11.33 x 13.67
    # Bath (upper): 7'3" x 8'5" = 7.25 x 8.42
    # Bath (right): 8'11" x 11'3" = 8.92 x 11.25
    # Office: 10'4" x 9'10" = 10.33 x 9.83
    # Hallway: 5'7" x 19'9" = 5.58 x 19.75
    # Hall (upper): 12'1" x 4'10" = 12.08 x 4.83
    # Hall (right): 9'3" x 4'3" = 9.25 x 4.25
    # Pantry: 4'2" x 4'4" = 4.17 x 4.33
    # Laundry Room: 6'8" x 6'10" = 6.67 x 6.83
    # Closet: 5'3" x 11'3" = 5.25 x 11.25
    # Room: 3'2" x 5'1" = 3.17 x 5.08
    # Porch: 3'10" x 4'0" = 3.83 x 4
    # Garage: 21'5" x 20'9" = 21.42 x 20.75

    # LAYOUT ANALYSIS:
    # Top row (from left): Living (22.92) | Kitchen (13.33) | Master (14.83)
    # Total top width: 51.08'
    #
    # The garage is on the bottom-right: 21.42' x 20.75'
    # But looking at the image, the garage shares the right edge
    # Master is 14.83' wide, Garage is 21.42' wide
    # The difference (21.42 - 14.83 = 6.59') is the Hall/Bath/Closet area width
    #
    # Actually looking more carefully:
    # The right side has Master (top) then below that: Hall, Closet, Bath, Room
    # Then Garage at the very bottom
    #
    # The building's exterior perimeter:
    # - Runs full width at top
    # - Right side has step-in where Garage meets Master area
    # - Left side has bump-out for lower Bedroom
    # - Bottom has Porch indentation

    # Let me set coordinates:
    # Total width = max(Living+Kitchen+Master, Garage_right_edge)
    # Living(22.92) + Kitchen(13.33) + Master(14.83) = 51.08
    #
    # Looking at the drawing proportions:
    # The garage appears to be roughly same right edge as Master
    # Hall (9.25) + Closet (5.25) + Bath (8.92) + Room (3.17) ≈ 26.59' (but this seems too wide)
    # Let me use: Master + some = Garage width
    # Master = 14.83, Closet = 5.25, so maybe right column = 20.08'?
    # That's close to Garage's 21.42'

    # Simplified approach - use room dimensions to place walls:
    #
    # X coordinates:
    $x0 = 0          # Left edge
    $x1 = 11.33      # Right of lower Bedroom (bump-out ends)
    $x2 = 22.92      # Right of Living room / Left of Kitchen
    $x3 = 36.25      # Right of Kitchen / Left of Master (22.92 + 13.33)
    $x4 = 51.08      # Right edge (22.92 + 13.33 + 14.83)

    # The garage is at bottom-right
    # Garage width = 21.42, so Garage left = 51.08 - 21.42 = 29.66
    $xGarageLeft = 29.66

    # Y coordinates:
    $y0 = 0          # Bottom of building (Garage bottom, lower Bedroom bottom)
    $y1 = 13.67      # Top of lower Bedroom (13'8")
    $y2 = 20.75      # Top of Garage (20'9")
    $y3 = 35.5       # Top of building (rough estimate from Living 18' + lower section ~17.5')

    # Actually, let me recalculate Y more carefully:
    # From the image, the top floor (Living/Kitchen/Master) appears to be about half the total height
    # Living is 18' tall, Master is 17.5' tall
    # Below that are the middle rooms
    # Below that is Garage (20.75' tall) and lower Bedroom (13.67' tall)
    #
    # Looking at it differently:
    # The building appears to have the Garage and lower Bedroom at the SAME bottom level
    # The middle section (Bedroom/Bath/Hall/Office/Hallway) is above that
    # The top section (Living/Kitchen/Master) is at the very top
    #
    # But the middle and top sections may overlap vertically

    # Let me trace the EXTERIOR perimeter as I see it:
    # (This forms a complex polygon)
    #
    # Tracing clockwise from top-left corner (0, Y_top):
    # 1. Top-left corner
    # 2. Go right along top to top-right corner
    # 3. Go down the right side (Master, then step in at garage level?)
    # 4. Continue down garage right side
    # 5. Go left along garage bottom
    # 6. Step up at laundry/porch area
    # 7. Go left past porch
    # 8. Go up porch left side (or skip if porch is exterior)
    # 9. Continue left to lower bedroom
    # 10. Go down lower bedroom right side
    # 11. Go left along lower bedroom bottom
    # 12. Go up the full left side back to top

    # Looking at the image again - the exterior perimeter is:
    # A large rectangle MINUS the porch indentation, PLUS the lower bedroom bump-out
    # The GARAGE is INSIDE the main rectangle (thick exterior walls around it for fire rating)

    # Actually I see now - the garage has THICK walls all around it
    # This suggests it's a separate exterior-walled space (attached garage with fire separation)

    # Let me try a different approach:
    # Main house rectangle + garage rectangle + lower bedroom bump-out

    # Main house: roughly 36' wide x 35.5' tall (not including garage or bump-out)
    # Garage: 21.42' x 20.75' attached to right side
    # Lower bedroom bump-out: 11.33' x 13.67'

    # SIMPLIFIED PERIMETER (exterior walls only):
    #
    # The building outline from the image:
    # - Top runs the full width
    # - Right side is vertical
    # - Bottom-right has garage
    # - Bottom-center has porch notch
    # - Bottom-left has bedroom bump extending down
    # - Left side has step at bedroom bump

    # Setting final coordinates based on proportions:
    # Total width: ~58' (Living 22.92 + Kitchen 13.33 + right section ~22')
    # Total height: ~56' (Garage 20.75 + upper area 35')
    # BUT that seems too tall - let me reconsider

    # Looking at Garage: 21.42' wide x 20.75' tall
    # Master above garage: 14.83' wide x 17.5' tall
    # These don't stack to 38' - there's overlap

    # The key is that the Garage and Master share roughly the same right edge
    # but the Master is narrower - there's space for Hall/Closet/Bath between

    # New coordinate system:
    # X: 0 to 58 (total width)
    # Y: 0 to 38 (total height estimate)

    # EXTERIOR PERIMETER walls - following thick black lines:
    # I'll trace starting from (0, 38) top-left, going clockwise

    # Key X positions:
    # 0 = left edge (bedroom bump)
    # 11.33 = right of bedroom bump (step in)
    # 22.92 = right of Living
    # 36.25 = right of Kitchen
    # 51.08 = right edge (Master/Garage)

    # Wait - 51 seems narrow compared to what I see
    # Let me check: the Garage is 21.42' wide
    # Looking at proportions, Garage appears to be ~40% of total width
    # So total width ≈ 21.42 / 0.4 ≈ 53.5'

    # Let's use: total width = 53' (round number)
    # Garage left edge = 53 - 21.42 = 31.58

    # Y positions (bottom to top):
    # 0 = Bottom (garage and bedroom bump)
    # 6.67 = Top of Laundry (if Laundry is at garage level top)
    # 13.67 = Top of bedroom bump
    # 20.75 = Top of Garage
    # 38 = Top of building

    # Actually, I need to step back and look at this more systematically.
    # The top row is: Living (22.92) + Kitchen (13.33) + Master (14.83) = 51.08'
    # The garage is 21.42' wide
    # The garage is to the RIGHT of the laundry room

    # From the image, the building seems to be:
    # - Width: ~51' (from room dimensions)
    # - Height: Living(18) + middle_section + lower(varies)

    # Let me just place walls based on what I calculate and see:
    # I'll use:
    # Width = 51.08', Height = 38'
    # Lower bedroom bump starts at X=0, Y=0, extends to X=11.33, Y=13.67
    # Main building is a rectangle from X=11.33 to X=51.08, Y=13.67 to Y=38
    # Garage is X=29.66 to X=51.08, Y=0 to Y=20.75

    # EXTERIOR WALLS:
    $exteriorWalls = @()

    # TOP WALL - full width
    $exteriorWalls += '{"startPoint":[0,38,0],"endPoint":[51.08,38,0]}'

    # RIGHT WALL - Master down to Garage, then down
    $exteriorWalls += '{"startPoint":[51.08,38,0],"endPoint":[51.08,0,0]}'

    # BOTTOM - Garage bottom
    $exteriorWalls += '{"startPoint":[51.08,0,0],"endPoint":[29.66,0,0]}'

    # Garage left wall up to house level
    $exteriorWalls += '{"startPoint":[29.66,0,0],"endPoint":[29.66,20.75,0]}'

    # Step from Garage to main house (going left at Y=20.75)
    # But wait - looking at image, there's Laundry at 6.67' tall between Garage and Porch
    # The step happens at different Y levels on each side

    # Let me trace bottom edge from Garage left:
    # From Garage left (29.66, 0) go up to Laundry top (29.66, 6.83)
    # Then go left to Porch area
    # Porch is 3.83' wide at X = ~22 area

    # Actually, looking at the image again:
    # The PORCH is an exterior indentation - the building wall steps IN at the porch
    # So there's no exterior wall along the porch floor

    # Let me trace more carefully:
    # From Garage going left:
    # - Garage bottom (51.08,0) to (29.66,0) [DONE]
    # - Up Garage left side (29.66,0) to (29.66,6.83) - Laundry height
    $exteriorWalls += '{"startPoint":[29.66,0,0],"endPoint":[29.66,6.83,0]}'

    # - Left along Laundry top/Hallway bottom (29.66,6.83) to (23.92,6.83)
    $exteriorWalls += '{"startPoint":[29.66,6.83,0],"endPoint":[23.92,6.83,0]}'

    # - Now there's the PORCH indentation
    # Porch is 3.83' x 4' - let's say it's between X=20 and X=23.83
    # Porch bottom at Y=6.83, porch walls go up 4' to Y=10.83

    # Porch right wall down
    $exteriorWalls += '{"startPoint":[23.92,6.83,0],"endPoint":[23.92,2.83,0]}'

    # Porch bottom (open - this is outside, no wall)
    # Actually looking at image - the porch has walls on 3 sides (not the front)
    # Let me skip the porch detail for now and just go around it

    # Porch left wall up
    $exteriorWalls += '{"startPoint":[20.08,2.83,0],"endPoint":[20.08,6.83,0]}'

    # Porch bottom
    $exteriorWalls += '{"startPoint":[23.92,2.83,0],"endPoint":[20.08,2.83,0]}'

    # Continue left from porch to lower bedroom
    # From (20.08, 6.83) going left then down to bedroom bump

    # Office/Hall area bottom - going to bedroom bump
    $exteriorWalls += '{"startPoint":[20.08,6.83,0],"endPoint":[11.33,6.83,0]}'

    # Down to lower bedroom level
    $exteriorWalls += '{"startPoint":[11.33,6.83,0],"endPoint":[11.33,0,0]}'

    # Lower bedroom bottom
    $exteriorWalls += '{"startPoint":[11.33,0,0],"endPoint":[0,0,0]}'

    # LEFT WALL - lower bedroom up, then main building
    $exteriorWalls += '{"startPoint":[0,0,0],"endPoint":[0,38,0]}'

    # Create all exterior walls
    $wallJson = '[' + ($exteriorWalls -join ',') + ']'
    $request = '{"method":"createWallBatch","params":{"walls":' + $wallJson + ',"levelId":30,"height":10.0,"wallTypeId":441451}}'

    Write-Output "Creating exterior walls (version 2)..."
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    Write-Output "Exterior: $response"

    $pipe.Close()
} catch {
    Write-Output "Error: $_"
}
