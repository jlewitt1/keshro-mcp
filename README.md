# Keshro MCP

MCP server for Keshro — the intelligent execution layer for coding agents. Exposes Keshro plans, tasks, and project state as MCP tools for any MCP-compatible agent.

> **For most users, the CLI is recommended.** Run `keshro continue -p <plan-id>` — it handles auth, fetches the plan, and gives your agent the execution context automatically. Use MCP only if you need tool-based integration inside an MCP-compatible environment.

## Install

```bash
pip install keshro-mcp
```

## Setup

```bash
export KESHRO_API_URL="https://api.keshro.com"
export KESHRO_API_TOKEN="ksh_pat_..."
```

Get your token from **Account → API** in the Keshro app.

## Run

```bash
keshro-mcp
# or: python -m keshro_mcp.server
```

## Claude Code setup

Add to `~/.claude.json`:

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

Restart Claude Code and run `/mcp` to verify — you should see **Keshro MCP Server** connected.

## Tools

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects |
| `list_plans` | List all plans |
| `list_templates` | List available plan templates |
| `get_project` | Get project details |
| `get_plan` | Get plan with all tasks |
| `next_task` | Get the next actionable task |
| `create_plan` | Create a new plan |
| `update_plan` | Update plan metadata |
| `add_task` | Add a task to a plan |
| `edit_task` | Edit task title/description |
| `start_task` | Mark task as in progress |
| `complete_task` | Mark task as done |
| `block_task` | Mark task as blocked |
| `unblock_task` | Clear a blocker |
| `append_task_note` | Add a note to a task |
| `add_task_artifact` | Attach an artifact link |
| `append_replan_note` | Add a replan note |
| `export_project` | Export project data |

## CLI vs MCP

| | CLI (`keshro continue`) | MCP |
|---|---|---|
| **Setup** | `pip install keshro` + `keshro login` | `pip install keshro-mcp` + configure `~/.claude.json` |
| **How it works** | Prints execution prompt to stdout; agent reads and follows | Agent calls MCP tools directly |
| **Parallel agents** | Built-in — launches concurrent agents in git worktrees | Agent must coordinate externally |
| **Topical context** | Built-in — learnings route by domain tag automatically | Agent must implement |
| **Git checkpoints** | Built-in — auto-commit before each task | Agent must implement |
| **Validation gates** | Built-in — verifies changes before marking done | Agent must implement |
| **Task handoff** | Built-in — "Next task should know" notes flow automatically | Agent must implement |
| **Best for** | Claude Code terminal workflow (recommended) | Non-CLI agent environments |
