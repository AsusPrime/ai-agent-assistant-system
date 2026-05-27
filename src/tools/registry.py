from typing import Callable

from tools.api_handler import http_request
from tools.handlers import open_app, read_file, run_command, run_skill, write_file
from tools.mcp_handler import mcp_call
from tools.rag_handler import index_knowledge, search_knowledge
from tools.system_control import system_control
from tools.web_handlers import image_search, web_read, web_search

TOOL_REGISTRY: dict[str, Callable] = {
    "open_app": open_app,
    "run_command": run_command,
    "run_skill": run_skill,
    "write_file": write_file,
    "read_file": read_file,
    "search_knowledge": search_knowledge,
    "index_knowledge": index_knowledge,
    "web_search": web_search,
    "image_search": image_search,
    "web_read": web_read,
    "http_request": http_request,
    "mcp_call": mcp_call,
    "system_control": system_control,
}
