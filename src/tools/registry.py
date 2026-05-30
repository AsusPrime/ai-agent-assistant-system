from typing import Callable

from tools.api_handler import http_request
from tools.handlers import open_app, read_file, run_command, write_file
from tools.mcp_handler import mcp_call
from tools.rag_handler import index_knowledge, search_knowledge
from tools.recipe_handler import (
    handle_list_recipes,
    handle_run_recipe,
    handle_save_recipe,
)
from tools.system_control import system_control
from tools.web_handlers import image_search, web_read, web_search

TOOL_REGISTRY: dict[str, Callable] = {
    "open_app": open_app,
    "run_command": run_command,
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
    "save_recipe": handle_save_recipe,
    "run_recipe": handle_run_recipe,
    "list_recipes": handle_list_recipes,
}
