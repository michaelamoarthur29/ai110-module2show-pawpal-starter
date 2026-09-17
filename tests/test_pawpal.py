"""Tests for the PawPal+ logic layer."""

from datetime import date, datetime, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

TODAY = date(2026, 9, 16)


def make_task(title="Morning walk", hour=8, minute=0, duration=30, **kwargs):
    """Return a Task on TODAY at the given time, with sensible defaults."""
    return Task(
        title=title,
        task_type=kwargs.pop("task_type", "exercise"),
        date_time=datetime.combine(TODAY, datetime.min.time()).replace(hour=hour, minute=minute),
        duration_minutes=duration,
        **kwargs,
    )


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from not-done to done."""
    task = make_task()
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_mark_incomplete_undoes_completion():
    """mark_incomplete() puts a finished task back to not-done."""
    task = make_task()
    task.mark_complete()

    task.mark_incomplete()

    assert task.completed is False


def test_adding_a_task_increases_pet_task_count():
    """Adding a task to a Pet raises that pet's task count by one."""
    pet = Pet("Mochi", "dog", 3)
    assert len(pet.get_tasks()) == 0

    pet.add_task(make_task())

    assert len(pet.get_tasks()) == 1


def test_end_time_is_start_plus_duration():
    """A task's end time is its start time plus its duration."""
    task = make_task(hour=8, minute=0, duration=30)

    assert task.end_time() == task.date_time + timedelta(minutes=30)


def test_owner_collects_tasks_from_every_pet():
    """Owner.get_all_tasks() returns the tasks of all its pets combined."""
    owner = Owner("Jordan")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    biscuit = owner.add_pet(Pet("Biscuit", "cat", 7))
    mochi.add_task(make_task("Walk"))
    biscuit.add_task(make_task("Meds", hour=9))

    titles = [task.title for task in owner.get_all_tasks()]

    assert sorted(titles) == ["Meds", "Walk"]


def test_scheduler_sorts_by_priority_then_time():
    """get_sorted_tasks() puts high priority first and orders ties by start time."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    pet.add_task(make_task("Puzzle", hour=14, priority="low"))
    pet.add_task(make_task("Late meds", hour=20, priority="high"))
    pet.add_task(make_task("Walk", hour=8, priority="high"))

    order = [task.title for task in Scheduler(owner).get_sorted_tasks()]

    assert order == ["Walk", "Late meds", "Puzzle"]


def test_detect_conflicts_finds_overlapping_tasks():
    """Two tasks whose time ranges overlap are reported as a conflict."""
    owner = Owner("Jordan")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    biscuit = owner.add_pet(Pet("Biscuit", "cat", 7))
    mochi.add_task(make_task("Mochi breakfast", hour=8, minute=45, duration=10))
    biscuit.add_task(make_task("Biscuit breakfast", hour=8, minute=50, duration=10))
    mochi.add_task(make_task("Evening walk", hour=18, duration=30))

    conflicts = Scheduler(owner).detect_conflicts()

    assert len(conflicts) == 1
    assert {conflicts[0][0].title, conflicts[0][1].title} == {
        "Mochi breakfast",
        "Biscuit breakfast",
    }


def test_back_to_back_tasks_do_not_conflict():
    """A task starting exactly when another ends is not a conflict."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    pet.add_task(make_task("Walk", hour=8, duration=30))
    pet.add_task(make_task("Breakfast", hour=8, minute=30, duration=10))

    assert Scheduler(owner).detect_conflicts() == []


def test_create_recurring_tasks_expands_daily_task():
    """A daily task is copied forward one occurrence per day through `until`."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    pet.add_task(make_task("Walk", hour=8, frequency="daily"))
    scheduler = Scheduler(owner)

    created = scheduler.create_recurring_tasks(until=TODAY + timedelta(days=3))

    assert len(created) == 3
    assert [t.date_time.date() for t in created] == [
        TODAY + timedelta(days=n) for n in (1, 2, 3)
    ]


def test_create_recurring_tasks_is_not_duplicated_on_a_second_run():
    """Running the expansion twice does not create duplicate occurrences."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    pet.add_task(make_task("Walk", hour=8, frequency="daily"))
    scheduler = Scheduler(owner)
    until = TODAY + timedelta(days=3)

    scheduler.create_recurring_tasks(until=until)
    second_run = scheduler.create_recurring_tasks(until=until)

    assert second_run == []
    assert len(pet.get_tasks()) == 4


def test_one_off_task_is_not_expanded():
    """A task with frequency 'none' produces no future occurrences."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    pet.add_task(make_task("Vet visit", hour=11))

    assert Scheduler(owner).create_recurring_tasks(until=TODAY + timedelta(days=7)) == []


def test_get_daily_tasks_only_returns_that_day():
    """get_daily_tasks() filters out tasks scheduled on other days."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    today_task = make_task("Walk", hour=8)
    tomorrow_task = make_task("Walk", hour=8)
    tomorrow_task.date_time += timedelta(days=1)
    pet.add_task(today_task)
    pet.add_task(tomorrow_task)

    assert Scheduler(owner).get_daily_tasks(TODAY) == [today_task]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"priority": "urgent"},
        {"frequency": "hourly"},
        {"duration": 0},
    ],
)
def test_invalid_task_values_are_rejected(kwargs):
    """Task refuses priorities, frequencies, and durations the scheduler can't use."""
    with pytest.raises(ValueError):
        make_task(**kwargs)
