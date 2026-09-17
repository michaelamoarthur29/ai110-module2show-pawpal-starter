# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running the demo script exercises the whole logic layer in `pawpal_system.py`:

```bash
python main.py
```

```
PawPal+ daily plan

Jordan's pets
==========================================================
  Mochi (dog, 3)  -  4 tasks
  Biscuit (cat, 7)  -  3 tasks

Today's Schedule - Wednesday, September 16
==========================================================
  08:00 - Morning walk (30 min) [high, daily]
      for Mochi - exercise
  08:45 - Breakfast (10 min) [high]
      for Mochi - feeding
  08:50 - Breakfast (10 min) [high]
      for Biscuit - feeding
  09:00 - Thyroid meds (5 min) [high, daily]
      for Biscuit - medication
  14:00 - Puzzle feeder (20 min) [low]
      for Mochi - enrichment
  18:30 - Evening walk (30 min) [medium]
      for Mochi - exercise
  19:00 - Brushing (15 min) [medium, weekly]
      for Biscuit - grooming

All tasks by priority
==========================================================
  high    Wed 08:00  Morning walk (Mochi)
  high    Wed 08:45  Breakfast (Mochi)
  high    Wed 08:50  Breakfast (Biscuit)
  high    Wed 09:00  Thyroid meds (Biscuit)
  medium  Wed 18:30  Evening walk (Mochi)
  medium  Wed 19:00  Brushing (Biscuit)
  low     Wed 14:00  Puzzle feeder (Mochi)

Scheduling conflicts
==========================================================
  ! Breakfast (Mochi) overlaps Breakfast (Biscuit)
      08:45-08:55 vs 08:50-09:00

Marking the morning walk complete
==========================================================
  08:00 - Morning walk (30 min) [high, daily] ✓

Rolled 2 recurring tasks forward
==========================================================

Tomorrow's Schedule - Thursday, September 17
==========================================================
  08:00 - Morning walk (30 min) [high, daily]
      for Mochi - exercise
  09:00 - Thyroid meds (5 min) [high, daily]
      for Biscuit - medication
```

The two 10-minute breakfasts at 08:45 and 08:50 are deliberate — they show
`detect_conflicts()` catching an overlap across two different pets. Only the
two `daily` tasks roll into tomorrow; Biscuit's `weekly` brushing is not due
again until next week.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/mikeyamo-arthur/Documents/ai110-module2show-pawpal-starter
plugins: anyio-4.11.0
collected 14 items

tests/test_pawpal.py ..............                                      [100%]

============================== 14 passed in 0.03s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.get_sorted_tasks()` | Orders by priority (high → medium → low), then start time |
| Filtering | `Scheduler.get_daily_tasks(day)` | Keeps only tasks on the requested date, in time order |
| Conflict handling | `Scheduler.detect_conflicts(day=None)` | Returns pairs of unfinished tasks whose ranges overlap, across all pets; back-to-back tasks don't count |
| Recurring tasks | `Scheduler.create_recurring_tasks(until)`, `Task.is_recurring()` | Expands `daily` / `weekly` tasks into dated copies through `until`; skips occurrences that already exist so re-running is safe |
| Task duration | `Task.end_time()` | Start time plus `duration_minutes` — what makes conflict detection possible |
| Reading pet data | `Owner.get_all_tasks()`, `Scheduler.pet_for(task)` | The scheduler holds an `Owner` and reads tasks through its pets, so there is one source of truth |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
