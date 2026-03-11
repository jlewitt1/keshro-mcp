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
    linear_issue_id: str | None = None,
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
            linear_issue_id=linear_issue_id,
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
    linear_issue_id: str | None = None,
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
            linear_issue_id=linear_issue_id,
            artifact_links=artifact_links,
        )
    )


@mcp.tool()
def save_outcome(
    plan_id: str,
    status: str,
    summary: str,
    actual_hours: int | None = None,
    actual_cost: int | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return _run_with_client(
        lambda client: client.save_outcome(
            plan_id,
            status=status,
            summary=summary,
            actual_hours=actual_hours,
            actual_cost=actual_cost,
            notes=notes,
        )
    )


@mcp.tool()
def export_project(migration_id: str) -> str | dict[str, Any]:
    return _run_with_client(lambda client: client.export_project(migration_id))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
