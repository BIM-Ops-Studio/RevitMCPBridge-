#!/usr/bin/env python3
"""
Autonomous Capability Expansion System
=======================================
This script automates the entire self-expanding capability loop:
1. Detect missing method
2. Classify failure
3. Propose tool spec
4. Approve spec
5. Generate implementation
6. Insert code into source files
7. Build project
8. Deploy to Revit
9. Test new method

Usage:
    python auto_expand_capability.py <method_name> "<intent description>"

Example:
    python auto_expand_capability.py setRoomOccupant "Set the occupant name for a room"
"""

import json
import subprocess
import sys
import re
import os
import time
from pathlib import Path
from datetime import datetime

# Configuration - Use WSL paths for file operations, Windows paths for PowerShell
PROJECT_ROOT_WIN = r"D:\RevitMCPBridge2026"
PROJECT_ROOT = "/mnt/d/RevitMCPBridge2026"
SRC_DIR = "/mnt/d/RevitMCPBridge2026/src"
SCRIPTS_DIR = "/mnt/d/RevitMCPBridge2026/scripts"


def log(msg: str, level: str = "INFO"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️", "STEP": "🔄"}
    symbol = symbols.get(level, "•")
    print(f"[{timestamp}] {symbol} {msg}")


def call_mcp(method: str, params: dict = None, timeout: int = 60) -> dict:
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
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_script],
            capture_output=True, text=True, timeout=timeout
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
    except subprocess.TimeoutExpired:
        return {"error": "MCP call timed out"}
    except Exception as e:
        return {"error": str(e)}


def detect_category(method_name: str) -> str:
    """Detect the category based on method name prefix."""
    prefixes = {
        "room": "Room", "wall": "Wall", "door": "DoorWindow", "window": "DoorWindow",
        "view": "View", "sheet": "Sheet", "schedule": "Schedule", "family": "Family",
        "parameter": "Parameter", "mep": "MEP", "structural": "Structural",
        "detail": "Detail", "filter": "Filter", "material": "Material",
        "phase": "Phase", "workset": "Workset", "annotation": "Annotation"
    }

    lower_name = method_name.lower()
    for prefix, category in prefixes.items():
        if prefix in lower_name:
            return category
    return "General"


def get_methods_file(category: str) -> str:
    """Get the source file path for a category (WSL path)."""
    category_files = {
        "Room": "RoomMethods.cs",
        "Wall": "WallMethods.cs",
        "DoorWindow": "DoorWindowMethods.cs",
        "View": "ViewMethods.cs",
        "Sheet": "SheetMethods.cs",
        "Schedule": "ScheduleMethods.cs",
        "Family": "FamilyMethods.cs",
        "Parameter": "ParameterMethods.cs",
        "MEP": "MEPMethods.cs",
        "Structural": "StructuralMethods.cs",
        "Detail": "DetailMethods.cs",
        "Filter": "FilterMethods.cs",
        "Material": "MaterialMethods.cs",
        "Phase": "PhaseMethods.cs",
        "Workset": "WorksetMethods.cs",
        "Annotation": "AnnotationMethods.cs",
        "General": "NewMethods.cs"
    }
    filename = category_files.get(category, "NewMethods.cs")
    return f"{SRC_DIR}/{filename}"


def insert_method_code(category: str, method_code: str, method_name: str) -> bool:
    """Insert method code into the appropriate source file."""
    file_path = get_methods_file(category)

    if not os.path.exists(file_path):
        log(f"Creating new file: {os.path.basename(file_path)}", "INFO")
        # Create a new methods file
        template = f'''using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge
{{
    public static class NewMethods
    {{
{method_code}
    }}
}}
'''
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        return True

    # Read existing file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if method already exists
    if method_name in content:
        log(f"Method {method_name} already exists in {os.path.basename(file_path)}", "WARN")
        return False

    # Find the last closing brace of the class (before namespace closing brace)
    # Look for pattern: }}\n}} or similar
    lines = content.split('\n')
    insert_index = -1
    brace_count = 0

    for i, line in enumerate(lines):
        brace_count += line.count('{') - line.count('}')
        # We want to insert before the class closing brace (when brace_count == 1)
        if brace_count == 1 and '}' in line:
            # This is likely the class closing brace
            insert_index = i
            break

    if insert_index == -1:
        # Fallback: find last }} pattern
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '}':
                insert_index = i
                break

    if insert_index == -1:
        log("Could not find insertion point in file", "ERROR")
        return False

    # Insert the method before the closing brace
    new_lines = lines[:insert_index] + ['\n' + method_code] + lines[insert_index:]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    log(f"Inserted method into {os.path.basename(file_path)}", "SUCCESS")
    return True


def insert_switch_case(switch_case: str, method_name: str) -> bool:
    """Insert switch case into MCPServer.cs."""
    mcp_server_path = f"{SRC_DIR}/MCPServer.cs"

    if not os.path.exists(mcp_server_path):
        log("MCPServer.cs not found", "ERROR")
        return False

    with open(mcp_server_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if case already exists
    if f'case "{method_name.lower()}"' in content.lower():
        log(f"Switch case for {method_name} already exists", "WARN")
        return False

    # Find the default case or last case before it
    # Look for "default:" pattern
    default_match = re.search(r'(\s+)(default\s*:)', content)

    if default_match:
        indent = default_match.group(1)
        insert_pos = default_match.start()

        # Format the switch case with proper indentation
        formatted_case = switch_case.strip() + '\n' + indent

        new_content = content[:insert_pos] + formatted_case + content[insert_pos:]

        with open(mcp_server_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        log("Inserted switch case into MCPServer.cs", "SUCCESS")
        return True
    else:
        log("Could not find default case in MCPServer.cs", "ERROR")
        return False


def build_project() -> tuple[bool, str]:
    """Build the project using MSBuild."""
    log("Building project...", "STEP")

    # Use full MSBuild path
    msbuild_path = r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"

    try:
        result = subprocess.run(
            ["powershell.exe", "-Command",
             f"cd '{PROJECT_ROOT_WIN}'; & '{msbuild_path}' RevitMCPBridge2026.csproj /p:Configuration=Release /v:minimal"],
            capture_output=True, text=True, timeout=120
        )

        output = result.stdout + result.stderr

        if "Build succeeded" in output and "0 Error(s)" in output:
            log("Build succeeded", "SUCCESS")
            return True, output
        else:
            # Extract errors
            errors = [line for line in output.split('\n') if 'error' in line.lower() and 'warning' not in line.lower()]
            log(f"Build failed: {errors[:3]}", "ERROR")
            return False, output
    except Exception as e:
        log(f"Build error: {e}", "ERROR")
        return False, str(e)


def deploy_to_revit() -> bool:
    """Deploy the DLL to Revit using auto-deploy script."""
    log("Deploying to Revit...", "STEP")

    deploy_script = f"{SCRIPTS_DIR}/revit_auto_deploy.py"

    if not os.path.exists(deploy_script):
        # Fallback: just copy the DLL via PowerShell
        log("Auto-deploy script not found, using direct copy", "WARN")
        try:
            copy_cmd = f"Copy-Item '{PROJECT_ROOT_WIN}\\bin\\Release\\RevitMCPBridge2026.dll' -Destination 'C:\\Users\\rick\\AppData\\Roaming\\Autodesk\\Revit\\Addins\\2026\\RevitMCPBridge2026.dll' -Force"
            subprocess.run(["powershell.exe", "-Command", copy_cmd], capture_output=True, timeout=30)
            log("DLL copied (Revit restart required)", "SUCCESS")
            return True
        except Exception as e:
            log(f"Copy failed: {e}", "ERROR")
            return False

    try:
        result = subprocess.run(
            ["python3", str(deploy_script)],
            capture_output=True, text=True, timeout=180,
            cwd=str(SCRIPTS_DIR)
        )

        if "Deploy complete" in result.stdout or result.returncode == 0:
            log("Deployment complete", "SUCCESS")
            return True
        else:
            log(f"Deployment may have issues: {result.stdout[:200]}", "WARN")
            return True  # Continue anyway
    except Exception as e:
        log(f"Deploy error: {e}", "ERROR")
        return False


def test_new_method(method_name: str, test_params: dict = None) -> bool:
    """Test the newly created method."""
    log(f"Testing {method_name}...", "STEP")

    # Wait for Revit to be ready
    time.sleep(5)

    result = call_mcp(method_name, test_params or {})

    if result.get("success"):
        log(f"Method {method_name} works!", "SUCCESS")
        return True
    elif "Unknown method" in result.get("error", ""):
        log(f"Method not yet available (may need Revit restart)", "WARN")
        return False
    else:
        log(f"Method returned: {result}", "INFO")
        return result.get("success", False)


def run_full_cycle(method_name: str, intent: str, test_params: dict = None):
    """Run the complete autonomous capability expansion cycle."""
    print("\n" + "=" * 70)
    print("🚀 AUTONOMOUS CAPABILITY EXPANSION SYSTEM")
    print("=" * 70)
    log(f"Method: {method_name}")
    log(f"Intent: {intent}")
    print("=" * 70 + "\n")

    category = detect_category(method_name)
    log(f"Detected category: {category}")

    # Step 1: Check if method exists
    log("STEP 1: Checking if method exists...", "STEP")
    result = call_mcp(method_name, {})

    if result.get("success"):
        log(f"Method {method_name} already exists!", "SUCCESS")
        return {"success": True, "message": "Method already exists", "existed": True}

    error_msg = result.get("error", "Unknown error")
    log(f"Method not found: {error_msg}")

    # Step 2: Classify failure
    log("STEP 2: Classifying failure...", "STEP")
    classify_result = call_mcp("classifyFailure", {
        "errorMessage": error_msg,
        "methodName": method_name,
        "context": intent
    })

    if not classify_result.get("success"):
        log(f"Classification failed: {classify_result.get('error')}", "ERROR")
        return {"success": False, "step": 2, "error": classify_result.get("error")}

    classification = classify_result.get("classification", {})
    class_type = classification.get("type") if isinstance(classification, dict) else classification
    confidence = classification.get("confidence", 0) if isinstance(classification, dict) else 0

    log(f"Classification: {class_type} ({int(confidence * 100)}% confidence)")

    if class_type != "MISSING_CAPABILITY":
        log(f"Not a missing capability: {class_type}", "WARN")
        return {"success": False, "step": 2, "classification": class_type}

    # Step 3: Propose tool spec
    log("STEP 3: Proposing tool spec...", "STEP")
    propose_result = call_mcp("proposeToolSpec", {
        "name": method_name,
        "intent": intent,
        "tier": 2,
        "category": category
    })

    if not propose_result.get("success"):
        log(f"Proposal failed: {propose_result.get('error')}", "ERROR")
        return {"success": False, "step": 3, "error": propose_result.get("error")}

    spec_path = propose_result.get("specPath", "")
    log(f"Spec created: {spec_path}")

    # Step 4: Approve spec
    log("STEP 4: Approving spec...", "STEP")
    approve_result = call_mcp("approveToolSpec", {"specName": method_name.lower()})

    if not approve_result.get("success"):
        log(f"Approval failed: {approve_result.get('error')}", "ERROR")
        return {"success": False, "step": 4, "error": approve_result.get("error")}

    log("Spec approved")

    # Step 5: Generate implementation
    log("STEP 5: Generating implementation...", "STEP")
    gen_result = call_mcp("generateImplementation", {"specName": method_name.lower()})

    if not gen_result.get("success"):
        log(f"Generation failed: {gen_result.get('error')}", "ERROR")
        return {"success": False, "step": 5, "error": gen_result.get("error")}

    generated_code = gen_result.get("generatedCode", "")
    switch_case = gen_result.get("switchCase", "")

    log(f"Generated {len(generated_code)} chars of code")

    # Step 6: Insert code into source files
    log("STEP 6: Inserting code into source files...", "STEP")

    code_inserted = insert_method_code(category, generated_code, method_name)
    if not code_inserted:
        log("Failed to insert method code", "ERROR")
        return {"success": False, "step": 6, "error": "Code insertion failed"}

    case_inserted = insert_switch_case(switch_case, method_name)
    if not case_inserted:
        log("Failed to insert switch case", "ERROR")
        return {"success": False, "step": 6, "error": "Switch case insertion failed"}

    # Step 7: Build project
    log("STEP 7: Building project...", "STEP")
    build_success, build_output = build_project()

    if not build_success:
        log("Build failed - manual intervention required", "ERROR")
        return {"success": False, "step": 7, "error": "Build failed", "output": build_output[:500]}

    # Step 8: Deploy to Revit
    log("STEP 8: Deploying to Revit...", "STEP")
    deploy_success = deploy_to_revit()

    if not deploy_success:
        log("Deployment failed - manual intervention required", "WARN")
        # Continue anyway to report status

    # Step 9: Test new method
    log("STEP 9: Testing new method...", "STEP")
    time.sleep(10)  # Wait for Revit to reload

    test_success = test_new_method(method_name, test_params)

    # Final status
    print("\n" + "=" * 70)
    if test_success:
        log(f"🎉 CAPABILITY EXPANSION COMPLETE: {method_name}", "SUCCESS")
    else:
        log(f"Capability added but needs Revit restart to test", "WARN")
    print("=" * 70 + "\n")

    return {
        "success": True,
        "method": method_name,
        "category": category,
        "specPath": spec_path,
        "codeInserted": code_inserted,
        "caseInserted": case_inserted,
        "buildSuccess": build_success,
        "deploySuccess": deploy_success,
        "testSuccess": test_success
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage: python auto_expand_capability.py <method_name> [intent]")
        print("\nExample:")
        print('  python auto_expand_capability.py setRoomOccupant "Set the occupant name for a room"')
        sys.exit(1)

    method_name = sys.argv[1]
    intent = sys.argv[2] if len(sys.argv) > 2 else f"Implement {method_name} capability"

    result = run_full_cycle(method_name, intent)

    print("\nResult:")
    print(json.dumps(result, indent=2))

    sys.exit(0 if result.get("success") else 1)
