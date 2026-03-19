# Keshro MCP

`keshro-mcp` is a thin MCP server over the private Keshro API. It lets Claude or another MCP client read and update Keshro Migration Projects without moving business logic out of the hosted backend.

> **For most users, the CLI is the recommended way to use Keshro with Claude Code.** Run `keshro continue -p <plan-id>` in your terminal — it handles auth, fetches the plan, and gives Claude the execution context automatically. Use MCP only if you specifically need tool-based integration inside an MCP-compatible agent environment.

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

## Publishing a new MCP version

### Via GitHub Actions (recommended)

1. Update the version in `pyproject.toml` and push
2. Go to Actions → "Publish MCP" → Run workflow
3. Select production or staging and run

Requires `DEPLOY_SECRET` in the repo's GitHub secrets (must match the `DEPLOY_SECRET` env var on the backend).

### Manual

1. Update the version in `pyproject.toml`
2. Build: `python -m build --sdist`
3. Upload:
   ```bash
   curl -X PUT -H "X-Deploy-Secret: $DEPLOY_SECRET" \
     -F "file=@dist/keshro_mcp-0.1.0.tar.gz" \
     https://api.keshro.com/api/mcp/upload
   ```

## Exposed tools

- `list_templates`
- `list_projects`
- `list_plans`
- `get_project`
- `get_plan`
- `next_task`
- `get_history`
- `create_plan`
- `update_plan`
- `add_task`
- `edit_task`
- `start_task`
- `complete_task`
- `block_task`
- `unblock_task`
- `append_task_note`
- `add_task_artifact`
- `append_replan_note`
- `export_project`

## Tooling model

- Keshro remains the system of record.
- The MCP server only wraps the existing Keshro API.
- Claude or another agent can pull project/plan state, refine it from repo context, and sync changes back.
- Pre-analysis follow-up questions should stay product-owned as structured `AskUserQuestions` data rather than vendor-specific interactive prompts, so the same question set can be reused in the web app, CLI, or MCP workflows.

## CLI vs MCP

| | CLI (`keshro continue`) | MCP |
|---|---|---|
| **Setup** | `pip install keshro` + `keshro login` | Clone repo, configure `~/.claude.json`, restart Claude Code |
| **How it works** | Prints execution prompt to stdout; Claude reads and follows | Claude calls MCP tools directly |
| **Auth** | CLI handles it automatically | Requires `KESHRO_API_TOKEN` in env config |
| **Best for** | Claude Code terminal workflow (recommended) | Non-CLI agent environments, or when you want Keshro as tools inside the agent loop |
| **Task handoff** | Built into the prompt (asks user before continuing) | Agent must implement its own handoff logic |
| **Session history** | Includes prior task progress so Claude knows what was already done | Agent must track this itself |
| **Git checkpoints** | Auto-creates checkpoint commits before each task | Agent must implement this itself |
| **Validation** | Prompts Claude to verify changes before marking done | Agent must implement this itself |
| **Multi-repo** | `--dir` flag to point Claude at a different codebase | N/A |

## Claude Code MCP Setup

> **Prefer the CLI instead.** Install the `keshro` CLI, run `keshro login`, then `keshro continue -p <plan-id>` in your Claude Code terminal. No MCP config needed.

If you still want MCP:

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

*Note: For local development use `http://localhost:8000/api"`*

### 4. Restart Claude Code and verify

```
/exit
claude
/mcp
```

You should see **Keshro MCP Server · ✔ connected** with 19 tools available.

### First test

Ask Claude Code to `list all keshro templates` to confirm everything is working.

## Execution loop (MCP)

If you are using MCP instead of the CLI, follow this loop:

1. `get_project(migration_id=...)`
2. `get_plan(plan_id=...)`
3. `next_task(plan_id=...)`
4. `start_task(plan_id=..., task_id=...)`
5. `append_task_note(...)` and `add_task_artifact(...)` as work progresses
6. `block_task(...)` when a real blocker appears
7. `unblock_task(...)` when the blocker is cleared
8. `append_replan_note(...)` if the migration shape changes
9. `complete_task(...)` once the task is actually done — ask the user first

## Event behavior

Write immediately:

- `start_task`
- `append_task_note`
- `add_task_artifact`
- `block_task`
- `unblock_task`

Ask first:

- `complete_task`
- major replans that materially change scope or sequencing

Important:

- `next_task` returns the next actionable task, preferring `in_progress` tasks first and then `todo` tasks.
- Do not automatically move past a blocked task unless the plan clearly supports parallel or out-of-order work.
- After completing a task, summarize what was accomplished and ask the user before continuing to the next task.
