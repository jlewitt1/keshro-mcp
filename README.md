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

## Recommended execution loop

Use the MCP tools for the same execution loop that the CLI now drives with `keshro continue` or `keshro agent-prompt`:

1. `get_project(migration_id=...)`
2. `get_plan(plan_id=...)`
3. `next_task(plan_id=...)`
4. `start_task(plan_id=..., task_id=...)`
5. `append_task_note(...)` and `add_task_artifact(...)` as work progresses
6. `block_task(...)` when a real blocker appears
7. `unblock_task(...)` when the blocker is cleared
8. `append_replan_note(...)` if the migration shape changes
9. `complete_task(...)` once the task is actually done

MCP is best when you want Keshro available as tools inside the agent loop. For the normal Claude Code terminal workflow, prefer the CLI. Use MCP when you specifically want tool-based reads and writes inside the agent itself.

## Event behavior

Use the MCP tools as the live execution-write path while Claude is working.

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

Concrete examples:

- Claude starts on the next task:
  - `start_task(plan_id=..., task_id=...)`
- Claude discovers a meaningful execution detail:
  - `append_task_note(plan_id=..., task_id=..., note="Airflow will orchestrate Batch during pilot")`
- Claude opens a PR or issue:
  - `add_task_artifact(plan_id=..., task_id=..., artifact_link="<url>")`
- Claude hits a real blocker:
  - `block_task(plan_id=..., task_id=..., blocked_reason="Waiting on Terraform IAM role changes")`
- Claude resumes after the blocker is cleared:
  - `unblock_task(plan_id=..., task_id=..., notes="IAM fix applied; resuming pilot")`
- Claude believes the task is done:
  - ask first, then `complete_task(plan_id=..., task_id=..., notes="<what landed>")`
