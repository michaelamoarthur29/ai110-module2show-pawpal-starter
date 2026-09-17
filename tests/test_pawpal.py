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


# --- sorting and filtering -------------------------------------------------


def two_pet_owner():
    """Return an owner with Mochi and Biscuit and tasks added out of time order."""
    owner = Owner("Jordan")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    biscuit = owner.add_pet(Pet("Biscuit", "cat", 7))
    mochi.add_task(make_task("Evening walk", hour=18))
    biscuit.add_task(make_task("Meds", hour=9, duration=5))
    mochi.add_task(make_task("Morning walk", hour=8))
    return owner, mochi, biscuit


def test_sort_by_time_orders_chronologically():
    """sort_by_time() returns tasks earliest-first regardless of insertion order."""
    owner, _, _ = two_pet_owner()

    order = [t.title for t in Scheduler(owner).sort_by_time()]

    assert order == ["Morning walk", "Meds", "Evening walk"]


def test_sort_by_time_spans_days_correctly():
    """Sorting uses real datetimes, so a late task today precedes an early one tomorrow."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    early_tomorrow = make_task("Tomorrow 06:00", hour=6)
    early_tomorrow.date_time += timedelta(days=1)
    pet.add_task(early_tomorrow)
    pet.add_task(make_task("Today 23:00", hour=23))

    order = [t.title for t in Scheduler(owner).sort_by_time()]

    assert order == ["Today 23:00", "Tomorrow 06:00"]


def test_filter_by_pet_returns_only_that_pets_tasks():
    """filter_by_pet() narrows to one pet's tasks, in time order."""
    owner, _, _ = two_pet_owner()

    titles = [t.title for t in Scheduler(owner).filter_by_pet("Mochi")]

    assert titles == ["Morning walk", "Evening walk"]


def test_filter_by_pet_with_unknown_name_is_empty():
    """An unknown pet name returns an empty list rather than raising."""
    owner, _, _ = two_pet_owner()

    assert Scheduler(owner).filter_by_pet("Nobody") == []


def test_filter_by_status_splits_done_from_outstanding():
    """filter_by_status() separates finished tasks from the rest."""
    owner, mochi, _ = two_pet_owner()
    mochi.get_tasks()[0].mark_complete()  # Evening walk
    scheduler = Scheduler(owner)

    done = [t.title for t in scheduler.filter_by_status(completed=True)]
    outstanding = [t.title for t in scheduler.filter_by_status(completed=False)]

    assert done == ["Evening walk"]
    assert outstanding == ["Morning walk", "Meds"]


def test_filter_tasks_combines_filters():
    """filter_tasks() applies pet, status, and day together; None means 'ignore'."""
    owner, mochi, _ = two_pet_owner()
    mochi.get_tasks()[0].mark_complete()  # Evening walk
    scheduler = Scheduler(owner)

    result = scheduler.filter_tasks(pet_name="Mochi", completed=False, day=TODAY)

    assert [t.title for t in result] == ["Morning walk"]


def test_filter_tasks_with_no_filters_returns_everything():
    """Calling filter_tasks() with no arguments returns all tasks in time order."""
    owner, _, _ = two_pet_owner()

    assert len(Scheduler(owner).filter_tasks()) == 3


# --- conflict warnings -----------------------------------------------------


def test_identical_start_times_are_a_conflict():
    """Two tasks starting at exactly the same time overlap."""
    owner = Owner("Jordan")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    biscuit = owner.add_pet(Pet("Biscuit", "cat", 7))
    mochi.add_task(make_task("Mochi breakfast", hour=8, minute=45, duration=10))
    biscuit.add_task(make_task("Biscuit breakfast", hour=8, minute=45, duration=10))

    assert len(Scheduler(owner).detect_conflicts()) == 1


def test_conflict_warnings_returns_strings_not_exceptions():
    """conflict_warnings() reports overlaps as readable text instead of raising."""
    owner = Owner("Jordan")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    biscuit = owner.add_pet(Pet("Biscuit", "cat", 7))
    mochi.add_task(make_task("Walk", hour=8, duration=30))
    biscuit.add_task(make_task("Meds", hour=8, minute=15, duration=5))

    warnings = Scheduler(owner).conflict_warnings()

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Meds" in warnings[0]
    assert "Mochi" in warnings[0] and "Biscuit" in warnings[0]


def test_conflict_warnings_is_empty_when_the_day_fits():
    """A day with no overlaps produces no warnings."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    pet.add_task(make_task("Walk", hour=8, duration=30))
    pet.add_task(make_task("Lunch", hour=12, duration=15))

    assert Scheduler(owner).conflict_warnings() == []


def test_completed_tasks_are_not_conflicts():
    """A finished task can't conflict with anything — it already happened."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    walk = pet.add_task(make_task("Walk", hour=8, duration=30))
    pet.add_task(make_task("Meds", hour=8, minute=15, duration=5))
    walk.mark_complete()

    assert Scheduler(owner).detect_conflicts() == []


# --- recurrence on completion ----------------------------------------------


def test_completing_a_daily_task_creates_tomorrows_copy():
    """Completing a daily task automatically queues the next day's occurrence."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    walk = pet.add_task(make_task("Walk", hour=8, frequency="daily"))

    follow_up = Scheduler(owner).mark_task_complete(walk)

    assert walk.completed is True
    assert follow_up is not None
    assert follow_up.completed is False
    assert follow_up.date_time.date() == TODAY + timedelta(days=1)
    assert len(pet.get_tasks()) == 2


def test_completing_a_weekly_task_jumps_seven_days():
    """A weekly task's next occurrence lands a week later."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    brush = pet.add_task(make_task("Brushing", hour=19, frequency="weekly"))

    follow_up = Scheduler(owner).mark_task_complete(brush)

    assert follow_up.date_time.date() == TODAY + timedelta(days=7)


def test_completing_a_one_off_task_creates_nothing():
    """A non-recurring task is simply marked done, with no follow-up."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    vet = pet.add_task(make_task("Vet visit", hour=11))

    follow_up = Scheduler(owner).mark_task_complete(vet)

    assert vet.completed is True
    assert follow_up is None
    assert len(pet.get_tasks()) == 1


def test_completion_does_not_duplicate_an_existing_occurrence():
    """If tomorrow's copy already exists, completing today creates no duplicate."""
    owner = Owner("Jordan")
    pet = owner.add_pet(Pet("Mochi", "dog", 3))
    walk = pet.add_task(make_task("Walk", hour=8, frequency="daily"))
    scheduler = Scheduler(owner)
    scheduler.create_recurring_tasks(until=TODAY + timedelta(days=2))
    count_before = len(pet.get_tasks())

    follow_up = scheduler.mark_task_complete(walk)

    assert follow_up is None
    assert len(pet.get_tasks()) == count_before


def test_next_occurrence_leaves_the_original_untouched():
    """next_occurrence() returns a new Task without mutating the one it came from."""
    task = make_task("Walk", hour=8, frequency="daily")
    task.mark_complete()

    follow_up = task.next_occurrence()

    assert task.completed is True
    assert follow_up.completed is False
    assert follow_up is not task
    assert task.date_time.date() == TODAY
