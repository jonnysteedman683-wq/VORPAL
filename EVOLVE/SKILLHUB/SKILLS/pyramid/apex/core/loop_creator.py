"""
OMNICORE LOOP CREATOR SKILL
Automated co-evolution loop creation engine with task decomposition and agent selection.
Pattern stolen from missionEngine.ts - Task decomposition → agent selection → execution.
"""
import asyncio
import random
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from time import time
import heapq


class TaskComplexity(Enum):
    SIMPLE = 1
    MODERATE = 2
    COMPLEX = 3
    CASCADE = 4  # Multi-step with dependencies


@dataclass
class SubTask:
    id: str
    description: str
    complexity: TaskComplexity
    dependencies: List[str]
    estimated_tokens: int
    assigned_agent: Optional[str] = None
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class ExecutionLoop:
    id: str
    name: str
    tasks: List[SubTask]
    created_at: float
    status: str = "pending"  # pending, running, completed, failed
    completion_rate: float = 0.0


class LoopCreator:
    """
    Automated loop creation engine that decomposes complex tasks
    into executable subtasks and assigns appropriate agents.

    Based on missionEngine.ts architecture:
    1. Decompose goal into atomic subtasks
    2. Select optimal agent for each subtask
    3. Execute with auto-healing and retry logic
    """

    def __init__(self):
        self._loops: Dict[str, ExecutionLoop] = {}
        self._agent_registry: Dict[str, Callable] = {}
        self._failure_history: Dict[str, List[dict]] = {}
    
    def register_agent(self, agent_name: str, handler: Callable):
        """Register an agent handler function."""
        self._agent_registry[agent_name] = handler

    def decompose_goal(self, goal_description: str) -> List[SubTask]:
        """Decompose high-level goal into atomic subtasks."""
        import hashlib
        task_id_prefix = hashlib.sha256(goal_description.encode()).hexdigest()[:8]
        
        # Simplified decomposition logic
        # In production, this would use an LLM to parse the goal
        tasks = []
        
        if "implement" in goal_description.lower():
            tasks.extend([
                SubTask(
                    id=f"{task_id_prefix}_1",
                    description=f"Design architecture for {goal_description}",
                    complexity=TaskComplexity.MODERATE,
                    dependencies=[],
                    estimated_tokens=800
                ),
                SubTask(
                    id=f"{task_id_prefix}_2",
                    description=f"Write core implementation for {goal_description}",
                    complexity=TaskComplexity.COMPLEX,
                    dependencies=[f"{task_id_prefix}_1"],
                    estimated_tokens=1200
                ),
                SubTask(
                    id=f"{task_id_prefix}_3",
                    description=f"Create test harness for {goal_description}",
                    complexity=TaskComplexity.MODERATE,
                    dependencies=[f"{task_id_prefix}_1"],
                    estimated_tokens=600
                ),
                SubTask(
                    id=f"{task_id_prefix}_4",
                    description=f"Execute tests and fix failures for {goal_description}",
                    complexity=TaskComplexity.CASCADE,
                    dependencies=[f"{task_id_prefix}_2", f"{task_id_prefix}_3"],
                    estimated_tokens=400
                )
            ])
        else:
            tasks.append(SubTask(
                id=f"{task_id_prefix}_1",
                description=goal_description,
                complexity=TaskComplexity.SIMPLE,
                dependencies=[],
                estimated_tokens=300
            ))
        
        return tasks

    def select_agent_for_task(self, task: SubTask) -> str:
        """Select optimal agent based on task complexity and capabilities."""
        if task.complexity == TaskComplexity.SIMPLE:
            return "axiom"  # Fast generator for simple tasks
        elif task.complexity == TaskComplexity.MODERATE:
            return "nexus"  # Reliable executor
        elif task.complexity == TaskComplexity.COMPLEX:
            return "axiom_entropy_pair"  # Generate + attack needed
        else:  # CASCADE
            return "nexus"  # Orchestrator with auto-healing

    async def auto_heal_task(self, task: SubTask) -> bool:
        """Attempt to auto-heal a failed task (stolen from recoverTaskFailure pattern)."""
        if task.retry_count >= 3:
            return False  # Max retries exceeded
        
        task.retry_count += 1
        task.status = "retrying"
        
        # Log failure for learning
        self._failure_history.setdefault(task.id, []).append({
            'attempt': task.retry_count,
            'error': task.error or "Unknown error",
            'timestamp': time()
        })
        
        # Exponential backoff
        await asyncio.sleep(min(2 ** task.retry_count, 10))
        return True

    async def execute_task(self, task: SubTask) -> SubTask:
        """Execute a single subtask with retry logic."""
        agent = self.select_agent_for_task(task)
        task.assigned_agent = agent
        task.status = "running"
        
        # Simplified execution (in production, calls actual agent handlers)
        try:
            # Simulate task execution
            if task.assigned_agent in self._agent_registry:
                handler = self._agent_registry[task.assigned_agent]
                result = handler(task)
                if asyncio.iscoroutine(result):
                    result = await result
                task.result = result
                task.status = "completed"
            else:
                # Default placeholder behavior
                task.result = f"Executed: {task.description}"
                task.status = "completed"
        
        except Exception as e:
            task.error = str(e)
            print(f"[LoopCreator] Task {task.id} failed: {e}")
            should_retry = await self.auto_heal_task(task)
            if should_retry:
                return await self.execute_task(task)
            task.status = "failed"
        
        return task

    async def create_and_execute_loop(self, goal: str) -> ExecutionLoop:
        """Create an execution loop from goal description and execute it."""
        import hashlib
        loop_id = hashlib.sha256(
            f"{goal}:{time()}".encode()
        ).hexdigest()[:12]
        
        tasks = self.decompose_goal(goal)
        loop = ExecutionLoop(
            id=loop_id,
            name=f"loop_{goal[:30]}",
            tasks=tasks,
            created_at=time()
        )
        
        self._loops[loop_id] = loop
        
        # Build dependency graph and execute topologically
        await self._execute_topologically(loop)
        
        # Calculate completion rate
        completed = sum(1 for t in loop.tasks if t.status == "completed")
        loop.completion_rate = completed / len(loop.tasks) if loop.tasks else 0.0
        loop.status = "completed" if loop.completion_rate == 1.0 else "failed"
        
        return loop

    async def _execute_topologically(self, loop: ExecutionLoop):
        """Execute tasks respecting dependency order."""
        # Build dependency graph
        task_map = {t.id: t for t in loop.tasks}
        in_degree = {t.id: len(t.dependencies) for t in loop.tasks}
        dependents = {t.id: [] for t in loop.tasks}
        
        for task in loop.tasks:
            for dep in task.dependencies:
                if dep in dependents:
                    dependents[dep].append(task.id)
        
        # Priority queue for execution
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        heapq.heapify(queue)
        
        executed = set()
        while queue:
            task_id = heapq.heappop(queue)
            task = task_map[task_id]
            
            # Check all dependencies completed
            deps_ok = all(dep in executed for dep in task.dependencies if dep in task_map)
            if not deps_ok:
                # Requeue if dependencies not ready
                heapq.heappush(queue, task_id)
                continue
            
            await self.execute_task(task)
            executed.add(task_id)
            
            # Reduce in-degree of dependents
            for dep_id in dependents[task_id]:
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    heapq.heappush(queue, dep_id)

    def get_loop_status(self, loop_id: str) -> Optional[dict]:
        """Get status of an execution loop."""
        loop = self._loops.get(loop_id)
        if not loop:
            return None
        return {
            'id': loop.id,
            'name': loop.name,
            'status': loop.status,
            'completion_rate': loop.completion_rate,
            'total_tasks': len(loop.tasks),
            'completed_tasks': sum(1 for t in loop.tasks if t.status == "completed"),
            'task_details': [
                {
                    'id': t.id,
                    'description': t.description,
                    'status': t.status,
                    'agent': t.assigned_agent,
                    'retries': t.retry_count,
                    'error': t.error
                }
                for t in loop.tasks
            ]
        }


# Singleton instance
CREATOR = LoopCreator()