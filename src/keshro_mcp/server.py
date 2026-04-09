from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import KeshroApiError, KeshroClient, load_steps_from_json_file
from .config import load_settings

mcp = FastMCP("keshro")


def _run_with_client(callback):
    settings = load_settings()
    client = KeshroClient(settings)
    try:
        return callback(client)
    except KeshroApiError as exc:
        return {"error": str(exc)}
    finally:
        client.close()


@mcp.tool()
def list_templates(
    template_key: str | None = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    def _impl(client: KeshroClient):
        templates = client.list_templates()
        if template_key:
            for item in templates:
                if item.get("key") == template_key:
                    return item
            return {"error": f"Template not found: {template_key}"}
        return templates

    return _run_with_client(_impl)


@mcp.tool()
def list_projects(
    search: str | None = None,
    limit: int = 20,
    org_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    return _run_with_client(
        lambda client: client.list_projects(
            search=search,
            limit=limit,
            org_id=org_id,
            status=status,
        )
    )


@mcp.tool()
def list_plans(
    search: str | None = None,
    limit: int = 100,
    org_id: str | None = None,
) -> list[dict[str, Any]]:
    return _run_with_client(
        lambda client: client.list_plans(search=search, limit=limit, org_id=org_id)
    )


@mcp.tool()
def get_project(migration_id: str) -> dict[str, Any]:
    return _run_with_client(lambda client: client.get_project(migration_id))


@mcp.tool()
def get_plan(
    migration_id: str | None = None, plan_id: str | None = None
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.get_plan(plan_id=plan_id, migration_id=migration_id)
    )


@mcp.tool()
def next_task(plan_id: str) -> dict[str, Any]:
    return _run_with_client(lambda client: client.next_task(plan_id))


@mcp.tool()
def get_history(
    migration_id: str | None = None, plan_id: str | None = None
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.get_history(migration_id=migration_id, plan_id=plan_id)
    )


@mcp.tool()
def create_plan(
    migration_id: str,
    template_key: str | None = None,
    title: str | None = None,
    summary: str | None = None,
    plan_json_path: str | None = None,
    claude_text: str | None = None,
) -> dict[str, Any]:
    def _impl(client: KeshroClient):
        plan_steps = (
            load_steps_from_json_file(plan_json_path) if plan_json_path else None
        )
        return client.create_plan(
            migration_id=migration_id,
            template_key=template_key,
            title=title,
            summary=summary,
            plan_steps=plan_steps,
            claude_text=claude_text,
        )

    return _run_with_client(_impl)


@mcp.tool()
def update_plan(
    plan_id: str,
    title: str | None = None,
    summary: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.update_plan(
            plan_id, title=title, summary=summary, status=status
        )
    )


@mcp.tool()
def add_task(
    plan_id: str,
    title: str,
    description: str,
    status: str = "todo",
    owner: str | None = None,
    owner_user_id: str | None = None,
    notes: str | None = None,
    blocked_reason: str | None = None,
    issue_id: str | None = None,
    external_issue_id: str | None = None,
    external_issue_key: str | None = None,
    external_issue_provider: str | None = None,
    depends_on: list[str] | None = None,
    parallelizable: bool | None = None,
    executor: str | None = None,
    artifact_links: list[str] | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.add_task(
            plan_id,
            title=title,
            description=description,
            status=status,
            owner=owner,
            owner_user_id=owner_user_id,
            notes=notes,
            blocked_reason=blocked_reason,
            linear_issue_id=issue_id,
            external_issue_id=external_issue_id,
            external_issue_key=external_issue_key,
            external_issue_provider=external_issue_provider,
            depends_on=depends_on,
            parallelizable=parallelizable,
            executor=executor,
            artifact_links=artifact_links or [],
        )
    )


@mcp.tool()
def edit_task(
    plan_id: str,
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    owner: str | None = None,
    owner_user_id: str | None = None,
    notes: str | None = None,
    blocked_reason: str | None = None,
    issue_id: str | None = None,
    external_issue_id: str | None = None,
    external_issue_key: str | None = None,
    external_issue_provider: str | None = None,
    depends_on: list[str] | None = None,
    parallelizable: bool | None = None,
    executor: str | None = None,
    artifact_links: list[str] | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.edit_task(
            plan_id,
            task_id,
            title=title,
            description=description,
            status=status,
            owner=owner,
            owner_user_id=owner_user_id,
            notes=notes,
            blocked_reason=blocked_reason,
            linear_issue_id=issue_id,
            external_issue_id=external_issue_id,
            external_issue_key=external_issue_key,
            external_issue_provider=external_issue_provider,
            depends_on=depends_on,
            parallelizable=parallelizable,
            executor=executor,
            artifact_links=artifact_links,
        )
    )


@mcp.tool()
def start_task(
    plan_id: str,
    task_id: str,
    owner: str | None = None,
    owner_user_id: str | None = None,
    notes: str | None = None,
    feedback_reason: str | None = None,
    artifact_links: list[str] | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.start_task(
            plan_id,
            task_id,
            owner=owner,
            owner_user_id=owner_user_id,
            notes=notes,
            feedback_reason=feedback_reason,
            artifact_links=artifact_links,
        )
    )


@mcp.tool()
def complete_task(
    plan_id: str,
    task_id: str,
    notes: str | None = None,
    feedback_reason: str | None = None,
    artifact_links: list[str] | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.complete_task(
            plan_id,
            task_id,
            notes=notes,
            feedback_reason=feedback_reason,
            artifact_links=artifact_links,
        )
    )


@mcp.tool()
def block_task(
    plan_id: str,
    task_id: str,
    blocked_reason: str,
    feedback_reason: str | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.block_task(
            plan_id,
            task_id,
            blocked_reason=blocked_reason,
            feedback_reason=feedback_reason,
        )
    )


@mcp.tool()
def unblock_task(
    plan_id: str,
    task_id: str,
    notes: str | None = None,
    feedback_reason: str | None = None,
    status: str = "in_progress",
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.unblock_task(
            plan_id,
            task_id,
            notes=notes,
            feedback_reason=feedback_reason,
            status=status,
        )
    )


@mcp.tool()
def append_task_note(
    plan_id: str,
    task_id: str,
    note: str,
    feedback_reason: str | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.append_task_note(
            plan_id,
            task_id,
            note=note,
            feedback_reason=feedback_reason,
        )
    )


@mcp.tool()
def add_task_artifact(
    plan_id: str,
    task_id: str,
    artifact_link: str,
    feedback_reason: str | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.add_task_artifact(
            plan_id,
            task_id,
            artifact_link=artifact_link,
            feedback_reason=feedback_reason,
        )
    )


@mcp.tool()
def append_replan_note(plan_id: str, note: str) -> dict[str, Any]:
    return _run_with_client(lambda client: client.append_replan_note(plan_id, note))


@mcp.tool()
def generate_plan(
    description: str,
    title: str | None = None,
    project_type: str = "generic",
    repo: str | None = None,
    discovered_context: str | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.generate_plan(
            description,
            title=title,
            project_type=project_type,
            repo=repo,
            discovered_context=discovered_context,
        )
    )


@mcp.tool()
def preview_plan(
    description: str,
    title: str | None = None,
    project_type: str = "generic",
    repo: str | None = None,
    discovered_context: str | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.preview_plan(
            description,
            title=title,
            project_type=project_type,
            repo=repo,
            discovered_context=discovered_context,
        )
    )


@mcp.tool()
def plan_status(plan_id: str) -> dict[str, Any]:
    return _run_with_client(lambda client: client.plan_status(plan_id))


@mcp.tool()
def record_decision(
    plan_id: str,
    task_id: str,
    context: str,
    choice: str,
    reasoning: str,
    alternatives: list[str] | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.record_decision(
            plan_id,
            task_id,
            context=context,
            choice=choice,
            reasoning=reasoning,
            alternatives=alternatives,
        )
    )


@mcp.tool()
def push_to_tracker(
    plan_id: str,
    provider: str = "linear",
    team_id: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.push_to_tracker(
            plan_id, provider=provider, team_id=team_id, project_id=project_id
        )
    )


@mcp.tool()
def sync_pull(plan_id: str) -> dict[str, Any]:
    return _run_with_client(lambda client: client.sync_pull(plan_id))


@mcp.tool()
def export_project(migration_id: str) -> str | dict[str, Any]:
    return _run_with_client(lambda client: client.export_project(migration_id))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
