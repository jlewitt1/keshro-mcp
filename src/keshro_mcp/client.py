from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from .config import Settings


class KeshroApiError(RuntimeError):
    pass


EXPORT_FORMAT = "keshro-plan-json"
EXPORT_SCHEMA_VERSION = "1"


class KeshroClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = httpx.Client(
            base_url=settings.api_url,
            timeout=settings.timeout_seconds,
            headers={
                "Authorization": f"Bearer {settings.api_token}",
                "Content-Type": "application/json",
                "X-Keshro-Client": "mcp",
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
            raise KeshroApiError(
                f"Keshro API error ({response.status_code}): {message}"
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def list_templates(self) -> list[dict[str, Any]]:
        return self._request("GET", "/plans/templates")

    def list_projects(
        self,
        *,
        limit: int = 20,
        org_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        params: list[str] = [f"limit={limit}"]
        if org_id:
            params.append(f"org_id={org_id}")
        if status:
            params.append(f"status={status}")
        path = "/migrations"
        if params:
            path += "?" + "&".join(params)
        items = self._request("GET", path)
        if not search:
            return items
        query = search.strip().lower()
        return [
            item
            for item in items
            if query in (item.get("id") or "").lower()
            or query in (item.get("source_type") or "").lower()
            or query in (item.get("target_type") or "").lower()
            or query in (item.get("status") or "").lower()
        ]

    def list_plans(
        self,
        *,
        limit: int = 100,
        org_id: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        params: list[str] = [f"limit={limit}"]
        if org_id:
            params.append(f"org_id={org_id}")
        path = "/plans"
        if params:
            path += "?" + "&".join(params)
        items = self._request("GET", path)
        if not search:
            return items
        query = search.strip().lower()
        return [
            item
            for item in items
            if query in (item.get("id") or "").lower()
            or query in (item.get("migration_id") or "").lower()
            or query in (item.get("title") or "").lower()
            or query in (item.get("source_type") or "").lower()
            or query in (item.get("target_type") or "").lower()
            or query in (item.get("template_key") or "").lower()
            or query in (item.get("summary") or "").lower()
        ]

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

    def get_plan(
        self, *, plan_id: str | None = None, migration_id: str | None = None
    ) -> dict[str, Any]:
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
            payload: dict[str, Any] = {
                "migration_id": migration_id,
                "template_key": template_key,
            }
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
        return self._request(
            "PATCH", f"/plans/{plan_id}/tasks/{task_id}", json_body=payload
        )

    def save_outcome(self, plan_id: str, **fields: Any) -> dict[str, Any]:
        payload = {key: value for key, value in fields.items() if value is not None}
        return self._request("POST", f"/plans/{plan_id}/outcome", json_body=payload)

    def export_project(self, migration_id: str) -> dict[str, Any]:
        data = self.get_project(migration_id)
        project = data.get("project") or {}
        plan = data.get("execution_plan") or {}
        plan_outcome = data.get("execution_outcome") or {}
        run_feedback = data.get("analysis_run_feedback") or {}
        return {
            "kind": "keshro.project.export",
            "format": EXPORT_FORMAT,
            "schema_version": EXPORT_SCHEMA_VERSION,
            "exported_at": _utc_now(),
            "project": {
                "migration_id": project.get("id"),
                "source_type": project.get("source_type"),
                "target_type": project.get("target_type"),
                "status": project.get("status"),
                "migration_mode": project.get("migration_mode"),
                "input_method": project.get("input_method"),
                "org_id": project.get("org_id"),
                "created_at": project.get("created_at"),
                "github_url": project.get("github_url"),
                "resource_url": project.get("resource_url"),
            },
            "analysis": {
                "confidence_score": project.get("confidence_score"),
                "confidence_explanation": project.get("confidence_explanation"),
                "analysis_revision": project.get("analysis_revision"),
                "similar_migrations_used": project.get("similar_migrations_used"),
                "notes": project.get("notes"),
                "risks": project.get("risks") or [],
                "unknowns": project.get("unknowns") or [],
                "migration_steps": project.get("migration_steps") or [],
                "migration_script": project.get("migration_script"),
                "assessment_quality": project.get("assessment_quality"),
                "context": project.get("context"),
                "custom_fields": project.get("custom_fields") or {},
            },
            "execution_plan": plan or None,
            "execution_outcome": plan_outcome or None,
            "analysis_run_feedback": run_feedback or None,
            "adapter_hints": {
                "canonical_task_id_field": "id",
                "canonical_task_status_field": "status",
                "owner_fields": ["owner_user_id", "owner"],
                "external_issue_fields": ["linear_issue_id", "artifact_links"],
                "supported_targets": ["linear", "jira"],
            },
        }


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


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
    raise KeshroApiError(
        "Plan file must be a JSON array of steps or an object with plan_steps"
    )
