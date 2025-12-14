from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from backend.state import AgentState
from pydantic import BaseModel

class Route(BaseModel):
    next: Literal["Drafter", "Critic", "Safety", "Interrupt"]

supervisor_model = ChatOpenAI(model="gpt-5-mini", max_tokens=100)

SYSTEM_PROMPT = """You are the Supervisor of the Cerina Foundry.
Your goal is to manage a team of agents to create a high-quality CBT protocol.
The team members are:
- Drafter: Writes the initial draft or revisions.
- Safety: Checks for self-harm, medical advice risks, or unsafe content.
- Critic: Reviews for clinical tone, empathy, and structure.

Rules:
1. If there is no artifact/draft yet, route to 'Drafter'.
2. If draft exists but Safety hasn't checked, route to 'Safety'.
3. If Safety passed (SAFE) but Critic hasn't reviewed, route to 'Critic'.
4. If Critic says 'APPROVE', route to 'Interrupt' for human approval.
5. If Critic says 'CRITIQUE:', route back to 'Drafter' for revisions.

Assess the current scratchpad and decide the next step.
"""

def supervisor_node(state: AgentState):
    messages = state["messages"]
    scratchpad = state.get("scratchpad", {})
    artifact = state.get("artifact", "")
    
    # Add explicit logic to prevent infinite loops
    safety_result = scratchpad.get("Safety", "")
    critic_result = scratchpad.get("Critic", "")
    
    # If both Safety passed AND Critic approved, go to Interrupt
    if "SAFE" in safety_result and "APPROVE" in critic_result:
        return {"next": "Interrupt", "status": "Routing to Interrupt (All Approved)"}
    
    # If draft exists and Safety not done, go to Safety
    if artifact and not safety_result:
        return {"next": "Safety", "status": "Routing to Safety"}
    
    # If Safety passed and Critic not done, go to Critic
    if "SAFE" in safety_result and not critic_result:
        return {"next": "Critic", "status": "Routing to Critic"}
    
    # If Critic gave critique, go back to Drafter
    if "CRITIQUE:" in critic_result:
        return {"next": "Drafter", "status": "Routing to Drafter (Revisions Needed)"}
    
    # If no artifact, start with Drafter
    if not artifact:
        return {"next": "Drafter", "status": "Routing to Drafter (Initial Draft)"}
    
    # Fallback: use LLM for complex cases
    scratchpad_text = "\n".join([f"{k}: {v}" for k, v in scratchpad.items()])
    
    chain = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("system", "Current Scratchpad:\n{scratchpad}"),
        ("system", "Current Artifact exists: {has_artifact}"),
        MessagesPlaceholder(variable_name="messages"),
    ]) | supervisor_model.with_structured_output(Route)
    
    response = chain.invoke({
        "messages": messages, 
        "scratchpad": scratchpad_text,
        "has_artifact": "Yes" if artifact else "No"
    })
    
    return {"next": response.next, "status": f"Routing to {response.next}"}
