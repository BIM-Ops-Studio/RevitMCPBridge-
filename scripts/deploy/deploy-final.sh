#!/bin/bash

DLL_PATH="/mnt/c/ProgramData/Autodesk/Revit/Addins/2026"
ADDIN_PATH="/mnt/c/Users/rick/AppData/Roaming/Autodesk/Revit/Addins/2026"

echo -e "\033[36mDeploying MCP Bridge to Revit 2026...\033[0m"

# Check if we have a built DLL
if [ -f "bin/Debug/RevitMCPBridge2026.dll" ]; then
    echo -e "\033[32mFound compiled DLL, deploying new version...\033[0m"
    
    # Backup existing
    if [ -f "$DLL_PATH/RevitMCPBridge2026.dll" ]; then
        cp "$DLL_PATH/RevitMCPBridge2026.dll" "$DLL_PATH/RevitMCPBridge2026.dll.backup"
    fi
    
    # Copy new DLL
    cp "bin/Debug/RevitMCPBridge2026.dll" "$DLL_PATH/"
    echo -e "\033[32m✓ DLL deployed\033[0m"
else
    echo -e "\033[33mNo new DLL found, keeping existing DLL\033[0m"
fi

# Always update the manifest to ensure proper tab creation
echo -e "\033[36mUpdating manifest...\033[0m"
cp "RevitMCPBridge2026.addin" "$ADDIN_PATH/"
echo -e "\033[32m✓ Manifest deployed\033[0m"

echo -e "\n\033[32mDeployment complete!\033[0m"
echo -e "\033[36mRestart Revit 2026 to see MCP Bridge in its own ribbon tab.\033[0m"