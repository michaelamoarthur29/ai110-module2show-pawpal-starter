"""Terminal demo for the PawPal+ logic layer.

Builds a small owner/pet/task setup — deliberately adding tasks out of
chronological order — and exercises sorting, filtering, conflict detection,
and recurring tasks so you can verify pawpal_system.py from the terminal.

Run it with:  python main.py
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task

LINE_WIDTH = 62


def at(hour: int, minute: int = 0, day: date | None = None) -> datetime:
    """Return a datetime on the given day (today by default) at hour:minute."""
    return datetime.combine(day or date.today(), time(hour, minute))


def heading(text: str) -> None:
    """Print a section heading with a rule under it."""
    print(f"\n{text}")
    print("=" * LINE_WIDTH)


def line(task: Task, scheduler: Scheduler) -> str:
    """Return one formatted schedule row for a task."""
    pet = scheduler.pet_for(task)
    pet_name = pet.name if pet else "unassigned"
    status = "✓" if task.completed else " "
    repeats = f" ({task.frequency})" if task.is_recurring() else ""
    return (
        f"  [{status}] {task.date_time:%a %H:%M}–{task.end_time():%H:%M}  "
        f"{task.title:<16} {pet_name:<9} {task.priority:<7}{repeats}"
    )


def build_demo_owner() -> Owner:
    """Return an owner with two pets whose tasks are added out of time order."""
    owner = Owner("Jordan")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    biscuit = owner.add_pet(Pet("Biscuit", "cat", 7))

    # Deliberately out of chronological order — the scheduler does the sorting.
    mochi.add_task(Task("Evening walk", "exercise", at(18, 30), 30, "medium"))
    biscuit.add_task(Task("Brushing", "grooming", at(19, 0), 15, "low", frequency="weekly"))
    mochi.add_task(Task("Morning walk", "exercise", at(8, 0), 30, "high", frequency="daily"))
    mochi.add_task(Task("Puzzle feeder", "enrichment", at(14, 0), 20, "low"))
    biscuit.add_task(Task("Thyroid meds", "medication", at(9, 0), 5, "high", frequency="daily"))

    # Two tasks at exactly the same time, on two different pets: the owner
    # cannot be in both places at 08:45, so this must be flagged.
    mochi.add_task(Task("Breakfast", "feeding", at(8, 45), 10, "high"))
    biscuit.add_task(Task("Breakfast", "feeding", at(8, 45), 10, "high"))

    return owner


def demo_sorting(scheduler: Scheduler) -> None:
    """Show the same tasks ordered by time and then by priority."""
    heading("Sorted by time — Scheduler.sort_by_time()")
    for task in scheduler.sort_by_time():
        print(line(task, scheduler))

    heading("Sorted by priority — Scheduler.get_sorted_tasks()")
    for task in scheduler.get_sorted_tasks():
        print(line(task, scheduler))


def demo_filtering(scheduler: Scheduler) -> None:
    """Show filtering by pet and by completion status."""
    heading("Filtered to Biscuit — Scheduler.filter_by_pet('Biscuit')")
    for task in scheduler.filter_by_pet("Biscuit"):
        print(line(task, scheduler))

    heading("Outstanding tasks — Scheduler.filter_by_status(completed=False)")
    for task in scheduler.filter_by_status(completed=False):
        print(line(task, scheduler))

    heading("Combined — Mochi's outstanding tasks today")
    for task in scheduler.filter_tasks(pet_name="Mochi", completed=False, day=date.today()):
        print(line(task, scheduler))


def demo_conflicts(scheduler: Scheduler) -> None:
    """Show the conflict warnings for today, if any."""
    heading("Conflict check — Scheduler.conflict_warnings()")
    warnings = scheduler.conflict_warnings(date.today())
    if not warnings:
        print("  No conflicts — the day fits together.")
        return
    for warning in warnings:
        print(f"  {warning}")
    print(f"\n  {len(warnings)} conflict(s) found. Nothing crashed — these are warnings.")


def demo_recurring(scheduler: Scheduler) -> None:
    """Complete a daily task and show its next occurrence appear automatically."""
    heading("Completing a daily task — Scheduler.mark_task_complete()")
    walk = next(t for t in scheduler.sort_by_time() if t.title == "Morning walk")
    print(f"  Before: {len(scheduler.get_all_tasks())} tasks total")

    follow_up = scheduler.mark_task_complete(walk)

    print(f"  Completed: {walk.title} on {walk.date_time:%a %d %b}")
    if follow_up:
        print(f"  Auto-created: {follow_up.title} on {follow_up.date_time:%a %d %b} "
              f"(completed={follow_up.completed})")
    print(f"  After:  {len(scheduler.get_all_tasks())} tasks total")

    heading("Tomorrow's schedule")
    tomorrow = date.today() + timedelta(days=1)
    for task in scheduler.get_daily_tasks(tomorrow):
        print(line(task, scheduler))


def main() -> None:
    """Run every demo section against one shared owner."""
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    print("PawPal+ scheduling demo")
    heading(f"{owner.name}'s pets")
    for pet in owner.get_pets():
        print(f"  {pet}  -  {len(pet.get_tasks())} tasks")

    demo_sorting(scheduler)
    demo_filtering(scheduler)
    demo_conflicts(scheduler)
    demo_recurring(scheduler)


if __name__ == "__main__":
    main()
