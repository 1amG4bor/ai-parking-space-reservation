import os

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from chat_engine.core.agents.agent_models import APSRState
from chat_engine.core.graph.node import (
    block_node,
    guardrail_node,
    reservation_info_node,
    reservation_management_node,
    reservation_persistence_node,
    router_node,
    router_semaphore,
    search_node,
    synthesizer_node,
    user_input_node,
    user_intent_classifier_node,
)

# Singleton checkpointer — persists state across invocations for HITL resume
_checkpointer = InMemorySaver()


def build_state_graph() -> CompiledStateGraph:
    graph = StateGraph(APSRState)

    graph.add_node("guardrail", guardrail_node)
    graph.add_node("block", block_node)
    graph.add_node("user_intent", user_intent_classifier_node)
    graph.add_node("uc_router", router_node)
    graph.add_node("user_input", user_input_node)
    graph.add_node("search", search_node)
    graph.add_node("get_reservation_info", reservation_info_node)
    graph.add_node("submit_reservation", reservation_management_node)
    graph.add_node("save_reservation_snapshot", reservation_persistence_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "guardrail")
    graph.add_edge("guardrail", "user_intent")
    graph.add_edge("user_intent", "uc_router")
    graph.add_conditional_edges(source="uc_router", path=router_semaphore)

    graph.add_edge("user_input", "guardrail")
    graph.add_edge("search", "uc_router")
    graph.add_edge("get_reservation_info", "uc_router")

    graph.add_edge("submit_reservation", "save_reservation_snapshot")
    graph.add_edge("save_reservation_snapshot", "synthesizer")
    graph.add_edge("block", END)
    graph.add_edge("synthesizer", END)

    kwargs = {"checkpointer": _checkpointer}
    if os.getenv("ENV", "").lower() == "development":
        kwargs["debug"] = True
    return graph.compile(**kwargs)
