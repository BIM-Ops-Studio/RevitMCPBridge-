Get-ChildItem -Path "D:\" -Recurse -Filter "*512*.rvt" -ErrorAction SilentlyContinue | Select-Object -First 5 FullName
