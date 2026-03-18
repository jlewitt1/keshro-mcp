# Keshro MCP

Optional MCP server over the Keshro API. Exposes 19 tools for reading/writing migrations, plans, and tasks from MCP-compatible agents.

**For most users, the CLI (`keshro continue`) is recommended over MCP.**

## Related repos

- **`../keshro`** — Main backend + frontend
- **`../keshro-cli`** — CLI (recommended over MCP)
- **`../batch-to-airflow-demo`** — Demo repo for testing

## Development

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run the server locally
KESHRO_API_URL=http://localhost:8000/api KESHRO_API_TOKEN=ksh_pat_... python -m keshro_mcp.server

# Run tests
python -m pytest tests/ -v
```

## Key files

- `src/keshro_mcp/server.py` — FastMCP server with all 19 tool definitions
- `src/keshro_mcp/client.py` — HTTP client that wraps the Keshro API
- `src/keshro_mcp/config.py` — Settings from env vars (KESHRO_API_URL, KESHRO_API_TOKEN)

## Architecture

The MCP server is a thin wrapper — each tool calls one or two Keshro API endpoints. No business logic lives here. The client handles HTTP, auth, and error formatting.

Auth is via env var (`KESHRO_API_TOKEN`), not interactive login like the CLI.

## Publishing

Use the GitHub Action (Actions → "Publish MCP" → Run workflow) or manually:

```bash
python -m build --sdist
curl -X PUT -H "X-Deploy-Secret: $DEPLOY_SECRET" \
  -F "file=@dist/keshro_mcp-0.1.0.tar.gz" \
  https://api.keshro.com/api/mcp/upload
```
