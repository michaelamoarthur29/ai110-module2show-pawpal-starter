"""PawPal+ logic layer.

Backend classes for the pet care planning assistant: Task, Pet, Owner, and
Scheduler. Mirrors diagrams/uml.mmd.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta

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

    def next_occurrence(self) -> Task | None:
        """Return the next unfinished copy of this task, or None if it doesn't repeat.

        timedelta does the date arithmetic, so month ends and leap days are
        handled for free: Jan 31 + 1 day is Feb 1, not an invalid Jan 32.
        """
        if not self.is_recurring():
            return None
        step = timedelta(days=_REPEAT_DAYS[self.frequency])
        return replace(self, date_time=self.date_time + step, completed=False)

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

    # --- sorting ---

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks in chronological order, earliest start first.

        Defaults to every task the owner has. `date_time` is a real datetime,
        so sorted() orders it directly — no "HH:MM" string parsing needed, and
        tasks on different days can't interleave the way text sorting would.
        """
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: t.date_time)

    def get_sorted_tasks(self) -> list[Task]:
        """Return all tasks ordered by priority, then by start time."""
        return sorted(self.get_all_tasks(), key=lambda t: (t.priority_rank(), t.date_time))

    # --- filtering ---

    def get_daily_tasks(self, day: date) -> list[Task]:
        """Return the tasks scheduled on the given day, in time order."""
        on_day = [t for t in self.get_all_tasks() if t.date_time.date() == day]
        return sorted(on_day, key=lambda t: (t.date_time, t.priority_rank()))

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return that pet's tasks in time order; empty if no pet has that name."""
        matches = [pet for pet in self.owner.get_pets() if pet.name == pet_name]
        return self.sort_by_time([task for pet in matches for task in pet.get_tasks()])

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return the finished tasks (completed=True) or the outstanding ones."""
        return self.sort_by_time([t for t in self.get_all_tasks() if t.completed == completed])

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        day: date | None = None,
    ) -> list[Task]:
        """Return tasks matching every filter given; a filter left as None is ignored."""
        tasks = self.get_all_tasks()
        if pet_name is not None:
            names = {pet.name for pet in self.owner.get_pets() if pet.name == pet_name}
            tasks = [t for t in tasks if self._pet_name(t) in names]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if day is not None:
            tasks = [t for t in tasks if t.date_time.date() == day]
        return self.sort_by_time(tasks)

    def _pet_name(self, task: Task) -> str | None:
        """Return the name of the pet a task belongs to, or None."""
        pet = self.pet_for(task)
        return pet.name if pet else None

    # --- conflicts ---

    def tasks_touching(self, day: date) -> list[Task]:
        """Return tasks overlapping the given day, including ones running into it.

        Unlike get_daily_tasks(), this keeps a task that starts at 23:50 the
        night before, because it is still running during `day` and can still
        collide with something scheduled on it.
        """
        window_start = datetime.combine(day, time.min)
        window_end = window_start + timedelta(days=1)
        return self.sort_by_time(
            [
                task
                for task in self.get_all_tasks()
                if task.date_time < window_end and task.end_time() > window_start
            ]
        )

    def detect_conflicts(self, day: date | None = None) -> list[tuple[Task, Task]]:
        """Return pairs of unfinished tasks whose time ranges overlap.

        Sorting by start time first means the inner loop can stop as soon as a
        task starts after the current one ends — everything later starts later
        still, so it can't overlap either.
        """
        tasks = self.tasks_touching(day) if day else self.get_all_tasks()
        pending = self.sort_by_time([t for t in tasks if not t.completed])

        conflicts: list[tuple[Task, Task]] = []
        for index, first in enumerate(pending):
            for second in pending[index + 1 :]:
                if second.date_time >= first.end_time():
                    break
                conflicts.append((first, second))
        return conflicts

    def conflict_warnings(self, day: date | None = None) -> list[str]:
        """Return a readable warning line per conflict — never raises, empty if none."""
        warnings = []
        for first, second in self.detect_conflicts(day):
            warnings.append(
                f"⚠️  {first.title} ({self._pet_name(first)}) "
                f"{first.date_time:%H:%M}–{first.end_time():%H:%M} overlaps "
                f"{second.title} ({self._pet_name(second)}) "
                f"{second.date_time:%H:%M}–{second.end_time():%H:%M}"
            )
        return warnings

    # --- recurring tasks ---

    def mark_task_complete(self, task: Task) -> Task | None:
        """Mark a task done and queue its next occurrence if it repeats.

        Returns the newly created follow-up task, or None when the task doesn't
        repeat or its next occurrence is already on the schedule.
        """
        task.mark_complete()

        follow_up = task.next_occurrence()
        if follow_up is None:
            return None

        pet = self.pet_for(task)
        if pet is None or pet.has_task(follow_up.title, follow_up.date_time):
            return None
        return pet.add_task(follow_up)

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
