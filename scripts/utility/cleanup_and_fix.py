"""
Clean up duplicate wall and attempt to fix door cuts
"""
import win32file
import json

pipe = win32file.CreateFile(
    r'\\.\pipe\RevitMCPBridge2026',
    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
    0, None, win32file.OPEN_EXISTING, 0, None
)

def call_mcp(method, params={}):
    request = json.dumps({'method': method, 'params': params}) + '\n'
    win32file.WriteFile(pipe, request.encode())
    chunks = []
    while True:
        result, data = win32file.ReadFile(pipe, 65536)
        chunks.append(data)
        combined = b''.join(chunks).decode()
        if combined.strip().endswith('}') or combined.strip().endswith(']'):
            break
        if len(data) < 1024:
            break
    return json.loads(b''.join(chunks).decode().strip())

print("=" * 60)
print("CLEANUP AND FIX DOOR CUTS")
print("=" * 60)

# Delete duplicate wall
print("\n[1] Deleting duplicate wall 1240506...")
r = call_mcp("deleteElement", {"elementId": 1240506})
if r.get("success"):
    print("  Deleted successfully")
else:
    # Try alternative method
    print(f"  deleteElement not available: {r.get('error', 'Unknown')}")
    print("  You may need to delete wall 1240506 manually in Revit")

# Count remaining walls
r = call_mcp("getElements", {"category": "Walls"})
walls = r.get("result", {}).get("elements", [])
print(f"\n  Remaining walls: {len(walls)}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("MANUAL FIX FOR DOOR CUTS")
print("=" * 60)
print("""
The Bifold, Sliding, and some specialty door families may not
automatically cut walls. To fix manually in Revit:

1. SELECT the problem door
2. Go to MODIFY tab > Geometry panel
3. Click "Cut" button
4. Click the HOST WALL

This will create a manual cut relationship.

Alternatively:
- Check door family > Edit Family
- Look for "Cuts Wall" parameter
- Ensure it's checked/enabled

Problem doors to fix:
- Double door at (8.6, 26.8) - Wall 1240472
- Bifold at (-6.1, 3.6) - Wall 1240497
- Sliding 60x80 at (-20.4, 14.3) - Wall 1240481
- Sliding 60x80 at (-20.4, 3.8) - Wall 1240484
- Sliding 48x80 at (-8.3, -4.6) - Wall 1240495
- Entry door at (7.4, -13.2) - Wall 1240476
""")
