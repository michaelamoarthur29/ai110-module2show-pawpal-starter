"""PawPal+ logic layer.

Backend classes for the pet care planning assistant. These are skeletons
generated from diagrams/uml.mmd — attributes and method signatures only,
no scheduling logic yet.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

# Task.frequency values
FREQUENCIES = ("none", "daily", "weekly")

# Task.priority values
PRIORITIES = ("low", "medium", "high")


@dataclass
class Task:
    """A single care task, e.g. a 20-minute morning walk at high priority."""

    title: str
    task_type: str
    date_time: datetime
    duration_minutes: int
    priority: str = "medium"
    completed: bool = False
    frequency: str = "none"

    def mark_complete(self) -> None:
        """Mark this task as done."""
        raise NotImplementedError

    def end_time(self) -> datetime:
        """Return when this task finishes (start + duration)."""
        raise NotImplementedError

    def is_recurring(self) -> bool:
        """Return True if this task repeats."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        raise NotImplementedError

    def get_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        raise NotImplementedError


@dataclass
class Owner:
    """A pet owner and the pets they care for."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def get_pets(self) -> list[Pet]:
        """Return this owner's pets."""
        raise NotImplementedError


@dataclass
class Scheduler:
    """Plans and organizes tasks across the pets it manages."""

    pets: list[Pet] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def get_sorted_tasks(self) -> list[Task]:
        """Return all tasks ordered by priority, then start time."""
        raise NotImplementedError

    def get_daily_tasks(self, day: date) -> list[Task]:
        """Return the tasks scheduled on the given day."""
        raise NotImplementedError

    def detect_conflicts(self) -> list[tuple[Task, Task]]:
        """Return pairs of tasks whose time ranges overlap."""
        raise NotImplementedError

    def create_recurring_tasks(self, until: date) -> list[Task]:
        """Expand recurring tasks into dated copies through `until`."""
        raise NotImplementedError
