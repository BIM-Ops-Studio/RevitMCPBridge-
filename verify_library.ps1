$libraryPath = "D:\Revit Detail Libraries\Revit Details"

Write-Output "=== Detail Library Verification ==="
Write-Output ""
Write-Output "--- Category Counts ---"

Get-ChildItem $libraryPath -Directory | Sort-Object Name | ForEach-Object {
    $count = (Get-ChildItem $_.FullName -Filter "*.rvt").Count
    Write-Output ("{0}: {1} files" -f $_.Name, $count)
}

Write-Output ""
Write-Output "--- Summary ---"
$total = (Get-ChildItem $libraryPath -Recurse -Filter "*.rvt").Count
$categories = (Get-ChildItem $libraryPath -Directory).Count
Write-Output ("Total Categories: {0}" -f $categories)
Write-Output ("Total Detail Files: {0}" -f $total)
