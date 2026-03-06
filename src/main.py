from core.schemas import Task
from core.executor import Executor

ex = Executor()

task = Task(action="open_app", name="discord", params={})
print(ex.execute(task))
task2 = Task(action="run_command", name="ls", params={})
print(ex.execute(task2))
task3 = Task(action="run_skill", name="skill_hello.py", params={})
print(ex.execute(task3))

try:
    Task(action="open_app", name="rm_rf_test", params={})
except Exception as e:
    print(f"ValidationError (очікувано): {e}")
