from core.schemas import Task
from core.executor import Executor

ex = Executor()
test_task = Task(action="open_app", params={"name": "notepad"})
print(ex.execute(test_task))
