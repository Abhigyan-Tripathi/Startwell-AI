"""Reusable Streamlit UI components — no business logic here."""
from datetime import date, timedelta
import streamlit as st

from core.database import DatabaseManager


def render_log_form() -> tuple[bool, dict]:
    with st.sidebar.form("log_form"):
        st.header("Daily Wellness Log")
        sleep = st.slider("Sleep (hrs)", 0.0, 12.0, 8.0, 0.5)
        exercise = st.number_input("Exercise (hrs)", 0.0, 24.0, 1.0, 0.25)
        productivity = st.number_input("Productivity (hrs)", 0.0, 24.0, 2.0, 0.25)
        self_help = st.number_input("Self-help (hrs)", 0.0, 24.0, 1.0, 0.25)
        notes = st.text_area("Notes (goals/reflection)", "")
        submitted = st.form_submit_button("Submit Log & Generate Plan")

    user_logs = {
        "sleep": sleep,
        "exercise": exercise,
        "productivity": productivity,
        "self_help": self_help,
        "notes": notes,
    }
    return submitted, user_logs


def render_goal(weekly_goal: str, submitted: bool) -> None:
    st.subheader("🎯 Weekly SMART Goal")
    if weekly_goal:
        st.write(weekly_goal)
    elif submitted:
        st.info("No weekly goal generated yet. Submit your daily log to get started!")


def render_today_tasks(db: DatabaseManager) -> None:
    st.subheader("✅ Today's Tasks")
    today = date.today().isoformat()
    tasks = db.get_tasks_for_date(today)

    if not tasks:
        st.info("No tasks planned for today. Submit a log to get your first tasks!")
        return

    for task, done in tasks:
        key = f"task_checkbox_{today}_{task}"
        new_status = st.checkbox(task, value=bool(done), key=key)
        if new_status != bool(done):
            db.set_task_done(today, task, new_status)
            st.rerun()


def render_weekly_calendar(db: DatabaseManager) -> None:
    st.subheader("📅 Weekly Calendar")
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    dates_in_week = [(start_date + timedelta(days=i)).isoformat() for i in range(7)]

    rows = db.get_tasks_for_range(dates_in_week[0], dates_in_week[-1])
    if not rows:
        st.info("No weekly tasks available. Generate a plan to see your calendar!")
        return

    tasks_by_date: dict[str, list[dict]] = {d: [] for d in dates_in_week}
    for d, task, done in rows:
        tasks_by_date[d].append({"task": task, "done": bool(done)})

    display_data = []
    for d in dates_in_week:
        entries = tasks_by_date.get(d, [])
        if entries:
            for e in entries:
                display_data.append({"Date": d, "Task": e["task"], "Status": "✅ Done" if e["done"] else "❌ Not Done"})
        else:
            display_data.append({"Date": d, "Task": "No task planned", "Status": "-"})
    st.dataframe(display_data, hide_index=True)


def render_advice(weekly_advice: str, submitted: bool) -> None:
    st.subheader("💡 Weekly Reflection & Advice")
    if weekly_advice:
        st.write(weekly_advice)
    elif submitted:
        st.info("No weekly advice generated yet. Complete your tasks and logs for the agent to provide feedback.")
