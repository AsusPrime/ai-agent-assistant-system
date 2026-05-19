import json
from pathlib import Path

from pydantic import BaseModel

from core.requirements import Requirement
from core.schemas import Plan, Task

_RECIPES_DIR = Path(__file__).resolve().parent.parent / "recipes"


class Recipe(BaseModel):
    tasks: list[Task]
    reasoning: str = ""
    requirements: list[Requirement] = []

    def to_plan(self) -> Plan:
        return Plan(tasks=self.tasks, reasoning=self.reasoning)


def list_recipes() -> list[str]:
    if not _RECIPES_DIR.exists():
        return []
    return [p.stem for p in _RECIPES_DIR.glob("*.json")]


def load_recipe(name: str) -> Recipe:
    path = _RECIPES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Recipe '{name}' not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = [Task(**t) for t in data["tasks"]]
    requirements = [Requirement(**r) for r in data.get("requirements", [])]
    return Recipe(
        tasks=tasks, reasoning=data.get("reasoning", ""), requirements=requirements
    )


def save_recipe(name: str, recipe: Recipe) -> Path:
    _RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    path = _RECIPES_DIR / f"{name}.json"
    data = {
        "tasks": [t.model_dump() for t in recipe.tasks],
        "reasoning": recipe.reasoning,
        "requirements": [r.model_dump() for r in recipe.requirements],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
