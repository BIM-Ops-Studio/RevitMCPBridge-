#!/bin/bash

ADDIN_PATH="/mnt/c/Users/rick/AppData/Roaming/Autodesk/Revit/Addins/2026"

echo -e "\033[36mUpdating MCP Bridge manifest for Revit 2026...\033[0m"

# Backup existing files
if [ -f "$ADDIN_PATH/RevitMCPBridge2026.addin" ]; then
    echo -e "\033[33mBacking up existing manifest...\033[0m"
    cp "$ADDIN_PATH/RevitMCPBridge2026.addin" "$ADDIN_PATH/RevitMCPBridge2026.addin.backup"
fi

# Update the manifest to ensure it creates its own tab
cat > "$ADDIN_PATH/RevitMCPBridge2026.addin" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="Application">
    <Name>MCP Bridge</Name>
    <Assembly>RevitMCPBridge2026.dll</Assembly>
    <FullClassName>RevitMCPBridge.RevitMCPBridgeApp</FullClassName>
    <ClientId>8B8B6F55-9C7A-4F5E-8D8A-1B2C3D4E5F61</ClientId>
    <VendorId>ADSK</VendorId>
    <VendorDescription>Autodesk Developer Network</VendorDescription>
    <Description>MCP Bridge for Revit 2026 - Enables Claude AI integration with Revit API through Model Context Protocol</Description>
  </AddIn>
</RevitAddIns>
EOF

echo -e "\n\033[32m✓ Manifest updated successfully!\033[0m"
echo -e "\033[36mThe MCP Bridge should now appear in its own ribbon tab when you restart Revit 2026.\033[0m"
echo -e "\033[33mNote: Using the existing DLL. To fully update, we'll need to build the new project.\033[0m"