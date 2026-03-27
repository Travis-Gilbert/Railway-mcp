# Railway MCP Server

Python FastMCP server wrapping the Railway GraphQL API for use in claude.ai.

## Quick Reference

- Entrypoint: `python -m railway_mcp`
- All tools prefixed with `railway_`
- GraphQL endpoint: https://backboard.railway.app/graphql/v2
- Auth: Bearer token via RAILWAY_API_TOKEN env var
- Transport: streamable-http on Railway, stdio for local dev

## File Map

- `railway_mcp/server.py` - FastMCP instance + all 23 tool registrations
- `railway_mcp/client.py` - Async GraphQL client with error handling
- `railway_mcp/queries.py` - All GraphQL query/mutation string constants
- `railway_mcp/models.py` - Pydantic v2 input models for every tool
- `railway_mcp/formatting.py` - Markdown/JSON response formatting helpers
- `railway_mcp/__main__.py` - Entrypoint (transport + port from env)
- `railway_mcp/__init__.py` - Package marker

## Architecture

This follows the exact same pattern as Travis-Gilbert/ticktick-mcp:
- FastMCP handles MCP protocol + transport (streamable-http or stdio)
- httpx.AsyncClient talks to Railway's GraphQL v2 API
- Pydantic models validate all tool inputs
- Every tool returns formatted markdown or JSON based on response_format param

## Key Patterns

- The GraphQL client is a module-level singleton (get_client())
- All tools catch RailwayAPIError and return error strings (never raise)
- Relay-style pagination (edges/node) is extracted via _extract_edges()
- Destructive tools (delete_variable, bulk_set with replace=True, delete_service) have destructiveHint=True
- Projects/services/environments are referenced by UUID strings
- Railway's staged config model: serviceInstanceUpdate writes config,
  then serviceInstanceDeployV2 applies it. The tools guide users
  through this two-step flow via descriptions.

## Tool Count

23 total: 10 read-only, 13 write (3 destructive)

Categories:
- Projects (2): list, get
- Services (6): list, get, create, delete, connect, disconnect
- Service Config (1): update (Dockerfile path, start command, root dir, health check, replicas)
- Environments (3): list, create, duplicate
- Variables (5): list, list unresolved, set, bulk set, delete
- Deployments (6): status, build logs, deploy logs, redeploy, deploy (fresh), restart

## Testing

```bash
# Syntax check
python -m py_compile railway_mcp/server.py

# Local run (needs RAILWAY_API_TOKEN in .env)
python -m railway_mcp

# With stdio transport for local testing
MCP_TRANSPORT=stdio python -m railway_mcp
```

## GraphQL API Docs

- Endpoint: https://backboard.railway.app/graphql/v2
- Playground: https://railway.com/graphiql
- API cookbook: https://docs.railway.com/integrations/api/api-cookbook
- Variable management: https://docs.railway.com/integrations/api/manage-variables
- Deployment management: https://docs.railway.com/guides/manage-deployments
- Environment management: https://docs.railway.com/integrations/api/manage-environments
- Service management: https://docs.railway.com/guides/manage-services

## Deployment

Deployed on Railway with these env vars:
- RAILWAY_API_TOKEN (account token from https://railway.com/account/tokens)
- PORT=8000 (Railway injects this)
- MCP_TRANSPORT=streamable-http

Connected to claude.ai via the public domain URL + /mcp path.

## No Em Dashes

Do not use em dashes anywhere in code, comments, or documentation.
