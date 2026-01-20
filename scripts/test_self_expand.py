#!/usr/bin/env python3
"""
Test the self-expanding capability loop end-to-end.
This script simulates the full cycle:
1. Call a non-existent method
2. Classify the failure
3. Propose a tool spec
4. Show approval options
"""
import json
import subprocess
import sys
import re

def call_mcp(method: str, params: dict = None):
    """Call MCP method via named pipe."""
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    })

    ps_script = f'''
$pipeName = "RevitMCPBridge2026"
$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {{
    $pipeClient.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipeClient)
    $reader = New-Object System.IO.StreamReader($pipeClient)
    $message = '{request.replace("'", "''")}'
    $writer.WriteLine($message)
    $writer.Flush()
    $response = $reader.ReadLine()
    Write-Output $response
}} finally {{
    $pipeClient.Close()
}}
'''
    result = subprocess.run(
        ["powershell.exe", "-Command", ps_script],
        capture_output=True, text=True, timeout=60
    )

    output = result.stdout.strip()
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('{'):
            line = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', line)
            try:
                return json.loads(line)
            except:
                continue
    return {"error": "No JSON found", "raw": output[:500]}


def test_full_loop(method_name: str):
    """Test the complete self-expanding loop."""
    print("=" * 60)
    print(f"SELF-EXPANDING CAPABILITY LOOP TEST")
    print(f"Testing method: {method_name}")
    print("=" * 60)

    # Step 1: Try to call the non-existent method
    print("\n[STEP 1] Calling non-existent method...")
    result = call_mcp(method_name, {})
    print(f"Result: {json.dumps(result, indent=2)[:500]}")

    if result.get("success"):
        print("\n⚠️  Method exists! Choose a different method name.")
        return

    error_msg = result.get("error", "")
    print(f"Error: {error_msg}")

    # Step 2: Classify the failure
    print("\n[STEP 2] Classifying failure...")
    classify_result = call_mcp("classifyFailure", {
        "errorMessage": error_msg,
        "methodName": method_name,
        "context": "User requested this capability"
    })
    print(f"Classification: {json.dumps(classify_result, indent=2)[:800]}")

    if not classify_result.get("success"):
        print("❌ Classification failed!")
        return

    # Handle nested classification structure
    classification_obj = classify_result.get("classification", {})
    if isinstance(classification_obj, dict):
        classification = classification_obj.get("type", "")
        confidence = int(classification_obj.get("confidence", 0) * 100)
    else:
        classification = classification_obj
        confidence = classify_result.get("confidence", 0)

    print(f"\n📊 Classification: {classification} (confidence: {confidence}%)")

    if classification != "MISSING_CAPABILITY":
        print("⚠️  Not classified as MISSING_CAPABILITY")
        return

    # Step 3: Propose a tool spec
    print("\n[STEP 3] Proposing tool spec...")
    propose_result = call_mcp("proposeToolSpec", {
        "name": method_name,
        "intent": f"Set the occupant information for a room element",
        "tier": 2,
        "category": "Room"
    })
    print(f"Proposal: {json.dumps(propose_result, indent=2)[:1000]}")

    if not propose_result.get("success"):
        print("❌ Spec proposal failed!")
        return

    spec_path = propose_result.get("specPath", "")
    print(f"\n✅ Spec created at: {spec_path}")

    # Step 4: Show next steps
    print("\n[STEP 4] Next steps:")
    print("  1. Review the spec file")
    print("  2. Approve with: approveToolSpec")
    print("  3. Generate code with: generateImplementation")
    print("  4. Add to MCPServer.cs and build")
    print("  5. Test the new method")

    print("\n" + "=" * 60)
    print("LOOP TEST COMPLETE")
    print("=" * 60)

    return {
        "method": method_name,
        "classification": classification,
        "confidence": confidence,
        "spec_path": spec_path
    }


if __name__ == "__main__":
    method = sys.argv[1] if len(sys.argv) > 1 else "setRoomDepartment"
    test_full_loop(method)
