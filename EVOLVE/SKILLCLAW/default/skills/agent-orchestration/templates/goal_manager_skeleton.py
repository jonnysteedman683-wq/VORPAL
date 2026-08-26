from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum, auto
import uuid

class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    BLOCKED = auto()

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    dependencies: Set[str] = field(default_factory=set)
    assigned_to: Optional[str] = None
    result: Optional[str] = None
    logs: List[str] = field(default_factory=list)

class GoalManager:
    def __init__(self, root_goal: str):
        self.root_goal = root_goal
        self.tasks: Dict[str, Task] = {}
        self.dependency_graph: Dict[str, List[str]] = {}

    def add_task(self, description: str, dependencies: List[str] = None) -> str:
        task = Task(description=description)
        if dependencies:
            task.dependencies = set(dependencies)
        self.tasks[task.id] = task
        for dep_id in (dependencies or []):
            if dep_id not in self.dependency_graph:
                self.dependency_graph[dep_id] = []
            self.dependency_graph[dep_id].append(task.id)
        return task.id

    def get_ready_tasks(self) -> List[Task]:
        return [t for t in self.tasks.values() 
                if t.status == TaskStatus.PENDING 
                and all(self.tasks[d].status == TaskStatus.COMPLETED for d in t.dependencies)]

    def update_task_status(self, task_id: str, status: TaskStatus, result: str = None):
        if task := self.tasks.get(task_id):
            task.status = status
            if result: task.result = result
