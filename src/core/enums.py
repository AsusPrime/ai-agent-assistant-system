from enum import Enum


class ActionTypeEnum(str, Enum):
    OPEN_APP = "open_app"
    RUN_COMMAND = "run_command"
    RUN_SKILL = "run_skill"
