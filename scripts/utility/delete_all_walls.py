#!/usr/bin/env python3
"""Delete ALL walls from the model - complete cleanup"""
import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call_mcp(method, params=None):
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None, win32file.OPEN_EXISTING, 0, None
        )
        request = {"method": method, "params": params or {}}
        message = json.dumps(request) + '\n'
        win32file.WriteFile(handle, message.encode('utf-8'))

        response_data = b''
        while True:
            result, chunk = win32file.ReadFile(handle, 64 * 1024)
            response_data += chunk
            if b'\n' in chunk or len(chunk) == 0:
                break

        win32file.CloseHandle(handle)
        return json.loads(response_data.decode('utf-8').strip())
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Delete all known wall IDs from previous runs
    known_wall_ids = [
        # Original batch
        1240788, 1240789, 1240790, 1240791, 1240792, 1240793, 1240794,
        1240795, 1240796, 1240797, 1240798, 1240799, 1240800, 1240801,
        1240802, 1240803, 1240804, 1240805, 1240806, 1240807, 1240808,
        1240809, 1240810,
        # Second batch
        1240813, 1240814, 1240815, 1240816, 1240817,
        # Latest batch
        1240820, 1240821, 1240825, 1240826, 1240829, 1240830, 1240831,
        1240832, 1240835, 1240836, 1240837, 1240838, 1240839, 1240840,
    ]

    print(f"Deleting {len(known_wall_ids)} walls...")
    delete_result = call_mcp("deleteElements", {"elementIds": known_wall_ids})
    print(f"Delete result: {json.dumps(delete_result, indent=2)}")
