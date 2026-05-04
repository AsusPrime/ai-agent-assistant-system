import os
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class RequirementType(str, Enum):
    APP = "app"
    COMMAND = "command"
    ENV_VAR = "env_var"
    FILE = "file"


class Requirement(BaseModel):
    type: RequirementType
    name: str
    description: str = ""
    optional: bool = False


@dataclass
class CheckResult:
    requirement: Requirement
    satisfied: bool
    message: str = ""


@dataclass
class PreflightResult:
    passed: bool
    results: list[CheckResult] = field(default_factory=list)
    missing_vars: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if self.passed:
            return "All requirements satisfied."
        failed = [r for r in self.results if not r.satisfied]
        lines = [f"Missing {len(failed)} requirement(s):"]
        for r in failed:
            lines.append(f"  - [{r.requirement.type.value}] {r.requirement.name}: {r.message}")
        return "\n".join(lines)


def check_requirements(requirements: list[Requirement]) -> PreflightResult:
    results: list[CheckResult] = []
    missing_vars: list[str] = []

    for req in requirements:
        result = _check_one(req)
        results.append(result)
        if not result.satisfied and req.type == RequirementType.ENV_VAR:
            missing_vars.append(req.name)

    all_required_ok = all(
        r.satisfied for r in results if not r.requirement.optional
    )
    return PreflightResult(
        passed=all_required_ok,
        results=results,
        missing_vars=missing_vars,
    )


def _check_one(req: Requirement) -> CheckResult:
    match req.type:
        case RequirementType.APP:
            found = _app_exists(req.name)
            msg = "" if found else f"'{req.name}' not found"
            return CheckResult(requirement=req, satisfied=found, message=msg)

        case RequirementType.COMMAND:
            found = shutil.which(req.name) is not None
            msg = "" if found else f"'{req.name}' not found in PATH"
            return CheckResult(requirement=req, satisfied=found, message=msg)

        case RequirementType.ENV_VAR:
            value = os.environ.get(req.name)
            found = value is not None and value != ""
            msg = "" if found else f"env var '{req.name}' is not set"
            return CheckResult(requirement=req, satisfied=found, message=msg)

        case RequirementType.FILE:
            found = Path(req.name).expanduser().exists()
            msg = "" if found else f"file '{req.name}' does not exist"
            return CheckResult(requirement=req, satisfied=found, message=msg)


def _app_exists(name: str) -> bool:
    import platform
    import subprocess

    if shutil.which(name) is not None:
        return True
    if platform.system() == "Darwin":
        app_dirs = [Path("/Applications"), Path.home() / "Applications"]
        name_lower = name.lower()
        for d in app_dirs:
            if not d.exists():
                continue
            for entry in d.iterdir():
                if entry.suffix == ".app" and entry.stem.lower().startswith(name_lower):
                    return True
        try:
            result = subprocess.run(
                ["mdfind", f"kMDItemKind == 'Application' && kMDItemDisplayName == '{name}*'"],
                capture_output=True, text=True, timeout=5,
            )
            return bool(result.stdout.strip())
        except Exception:
            pass
    return False
