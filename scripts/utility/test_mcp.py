"""
Test MCP connectivity to Revit.
"""

import json
import win32file
import pywintypes

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

print('Testing MCP connectivity...')
print()

try:
    handle = win32file.CreateFile(
        PIPE_NAME,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None, win32file.OPEN_EXISTING, 0, None
    )

    # Test with getLevels
    request = {'method': 'getLevels', 'params': {}}
    message = json.dumps(request) + '\n'

    win32file.WriteFile(handle, message.encode('utf-8'))

    response_data = b''
    while True:
        result, chunk = win32file.ReadFile(handle, 64 * 1024)
        response_data += chunk
        if b'\n' in chunk or len(chunk) == 0:
            break

    win32file.CloseHandle(handle)
    response = json.loads(response_data.decode('utf-8').strip())

    if response.get('success'):
        print('SUCCESS - MCP connected!')
        print('Levels found:')
        for level in response.get('levels', []):
            name = level.get('name', 'Unknown')
            lid = level.get('levelId', 'N/A')
            elev = level.get('elevation', 0)
            print(f'  {name} (ID: {lid}) at {elev} ft')
    else:
        print(f'ERROR: {response.get("error")}')

except pywintypes.error as e:
    print(f'PIPE ERROR: {e}')
    print('Make sure Revit is open and the MCP server is running!')
except Exception as e:
    print(f'ERROR: {e}')
