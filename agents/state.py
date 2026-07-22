from typing_extensions import TypedDict


class WellnessState(TypedDict):
    user_input: str
    date: str
    user_logs: dict
    weekly_goal: str
    daily_tasks: dict
    weekly_advice: str
