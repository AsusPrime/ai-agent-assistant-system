import re
from typing import Callable

from config import settings
from core.enums import ActionTypeEnum
from core.engine import ExecutionEngine
from core.memory import MessageRepository
from core.planner import build_planner_agent, format_mcp_tools_section, planner_agent
from core.privacy import PrivacyGuard
from core.schemas import Plan, Task, TaskResult
from core.session import SessionState
from core.summarizer import summary_agent
from integrations.mcp_client import MCPManager
from integrations.mcp_config import load_config as load_mcp_config

ConfirmFn = Callable[[str], bool]
MessageFn = Callable[[str], None]


class QueryResult:
    def __init__(
        self,
        reply: str | None = None,
        task_results: list[TaskResult] | None = None,
        summary: str | None = None,
    ):
        self.reply = reply
        self.task_results = task_results or []
        self.summary = summary

    @property
    def is_chat(self) -> bool:
        return self.reply is not None


class AssistantCore:
    def __init__(
        self,
        confirm_fn: ConfirmFn | None = None,
        on_message: MessageFn | None = None,
        mcp_manager: MCPManager | None = None,
    ):
        self.guard = PrivacyGuard()
        self.msg_repo = MessageRepository(data_dir=settings.DATA_DIR)
        self.session = SessionState()
        self._confirm = confirm_fn or self._default_confirm
        self._print = on_message or print
        self.engine = ExecutionEngine(
            session=self.session,
            confirm_fn=self._confirm,
            on_message=self._print,
        )

        if mcp_manager is None:
            cfg = load_mcp_config(settings.MCP_CONFIG_PATH)
            mcp_manager = MCPManager(config=cfg)
            try:
                mcp_manager.start()
            except Exception as e:
                self._print(f"[MCP] Failed to start: {e}")
        self.mcp_manager = mcp_manager
        self.session.mcp_manager = mcp_manager
        self.session.confirm_fn = self._confirm

        self.planner_agent = self._build_planner_agent()

        self.session.message_history = self.msg_repo.load_recent(settings.MEMORY_TURNS)

    def _build_planner_agent(self):
        if self.mcp_manager is None or not self.mcp_manager.connected:
            return planner_agent
        try:
            tools = self.mcp_manager.list_tools()
        except Exception as e:
            self._print(f"[MCP] list_tools failed, planner will not see MCP tools: {e}")
            return planner_agent
        if not tools:
            return planner_agent
        servers = list(self.mcp_manager.config.servers.keys())
        section = format_mcp_tools_section(tools, servers=servers)
        return build_planner_agent(section)

    def close(self) -> None:
        if self.mcp_manager is not None:
            try:
                self.mcp_manager.stop()
            except Exception as e:
                self._print(f"[MCP] Stop failed: {e}")

    @staticmethod
    def _default_confirm(prompt: str) -> bool:
        return input(prompt).strip().lower() == "y"

    def process_query(self, user_input: str) -> QueryResult:
        masked_input, pii_map = self.guard.mask(user_input)
        self.session.pii_map.update(pii_map)
        if pii_map:
            self._print(
                f"[Privacy] Masked {len(pii_map)} sensitive pattern(s) before sending to LLM."
            )
            self.session.privacy_events.append(
                {"input_length": len(user_input), "masked_count": len(pii_map)}
            )

        return self._react_loop(user_input, masked_input)

    def _react_loop(self, user_input: str, masked_input: str) -> QueryResult:
        observations: list[TaskResult] = []
        max_iter = settings.REACT_MAX_ITERATIONS

        for iteration in range(max_iter):
            prompt = self._build_react_prompt(masked_input, observations)
            plan = self._get_plan(prompt)
            if plan is None:
                break
            plan = _unmask_plan(plan, self.session.pii_map)

            if len(plan.tasks) == 1 and plan.tasks[0].action == ActionTypeEnum.CHAT:
                reply = _extract_chat_reply(plan)
                return QueryResult(reply=reply, task_results=observations)

            task = plan.tasks[0]
            self._print(f"[Step {iteration + 1}] {task.action.value} | {task.name}")

            if not self._confirm(
                f"  Виконати {task.action.value} | {task.name}? [y/N]: "
            ):
                self._print("Cancelled by user.")
                observations.append(TaskResult(task=task, skipped=True))
                break

            result = self.engine.run_single(task, pre_approved=True)
            observations.append(result)

            if result.skipped:
                break

        summary = self._summarize(user_input, observations, retries_exhausted=False)
        return QueryResult(task_results=observations, summary=summary)

    def _build_react_prompt(
        self, original_query: str, observations: list[TaskResult]
    ) -> str:
        if not observations:
            return original_query

        lines = [f'Original request: "{original_query}"', "", "Steps completed so far:"]
        for i, r in enumerate(observations, 1):
            lines.append(
                f"  Step {i}: [{r.status}] {r.task.action.value} {r.task.name}"
            )
            if r.stdout.strip():
                masked, _ = self.guard.mask(r.stdout.strip()[:500])
                lines.append(f"    stdout: {masked}")
            if r.stderr.strip():
                masked, _ = self.guard.mask(r.stderr.strip()[:300])
                lines.append(f"    stderr: {masked}")
            if r.skipped:
                lines.append("    (skipped by user)")
        lines.append("")
        lines.append(
            "Based on these results, return the NEXT single step, or a chat task if the request is fulfilled."
        )
        return "\n".join(lines)

    # -- planning --------------------------------------------------------

    def _get_plan(self, masked_input: str) -> Plan | None:
        prev_len = len(self.session.message_history)
        try:
            result = self._run_planner(masked_input)
        except Exception as e:
            self._print(f"[LLM Error] {e}")
            return None

        self.session.message_history = result.all_messages()
        new_msgs = self.session.message_history[prev_len:]
        if new_msgs:
            self.msg_repo.save_turn(self.session.session_id, new_msgs)
        return result.output

    def _run_planner(self, prompt: str):
        try:
            return self.planner_agent.run_sync(
                prompt, message_history=self.session.message_history
            )
        except Exception as e:
            if _is_event_loop_bound_error(e):
                # pydantic-ai + google-genai caches httpx.AsyncClient whose
                # asyncio primitives bind to the first run_sync's event loop.
                # Rebuilding the agent forces a fresh client on the new loop.
                if settings.DEBUG:
                    self._print(f"[Planner] Event-loop mismatch, rebuilding agent: {e}")
                self.planner_agent = self._build_planner_agent()
                return self.planner_agent.run_sync(
                    prompt, message_history=self.session.message_history
                )
            if _is_history_malformed_error(e) and self.session.message_history:
                if settings.DEBUG:
                    self._print(
                        f"[Memory] History rejected by LLM, retrying without it: {e}"
                    )
                else:
                    self._print(
                        "[Memory] Previous session history was malformed — starting fresh."
                    )
                self.session.message_history = []
                return self.planner_agent.run_sync(prompt)
            raise

    # -- execution -------------------------------------------------------

    def _execute_plan(self, plan: Plan, pre_approved: bool = False) -> list[TaskResult]:
        results = self.engine.run(plan, pre_approved=pre_approved)
        if settings.DEBUG:
            self._print_execution_log(results)
        return results

    def execute_plan(self, plan: Plan, pre_approved: bool = False) -> list[TaskResult]:
        return self._execute_plan(plan, pre_approved=pre_approved)

    def summarize(self, user_input: str, results: list[TaskResult]) -> str | None:
        return self._summarize(user_input, results, retries_exhausted=False)

    def react_step(
        self,
        user_input: str,
        observations: list[dict],
    ) -> tuple[Task | None, str | None]:
        masked_input, pii_map = self.guard.mask(user_input)
        self.session.pii_map.update(pii_map)

        obs_results = [
            TaskResult(
                task=Task(
                    action=o["action"], name=o["name"], params=o.get("params", {})
                ),
                stdout=o.get("stdout", ""),
                stderr=o.get("stderr", ""),
                returncode=o.get("returncode", 0),
                skipped=o.get("skipped", False),
            )
            for o in observations
        ]

        prompt = self._build_react_prompt(masked_input, obs_results)
        plan = self._get_plan(prompt)
        if plan is None:
            return None, None

        plan = _unmask_plan(plan, self.session.pii_map)

        if len(plan.tasks) == 1 and plan.tasks[0].action == ActionTypeEnum.CHAT:
            reply = _extract_chat_reply(plan)
            return None, reply

        return plan.tasks[0], None

    def execute_single(self, task_dict: dict) -> TaskResult:
        task = Task(
            action=task_dict["action"],
            name=task_dict["name"],
            params=task_dict.get("params", {}),
        )
        return self.engine.run_single(task, pre_approved=True)

    # -- summarization ---------------------------------------------------

    def _summarize(
        self, user_input: str, results: list[TaskResult], retries_exhausted: bool
    ) -> str | None:
        lines = [f'User asked: "{user_input}"', "Execution results:"]
        for r in results:
            masked_out, _ = self.guard.mask(r.stdout.strip()[:100])
            masked_err, _ = self.guard.mask(r.stderr.strip()[:100])
            lines.append(
                f"  [{r.status}] {r.task.name} → "
                f"stdout: {masked_out!r}, stderr: {masked_err!r}"
            )
        if retries_exhausted:
            lines.append("\nAll retry attempts failed. Inform the user clearly.")
        lines.append(
            "\nProvide a short, friendly summary in the same language the user used."
        )

        try:
            result = summary_agent.run_sync("\n".join(lines))
            return result.output
        except Exception as e:
            if settings.DEBUG:
                self._print(f"[Summary Error] {e}")
            return None

    # -- display helpers -------------------------------------------------

    def _print_plan(self, plan: Plan) -> None:
        self._print(f"[Plan] {len(plan.tasks)} step(s):")
        for i, task in enumerate(plan.tasks, 1):
            self._print(f"  {i}. {task.action.value} | {task.name} | {task.params}")
        if plan.reasoning and settings.DEBUG:
            self._print(f"  Reasoning: {plan.reasoning}")

    def _print_execution_log(self, results: list[TaskResult]) -> None:
        self._print("\n[Execution log]")
        for r in results:
            self._print(
                f"  {r.status:7} | {r.task.action.value:12} | {r.task.name} | {r.duration_ms}ms"
            )


# -- module-level helpers ------------------------------------------------


_MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")


def _fix_image_urls(text: str) -> str:
    matches = list(_MD_IMG_RE.finditer(text))
    if not matches:
        return text

    try:
        from ddgs import DDGS

        ddgs = DDGS()
    except Exception:
        return _MD_IMG_RE.sub(r"", text)

    for m in matches:
        alt = m.group(1).strip()
        query = alt or "image"
        try:
            results = ddgs.images(query, max_results=1)
            if results:
                real_url = results[0].get("image", "")
                if real_url:
                    text = text.replace(m.group(0), f"![{alt}]({real_url})", 1)
                    continue
        except Exception:
            pass
        text = text.replace(m.group(0), "", 1)

    return text


def _extract_chat_reply(plan: Plan) -> str:
    name = plan.tasks[0].name
    if " " in name and len(name) > 20:
        reply = name
    elif plan.reasoning and len(plan.reasoning) > len(name):
        reply = plan.reasoning
    else:
        reply = name
    return _fix_image_urls(reply)


def _unmask_str(s: str, mapping: dict[str, str]) -> str:
    for placeholder, original in mapping.items():
        s = s.replace(placeholder, original)
    return s


def _unmask_plan(plan: Plan, mapping: dict[str, str]) -> Plan:
    if not mapping:
        return plan
    unmasked_tasks = []
    for task in plan.tasks:
        unmasked_name = _unmask_str(task.name, mapping)
        unmasked_params: dict = {}
        for k, v in task.params.items():
            if isinstance(v, str):
                unmasked_params[k] = _unmask_str(v, mapping)
            elif isinstance(v, list):
                unmasked_params[k] = [
                    _unmask_str(i, mapping) if isinstance(i, str) else i for i in v
                ]
            else:
                unmasked_params[k] = v
        unmasked_tasks.append(
            task.model_copy(update={"name": unmasked_name, "params": unmasked_params})
        )
    return plan.model_copy(update={"tasks": unmasked_tasks})


def _is_history_malformed_error(err: Exception) -> bool:
    msg = str(err).lower()
    return "function response" in msg or "function call" in msg


def _is_event_loop_bound_error(err: Exception) -> bool:
    msg = str(err).lower()
    return "bound to a different event loop" in msg or "different event loop" in msg
