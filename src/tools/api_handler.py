import json

import httpx

from config import settings
from core.schemas import Task, TaskResult
from core.session import SessionState

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


def _parse_json_body(raw) -> tuple[dict | list | None, str | None]:
    # Returns (parsed_body, error). `_coerce_dict` is not reused here because it
    # silently swallows malformed JSON — for a request body we need an explicit
    # error so the caller sees why the request was not sent.
    if raw is None or isinstance(raw, (dict, list)):
        return raw, None
    if isinstance(raw, str):
        try:
            return json.loads(raw), None
        except (json.JSONDecodeError, ValueError) as e:
            return None, f"json param is not valid JSON: {e}"
    return None, f"unsupported json param type: {type(raw).__name__}"


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
    json_body, body_err = _parse_json_body(task.params.get("json"))
    if body_err is not None:
        return TaskResult(task=task, stderr=body_err, returncode=1)

    raw_timeout = task.params.get("timeout", settings.HTTP_TIMEOUT)
    try:
        timeout = (
            float(raw_timeout) if raw_timeout is not None else settings.HTTP_TIMEOUT
        )
    except (TypeError, ValueError):
        timeout = settings.HTTP_TIMEOUT

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
    if len(body) > settings.HTTP_MAX_BODY_LEN:
        body = body[: settings.HTTP_MAX_BODY_LEN] + "\n... [truncated]"

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
