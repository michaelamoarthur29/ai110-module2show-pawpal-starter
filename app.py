"""PawPal+ Streamlit UI.

The thin presentation layer over pawpal_system.py. Every button here calls a
method on Owner, Pet, or Scheduler — this file holds no scheduling logic of
its own.
"""

from datetime import date, datetime, time, timedelta

import streamlit as st

from pawpal_system import FREQUENCIES, PRIORITIES, Owner, Pet, Scheduler, Task

TASK_TYPES = ["exercise", "feeding", "medication", "enrichment", "grooming", "vet", "other"]

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")


def get_owner() -> Owner:
    """Return the Owner held in session state, creating it on the first run.

    Streamlit re-runs this script top to bottom on every interaction, so an
    Owner built as a plain local would be rebuilt empty each time. Storing it
    in st.session_state keeps the same object — and everything added to it —
    alive across re-runs.
    """
    if "owner" not in st.session_state:
        st.session_state.owner = Owner("Jordan")
    return st.session_state.owner


def load_demo_pets(owner: Owner) -> None:
    """Fill an empty owner with two pets and a few tasks to try the app out."""
    today = date.today()

    def at(hour: int, minute: int = 0) -> datetime:
        return datetime.combine(today, time(hour, minute))

    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    biscuit = owner.add_pet(Pet("Biscuit", "cat", 7))

    mochi.add_task(Task("Morning walk", "exercise", at(8, 0), 30, "high", frequency="daily"))
    mochi.add_task(Task("Breakfast", "feeding", at(8, 45), 10, "high"))
    mochi.add_task(Task("Evening walk", "exercise", at(18, 30), 30, "medium"))
    biscuit.add_task(Task("Breakfast", "feeding", at(8, 50), 10, "high"))
    biscuit.add_task(Task("Thyroid meds", "medication", at(9, 0), 5, "high", frequency="daily"))


owner = get_owner()
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")
st.caption("A care planner for busy pet owners.")


# --- Owner -----------------------------------------------------------------

new_name = st.text_input("Owner name", value=owner.name)
if new_name and new_name != owner.name:
    owner.name = new_name

if not owner.get_pets():
    st.info("No pets yet. Add one below, or load the demo data to look around.")
    if st.button("Load demo data"):
        load_demo_pets(owner)
        st.rerun()


# --- Add a pet -------------------------------------------------------------

st.subheader("Pets")

with st.form("add_pet", clear_on_submit=True):
    st.markdown("**Add a pet**")
    col1, col2, col3 = st.columns([2, 2, 1])
    pet_name = col1.text_input("Name")
    species = col2.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
    age = col3.number_input("Age", min_value=0, max_value=40, value=1)

    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.warning("Give your pet a name first.")
        else:
            # Owner.add_pet() is the method that owns this data change.
            owner.add_pet(Pet(pet_name.strip(), species, int(age)))
            st.success(f"Added {pet_name.strip()}.")
            st.rerun()

pets = owner.get_pets()
if pets:
    st.table(
        [
            {"Pet": pet.name, "Species": pet.species, "Age": pet.age, "Tasks": len(pet.get_tasks())}
            for pet in pets
        ]
    )


# --- Add a task ------------------------------------------------------------

if pets:
    st.subheader("Tasks")

    with st.form("add_task", clear_on_submit=True):
        st.markdown("**Add a task**")
        pet_names = [pet.name for pet in pets]
        target_name = st.selectbox("For which pet?", pet_names)

        col1, col2 = st.columns([3, 2])
        title = col1.text_input("Task title", placeholder="Morning walk")
        task_type = col2.selectbox("Type", TASK_TYPES)

        col3, col4, col5 = st.columns(3)
        task_day = col3.date_input("Date", value=date.today())
        task_time = col4.time_input("Start time", value=time(8, 0))
        duration = col5.number_input("Duration (min)", min_value=1, max_value=240, value=20)

        col6, col7 = st.columns(2)
        priority = col6.selectbox("Priority", list(PRIORITIES))
        frequency = col7.selectbox("Repeats", list(FREQUENCIES))

        if st.form_submit_button("Add task"):
            if not title.strip():
                st.warning("Give the task a title first.")
            else:
                target = next(pet for pet in pets if pet.name == target_name)
                # Pet.add_task() handles the data change; the UI just re-reads it.
                target.add_task(
                    Task(
                        title=title.strip(),
                        task_type=task_type,
                        date_time=datetime.combine(task_day, task_time),
                        duration_minutes=int(duration),
                        priority=priority,
                        frequency=frequency,
                    )
                )
                st.success(f"Added “{title.strip()}” for {target_name}.")
                st.rerun()


# --- Schedule --------------------------------------------------------------

st.divider()
st.subheader("Schedule")

if not scheduler.get_all_tasks():
    st.info("No tasks yet. Add one above to see a plan.")
    st.stop()

view_day = st.date_input("Plan for", value=date.today(), key="view_day")
daily_tasks = scheduler.get_daily_tasks(view_day)

st.markdown(f"### {view_day:%A, %B %d}")

if not daily_tasks:
    st.write("Nothing scheduled for this day.")
else:
    for task in daily_tasks:
        pet = scheduler.pet_for(task)
        pet_name = pet.name if pet else "unassigned"
        cols = st.columns([1, 6])

        # Key on the Task object's identity, not its position: the same object
        # survives every re-run, so a checkbox stays attached to its own task
        # even when adding a task reorders the day.
        done = cols[0].checkbox(
            "Done",
            value=task.completed,
            key=f"done-{id(task)}",
            label_visibility="collapsed",
        )
        if done and not task.completed:
            # Completing a recurring task queues its next occurrence.
            follow_up = scheduler.mark_task_complete(task)
            if follow_up is not None:
                st.toast(f"Next {task.title} scheduled for {follow_up.date_time:%a %d %b}.")
        elif not done and task.completed:
            task.mark_incomplete()

        window = f"{task.date_time:%H:%M}–{task.end_time():%H:%M}"
        label = f"~~{task.title}~~" if task.completed else f"**{task.title}**"
        repeats = f" · repeats {task.frequency}" if task.is_recurring() else ""
        cols[1].markdown(
            f"{label} — {window} ({task.duration_minutes} min)  \n"
            f"<small>{pet_name} · {task.task_type} · {task.priority} priority{repeats}</small>",
            unsafe_allow_html=True,
        )

conflicts = scheduler.detect_conflicts(view_day)
if conflicts:
    st.warning(f"{len(conflicts)} scheduling conflict(s) on this day:")
    for first, second in conflicts:
        first_pet = scheduler.pet_for(first)
        second_pet = scheduler.pet_for(second)
        st.markdown(
            f"- **{first.title}** ({first_pet.name}) "
            f"{first.date_time:%H:%M}–{first.end_time():%H:%M} overlaps "
            f"**{second.title}** ({second_pet.name}) "
            f"{second.date_time:%H:%M}–{second.end_time():%H:%M}"
        )
else:
    st.success("No conflicts — the day fits together.")


# --- Everything by priority ------------------------------------------------

with st.expander("All tasks by priority"):
    st.table(
        [
            {
                "Priority": task.priority,
                "When": f"{task.date_time:%a %d %b %H:%M}",
                "Task": task.title,
                "Pet": (scheduler.pet_for(task) or Pet("?", "?", 0)).name,
                "Done": "✓" if task.completed else "",
            }
            for task in scheduler.get_sorted_tasks()
        ]
    )


# --- Recurring tasks -------------------------------------------------------

with st.expander("Roll recurring tasks forward"):
    st.caption(
        "Expands every daily and weekly task into dated copies through the date you pick. "
        "Safe to run twice — occurrences that already exist are skipped."
    )
    until = st.date_input("Through", value=date.today() + timedelta(days=7), key="until")
    if st.button("Create recurring tasks"):
        created = scheduler.create_recurring_tasks(until=until)
        if created:
            st.success(f"Created {len(created)} task(s).")
        else:
            st.info("Nothing new to create.")
        st.rerun()


# --- Reset -----------------------------------------------------------------

st.divider()
if st.button("Reset all data"):
    del st.session_state["owner"]
    st.rerun()
