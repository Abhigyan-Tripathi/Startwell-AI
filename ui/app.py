"""Streamlit entry point — wires dependencies together and renders the page."""
from datetime import date
import streamlit as st

from core.database import DatabaseManager
from core.vectorstore import VectorStore
from core.llm_client import LLMClient
from agents.nodes import WellnessAgentNodes
from agents.graph import build_graph
from ui import components


@st.cache_resource
def get_dependencies():
    """Instantiated once per Streamlit session (cached across reruns)."""
    db = DatabaseManager()
    vectorstore = VectorStore()
    llm = LLMClient()
    nodes = WellnessAgentNodes(db=db, vectorstore=vectorstore, llm=llm)
    graph = build_graph(nodes)
    return db, llm, graph


def _init_session_state() -> None:
    defaults = {"weekly_goal": "", "daily_tasks": {}, "weekly_advice": ""}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    st.set_page_config(page_title="Holistic Habit Coach", layout="centered")
    st.title("🧘 StartWell AI: Daily Wellness Coach")

    db, llm, graph = get_dependencies()
    _init_session_state()

    if not llm.is_ready:
        st.warning("Hugging Face token (HF_TOKEN) not found. LLM queries may not work.")

    submitted, user_logs = components.render_log_form()

    if submitted:
        today = date.today().isoformat()
        state_input = {"user_logs": user_logs, "date": today, "weekly_advice": ""}

        with st.spinner("Generating your plan and advice..."):
            try:
                result = graph.invoke(state_input)
                st.session_state.weekly_goal = str(result.get("weekly_goal", "")).strip()
                daily_tasks = result.get("daily_tasks", {})
                st.session_state.daily_tasks = daily_tasks if isinstance(daily_tasks, dict) else {}
                st.session_state.weekly_advice = str(result.get("weekly_advice", "")).strip()
                st.success("Log submitted and plan generated!")
            except Exception as exc:
                st.error(f"An error occurred during plan generation: {exc}")
                st.session_state.weekly_goal = ""
                st.session_state.daily_tasks = {}
                st.session_state.weekly_advice = f"Error: Could not generate plan due to an internal issue. ({exc})"

    components.render_goal(st.session_state.weekly_goal, submitted)
    components.render_today_tasks(db)
    components.render_weekly_calendar(db)
    components.render_advice(st.session_state.weekly_advice, submitted)


if __name__ == "__main__":
    main()
