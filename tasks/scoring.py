# backend/tasks/scoring.py
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, Iterable, List, Optional, Set

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "urgency": 0.35,
    "importance": 0.35,
    "effort": 0.20,
    "dependency": 0.10,
}

@dataclass
class Task:
    id: Optional[str]
    title: str
    due_date: Optional[date]
    estimated_hours: Optional[float]
    importance: Optional[float]
    dependencies: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Dict) -> "Task":
        # Parse due_date (ISO or YYYY-MM-DD) if present
        due_date = None
        if d.get("due_date"):
            try:
                due_date = datetime.fromisoformat(d["due_date"]).date()
            except Exception as e:
                raise ValueError(f"Invalid due_date for task '{d.get('title', '')}': {e}")

        estimated_hours = d.get("estimated_hours")
        if estimated_hours is not None:
            try:
                estimated_hours = float(estimated_hours)
            except Exception as e:
                raise ValueError(f"Invalid estimated_hours for task '{d.get('title','')}': {e}")

        importance = d.get("importance")
        if importance is not None:
            try:
                importance = float(importance)
            except Exception as e:
                raise ValueError(f"Invalid importance for task '{d.get('title','')}': {e}")

        deps = d.get("dependencies") or []
        if not isinstance(deps, list):
            raise ValueError("dependencies must be a list of task IDs")

        return Task(
            id=str(d.get("id")) if d.get("id") is not None else None,
            title=str(d.get("title", "")).strip(),
            due_date=due_date,
            estimated_hours=estimated_hours,
            importance=importance,
            dependencies=[str(x) for x in deps],
        )

def load_weights_from_config(config_path: Optional[str]) -> Dict[str, float]:
    if not config_path:
        return DEFAULT_WEIGHTS
    try:
        with open(config_path, "r") as fh:
            cfg = json.load(fh)
            weights = {k: float(cfg.get(k, DEFAULT_WEIGHTS[k])) for k in DEFAULT_WEIGHTS}
            total = sum(weights.values())
            if total <= 0:
                logger.warning("weights sum <= 0, using defaults")
                return DEFAULT_WEIGHTS
            return {k: v / total for k, v in weights.items()}
    except Exception:
        logger.exception("Failed to load scoring config, using defaults")
        return DEFAULT_WEIGHTS

def compute_urgency(task: Task, today: Optional[date] = None) -> float:
    if today is None:
        today = datetime.now(timezone.utc).date()
    if not task.due_date:
        return 2.0
    days_left = (task.due_date - today).days
    if days_left < 0:
        return 10.0
    urgency = max(0.0, 10.0 - float(days_left))
    return min(max(urgency, 0.0), 10.0)

def compute_importance(task: Task) -> float:
    if task.importance is None:
        return 5.0
    return min(max(task.importance, 0.0), 10.0)

def compute_effort_score(task: Task) -> float:
    if task.estimated_hours is None:
        return 5.0
    h = task.estimated_hours
    if h <= 0:
        return 8.0
    if h <= 1:
        return 10.0
    if h <= 3:
        return 7.0
    if h <= 8:
        return 4.0
    return 1.0

def compute_dependency_score(task: Task, graph: Dict[str, Task]) -> float:
    if not task.id:
        return 2.0
    count = 0
    for t in graph.values():
        if task.id in t.dependencies:
            count += 1
    if count == 0:
        return 0.0
    return min(10.0, float(count) / 5.0 * 10.0)

def detect_cycles(tasks: Iterable[Task]) -> Optional[List[str]]:
    graph = {t.id if t.id is not None else str(i): t for i, t in enumerate(tasks)}
    visited: Set[str] = set()
    onstack: Set[str] = set()
    parent: Dict[str, str] = {}

    def dfs(node: str) -> Optional[List[str]]:
        visited.add(node)
        onstack.add(node)
        node_deps = graph[node].dependencies if graph[node].dependencies else []
        for dep in node_deps:
            if dep not in graph:
                continue
            if dep not in visited:
                parent[dep] = node
                cyc = dfs(dep)
                if cyc:
                    return cyc
            elif dep in onstack:
                path = [dep]
                cur = node
                while cur != dep:
                    path.append(cur)
                    cur = parent.get(cur, dep)
                    if cur is None:
                        break
                path.reverse()
                return path
        onstack.remove(node)
        return None

    for node in list(graph.keys()):
        if node not in visited:
            cyc = dfs(node)
            if cyc:
                return cyc
    return None

def score_task(task: Task, all_tasks: Dict[str, Task], weights: Optional[Dict[str, float]] = None, today: Optional[date] = None) -> Dict:
    weights = weights or DEFAULT_WEIGHTS
    today = today or datetime.now(timezone.utc).date()

    urgency = compute_urgency(task, today=today)
    importance = compute_importance(task)
    effort = compute_effort_score(task)
    dependency = compute_dependency_score(task, all_tasks)

    total = (
        weights["urgency"] * urgency
        + weights["importance"] * importance
        + weights["effort"] * effort
        + weights["dependency"] * dependency
    )

    explanation = {
        "urgency": round(urgency, 3),
        "importance": round(importance, 3),
        "effort": round(effort, 3),
        "dependency": round(dependency, 3),
        "weights": weights,
    }

    return {"score": round(total, 3), "explanation": explanation}

def analyze_tasks(task_dicts: List[Dict], weights: Optional[Dict[str, float]] = None, today: Optional[date] = None) -> Dict:
    today = today or datetime.now(timezone.utc).date()
    tasks: List[Task] = []
    errors: List[str] = []
    id_map: Dict[str, Task] = {}

    for i, raw in enumerate(task_dicts):
        try:
            t = Task.from_dict(raw)
            if not t.id:
                t.id = f"__generated__{i}"
            if t.id in id_map:
                t.id = f"{t.id}__dup__{i}"
            tasks.append(t)
            id_map[t.id] = t
        except ValueError as e:
            errors.append(str(e))

    cycle = detect_cycles(tasks)
    if cycle:
        return {"tasks": [], "sorted": [], "cycle": cycle, "errors": errors}

    scored = []
    for t in tasks:
        s = score_task(t, id_map, weights=weights, today=today)
        obj = {
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "estimated_hours": t.estimated_hours,
            "importance": t.importance,
            "dependencies": t.dependencies,
            "score": s["score"],
            "explanation": s["explanation"],
        }
        scored.append(obj)

    def tie_key(x):
        due = x["due_date"] or "9999-12-31"
        est = x["estimated_hours"] if x["estimated_hours"] is not None else 9999
        return (-x["score"], due, est, x["title"])

    sorted_tasks = sorted(scored, key=tie_key)

    return {"tasks": scored, "sorted": sorted_tasks, "cycle": None, "errors": errors}
