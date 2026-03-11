from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from .config import Settings


class KeshroApiError(RuntimeError):
    pass


class KeshroClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = httpx.Client(
            base_url=settings.api_url,
            timeout=settings.timeout_seconds,
            headers={
                "Authorization": f"Bearer {settings.api_token}",
                "Content-Type": "application/json",
            },
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, *, json_body: Any | None = None) -> Any:
        try:
            response = self._client.request(method, path, json=json_body)
        except httpx.HTTPError as exc:
            raise KeshroApiError(f"Keshro request failed: {exc}") from exc
        if response.status_code >= 400:
            detail = None
            try:
                payload = response.json()
                detail = payload.get("detail") if isinstance(payload, dict) else None
            except Exception:
                detail = response.text.strip() or None
            message = detail or response.reason_phrase
            raise KeshroApiError(f"Keshro API error ({response.status_code}): {message}")
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def list_templates(self) -> list[dict[str, Any]]:
        return self._request("GET", "/plans/templates")

    def get_project(self, migration_id: str) -> dict[str, Any]:
        project = self._request("GET", f"/migrations/{migration_id}")
        try:
            plan = self._request("GET", f"/migrations/{migration_id}/plan")
        except KeshroApiError:
            plan = None
        try:
            run_outcome = self._request("GET", f"/migrations/{migration_id}/outcomes")
        except KeshroApiError:
            run_outcome = None
        if plan:
            try:
                plan_outcome = self._request("GET", f"/plans/{plan['id']}/outcome")
            except KeshroApiError:
                plan_outcome = None
        else:
            plan_outcome = None
        return {
            "project": project,
            "execution_plan": plan,
            "execution_outcome": plan_outcome,
            "analysis_run_feedback": run_outcome,
        }

    def get_plan(self, *, plan_id: str | None = None, migration_id: str | None = None) -> dict[str, Any]:
        if plan_id:
            plan = self._request("GET", f"/plans/{plan_id}")
        elif migration_id:
            plan = self._request("GET", f"/migrations/{migration_id}/plan")
        else:
            raise KeshroApiError("Either plan_id or migration_id is required")
        try:
            outcome = self._request("GET", f"/plans/{plan['id']}/outcome")
        except KeshroApiError:
            outcome = None
        return {"plan": plan, "outcome": outcome}

    def create_plan(
        self,
        *,
        migration_id: str,
        title: str | None = None,
        summary: str | None = None,
        template_key: str | None = None,
        plan_steps: list[dict[str, Any]] | None = None,
        claude_text: str | None = None,
    ) -> dict[str, Any]:
        if template_key:
            payload: dict[str, Any] = {"migration_id": migration_id, "template_key": template_key}
            if title:
                payload["title"] = title
            if summary:
                payload["summary"] = summary
            return self._request("POST", "/plans/from-template", json_body=payload)

        payload = {
            "migration_id": migration_id,
            "title": title or "Execution Plan",
            "summary": summary,
            "plan_steps": plan_steps or _steps_from_claude_text(claude_text),
        }
        return self._request("POST", "/plans", json_body=payload)

    def update_plan(self, plan_id: str, **fields: Any) -> dict[str, Any]:
        payload = {key: value for key, value in fields.items() if value is not None}
        return self._request("PATCH", f"/plans/{plan_id}", json_body=payload)

    def add_task(self, plan_id: str, **fields: Any) -> dict[str, Any]:
        payload = {key: value for key, value in fields.items() if value is not None}
        return self._request("POST", f"/plans/{plan_id}/tasks", json_body=payload)

    def edit_task(self, plan_id: str, task_id: str, **fields: Any) -> dict[str, Any]:
        payload = {key: value for key, value in fields.items() if value is not None}
        return self._request("PATCH", f"/plans/{plan_id}/tasks/{task_id}", json_body=payload)

    def save_outcome(self, plan_id: str, **fields: Any) -> dict[str, Any]:
        payload = {key: value for key, value in fields.items() if value is not None}
        return self._request("POST", f"/plans/{plan_id}/outcome", json_body=payload)

    def export_project(self, migration_id: str) -> str:
        data = self.get_project(migration_id)
        project = data.get("project") or {}
        plan = data.get("execution_plan") or {}
        plan_outcome = data.get("execution_outcome") or {}
        run_feedback = data.get("analysis_run_feedback") or {}
        lines: list[str] = []
        lines.append(f"# Migration Project: {project.get('source_type', 'Unknown')} -> {project.get('target_type', 'Unknown')}")
        lines.append("")
        lines.append("## Analysis")
        lines.append("")
        for key in ("status", "created_at", "confidence_score", "analysis_revision", "outcome_status"):
            value = project.get(key)
            if value is not None:
                lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        if project.get("notes"):
            lines.append("")
            lines.append(project["notes"].strip())
        if project.get("risks"):
            lines.append("")
            lines.append("### Risks")
            for risk in project["risks"]:
                lines.append(f"- {risk.get('title', 'Untitled risk')} [{risk.get('severity', 'unknown')}]")
        if project.get("unknowns"):
            lines.append("")
            lines.append("### Unknowns")
            for unknown in project["unknowns"]:
                lines.append(f"- {unknown.get('question', 'Unknown question')} ({unknown.get('priority', 'unknown')})")
                if unknown.get("answer"):
                    lines.append(f"  - Answer: {unknown['answer']}")
        if project.get("context"):
            lines.append("")
            lines.append("## Context")
            lines.append("")
            lines.append(project["context"].strip())
        lines.append("")
        lines.append("## Execution Plan")
        lines.append("")
        if not plan:
            lines.append("No execution plan created.")
        else:
            lines.append(f"- Status: {plan.get('status', 'unknown')}")
            if plan.get("template_key"):
                lines.append(f"- Template: {plan['template_key']}")
            if plan.get("summary"):
                lines.append(f"- Summary: {plan['summary']}")
            lines.append("")
            for step in plan.get("plan_steps", []):
                lines.append(f"- {step.get('order', '?')}. {step.get('title', 'Untitled')} [{step.get('status', 'todo')}]")
                if step.get("owner"):
                    lines.append(f"  - Owner: {step['owner']}")
                if step.get("blocked_reason"):
                    lines.append(f"  - Blocked: {step['blocked_reason']}")
                if step.get("description"):
                    lines.append(f"  - {step['description']}")
        lines.append("")
        lines.append("## Execution Outcomes")
        lines.append("")
        if plan_outcome:
            for key in ("status", "summary", "actual_hours", "actual_cost", "notes"):
                value = plan_outcome.get(key)
                if value is not None:
                    lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        else:
            lines.append("No execution outcome recorded.")
        if run_feedback:
            lines.append("")
            lines.append("## Analysis Run Feedback")
            lines.append("")
            for key in ("outcome_status", "actual_hours", "actual_cost", "downtime_minutes", "notes"):
                value = run_feedback.get(key)
                if value is not None:
                    lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(lines).strip() + "\n"


def _steps_from_claude_text(text: str | None) -> list[dict[str, Any]]:
    if not text:
        return []
    steps: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("- ", "* ")):
            title = line[2:].strip()
            if title:
                steps.append({"title": title, "description": title, "status": "todo"})
    return steps


def load_steps_from_json_file(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("plan_steps"), list):
        return data["plan_steps"]
    raise KeshroApiError("Plan file must be a JSON array of steps or an object with plan_steps")
