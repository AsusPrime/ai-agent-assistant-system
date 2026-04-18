import json

import httpx

from core.schemas import Task, TaskResult
from core.session import SessionState

_DEFAULT_TIMEOUT = 15.0
_MAX_BODY_LEN = 8000
_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}


def _coerce_dict(raw) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def http_request(task: Task, session: SessionState) -> TaskResult:
    method = str(task.params.get("method", "GET")).upper()
    if method not in _ALLOWED_METHODS:
        return TaskResult(
            task=task, stderr=f"method not allowed: {method}", returncode=1
        )

    url = str(task.params.get("url") or task.name).strip()
    if not url.startswith(("http://", "https://")):
        return TaskResult(task=task, stderr=f"invalid url: {url}", returncode=1)

    headers = _coerce_dict(task.params.get("headers"))
    json_body = task.params.get("json")
    if isinstance(json_body, str): # TODO: is it not better to use _coerce_dict?
        try:
            json_body = json.loads(json_body)
        except (json.JSONDecodeError, ValueError):
            return TaskResult(
                task=task, stderr="json param is not valid JSON", returncode=1
            )

    raw_timeout = task.params.get("timeout", _DEFAULT_TIMEOUT)
    try:
        timeout = float(raw_timeout) if raw_timeout is not None else _DEFAULT_TIMEOUT
    except (TypeError, ValueError):
        timeout = _DEFAULT_TIMEOUT

    try:
        resp = httpx.request(
            method,
            url,
            headers=headers or None,
            json=json_body,
            timeout=timeout,
            follow_redirects=True,
        )
    except httpx.HTTPError as e:
        return TaskResult(task=task, stderr=f"request failed: {e}", returncode=1)

    body = resp.text
    if len(body) > _MAX_BODY_LEN:
        body = body[:_MAX_BODY_LEN] + "\n... [truncated]"

    out = {
        "status_code": resp.status_code,
        "headers": dict(resp.headers),
        "body": body,
    }
    rc = 0 if resp.is_success else 1
    return TaskResult(
        task=task,
        stdout=json.dumps(out, ensure_ascii=False, indent=2),
        returncode=rc,
    )
