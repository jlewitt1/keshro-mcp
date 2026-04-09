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
        return {
            "project": project,
            "execution_plan": plan,
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
        return {"plan": plan}

    def next_task(self, plan_id: str) -> dict[str, Any]:
        plan_bundle = self.get_plan(plan_id=plan_id)
        plan = plan_bundle.get("plan") or {}
        steps = sorted(
            plan.get("plan_steps") or [], key=lambda step: step.get("order", 0)
        )
        completed_ids = {
            s.get("id")
            for s in steps
            if (s.get("status") or "todo").strip().lower() == "completed"
        }

        def _deps_met(step: dict) -> bool:
            for dep in step.get("depends_on") or []:
                if dep not in completed_ids:
                    return False
            return True

        # Prefer in_progress first (resume), then first todo with deps met
        task = None
        for desired_status in ("in_progress", "todo"):
            task = next(
                (
                    step
                    for step in steps
                    if (step.get("status") or "todo").strip().lower() == desired_status
                    and (desired_status == "in_progress" or _deps_met(step))
                ),
                None,
            )
            if task:
                break
        return {
            "plan_id": plan_id,
            "task": task,
        }

    def get_history(
        self, *, migration_id: str | None = None, plan_id: str | None = None
    ) -> dict[str, Any]:
        if plan_id:
            plan_bundle = self.get_plan(plan_id=plan_id)
            plan = plan_bundle.get("plan") or {}
            return {
                "migration_id": plan.get("migration_id"),
                "plan_id": plan.get("id"),
                "task_feedback_events": plan.get("task_feedback_events") or [],
            }
        if migration_id:
            project = self.get_project(migration_id)
            plan = project.get("execution_plan") or {}
            return {
                "migration_id": migration_id,
                "plan_id": plan.get("id"),
                "task_feedback_events": plan.get("task_feedback_events") or [],
            }
        raise KeshroApiError("Either migration_id or plan_id is required")

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

    def start_task(self, plan_id: str, task_id: str, **fields: Any) -> dict[str, Any]:
        payload = {
            "status": "in_progress",
            **{key: value for key, value in fields.items() if value is not None},
        }
        return self._request(
            "PATCH", f"/plans/{plan_id}/tasks/{task_id}", json_body=payload
        )

    def complete_task(
        self, plan_id: str, task_id: str, **fields: Any
    ) -> dict[str, Any]:
        payload = {
            "status": "completed",
            "blocked_reason": "",
            **{key: value for key, value in fields.items() if value is not None},
        }
        return self._request(
            "PATCH", f"/plans/{plan_id}/tasks/{task_id}", json_body=payload
        )

    def append_replan_note(self, plan_id: str, note: str) -> dict[str, Any]:
        plan_bundle = self.get_plan(plan_id=plan_id)
        plan = plan_bundle.get("plan") or {}
        existing_summary = (plan.get("summary") or "").strip()
        note_line = f"[replan] {note.strip()}"
        summary = (
            f"{existing_summary}\n\n{note_line}".strip()
            if existing_summary
            else note_line
        )
        return self._request(
            "PATCH", f"/plans/{plan_id}", json_body={"summary": summary}
        )

    def block_task(self, plan_id: str, task_id: str, **fields: Any) -> dict[str, Any]:
        payload = {
            "status": "blocked",
            **{key: value for key, value in fields.items() if value is not None},
        }
        return self._request(
            "PATCH", f"/plans/{plan_id}/tasks/{task_id}", json_body=payload
        )

    def unblock_task(self, plan_id: str, task_id: str, **fields: Any) -> dict[str, Any]:
        payload = {
            "status": fields.pop("status", "in_progress"),
            "blocked_reason": "",
            **{key: value for key, value in fields.items() if value is not None},
        }
        return self._request(
            "PATCH", f"/plans/{plan_id}/tasks/{task_id}", json_body=payload
        )

    def append_task_note(
        self, plan_id: str, task_id: str, note: str, feedback_reason: str | None = None
    ) -> dict[str, Any]:
        plan_bundle = self.get_plan(plan_id=plan_id)
        plan = plan_bundle.get("plan") or {}
        task = next(
            (
                step
                for step in (plan.get("plan_steps") or [])
                if step.get("id") == task_id
            ),
            None,
        )
        if not task:
            raise KeshroApiError(f"Task not found: {task_id}")
        existing_notes = str(task.get("notes") or "").strip()
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        next_notes = (
            f"{existing_notes}\n\n[{timestamp}] {note.strip()}".strip()
            if existing_notes
            else f"[{timestamp}] {note.strip()}"
        )
        payload: dict[str, Any] = {"notes": next_notes}
        if feedback_reason:
            payload["feedback_reason"] = feedback_reason
        return self._request(
            "PATCH", f"/plans/{plan_id}/tasks/{task_id}", json_body=payload
        )

    def add_task_artifact(
        self,
        plan_id: str,
        task_id: str,
        artifact_link: str,
        feedback_reason: str | None = None,
    ) -> dict[str, Any]:
        plan_bundle = self.get_plan(plan_id=plan_id)
        plan = plan_bundle.get("plan") or {}
        task = next(
            (
                step
                for step in (plan.get("plan_steps") or [])
                if step.get("id") == task_id
            ),
            None,
        )
        if not task:
            raise KeshroApiError(f"Task not found: {task_id}")
        existing_links = [
            str(link).strip()
            for link in (task.get("artifact_links") or [])
            if str(link).strip()
        ]
        next_link = artifact_link.strip()
        next_links = (
            existing_links
            if next_link in existing_links
            else [*existing_links, next_link]
        )
        payload: dict[str, Any] = {"artifact_links": next_links}
        if feedback_reason:
            payload["feedback_reason"] = feedback_reason
        return self._request(
            "PATCH", f"/plans/{plan_id}/tasks/{task_id}", json_body=payload
        )

    def generate_plan(
        self,
        description: str,
        *,
        title: str | None = None,
        project_type: str = "generic",
        repo: str | None = None,
        discovered_context: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "description": description,
            "project_type": project_type,
        }
        if title:
            payload["title"] = title
        if repo:
            payload["repo"] = repo
        if discovered_context:
            payload["discovered_context"] = discovered_context
        return self._request("POST", "/plans/generate", json_body=payload)

    def preview_plan(
        self,
        description: str,
        *,
        title: str | None = None,
        project_type: str = "generic",
        repo: str | None = None,
        discovered_context: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "description": description,
            "project_type": project_type,
        }
        if title:
            payload["title"] = title
        if repo:
            payload["repo"] = repo
        if discovered_context:
            payload["discovered_context"] = discovered_context
        return self._request("POST", "/plans/describe/preview", json_body=payload)

    def plan_status(self, plan_id: str) -> dict[str, Any]:
        plan_bundle = self.get_plan(plan_id=plan_id)
        plan = plan_bundle.get("plan") or {}
        steps = plan.get("plan_steps") or []
        counts: dict[str, int] = {}
        for step in steps:
            status = (step.get("status") or "todo").strip().lower()
            counts[status] = counts.get(status, 0) + 1
        return {
            "plan_id": plan_id,
            "title": plan.get("title"),
            "status": plan.get("status"),
            "total_tasks": len(steps),
            "task_counts": counts,
            "enrichment_sources": plan.get("enrichment_sources") or [],
        }

    def record_decision(
        self,
        plan_id: str,
        task_id: str,
        *,
        context: str,
        choice: str,
        reasoning: str,
        alternatives: list[str] | None = None,
    ) -> dict[str, Any]:
        plan_bundle = self.get_plan(plan_id=plan_id)
        plan = plan_bundle.get("plan") or {}
        task = next(
            (
                step
                for step in (plan.get("plan_steps") or [])
                if step.get("id") == task_id
            ),
            None,
        )
        if not task:
            raise KeshroApiError(f"Task not found: {task_id}")
        from datetime import datetime, timezone

        decision = {
            "context": context,
            "choice": choice,
            "reasoning": reasoning,
            "alternatives": alternatives or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        existing_decisions = task.get("decisions") or []
        return self._request(
            "PATCH",
            f"/plans/{plan_id}/tasks/{task_id}",
            json_body={"decisions": [*existing_decisions, decision]},
        )

    def push_to_tracker(
        self,
        plan_id: str,
        *,
        provider: str = "linear",
        team_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"provider": provider}
        if team_id:
            payload["team_id"] = team_id
        if project_id:
            payload["project_id"] = project_id
        return self._request("POST", f"/plans/{plan_id}/push", json_body=payload)

    def sync_pull(self, plan_id: str) -> dict[str, Any]:
        return self._request("POST", f"/plans/{plan_id}/sync-pull", json_body={})

    def export_project(self, migration_id: str) -> dict[str, Any]:
        data = self.get_project(migration_id)
        project = data.get("project") or {}
        plan = data.get("execution_plan") or {}
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
