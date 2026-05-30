import json
from pathlib import Path

from pydantic import BaseModel

from core.requirements import Requirement
from core.schemas import Plan, Task

_RECIPES_DIR = Path(__file__).resolve().parent.parent / "recipes"


class Recipe(BaseModel):
    title: str = ""
    description: str = ""
    tasks: list[Task]
    reasoning: str = ""
    requirements: list[Requirement] = []

    def to_plan(self) -> Plan:
        return Plan(tasks=self.tasks, reasoning=self.reasoning)


class RecipeInfo(BaseModel):
    id: str
    title: str
    description: str


def list_recipes() -> list[str]:
    if not _RECIPES_DIR.exists():
        return []
    return [p.stem for p in _RECIPES_DIR.glob("*.json")]


def list_recipes_detailed() -> list[RecipeInfo]:
    if not _RECIPES_DIR.exists():
        return []
    result = []
    for p in _RECIPES_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        slug = p.stem
        title = data.get("title") or slug.replace("_", " ").title()
        description = data.get("description", "")
        result.append(RecipeInfo(id=slug, title=title, description=description))
    return result


def load_recipe(name: str) -> Recipe:
    path = _RECIPES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Recipe '{name}' not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = [Task(**t) for t in data["tasks"]]
    requirements = [Requirement(**r) for r in data.get("requirements", [])]
    return Recipe(
        title=data.get("title", ""),
        description=data.get("description", ""),
        tasks=tasks,
        reasoning=data.get("reasoning", ""),
        requirements=requirements,
    )


def save_recipe(name: str, recipe: Recipe) -> Path:
    _RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    path = _RECIPES_DIR / f"{name}.json"
    data = {
        "title": recipe.title or name.replace("_", " ").title(),
        "description": recipe.description,
        "tasks": [t.model_dump() for t in recipe.tasks],
        "reasoning": recipe.reasoning,
        "requirements": [r.model_dump() for r in recipe.requirements],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
