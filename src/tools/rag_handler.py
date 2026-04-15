import os

from config import settings
from core.schemas import Task, TaskResult
from core.session import SessionState
from core.vector_store import VectorStore

_vector_store: VectorStore | None = None


def _get_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(data_dir=settings.DATA_DIR)
    return _vector_store


def search_knowledge(task: Task, session: SessionState) -> TaskResult:
    query = str(task.params.get("query", task.name)).strip()
    if not query:
        return TaskResult(task=task, stderr="No query provided", returncode=1)
    try:
        chunks = _get_store().search(query)
    except Exception as e:
        return TaskResult(task=task, stderr=f"Search error: {e}", returncode=1)
    if not chunks:
        return TaskResult(
            task=task,
            stdout="No relevant documents found in the knowledge base.",
            returncode=0,
        )
    output = "\n\n---\n\n".join(chunks)
    return TaskResult(
        task=task, stdout=f"[Knowledge base results]\n\n{output}", returncode=0
    )


def index_knowledge(task: Task, session: SessionState) -> TaskResult:
    path = str(task.params.get("path", task.name)).strip()
    if not path:
        return TaskResult(task=task, stderr="No path provided", returncode=1)
    path = os.path.expanduser(path)
    store = _get_store()
    try:
        if os.path.isfile(path):
            count = store.index_file(path)
            msg = f"Indexed {count} chunk(s) from {path}"
        elif os.path.isdir(path):
            report = store.index_directory(path)
            total = sum(report.values())
            files = len(report)
            msg = f"Indexed {total} chunk(s) across {files} file(s) from {path}"
        else:
            return TaskResult(task=task, stderr=f"Path not found: {path}", returncode=1)
    except Exception as e:
        return TaskResult(task=task, stderr=str(e), returncode=1)
    return TaskResult(task=task, stdout=msg, returncode=0)
