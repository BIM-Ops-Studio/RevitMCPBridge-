import win32file, json, sys

def test_method(method_name):
    try:
        print(f"Testing {method_name}...", end=" ")
        h = win32file.CreateFile(r'\\.\pipe\RevitMCPBridge2026', win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
        win32file.WriteFile(h, json.dumps({"method": method_name, "parameters": {}}).encode('utf-8'))
        _, data = win32file.ReadFile(h, 64*1024)
        win32file.CloseHandle(h)
        result = json.loads(data)
        if result.get("success"):
            print("SUCCESS")
            return True
        else:
            print(f"FAILED: {result.get('error')}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

print("Testing known working methods:")
test_method("getActiveViewInfo")
test_method("getAllSheets")

print("\nTesting NEW Sheet Pattern methods:")
test_method("listKnownFirms")
test_method("getPatternRules")
