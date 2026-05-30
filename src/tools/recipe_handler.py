import json

from core.recipe_loader import Recipe, list_recipes_detailed, load_recipe, save_recipe
from core.schemas import Task, TaskResult
from core.session import SessionState


def handle_list_recipes(task: Task, session: SessionState) -> TaskResult:
    recipes = list_recipes_detailed()
    if not recipes:
        return TaskResult(task=task, stdout="No recipes found.", returncode=0)
    items = [
        {"id": r.id, "title": r.title, "description": r.description} for r in recipes
    ]
    return TaskResult(
        task=task, stdout=json.dumps(items, ensure_ascii=False), returncode=0
    )


def handle_save_recipe(task: Task, session: SessionState) -> TaskResult:
    name = task.params.get("name") or task.name
    if not name:
        return TaskResult(task=task, stderr="Recipe name is required", returncode=1)

    tasks_raw = task.params.get("tasks")
    if not tasks_raw:
        return TaskResult(task=task, stderr="Recipe tasks are required", returncode=1)

    if isinstance(tasks_raw, str):
        try:
            tasks_raw = json.loads(tasks_raw)
        except json.JSONDecodeError:
            return TaskResult(task=task, stderr="Invalid tasks JSON", returncode=1)

    recipe_tasks = []
    for t in tasks_raw:
        if isinstance(t, str):
            try:
                t = json.loads(t)
            except json.JSONDecodeError:
                return TaskResult(task=task, stderr=f"Invalid task: {t}", returncode=1)
        recipe_tasks.append(Task(**t))

    reasoning = task.params.get("reasoning", "") or ""
    if isinstance(reasoning, list):
        reasoning = " ".join(str(r) for r in reasoning)

    title = task.params.get("title", "") or ""
    if isinstance(title, list):
        title = " ".join(str(t) for t in title)
    description = task.params.get("description", "") or ""
    if isinstance(description, list):
        description = " ".join(str(d) for d in description)

    recipe = Recipe(
        title=str(title),
        description=str(description),
        tasks=recipe_tasks,
        reasoning=str(reasoning),
    )
    path = save_recipe(str(name), recipe)
    return TaskResult(
        task=task, stdout=f"Recipe '{name}' saved to {path}", returncode=0
    )


def handle_run_recipe(task: Task, session: SessionState) -> TaskResult:
    name = task.params.get("name") or task.name
    if not name:
        return TaskResult(task=task, stderr="Recipe name is required", returncode=1)

    try:
        recipe = load_recipe(str(name))
    except FileNotFoundError:
        return TaskResult(task=task, stderr=f"Recipe '{name}' not found", returncode=1)

    from core.executor import Executor

    executor = Executor()
    results = []
    for t in recipe.tasks:
        result = executor.execute(t, session)
        results.append(f"[{result.status}] {t.action.value} | {t.name}")
        if result.stdout.strip():
            results.append(result.stdout.strip())
        if not result.success:
            results.append(f"  Error: {result.stderr}")
            break

    return TaskResult(task=task, stdout="\n".join(results), returncode=0)
