$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'RevitMCPBridge2026', [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$w = New-Object System.IO.StreamWriter($pipe)
$w.AutoFlush = $true
$r = New-Object System.IO.StreamReader($pipe)

# All corrected values: ElementID, RoomNum, DisplaySF
$rooms = @(
    @(1314020, '701', '653'),
    @(1314021, '702', '866'),
    @(1314022, '703', '1062'),
    @(1314023, '704', '689'),
    @(1314024, '705', '913'),
    @(1314025, '706', '654'),
    @(1314026, '707', '719'),
    @(1314027, '708', '958'),
    @(1314028, '709', '826'),
    @(1314029, '710', '673'),
    @(1314030, '711', '688'),
    @(1314031, '712', '679'),
    @(1314032, '713', '671'),
    @(1314033, '714', '680'),
    @(1314034, '715', '672'),
    @(1314035, '716', '702'),
    @(1314036, '717', '703'),
    @(1314037, '718', '686'),
    @(1314038, '719', '670'),
    @(1314039, '720', '632'),
    @(1314040, '721', '644'),
    @(1314041, '722', '601'),
    @(1314042, '723', '608'),
    @(1314043, '724', '924'),
    @(1314044, '725', '1192'),
    @(1314045, '726', '1134'),
    @(1314046, '727', '1067'),
    @(1314047, '728', '1145'),
    @(1314048, '729', '1276'),
    @(1314049, '730', '931'),
    @(1314050, '731', '925'),
    @(1314051, '732', '1832'),
    @(1314052, '733', '1916'),
    @(1314053, '734', '931'),
    @(1314054, '735', '918'),
    @(1314055, '736', '1844'),
    @(1314056, '737', '929'),
    @(1314057, '738', '790'),
    @(1314058, '739', '1380'),
    @(1376339, '740', '983'),
    @(1314059, '741', '942')
)

$updated = 0
foreach ($room in $rooms) {
    $id = $room[0]
    $num = $room[1]
    $sf = $room[2]
    $cmd = '{"method":"setParameter","params":{"elementId":' + $id + ',"parameterName":"Comments","value":"' + $sf + ' SF"}}'
    $w.WriteLine($cmd)
    $resp = $r.ReadLine() | ConvertFrom-Json
    if ($resp.success) {
        $updated++
        Write-Host "Room $num -> $sf SF"
    } else {
        Write-Host "FAILED Room $num"
    }
}

$pipe.Close()
Write-Host "`nTotal: $updated rooms updated with CORRECTED values"
