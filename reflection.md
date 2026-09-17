# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each? 

Three core actions a PawPal+ user should be able to perform are:

1. **Add and manage pets** — An owner should be able to add a pet and store basic information such as the pet's name, species, age, and care needs.

2. **Create and manage tasks** — An owner should be able to schedule tasks such as feedings, walks, medications, and veterinary appointments for a specific pet.

3. **View an organized daily schedule** — The system should display upcoming pet-care tasks in a useful order based on factors such as time and priority so owners can easily see what needs to be completed. 

I designed PawPal+ around four main classes: Owner, Pet, Task, and Scheduler. The Owner class represents the person using the system and keeps track of their pets. The Pet class stores information about each animal and the care tasks associated with it. The Task class represents individual responsibilities such as feeding, walking, medications, or appointments. Finally, the Scheduler class handles the algorithmic side of the application by organizing tasks, filtering them by date, detecting scheduling conflicts, and managing recurring tasks.

I kept these responsibilities separate so that each class has one clear purpose. This should also make the system easier to test and expand when the Streamlit interface is added later.

**b. Design changes**

Yes. Three changes mattered, and the first was the most important.

**1. `Scheduler` stopped keeping its own task list.**

My original UML gave `Scheduler` both a `pets` list and a `tasks` list, mirroring
the idea that the scheduler "manages tasks and pets." As soon as I wrote the
class stubs, the problem was obvious: `Pet` already holds its own tasks, so
`Scheduler.tasks` would be a second copy of the same data. A task added with
`Pet.add_task()` would be invisible to the scheduler, and `get_daily_tasks()`
would silently work from stale information — the worst kind of bug, because
nothing crashes and the answer is just quietly wrong.

I replaced both fields with a single `owner` reference. `Scheduler` now reads
everything through `owner.get_all_tasks()`, which flattens `pet.get_tasks()`
across every pet, and exposes `pets` as a computed property. There is exactly
one place a task can live, so the two can never drift apart.

**2. `Task` gained `duration_minutes`.**

My first draft gave `Task` only a `date_time`. That is enough to say when
something starts but not when it ends, which makes "do these two tasks
conflict?" unanswerable — the best you could do is check for identical start
times. Adding a duration gave me `end_time()`, and with a real interval the
conflict check became a genuine overlap test instead of an equality test.

**3. `recurring: bool` became `frequency: str`.**

A boolean says *that* a task repeats but not *how often*, so
`create_recurring_tasks()` had nothing to read. I replaced it with a string
(`"none"` / `"daily"` / `"weekly"`) and kept an `is_recurring()` method so the
calling code still reads as a simple yes/no question. One field carries both
facts, which means they cannot contradict each other.

I also added two methods late, driven by the UI rather than the design:
`Task.mark_incomplete()`, so unticking a checkbox goes through a method instead
of the interface writing to `task.completed` directly, and
`Scheduler.tasks_touching()`, which fixed a real bug described in section 4.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler considers five things:

| Constraint | Where it lives | What it drives |
|---|---|---|
| **Start time** | `Task.date_time` | Chronological ordering (`sort_by_time()`) and day filtering |
| **Duration** | `Task.duration_minutes` → `end_time()` | Conflict detection, and the "minutes of care" total in the UI |
| **Priority** | `Task.priority` → `priority_rank()` | Priority ordering (`get_sorted_tasks()`), high → medium → low |
| **Completion** | `Task.completed` | Filtering, and excluding finished tasks from conflicts |
| **Frequency** | `Task.frequency` | Whether a completed task queues its next occurrence |

The sixth constraint is implicit but it is the one that makes the app useful:
**the owner is a shared resource across all their pets.** That is why
`detect_conflicts()` compares tasks across pets rather than within each pet. Two
tasks for the same pet clashing is obvious; a dog walk colliding with a cat's
medication is the failure a busy owner actually makes, because each pet's list
looks fine on its own.

**How I decided what mattered most.** I worked backwards from what would make
the plan *wrong* rather than merely unsorted. Time and duration came first,
because without them the system cannot answer "does this day fit?" at all —
that is why I added `duration_minutes` even though it was not in my original
brainstorm. Priority came second: it changes the order you *should* do things
but never makes the schedule impossible. Completion and frequency are
bookkeeping that keeps the plan current as the day goes on.

Deliberately out of scope: owner availability windows (working hours, sleep),
travel time between tasks, and dependencies between tasks (walk before
breakfast). Each would be a real improvement, but each also requires the owner
to enter a lot more information, and a planner nobody fills in is worse than a
simple one they do.

**b. Tradeoffs**

**The tradeoff: conflicts are detected as overlapping durations, but the
scheduler only warns — it never reorders or refuses a task.**

`Scheduler.detect_conflicts()` compares full time ranges, not just start times.
Each `Task` carries `duration_minutes`, so `end_time()` gives a real interval and
two tasks conflict when `first.date_time < second.end_time() and
second.date_time < first.end_time()`. That catches a 30-minute walk at 08:00
colliding with meds at 08:15, which an exact-start-time check would miss
entirely. Back-to-back tasks are deliberately *not* conflicts: a task starting
exactly when another ends is fine.

What the scheduler does *not* do is act on that finding.
`Scheduler.conflict_warnings()` returns a list of strings and
`mark_task_complete()` will happily complete a conflicted task. Nothing raises.
The owner is told "these two overlap" and decides what to do.

This is reasonable here because the scheduler doesn't know enough to resolve
the conflict correctly. Two pets needing breakfast at 08:45 might be a genuine
problem, or they might share one kitchen and take 30 seconds each. Auto-shifting
a medication dose to clear an overlap would be actively worse than leaving it
alone — the constraint that matters (when the vet said to give the pill) lives
outside the system. Warnings keep the human in the loop where the system's
information runs out.

Two known limits of the current approach:

- Conflict detection is pairwise and `O(n²)` in the worst case, though sorting
  by start time first lets the inner loop break early once a task starts after
  the current one ends. For one owner's daily task list this is irrelevant; for
  thousands of tasks an interval tree would be the right structure.
- Unticking a completed recurring task does not remove the follow-up occurrence
  that completing it created. Deleting it automatically risked destroying a task
  the owner had since edited, so the follow-up stays and can be removed by hand.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful? 

Used Ai to go over brainstorming ideas and coding said ideas, as well as refactoring code. 

More detailed prompts proved to be very helpful and more succesful.

**b. Judgment and verification**

**The suggestion I rejected: a "clever" one-line conflict detector.**

The first version of `detect_conflicts()` was a nested list comprehension that
compared every pair of tasks:

```python
return [
    (first, second)
    for i, first in enumerate(pending)
    for second in pending[i + 1:]
    if first.overlaps(second)
]
```

It is compact and it works. I replaced it with an explicit nested loop, because
the comprehension could not express the optimization the problem actually
allows: if the tasks are sorted by start time, then once you reach a task that
starts *after* the current one ends, every task after it starts later still and
cannot overlap either. You can stop scanning:

```python
for index, first in enumerate(pending):
    for second in pending[index + 1:]:
        if second.date_time >= first.end_time():
            break
        conflicts.append((first, second))
```

This was the unusual case where the less clever version won on both counts —
easier to read *and* faster, since it avoids comparing every pair. The lesson I
took was that "more Pythonic" is a style judgment, not a correctness or
performance one, and a comprehension that cannot break early is the wrong tool
no matter how neat it looks.

**How I verified suggestions generally.** Three habits:

1. **Run it, don't read it.** Every phase ended with `python -m pytest` and
   `python main.py`. For the Streamlit layer I went further and drove the real
   app through Streamlit's own `AppTest` runtime, which executes the script and
   operates the actual widgets — that is how I confirmed filters narrow
   correctly and the conflict markers land on the right rows.
2. **Probe edge cases before writing the test.** Instead of asking whether the
   code looked right, I ran the awkward inputs directly — an owner with no pets,
   a task crossing midnight, a weekly task spanning a leap day — and looked at
   what actually came back. That is how I found the bug in section 4.
3. **Check the diagram against the code mechanically.** Rather than eyeballing
   whether `uml_final.mmd` still matched, I extracted every method name from the
   diagram and confirmed all 27 exist in `pawpal_system.py`. Documentation drifts
   silently; a check that fails is worth more than a careful read.

**c. AI strategy**

**Which features were most effective.** Three, in order:

- **Agent/edit mode across multiple files.** The recurrence change in Phase 3
  touched `Task`, `Scheduler`, `app.py`, and the tests at once. Making that edit
  as one coherent change, rather than four disconnected snippets I had to
  reconcile by hand, is where the assistant saved the most time.
- **Chat on a specific method.** Asking about one function I could see on screen
  produced far better answers than asking about "my scheduler." The conflict
  detector rewrite came out of exactly that kind of narrow question.
- **Test generation from a stated plan.** Once I had written down the five
  behaviors I wanted covered, generating the cases was fast. Writing the plan
  first was the part that mattered — asking for "some tests" produced shallow
  ones that only confirmed what the code already did.

**A suggestion I modified to keep the design clean.** When the UI needed to untick
a completed task, the straightforward fix was to have `app.py` write
`task.completed = False` directly. That works, but it puts the interface in
charge of the logic layer's internal state — and `mark_complete()` existing as a
method while its opposite was a raw attribute assignment is exactly the kind of
inconsistency that spreads. I added `Task.mark_incomplete()` instead, so state
changes go through the class that owns them. The same judgment came up when the
UI needed a task's pet name and the only available method was named
`_pet_name()`; rather than call a private method from outside the class, I
renamed it `pet_name_for()` and made it part of the interface.

**Separating work by phase.** Keeping each phase's work in its own context —
design, implementation, algorithms, testing, packaging — made a real difference,
because each phase has a different question in front of it. When I was writing
tests I wanted to be adversarial and hunt for what breaks; when I was
implementing I wanted to make things work. Mixing those two mindsets in one
conversation tends to produce tests that agree with the code, since the same
reasoning that wrote the function is the reasoning checking it. Starting the
testing phase fresh, from a stated plan rather than from the implementation
conversation, is what led me to probe the midnight boundary at all.

**What being "lead architect" meant.** The assistant was faster than me at
producing correct code for a well-specified problem and consistently worse at
deciding what the problem was. Every decision that shaped the system was a
judgment call it could not have made for me: that `Scheduler` should have one
source of truth rather than two lists; that a conflict deserves a warning rather
than an automatic fix, because the system does not know why the vet chose that
dosing time; that `duration_minutes` had to exist before conflict detection
meant anything. Those are decisions about what the software is *for*.

The concrete lesson is that generated code is only as good as the specification
behind it, and the specification is the part I own. The most valuable thing I
did all project was not writing code — it was running the awkward inputs and
asking what *should* happen, because that is where a real bug was hiding that no
amount of well-written code would have surfaced on its own.

---

## 4. Testing and Verification

**a. What you tested**

44 tests in `tests/test_pawpal.py`, planned around five behaviors, each with a
happy path and the edge cases that actually break schedulers:

| Area | Why it mattered |
|---|---|
| **Task state** | `mark_complete()` / `mark_incomplete()` / `end_time()`, plus validation rejecting zero and negative durations and unknown priorities. A negative duration would make a task end before it starts, quietly corrupting every conflict check. |
| **Sorting** | Chronological and priority order. The important case is tasks on *different days*: 23:00 today must sort before 06:00 tomorrow. A `"HH:MM"` string sort gets this exactly backwards, and this test is what proves the design decision to store real `datetime` objects was right. |
| **Filtering** | By pet, status, day, and combined. Edge cases: an unknown pet name returns `[]` rather than raising, a pet with no tasks, and two pets sharing a name. |
| **Conflicts** | Identical start times, overlapping ranges across different pets, back-to-back tasks correctly *not* flagged, completed tasks excluded, and an overlap crossing midnight. |
| **Recurrence** | Daily creates tomorrow's copy, weekly jumps seven days, one-off tasks create nothing, completing the follow-up chains onward, and no duplicate when the occurrence already exists. Also the date arithmetic: Jan 31 → Feb 1, and Feb 26 2028 → Mar 4 across a leap day. |
| **Empty states** | An owner with no pets answers every query with `[]` instead of raising. |

**The test that earned its keep.** Before writing the edge-case tests I ran the
awkward inputs directly to see which would break something. One did. A task at
23:50 running 30 minutes overlaps medication at 00:10, and the global
`detect_conflicts()` caught it — but the day-scoped `detect_conflicts(day)`
returned nothing for *either* day:

```
cross-midnight global conflicts:      1
cross-midnight day-scoped (16th):     0
cross-midnight day-scoped (17th):     0
```

The cause was that the day-scoped version selected tasks whose *start* fell on
that date. A task beginning the night before was simply not in the candidate
set. This mattered because **the Streamlit UI calls the day-scoped version**, so
a real user would never have seen the warning — the feature would have looked
like it worked while silently missing the case.

The fix was `Scheduler.tasks_touching(day)`, which selects tasks *overlapping*
the day's window rather than starting inside it. The conflict is now reported on
the day the overlap actually happens.

**b. Confidence**

**★★★★☆ — 4 out of 5.**

What earns the four: every scheduling algorithm has both a happy-path and an
edge-case test; the suite runs clean on Python 3.9 and 3.11; the Streamlit layer
was driven end to end through Streamlit's own `AppTest` runtime rather than
assumed to work; and the suite found a real bug instead of only confirming what
the code already did. That last point is the one I trust most — a test suite
that has never failed has not been tested itself.

What holds back the fifth star, and what I would test next:

1. **Timezones and daylight saving.** Every `datetime` is naive. On a
   spring-forward night, "daily" adds 24 hours rather than "the same wall-clock
   time tomorrow," so an 08:00 walk would silently become 09:00. This is the gap
   I would close first, because it produces a wrong answer rather than an error.
2. **Scale.** The conflict scan is `O(n²)` in the worst case and has only ever
   run against a handful of tasks. I would generate a year of recurring tasks
   for several pets and measure it.
3. **`has_task()` deduplication.** It matches on title plus start time only, so
   two genuinely different tasks sharing both would be treated as one and the
   second silently skipped.
4. **Persistence.** Everything lives in `st.session_state`, so closing the tab
   loses the data. That is a design limit rather than a bug, but it is entirely
   untested territory.
5. **Property-based testing.** For overlap detection specifically, generating
   random task pairs and asserting the symmetry property (`a.overlaps(b) ==
   b.overlaps(a)`) would cover far more combinations than the cases I picked by
   hand.

---

## 5. Reflection

**a. What went well**

**The separation between the logic layer and the UI.** `pawpal_system.py`
contains no Streamlit code, and `app.py` contains no scheduling logic — every
button calls a method on `Owner`, `Pet`, or `Scheduler`. That split paid off
three separate times:

- `main.py` could demo the entire system in the terminal before Streamlit was
  even installed.
- All 44 tests run against plain Python objects, with no UI harness needed.
- When Streamlit could not be installed at one point because the machine was out
  of disk space, I could still verify the app's wiring by executing `app.py`
  against a stub module — only possible because the file contains so little
  logic of its own.

The single design decision I am most satisfied with is giving `Scheduler` one
source of truth. It looked like a small correction to the UML at the time, and
it quietly prevented an entire class of "why isn't my task showing up?" bugs.

**b. What you would improve**

- **Persistence.** Everything lives in `st.session_state` and disappears when
  the tab closes. Saving the owner to JSON would make PawPal+ actually usable
  rather than a demo, and it is the single change with the biggest gap between
  effort and value.
- **Timezone-aware datetimes.** As noted above, naive datetimes get daylight
  saving wrong in a way that produces a plausible wrong answer rather than a
  visible error.
- **Give `Task` a stable identity.** Right now the UI keys checkboxes on
  `id(task)` and `has_task()` deduplicates on title plus start time. Both work,
  but a real `task_id` would make deduplication exact, let tasks be edited and
  deleted, and let a recurring series know its own members.
- **Model the owner's day, not just the tasks.** Availability windows and travel
  time would turn conflict *detection* into genuine conflict *resolution* —
  the scheduler could then propose a fix instead of only reporting a problem.

**c. Key takeaway**

**The hard part of building a system is deciding what it should refuse to do.**

Most of my design time went not into writing algorithms but into drawing lines.
Should the scheduler reorder tasks to clear a conflict? No — it does not know
why the vet chose that dosing time. Should it delete the follow-up when you
untick a recurring task? No — you may have edited it since. Should a `Task` be
allowed to exist with a negative duration? Also no, and that one is enforced in
`__post_init__` so the invalid state cannot be created at all.

Working with an AI assistant sharpened this rather than replacing it. It could
produce a working conflict detector in seconds, but it could not tell me whether
a conflict should raise an exception, silently reschedule, or print a warning —
that depends on who is using the software and what happens when it is wrong. The
code was rarely the bottleneck. Knowing what the code should be was.
