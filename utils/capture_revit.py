"""
Capture Revit window screenshot for verification
Saves to shared_screenshots folder for Claude Code to analyze
"""
import subprocess
import datetime
import os

# Output directory
output_dir = r"D:\shared_screenshots"
os.makedirs(output_dir, exist_ok=True)

# Generate filename with timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"revit_capture_{timestamp}.png"
filepath = os.path.join(output_dir, filename)

# Use PowerShell to capture Revit window
ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$revit = Get-Process | Where-Object {{$_.MainWindowTitle -like "*Autodesk Revit*"}} | Select-Object -First 1
if ($revit) {{
    $handle = $revit.MainWindowHandle
    Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class Window {{
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")]
        public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    }}
    public struct RECT {{
        public int Left, Top, Right, Bottom;
    }}
"@
    [Window]::SetForegroundWindow($handle)
    Start-Sleep -Milliseconds 500

    $rect = New-Object RECT
    [Window]::GetWindowRect($handle, [ref]$rect)

    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top

    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
    $bitmap.Save("{filepath}")
    Write-Output "Captured: {filepath}"
}} else {{
    Write-Output "Revit not found"
}}
'''

result = subprocess.run(
    ["powershell.exe", "-NoProfile", "-Command", ps_script],
    capture_output=True, text=True
)

print(result.stdout)
if result.stderr:
    print(f"Error: {result.stderr}")
