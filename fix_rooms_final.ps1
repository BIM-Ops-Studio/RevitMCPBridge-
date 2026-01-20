$pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'RevitMCPBridge2026', [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$w = New-Object System.IO.StreamWriter($pipe)
$w.AutoFlush = $true
$r = New-Object System.IO.StreamReader($pipe)

# CORRECTED values from 003.PNG blown-up image
# Rooms 715-726 were all shifted by one position
# Room 729 had wrong source value (1063 instead of 1043)
$corrections = @(
    @(1314034, '715', '680'),   # Office 115 = 567 x 1.2 = 680
    @(1314035, '716', '672'),   # Office 116 = 560 x 1.2 = 672
    @(1314036, '717', '702'),   # Office 117 = 585 x 1.2 = 702
    @(1314037, '718', '703'),   # Office 118 = 586 x 1.2 = 703
    @(1314038, '719', '686'),   # Office 119 = 572 x 1.2 = 686
    @(1314039, '720', '670'),   # Office 120 = 558 x 1.2 = 670
    @(1314040, '721', '632'),   # Office 121 = 527 x 1.2 = 632
    @(1314041, '722', '644'),   # Office 122 = 537 x 1.2 = 644
    @(1314042, '723', '601'),   # Office 123 = 501 x 1.2 = 601
    @(1314043, '724', '608'),   # Office 124 = 507 x 1.2 = 608
    @(1314044, '725', '924'),   # Office 125 = 770 x 1.2 = 924
    @(1314045, '726', '1192'),  # Office 126 = 993 x 1.2 = 1192
    @(1314048, '729', '1252')   # Office 129 = 1043 x 1.2 = 1252
)

$fixed = 0
foreach ($room in $corrections) {
    $id = $room[0]
    $num = $room[1]
    $sf = $room[2]
    $cmd = '{"method":"setParameter","params":{"elementId":' + $id + ',"parameterName":"Comments","value":"' + $sf + ' SF"}}'
    $w.WriteLine($cmd)
    $resp = $r.ReadLine() | ConvertFrom-Json
    if ($resp.success) {
        $fixed++
        Write-Host "FIXED Room $num -> $sf SF"
    } else {
        Write-Host "FAILED Room $num : $($resp.error)"
    }
}

$pipe.Close()
Write-Host "`nTotal: $fixed of 13 rooms corrected"
