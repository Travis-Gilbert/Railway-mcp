"""Entry point for `python -m railway_mcp`."""

import os
from railway_mcp.server import mcp

transport = os.environ.get("MCP_TRANSPORT", "http")
port = int(os.environ.get("PORT", "8000"))

if transport == "stdio":
    mcp.run(transport="stdio")
else:
    mcp.run(transport="http", host="0.0.0.0", port=port)
