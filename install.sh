#!/bin/bash
# Installation script for Xiaohongshu MCP Server

set -e

echo "🚀 Installing Xiaohongshu MCP Server dependencies..."

# Install dependencies using --break-system-packages (safe for user packages)
python3 -m pip install --break-system-packages mcp httpx pydantic anyio

echo "✅ Dependencies installed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Set your API key: export XIAOHONGSHU_API_KEY='your-api-key'"
echo "2. Add to ~/.bashrc or ~/.zshrc to make it permanent"
echo "3. Restart OpenCode to load the MCP server"
