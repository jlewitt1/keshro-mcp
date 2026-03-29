# Keshro MCP

Keshro as an MCP server. Same plans, tasks, and execution tracking — exposed as tool calls for any MCP-compatible agent.

```bash
pip install keshro-mcp
```

## When to use this vs the CLI

**Use the CLI** (`pip install keshro`) if you want the full experience: parallel agent execution, git checkpoints, cross-task context routing, and execution orchestration built in.

**Use MCP** if your agent platform speaks MCP and you want direct tool-call access to Keshro plans and tasks.

The CLI does more. MCP is more flexible.

## Setup

Set your API token:

```bash
export KESHRO_API_TOKEN="ksh_pat_..."
```

Get one from [keshro.com/account](https://keshro.com/account?tab=api).

### Connect to your agent

MCP works with any agent that supports the protocol — Claude Code, Cline, Continue, Zed, and others.

**Claude Code** — add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "keshro": {
      "command": "keshro-mcp",
      "env": { "KESHRO_API_TOKEN": "ksh_pat_..." }
    }
  }
}
```

**Other MCP clients** — point your client at the `keshro-mcp` binary with `KESHRO_API_TOKEN` set in the environment. The server uses stdio transport.

## Available tools

| Tool | What it does |
|------|-------------|
| `list_plans` | List all plans |
| `get_plan` | Get a plan with all tasks |
| `next_task` | Get the next actionable task |
| `create_plan` | Create a new plan |
| `start_task` | Mark a task as in progress |
| `complete_task` | Mark a task as done |
| `block_task` | Mark a task as blocked |
| `unblock_task` | Clear a blocker |
| `append_task_note` | Add a note to a task |
| `add_task_artifact` | Attach an artifact link |
| `edit_task` | Edit task title or description |
| `export_project` | Export project data |

## License

MIT
