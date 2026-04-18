from typing import Callable

from tools.api_handler import http_request
from tools.handlers import open_app, read_file, run_command, run_skill, write_file
from tools.rag_handler import index_knowledge, search_knowledge
from tools.web_handlers import web_read, web_search

TOOL_REGISTRY: dict[str, Callable] = {
    "open_app": open_app,
    "run_command": run_command,
    "run_skill": run_skill,
    "write_file": write_file,
    "read_file": read_file,
    "search_knowledge": search_knowledge,
    "index_knowledge": index_knowledge,
    "web_search": web_search,
    "web_read": web_read,
    "http_request": http_request,
}
