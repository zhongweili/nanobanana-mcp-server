#!/bin/bash
# Cleanup script for MCP Inspector port conflicts
# This script kills any existing MCP Inspector processes that may be occupying ports

echo "🧹 Cleaning up MCP Inspector processes and ports..."

# Kill MCP Inspector processes
echo "Stopping MCP Inspector processes..."
pkill -f "@modelcontextprotocol/inspector" 2>/dev/null || true
pkill -f "inspector" 2>/dev/null || true

# Kill any FastMCP processes
echo "Stopping FastMCP processes..."
pkill -f "fastmcp.*server.py" 2>/dev/null || true

# Check specific ports and kill processes using them
for port in 6274 6275 6276 6277 6278; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "Killing process $pid using port $port"
        kill $pid 2>/dev/null || true
    fi
done

echo "✅ Port cleanup completed"
echo "You can now run: fastmcp dev server.py:create_app"