"""Builds and compiles the LangGraph multi-agent workflow."""
from langgraph.graph import StateGraph, END

from agents.state import WellnessState
from agents.nodes import WellnessAgentNodes


def build_graph(nodes: WellnessAgentNodes):
    graph = (
        StateGraph(WellnessState)
        .add_node("Intake", nodes.intake)
        .add_node("GoalAgent", nodes.goal)
        .add_node("Planner", nodes.planner)
        .add_node("Advisor", nodes.advisor)
        .add_edge("Intake", "GoalAgent")
        .add_edge("GoalAgent", "Planner")
        .add_edge("Planner", "Advisor")
        .set_entry_point("Intake")
        .set_finish_point("Advisor")
    )
    return graph.compile()
