import json
import csv
import time

def send_mcp_command(pipe_path, method, params):
    """Send command to Revit MCP and get response"""
    import win32file
    import win32pipe

    try:
        handle = win32file.CreateFile(
            pipe_path,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        request = json.dumps({"method": method, "params": params})
        win32file.WriteFile(handle, (request + "\n").encode())

        response = b""
        while True:
            try:
                _, data = win32file.ReadFile(handle, 64*1024)
                response += data
                if b"\n" in response:
                    break
            except:
                break

        win32file.CloseHandle(handle)
        return json.loads(response.decode().strip())
    except Exception as e:
        return {"success": False, "error": str(e)}

# Main
pipe_path = r"\\.\pipe\RevitMCPBridge2026"
csv_path = r"D:\001 - PROJECTS\01 - CLIENT PROJECTS\10 - BERNARDO RIEBER - DEVELOPMENTS\L7_PDF_to_Revit_SF_CORRECTED.csv"

# Get rooms
print("Getting L7 rooms...")
result = send_mcp_command(pipe_path, "getRooms", {"levelName": "L7"})

if result.get("success"):
    room_map = {}
    for room in result["rooms"]:
        if room["level"] == "L7":
            room_map[room["number"]] = room["roomId"]
    print(f"Found {len(room_map)} L7 rooms")

    # Read CSV and update
    updated = 0
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            revit_room = row["Revit_Room"]
            display_sf = row["Display_SF"]

            if revit_room in room_map:
                room_id = room_map[revit_room]
                result = send_mcp_command(pipe_path, "setParameter", {
                    "elementId": room_id,
                    "parameterName": "Comments",
                    "value": f"{display_sf} SF"
                })
                if result.get("success"):
                    print(f"Room {revit_room} -> {display_sf} SF")
                    updated += 1
                else:
                    print(f"FAILED {revit_room}: {result.get('error')}")
                time.sleep(0.1)

    print(f"\nTotal: {updated} rooms updated")
else:
    print(f"Error: {result.get('error')}")
