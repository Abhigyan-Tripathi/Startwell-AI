"""LangGraph node implementations. Each node is a bound method so agents share
the same DB / vector store / LLM client instances without relying on globals."""
from datetime import datetime
from langgraph.types import Command

from core.database import DatabaseManager
from core.vectorstore import VectorStore
from core.llm_client import LLMClient


class WellnessAgentNodes:
    def __init__(self, db: DatabaseManager, vectorstore: VectorStore, llm: LLMClient):
        self.db = db
        self.vectorstore = vectorstore
        self.llm = llm

    # ---- Intake -----------------------------------------------------
    def intake(self, state: dict) -> Command:
        logs: dict = state.get("user_logs", {})
        date_str: str = state.get("date")
        if not logs or not date_str:
            raise ValueError("state must include 'user_logs' and 'date'")

        self.db.upsert_daily_metrics(
            date_str,
            sleep=float(logs.get("sleep", 0.0)),
            exercise=float(logs.get("exercise", 0.0)),
            productivity=float(logs.get("productivity", 0.0)),
            self_help=float(logs.get("self_help", 0.0)),
        )

        text = "; ".join(f"{k}: {v}" for k, v in logs.items())
        self.vectorstore.add_log(date_str, text)

        return Command(update={"user_input": logs.get("notes", "")}, goto="GoalAgent")

    # ---- Goal setting -------------------------------------------------
    def goal(self, state: dict) -> Command:
        today_str = state["date"]
        dates = self.db.last_n_days(today_str, 7)
        contexts = self.vectorstore.get_logs(dates)

        initial_notes = state.get("user_logs", {}).get("notes", "").strip()
        if contexts:
            context_text = "Previous logs:\n" + "\n".join(f"- {doc}" for doc in contexts)
        elif initial_notes:
            context_text = f"No previous logs. User notes: {initial_notes}"
        else:
            context_text = "No previous logs or notes available. Proceed to set an initial goal."

        avg_sleep, avg_exercise, avg_prod, avg_self = self.db.get_weekly_averages(dates[0], dates[-1])

        prompt = f"""
        You are a wellness coach. Here is the context:
        {context_text}

        Their average metrics over the past week (if any):
        • Sleep:        {avg_sleep:.1f} hrs/day
        • Exercise:     {avg_exercise:.1f} hrs/day
        • Productivity: {avg_prod:.1f} hrs/day
        • Self‑help:    {avg_self:.1f} hrs/day

        Based on this (or the initial notes), propose one weekly SMART goal to improve their wellness balance.
        Return exactly in this format:

        Goal: <one-sentence SMART goal>

        S: <Specific aspect>
        M: <How to measure>
        A: <Why it's achievable>
        R: <Why it's relevant>
        T: <Time-bound target>
        """
        output = self.llm.generate(prompt)
        return Command(goto="Planner", update={"weekly_goal": output})

    # ---- Planning -------------------------------------------------
    def planner(self, state: dict) -> Command:
        weekly_goal = state.get("weekly_goal")
        start_date = datetime.fromisoformat(state.get("date"))

        if not weekly_goal or self._is_llm_error(weekly_goal):
            return Command(goto="Advisor", update={"daily_tasks": {}})

        prompt = f"""
        You are a task planning assistant. Given the following SMART weekly goal:

        {weekly_goal}

        Split this goal into one clear, actionable task for each day of the next 7 days.
        Return as a numbered list, with each line in the format:<Date>: <Task>
        Use ISO date format YYYY-MM-DD, starting from {start_date.date().isoformat()}.
        Ensure each line starts with a date in YYYY-MM-DD format followed by ':'.
        Example:
        2025-06-18: Meditate for 10 minutes.
        2025-06-19: Go for a 30-minute walk.
        """
        result = self.llm.generate(prompt)
        if self._is_llm_error(result):
            return Command(goto="Advisor", update={"daily_tasks": {}})

        daily_tasks = self._parse_tasks(result)
        if not daily_tasks:
            return Command(goto="Advisor", update={"daily_tasks": {}})

        self.db.bulk_insert_tasks(daily_tasks)
        return Command(goto="Advisor", update={"daily_tasks": daily_tasks})

    @staticmethod
    def _parse_tasks(raw_result: str) -> dict[str, str]:
        daily_tasks: dict[str, str] = {}
        for line in raw_result.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            date_str, _, task = line.partition(":")
            date_str, task = date_str.strip(), task.strip()
            try:
                datetime.fromisoformat(date_str)
            except ValueError:
                continue
            if task:
                daily_tasks[date_str] = task
        return daily_tasks

    # ---- Advisor -------------------------------------------------
    def advisor(self, state: dict) -> Command:
        end_date_str = state["date"]
        dates = self.db.last_n_days(end_date_str, 7)
        rows = self.db.get_tasks_for_range(dates[0], dates[-1])

        if rows:
            task_entries = [f"{d}: {task} - {'done' if done else 'not done'}" for d, task, done in rows]
            tasks_summary = "\n".join(task_entries)

            log_docs = self.vectorstore.get_logs(dates)
            context_text = "\n".join(f"- {doc}" for doc in log_docs) or "No detailed logs available for the past week."

            prompt = f"""
            You are a supportive wellness coach. Here are the details for the past week:

            Daily Logs:
            {context_text}

            Task Completion:
            {tasks_summary}

            Please provide:
            1. Praise for what the user did well.
            2. Constructive feedback on missed tasks.
            3. Suggestions to improve adherence next week.
            4. Any motivational encouragement.

            Return a concise paragraph of advice.
            """
            generated_advice = self.llm.generate(prompt)
            final_advice = (
                f"Advisor could not generate detailed advice: {generated_advice}"
                if self._is_llm_error(generated_advice)
                else generated_advice
            )
        else:
            weekly_goal = state.get("weekly_goal", "")
            if not weekly_goal.strip():
                final_advice = "No weekly goal provided, so no tasks could be planned for advice."
            elif self._is_llm_error(weekly_goal):
                final_advice = "No specific weekly goal was set, so no detailed tasks could be planned. Please ensure your input helps generate a clear goal."
            else:
                final_advice = f"A goal was set ({weekly_goal}), but no tasks were generated for the week. Please refine your goal or task planning."

        return Command(goto="__end__", update={"weekly_advice": final_advice.strip()})

    @staticmethod
    def _is_llm_error(text: str) -> bool:
        return "Error:" in text or "No meaningful response" in text
