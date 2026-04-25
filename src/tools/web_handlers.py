import json

import httpx
import trafilatura
from ddgs import DDGS

from config import settings
from core.schemas import Task, TaskResult
from core.session import SessionState

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def web_search(task: Task, session: SessionState) -> TaskResult:
    query = str(task.params.get("query") or task.name).strip()
    if not query:
        return TaskResult(task=task, stderr="empty query", returncode=1)

    raw_max = task.params.get("max_results", settings.WEB_MAX_RESULTS)
    try:
        max_results = int(raw_max) if raw_max is not None else settings.WEB_MAX_RESULTS
    except (TypeError, ValueError):
        max_results = settings.WEB_MAX_RESULTS

    try:
        results = DDGS().text(query, max_results=max_results)
    except Exception as e:
        return TaskResult(task=task, stderr=f"search failed: {e}", returncode=1)

    trimmed = [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in results
    ]
    return TaskResult(
        task=task,
        stdout=json.dumps(trimmed, ensure_ascii=False, indent=2),
        returncode=0,
    )


def web_read(task: Task, session: SessionState) -> TaskResult:
    url = str(task.params.get("url") or task.name).strip()
    if not url:
        return TaskResult(task=task, stderr="empty url", returncode=1)
    if not url.startswith(("http://", "https://")):
        return TaskResult(task=task, stderr=f"invalid url scheme: {url}", returncode=1)

    try:
        resp = httpx.get(
            url,
            timeout=settings.WEB_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        return TaskResult(task=task, stderr=f"fetch failed: {e}", returncode=1)

    text = trafilatura.extract(resp.text, url=url) or ""
    if not text:
        return TaskResult(task=task, stderr="no extractable content", returncode=1)
    if len(text) > settings.WEB_MAX_TEXT_LEN:
        text = text[: settings.WEB_MAX_TEXT_LEN] + "\n... [truncated]"
    return TaskResult(task=task, stdout=text, returncode=0)
