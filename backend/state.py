from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """State shared between all agents in the graph."""
    messages: Annotated[list, add_messages]  # Chat history
    artifact: str  # The CBT protocol being created
    scratchpad: dict  # Agent notes and feedback
    next: str  # Next node to route to
    status: str  # Current status for UI display
    revision_count: int  # Track number of revision cycles (max 3)
    # Bidirectional loop iteration counters (max 2 each)
    filter_safety_iterations: int  # Filter ↔ Safety loops
    critic_drafter_iterations: int  # Critic ↔ Drafter loops
    critic_safety_iterations: int   # Critic ↔ Safety loops
