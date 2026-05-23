from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QThread, Signal

import httpx


@dataclass
class TaskResult:
    action: str = ""
    name: str = ""
    status: str = ""
    stdout: str = ""
    stderr: str = ""
    params: dict = field(default_factory=dict)


@dataclass
class QueryResult:
    reply: str | None = None
    summary: str | None = None
    tasks: list[TaskResult] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class PlanResult:
    reply: str | None = None
    tasks: list[TaskResult] = field(default_factory=list)
    reasoning: str = ""
    messages: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class StepResult:
    task: dict | None = None
    reply: str | None = None
    done: bool = False
    messages: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class SingleExecResult:
    action: str = ""
    name: str = ""
    status: str = ""
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    skipped: bool = False
    duration_ms: int = 0
    error: str | None = None


class _StepWorker(QObject):
    finished = Signal(object)

    def __init__(self, base_url: str, text: str, observations: list[dict]) -> None:
        super().__init__()
        self._base_url = base_url
        self._text = text
        self._observations = observations

    def run(self) -> None:
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{self._base_url}/step",
                    json={"text": self._text, "observations": self._observations},
                )
                resp.raise_for_status()
                data = resp.json()

            result = StepResult(
                task=data.get("task"),
                reply=data.get("reply"),
                done=data.get("done", False),
                messages=data.get("messages", []),
            )
        except httpx.ConnectError:
            result = StepResult(
                error="Cannot connect to API. Is the server running?"
            )
        except httpx.HTTPStatusError as e:
            result = StepResult(error=f"API error: {e.response.status_code}")
        except Exception as e:
            result = StepResult(error=str(e))

        self.finished.emit(result)


class _ExecSingleWorker(QObject):
    finished = Signal(object)

    def __init__(self, base_url: str, task: dict) -> None:
        super().__init__()
        self._base_url = base_url
        self._task = task

    def run(self) -> None:
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{self._base_url}/execute-single",
                    json=self._task,
                )
                resp.raise_for_status()
                data = resp.json()

            result = SingleExecResult(
                action=data.get("action", ""),
                name=data.get("name", ""),
                status=data.get("status", ""),
                stdout=data.get("stdout", ""),
                stderr=data.get("stderr", ""),
                returncode=data.get("returncode", 0),
                skipped=data.get("skipped", False),
                duration_ms=data.get("duration_ms", 0),
            )
        except httpx.ConnectError:
            result = SingleExecResult(error="Cannot connect to API.")
        except httpx.HTTPStatusError as e:
            result = SingleExecResult(error=f"API error: {e.response.status_code}")
        except Exception as e:
            result = SingleExecResult(error=str(e))

        self.finished.emit(result)


class _PlanWorker(QObject):
    finished = Signal(object)

    def __init__(self, base_url: str, text: str) -> None:
        super().__init__()
        self._base_url = base_url
        self._text = text

    def run(self) -> None:
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{self._base_url}/plan",
                    json={"text": self._text},
                )
                resp.raise_for_status()
                data = resp.json()

            tasks = [
                TaskResult(
                    action=t.get("action", ""),
                    name=t.get("name", ""),
                    status="pending",
                    params=t.get("params", {}),
                )
                for t in data.get("tasks", [])
            ]
            result = PlanResult(
                reply=data.get("reply"),
                tasks=tasks,
                reasoning=data.get("reasoning", ""),
                messages=data.get("messages", []),
            )
        except httpx.ConnectError:
            result = PlanResult(
                error="Cannot connect to API. Is the server running?"
            )
        except httpx.HTTPStatusError as e:
            result = PlanResult(error=f"API error: {e.response.status_code}")
        except Exception as e:
            result = PlanResult(error=str(e))

        self.finished.emit(result)


class _ExecuteWorker(QObject):
    finished = Signal(object)

    def __init__(self, base_url: str, tasks: list[dict], query: str = "") -> None:
        super().__init__()
        self._base_url = base_url
        self._tasks = tasks
        self._query = query

    def run(self) -> None:
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{self._base_url}/execute",
                    json={"tasks": self._tasks, "query": self._query},
                )
                resp.raise_for_status()
                data = resp.json()

            tasks = [
                TaskResult(
                    action=t.get("action", ""),
                    name=t.get("name", ""),
                    status=t.get("status", ""),
                    stdout=t.get("stdout", ""),
                    stderr=t.get("stderr", ""),
                )
                for t in data.get("tasks", [])
            ]
            result = QueryResult(
                tasks=tasks,
                summary=data.get("summary"),
                messages=data.get("messages", []),
            )
        except httpx.ConnectError:
            result = QueryResult(
                error="Cannot connect to API. Is the server running?"
            )
        except httpx.HTTPStatusError as e:
            result = QueryResult(error=f"API error: {e.response.status_code}")
        except Exception as e:
            result = QueryResult(error=str(e))

        self.finished.emit(result)


class _QueryWorker(QObject):
    finished = Signal(object)
    task_started = Signal(str)

    def __init__(self, base_url: str, text: str) -> None:
        super().__init__()
        self._base_url = base_url
        self._text = text

    def run(self) -> None:
        self.task_started.emit(self._text)
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{self._base_url}/query",
                    json={"text": self._text},
                )
                resp.raise_for_status()
                data = resp.json()

            tasks = [
                TaskResult(
                    action=t.get("action", ""),
                    name=t.get("name", ""),
                    status=t.get("status", ""),
                    stdout=t.get("stdout", ""),
                    stderr=t.get("stderr", ""),
                )
                for t in data.get("tasks", [])
            ]
            result = QueryResult(
                reply=data.get("reply"),
                summary=data.get("summary"),
                tasks=tasks,
                messages=data.get("messages", []),
            )
        except httpx.ConnectError:
            result = QueryResult(
                error="Cannot connect to API. Is the server running?"
            )
        except httpx.HTTPStatusError as e:
            result = QueryResult(error=f"API error: {e.response.status_code}")
        except Exception as e:
            result = QueryResult(error=str(e))

        self.finished.emit(result)


class ApiClient(QObject):
    query_started = Signal(str)
    query_finished = Signal(object)
    plan_finished = Signal(object)
    execute_finished = Signal(object)
    step_finished = Signal(object)
    exec_single_finished = Signal(object)

    def __init__(
        self, base_url: str = "http://127.0.0.1:8000", parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._base_url = base_url
        self._thread: QThread | None = None
        self._worker: QObject | None = None

    @property
    def is_busy(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def send_plan(self, text: str) -> None:
        if self.is_busy:
            return

        self._thread = QThread()
        self._worker = _PlanWorker(self._base_url, text)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_plan_finished)

        self._thread.start()

    def _on_plan_finished(self, result: PlanResult) -> None:
        self._cleanup_thread()
        self.plan_finished.emit(result)

    def send_execute(self, tasks: list[dict], query: str = "") -> None:
        if self.is_busy:
            return

        self._thread = QThread()
        self._worker = _ExecuteWorker(self._base_url, tasks, query)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_execute_finished)

        self._thread.start()

    def _on_execute_finished(self, result: QueryResult) -> None:
        self._cleanup_thread()
        self.execute_finished.emit(result)

    def send_query(self, text: str) -> None:
        if self.is_busy:
            return

        self._thread = QThread()
        self._worker = _QueryWorker(self._base_url, text)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.task_started.connect(self.query_started.emit)
        self._worker.finished.connect(self._on_finished)

        self._thread.start()

    def _on_finished(self, result: QueryResult) -> None:
        self._cleanup_thread()
        self.query_finished.emit(result)

    def send_step(self, text: str, observations: list[dict]) -> None:
        if self.is_busy:
            return
        self._thread = QThread()
        self._worker = _StepWorker(self._base_url, text, observations)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_step_finished)
        self._thread.start()

    def _on_step_finished(self, result: StepResult) -> None:
        self._cleanup_thread()
        self.step_finished.emit(result)

    def send_exec_single(self, task: dict) -> None:
        if self.is_busy:
            return
        self._thread = QThread()
        self._worker = _ExecSingleWorker(self._base_url, task)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_exec_single_finished)
        self._thread.start()

    def _on_exec_single_finished(self, result: SingleExecResult) -> None:
        self._cleanup_thread()
        self.exec_single_finished.emit(result)

    def _cleanup_thread(self) -> None:
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None

    def check_health(self) -> bool:
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self._base_url}/health")
                return resp.status_code == 200
        except Exception:
            return False
