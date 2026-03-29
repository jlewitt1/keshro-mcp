# Keshro MCP

`keshro-mcp` exposes Keshro plans, tasks, and project state as MCP tools.

Use it when you want a tool-based Keshro integration inside an MCP-compatible agent environment instead of the standard terminal CLI flow.

## When to use this

Use `keshro-mcp` if:

- your agent platform speaks MCP
- you want tool calls instead of CLI commands
- you are integrating Keshro into an existing MCP toolchain

For most users, the CLI is still the better default:

```bash
keshro continue -p <plan-id>
```

The CLI handles execution flow, agent coordination, and task guidance automatically. MCP is more flexible, but thinner.

## What it provides

The MCP server exposes Keshro data and plan actions as tools, including:

- listing projects and plans
- reading plan details and tasks
- getting the next actionable task
- creating and updating plans
- starting, completing, blocking, and unblocking tasks
- appending task notes and artifacts
- exporting project data

## Install

```bash
pip install keshro-mcp
```

Or from source:

```bash
git clone https://github.com/jlewitt1/keshro-mcp.git
cd keshro-mcp
pip install -e .
```

## Configuration

Set these environment variables:

```bash
export KESHRO_API_TOKEN="ksh_pat_..."
```

Get your token from **Account -> API** at [keshro.com](https://keshro.com).

`KESHRO_API_URL` defaults to `https://api.keshro.com` — only override for self-hosted or local dev.

## Run

```bash
keshro-mcp
```

Or:

```bash
python -m keshro_mcp.server
```

## Claude Code example

Add this to `~/.claude.json`:

```json
{
  "mcpServers": {
    "keshro": {
      "command": "keshro-mcp",
      "env": {
        "KESHRO_API_URL": "https://api.keshro.com",
        "KESHRO_API_TOKEN": "ksh_pat_..."
      }
    }
  }
}
```

Then restart Claude Code and run `/mcp` to confirm the server is connected.

## Available tools

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects |
| `list_plans` | List all plans |
| `list_templates` | List available plan templates |
| `get_project` | Get project details |
| `get_plan` | Get a plan with all tasks |
| `next_task` | Get the next actionable task |
| `create_plan` | Create a new plan |
| `update_plan` | Update plan metadata |
| `add_task` | Add a task to a plan |
| `edit_task` | Edit task title or description |
| `start_task` | Mark a task as in progress |
| `complete_task` | Mark a task as done |
| `block_task` | Mark a task as blocked |
| `unblock_task` | Clear a blocker |
| `append_task_note` | Add a note to a task |
| `add_task_artifact` | Attach an artifact link |
| `append_replan_note` | Add a replan note |
| `export_project` | Export project data |

## CLI vs MCP

| | CLI (`keshro continue`) | MCP |
|---|---|---|
| **Primary interface** | Terminal and agent-in-chat workflows | MCP tool calls |
| **Setup** | `pip install keshro` + `keshro login` | `pip install keshro-mcp` + MCP config |
| **Execution guidance** | Built in | Agent must orchestrate it |
| **Parallel agent launching** | Built in | External orchestration required |
| **Git checkpoints** | Built in | External orchestration required |
| **Task handoff/context routing** | Built in | Agent must implement |
| **Best for** | Most users | Custom MCP environments |

## Notes

`keshro-mcp` is intentionally a thinner layer than the CLI.

It gives agents structured access to Keshro state, but it does not try to replace the CLI’s coordinator behaviors like:

- parallel worktree launching
- execution prompt shaping
- checkpoint management
- automatic execution flow

If you want the most opinionated Keshro experience, use the CLI.
