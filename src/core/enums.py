from enum import Enum


class ActionTypeEnum(str, Enum):
    OPEN_APP = "open_app"
    RUN_COMMAND = "run_command"
    RUN_SKILL = "run_skill"
    CHAT = "chat"
    WRITE_FILE = "write_file"
    READ_FILE = "read_file"
    SEARCH_KNOWLEDGE = "search_knowledge"
    INDEX_KNOWLEDGE = "index_knowledge"
