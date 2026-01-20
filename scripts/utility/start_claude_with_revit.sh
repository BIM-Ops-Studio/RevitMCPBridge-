#!/bin/bash
# Start Claude Code with Revit MCP Server Enabled
# This enables LIVE interaction with Revit models

echo "========================================"
echo "Starting Claude Code with Revit MCP"
echo "========================================"
echo ""

# Check if Revit is running
echo "Checking if Revit is running..."
revit_check=$(powershell.exe "Get-Process | Where-Object {\\$_.ProcessName -like '*Revit*'} | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null)

if [ "$revit_check" -gt 0 ]; then
    echo "✅ Revit is running!"
else
    echo "⚠️  Revit not detected - start Revit first for live workflow"
fi

echo ""
echo "Starting Claude Code with Revit MCP enabled..."
echo "Available tools once started:"
echo "  - ping() - Test Revit connection"
echo "  - get_project_info() - Current project details"
echo "  - query_elements() - Find elements in model"
echo "  - add_tags() - Tag elements"
echo "  - create_schedule() - Create schedules"
echo "  - And 400+ more Revit methods!"
echo ""

# Start Claude Code with Revit MCP config
cd /mnt/d/RevitMCPBridge2026
export CLAUDE_MCP_SERVERS_PATH=~/.claude/mcp-configs/revit.json
claude

