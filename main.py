"""Terminal demo for the PawPal+ logic layer.

Builds a small owner/pet/task setup and prints today's schedule so you can
verify the classes in pawpal_system.py work end to end.

Run it with:  python main.py
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task

LINE_WIDTH = 58


def at(hour: int, minute: int = 0, day: date | None = None) -> datetime:
    """Return a datetime on the given day (today by default) at hour:minute."""
    return datetime.combine(day or date.today(), time(hour, minute))


def heading(text: str) -> None:
    """Print a section heading with a rule under it."""
    print(f"\n{text}")
    print("=" * LINE_WIDTH)


def build_demo_owner() -> Owner:
    """Return an owner with two pets and a handful of scheduled tasks."""
    owner = Owner("Jordan")

    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    biscuit = owner.add_pet(Pet("Biscuit", "cat", 7))

    mochi.add_task(Task("Morning walk", "exercise", at(8, 0), 30, "high", frequency="daily"))
    mochi.add_task(Task("Breakfast", "feeding", at(8, 45), 10, "high"))
    mochi.add_task(Task("Puzzle feeder", "enrichment", at(14, 0), 20, "low"))
    mochi.add_task(Task("Evening walk", "exercise", at(18, 30), 30, "medium"))

    biscuit.add_task(Task("Breakfast", "feeding", at(8, 50), 10, "high"))
    biscuit.add_task(Task("Thyroid meds", "medication", at(9, 0), 5, "high", frequency="daily"))
    biscuit.add_task(Task("Brushing", "grooming", at(19, 0), 15, "medium", frequency="weekly"))

    return owner


def print_pets(owner: Owner) -> None:
    """Print the owner's pets and how many tasks each one has."""
    heading(f"{owner.name}'s pets")
    for pet in owner.get_pets():
        print(f"  {pet}  -  {len(pet.get_tasks())} tasks")


def print_daily_schedule(scheduler: Scheduler, day: date, label: str) -> None:
    """Print one day's tasks in time order, tagged with the pet they belong to."""
    heading(f"{label} - {day:%A, %B %d}")
    tasks = scheduler.get_daily_tasks(day)
    if not tasks:
        print("  Nothing scheduled.")
        return
    for task in tasks:
        pet = scheduler.pet_for(task)
        pet_name = pet.name if pet else "unassigned"
        print(f"  {task}")
        print(f"      for {pet_name} - {task.task_type}")


def print_by_priority(scheduler: Scheduler) -> None:
    """Print every task ordered by priority, highest first."""
    heading("All tasks by priority")
    for task in scheduler.get_sorted_tasks():
        pet = scheduler.pet_for(task)
        print(f"  {task.priority:<7} {task.date_time:%a %H:%M}  {task.title} ({pet.name})")


def print_conflicts(scheduler: Scheduler, day: date) -> None:
    """Print any overlapping tasks the owner can't physically do at once."""
    heading("Scheduling conflicts")
    conflicts = scheduler.detect_conflicts(day)
    if not conflicts:
        print("  None - the day fits together.")
        return
    for first, second in conflicts:
        first_pet = scheduler.pet_for(first)
        second_pet = scheduler.pet_for(second)
        print(f"  ! {first.title} ({first_pet.name}) overlaps {second.title} ({second_pet.name})")
        print(f"      {first.date_time:%H:%M}-{first.end_time():%H:%M} vs "
              f"{second.date_time:%H:%M}-{second.end_time():%H:%M}")


def main() -> None:
    """Build the demo data and print the schedule, priorities, and conflicts."""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    print("PawPal+ daily plan")
    print_pets(owner)
    print_daily_schedule(scheduler, today, "Today's Schedule")
    print_by_priority(scheduler)
    print_conflicts(scheduler, today)

    heading("Marking the morning walk complete")
    walk = scheduler.get_daily_tasks(today)[0]
    walk.mark_complete()
    print(f"  {walk}")

    created = scheduler.create_recurring_tasks(until=tomorrow)
    heading(f"Rolled {len(created)} recurring tasks forward")
    print_daily_schedule(scheduler, tomorrow, "Tomorrow's Schedule")


if __name__ == "__main__":
    main()
