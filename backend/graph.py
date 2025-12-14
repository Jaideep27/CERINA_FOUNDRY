from langgraph.graph import StateGraph, END
from backend.state import AgentState
from backend.agents.filter import filter_node
from backend.agents.drafter import drafter_node
from backend.agents.safety import safety_node
from backend.agents.critic import critic_node
from backend.database import get_checkpointer

MAX_REVISIONS = 3  # Safety limit to prevent infinite loops in global revisions

# Define Nodes
def interrupt_node(state: AgentState):
    """Pause for human approval - marks workflow as complete after approval"""
    return {
        "status": "Approved and Finalized",
        "next": None  # Explicitly mark as complete
    }

def rejection_node(state: AgentState):
    """Handle irrelevant queries"""
    return {"status": "Rejected", "artifact": "Your query is not related to CBT/mental health. Please try a relevant topic."}

# Build Graph with Bidirectional Routing
builder = StateGraph(AgentState)

# Add all nodes
builder.add_node("Filter", filter_node)
builder.add_node("Drafter", drafter_node)
builder.add_node("Safety", safety_node)
builder.add_node("Critic", critic_node)
builder.add_node("Interrupt", interrupt_node)
builder.add_node("Rejection", rejection_node)

# Entry point
builder.set_entry_point("Filter")

# Filter router - supports bidirectional loop with Safety
def filter_router(state):
    next_node = state.get("next", "Drafter")
    scratchpad = state.get("scratchpad", {})
    filter_safety_iterations = state.get("filter_safety_iterations", 0)
    
    # Check if Safety requested a recheck
    safety_requested_recheck = scratchpad.get("SafetyRequestsFilterRecheck", False)
    
    if next_node == "Rejection":
        return "Rejection"
    elif next_node == "Safety" and filter_safety_iterations > 0:
        # Bidirectional: Filter → Safety (PII check loop)
        return "Safety"
    else:
        # Normal forward flow: Filter → Drafter
        return "Drafter"

builder.add_conditional_edges("Filter", filter_router)

# Drafter → Safety (always, after creating/revising protocol)
builder.add_edge("Drafter", "Safety")

# Safety router - supports bidirectional loops with Filter and Critic
def safety_router(state):
    scratchpad = state.get("scratchpad", {})
    revision_count = state.get("revision_count", 0)
    filter_safety_iterations = state.get("filter_safety_iterations", 0)
    critic_safety_iterations = state.get("critic_safety_iterations", 0)
    
    # Check if Safety wants to request Filter recheck
    requests_filter_recheck = scratchpad.get("SafetyRequestsFilterRecheck", False)
    
    # Check safety decisions
    is_dangerous = scratchpad.get("SafetyDangerous", False)
    needs_revision = scratchpad.get("SafetyNeedsRevision", False)
    safety_responded = scratchpad.get("SafetyResponded", False)  # Responded to Critic
    
    if requests_filter_recheck and filter_safety_iterations < 2:
        # Bidirectional: Safety → Filter (request PII check)
        return "Filter"
    elif safety_responded:
        # Bidirectional: Safety → Critic (responded to consultation)
        return "Critic"
    elif is_dangerous:
        # Serious concern - go to human review immediately
        return "Interrupt"
    elif needs_revision and revision_count < MAX_REVISIONS:
        # Safety wants revision - back to Drafter
        return "Drafter"
    else:
        # Safe - proceed to Critic
        return "Critic"

builder.add_conditional_edges("Safety", safety_router)

# Critic router - supports bidirectional loops with Drafter and Safety
def critic_router(state):
    scratchpad = state.get("scratchpad", {})
    revision_count = state.get("revision_count", 0)
    critic_drafter_iterations = state.get("critic_drafter_iterations", 0)
    critic_safety_iterations = state.get("critic_safety_iterations", 0)
    
    critic_approved = scratchpad.get("CriticApproved", None)  # None means not yet decided
    critic_score = scratchpad.get("CriticScore", 0.5)
    requests_safety_consult = scratchpad.get("CriticRequestsSafetyConsult", False)
    
    # Priority 1: Check if Critic wants to consult Safety
    if requests_safety_consult and critic_safety_iterations < 2:
        # Bidirectional: Critic → Safety (safety consultation)
        return "Safety"
    
    # Priority 2: Check if needs improvement and can still iterate with Drafter
    if critic_approved == False and critic_drafter_iterations < 2:
        # Bidirectional: Critic → Drafter (quality improvement iteration)
        return "Drafter"
    
    # Priority 3: Check if approved
    if critic_approved == True or critic_score >= 0.9:
        # High quality! → Human approval
        return "Interrupt"
    
    # Priority 4: Max revisions/iterations reached → proceed anyway
    # If we've exhausted iterations or revisions, approve and move forward
    return "Interrupt"

builder.add_conditional_edges("Critic", critic_router)

# Terminal nodes
builder.add_edge("Interrupt", END)
builder.add_edge("Rejection", END)

async def build_graph():
    checkpointer = await get_checkpointer()
    return builder.compile(checkpointer=checkpointer, interrupt_before=["Interrupt"])

