# Railway MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) server that lets you manage Railway infrastructure from claude.ai (or any MCP client). Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) and deployed on Railway itself.

## What It Does

17 tools across 5 categories:

- **Projects** - List and inspect your Railway projects
- **Services** - View service configuration and status per environment
- **Environments** - List, create, and duplicate environments
- **Variables** - List, set, bulk set, and delete environment variables
- **Deployments** - Check status, read logs, redeploy, and restart

## Why

Railway has an [official MCP server](https://docs.railway.com/ai/mcp-server) but it wraps the CLI and only works locally (stdio transport). This server hits the Railway GraphQL API directly over HTTP, so it can be deployed as a remote service and connected to claude.ai as a connector.

## Setup

### 1. Get a Railway API Token

Go to [railway.com/account/tokens](https://railway.com/account/tokens) and create an account-level token.

### 2. Deploy to Railway

- Create a new Railway project
- Connect this GitHub repo
- Set environment variables:
  - `RAILWAY_API_TOKEN` = your token
  - `PORT` = `8000`
  - `MCP_TRANSPORT` = `streamable-http`
- Generate a public domain

### 3. Connect to claude.ai

Add the MCP connector URL: `https://{your-domain}/mcp`

### Local Development

```bash
# Clone and install
git clone https://github.com/Travis-Gilbert/railway-mcp.git
cd railway-mcp
pip install -e .

# Set up env
cp .env.example .env
# Edit .env with your Railway API token

# Run locally
python -m railway_mcp

# Or with stdio transport
MCP_TRANSPORT=stdio python -m railway_mcp
```

## Tech Stack

- Python 3.12
- FastMCP (MCP protocol + transport)
- httpx (async HTTP client)
- Pydantic v2 (input validation)
- Railway GraphQL API v2
