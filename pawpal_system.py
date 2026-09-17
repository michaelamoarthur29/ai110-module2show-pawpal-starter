"""PawPal+ logic layer.

Backend classes for the pet care planning assistant: Task, Pet, Owner, and
Scheduler. Mirrors diagrams/uml.mmd.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta

# Task.frequency values
FREQUENCIES = ("none", "daily", "weekly")

# Task.priority values, most urgent first
PRIORITIES = ("high", "medium", "low")

# How many days apart each frequency repeats
_REPEAT_DAYS = {"daily": 1, "weekly": 7}


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

    def __post_init__(self) -> None:
        """Reject priorities, frequencies, and durations the scheduler can't use."""
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {PRIORITIES}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not done again."""
        self.completed = False

    def end_time(self) -> datetime:
        """Return when this task finishes (start time plus its duration)."""
        return self.date_time + timedelta(minutes=self.duration_minutes)

    def is_recurring(self) -> bool:
        """Return True if this task repeats on a schedule."""
        return self.frequency != "none"

    def overlaps(self, other: Task) -> bool:
        """Return True if this task's time range overlaps another's."""
        return self.date_time < other.end_time() and other.date_time < self.end_time()

    def priority_rank(self) -> int:
        """Return a sort key for priority, where 0 is the most urgent."""
        return PRIORITIES.index(self.priority)

    def __str__(self) -> str:
        """Return a one-line summary, e.g. '08:00 - Morning walk (30 min) [high]'."""
        status = " ✓" if self.completed else ""
        repeats = f", {self.frequency}" if self.is_recurring() else ""
        return (
            f"{self.date_time:%H:%M} - {self.title} "
            f"({self.duration_minutes} min) [{self.priority}{repeats}]{status}"
        )


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> Task:
        """Attach a task to this pet and return it."""
        self.tasks.append(task)
        return task

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)

    def has_task(self, title: str, date_time: datetime) -> bool:
        """Return True if this pet already has a task with that title and start time."""
        return any(t.title == title and t.date_time == date_time for t in self.tasks)

    def __str__(self) -> str:
        """Return a one-line summary, e.g. 'Mochi (dog, 3)'."""
        return f"{self.name} ({self.species}, {self.age})"


@dataclass
class Owner:
    """A pet owner and the pets they care for."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> Pet:
        """Add a pet to this owner and return it."""
        self.pets.append(pet)
        return pet

    def get_pets(self) -> list[Pet]:
        """Return a copy of this owner's pet list."""
        return list(self.pets)

    def get_all_tasks(self) -> list[Task]:
        """Return every task belonging to every pet this owner has."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def __str__(self) -> str:
        """Return a one-line summary, e.g. 'Jordan (2 pets)'."""
        return f"{self.name} ({len(self.pets)} pets)"


@dataclass
class Scheduler:
    """Retrieves, organizes, and manages tasks across all of an owner's pets."""

    owner: Owner

    @property
    def pets(self) -> list[Pet]:
        """Return the pets this scheduler manages, read from its owner."""
        return self.owner.get_pets()

    def get_all_tasks(self) -> list[Task]:
        """Return every task across the owner's pets."""
        return self.owner.get_all_tasks()

    def pet_for(self, task: Task) -> Pet | None:
        """Return the pet a task belongs to, or None if no pet owns it."""
        for pet in self.owner.get_pets():
            if any(t is task for t in pet.tasks):
                return pet
        return None

    def get_sorted_tasks(self) -> list[Task]:
        """Return all tasks ordered by priority, then by start time."""
        return sorted(self.get_all_tasks(), key=lambda t: (t.priority_rank(), t.date_time))

    def get_daily_tasks(self, day: date) -> list[Task]:
        """Return the tasks scheduled on the given day, in time order."""
        on_day = [t for t in self.get_all_tasks() if t.date_time.date() == day]
        return sorted(on_day, key=lambda t: (t.date_time, t.priority_rank()))

    def detect_conflicts(self, day: date | None = None) -> list[tuple[Task, Task]]:
        """Return pairs of unfinished tasks whose time ranges overlap."""
        tasks = self.get_daily_tasks(day) if day else self.get_all_tasks()
        pending = sorted((t for t in tasks if not t.completed), key=lambda t: t.date_time)
        return [
            (first, second)
            for i, first in enumerate(pending)
            for second in pending[i + 1 :]
            if first.overlaps(second)
        ]

    def create_recurring_tasks(self, until: date) -> list[Task]:
        """Expand each recurring task into dated copies through `until` and attach them."""
        created: list[Task] = []
        for pet in self.owner.get_pets():
            for task in pet.get_tasks():
                if not task.is_recurring():
                    continue
                step = timedelta(days=_REPEAT_DAYS[task.frequency])
                occurrence = task.date_time + step
                while occurrence.date() <= until:
                    if not pet.has_task(task.title, occurrence):
                        created.append(
                            pet.add_task(replace(task, date_time=occurrence, completed=False))
                        )
                    occurrence += step
        return created
