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

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

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

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
