# Keshro MCP

`keshro-mcp` is a thin MCP server over the private Keshro API. It lets Claude or another MCP client read and update Keshro Migration Projects without moving business logic out of the hosted backend.

## Status

This package is intended to expose Keshro as a planning and sync surface, not as the migration executor.

## Setup

Set these environment variables before starting the server:

```bash
export KESHRO_API_URL="http://localhost:8000/api"
export KESHRO_API_TOKEN="ksh_pat_..."
```

Optional:

```bash
export KESHRO_API_TIMEOUT="30"
```

## Run

```bash
python -m keshro_mcp.server
```

Or after install:

```bash
keshro-mcp
```

## Exposed tools

- `list_templates`
- `get_project`
- `get_plan`
- `create_plan`
- `update_plan`
- `add_task`
- `edit_task`
- `save_outcome`
- `export_project`

## Tooling model

- Keshro remains the system of record.
- The MCP server only wraps the existing Keshro API.
- Claude or another agent can pull project/plan state, refine it from repo context, and sync changes back.


## Claude Code MCP Setup

Use Keshro directly from Claude Code via MCP.

### 1. Clone and install

```bash
git clone https://github.com/jlewitt1/keshro-mcp.git
cd keshro-mcp
python -m venv .venv
.venv/bin/pip install -e .
```

### 2. Get an API token

Log into the Keshro web app and go to **Account → API** to create a token.

### 3. Add to Claude Code config

Add the following to `~/.claude.json`, merging into any existing content:

```json
{
  "mcpServers": {
    "keshro": {
      "command": "/path/to/keshro-mcp/.venv/bin/python",
      "args": ["-m", "keshro_mcp.server"],
      "env": {
        "KESHRO_API_URL": "https://api.keshro.com",
        "KESHRO_API_TOKEN": "ksh_pat_..."
      }
    }
  }
}
```

Replace:
- `/path/to/keshro-mcp` with the absolute path to your clone
- `KESHRO_API_URL` with your Keshro instance URL
- `KESHRO_API_TOKEN` with your token from step 2

### 4. Restart Claude Code and verify

```
/exit
claude
/mcp
```

You should see **Keshro MCP Server · ✔ connected** with 9 tools available.

### First test

Ask Claude Code to `list all keshro templates` to confirm everything is working.
