# Keshro MCP

The intelligent execution layer for coding agents, exposed as an MCP server for high-stakes engineering projects.

```bash
pip install keshro-mcp
```

## When to use this vs the CLI

**Use the [CLI](https://github.com/jlewitt1/keshro-cli)** (`pip install keshro`) for the full experience: interactive clarifying questions, migration detection, parallel execution in isolated worktrees, git checkpoints, cross-task context routing, and cost tracking.

**Use MCP** if your agent platform speaks MCP and you want direct tool-call access to Keshro plans and tasks.

The CLI gives you more control. MCP is more flexible for custom integrations.

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
| `preview_plan` | Run Keshro's pre-plan intake and clarifying-question preview |
| `generate_plan` | Generate a plan from a description using AI |
| `list_plans` | List all plans |
| `get_plan` | Get a plan with all tasks |
| `plan_status` | Progress summary (task counts, enrichment sources) |
| `next_task` | Get the next actionable task |
| `create_plan` | Create a plan manually |
| `start_task` | Mark a task as in progress |
| `complete_task` | Mark a task as done |
| `block_task` | Mark a task as blocked |
| `unblock_task` | Clear a blocker |
| `append_task_note` | Add a note to a task |
| `add_task_artifact` | Attach an artifact link |
| `record_decision` | Log a decision with context, choice, and reasoning |
| `edit_task` | Edit task title or description |
| `push_to_tracker` | Push tasks to Linear, Jira, or GitHub as issues |
| `sync_pull` | Pull status updates from connected issue tracker |
| `export_project` | Export project data |

## Current parity notes

MCP now supports the newer task controls exposed in the web product:

- explicit `depends_on` task dependencies
- `parallelizable` task scheduling hints
- per-task `executor` selection
- generic issue linking via `issue_id`, plus external issue fields
- pre-plan intake via `preview_plan`

It still remains thinner than the CLI for actual execution orchestration. The CLI owns parallel local worktrees, git checkpoints, richer execution transcripts, and the direct `keshro continue` runtime loop.

## License

MIT
# Releases

Publish the MCP package with one GitHub Actions run after you bump `pyproject.toml`:

```bash
gh workflow run "Publish MCP"
```

That workflow reads the package version from `pyproject.toml`, publishes the package to PyPI, then creates the matching `vX.Y.Z` GitHub release automatically.
