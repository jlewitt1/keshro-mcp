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
