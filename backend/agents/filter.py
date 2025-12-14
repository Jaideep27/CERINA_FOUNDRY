from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.state import AgentState

filter_agent = ChatOpenAI(model="gpt-4o-mini", max_tokens=300)  # Increased for better classification

RELEVANCE_PROMPT = """You are the Cerina Foundry Filter.
Your job is to classify incoming user queries into one of two categories:
1. "relevant" - Related to CBT, mental health, anxiety, depression, sleep issues, stress, emotional regulation.
2. "irrelevant" - Not related to mental health (e.g., coding, recipes, general knowledge).

Respond with ONLY one word: "relevant" or "irrelevant"
"""

PII_DETECTION_PROMPT = """You are a Privacy Detector for the Cerina Foundry.
Analyze the user's message for Personally Identifiable Information (PII) or sensitive data:
- Email addresses, phone numbers, physical addresses
- Social Security Numbers, credit card numbers
- Full names, birth dates, medical record numbers
- Any other sensitive personal information

Respond in ONE of these formats:
- "CLEAN: No PII detected"
- "PII_FOUND: [brief description of what PII was detected]"
"""

def filter_node(state: AgentState):
    messages = state["messages"]
    scratchpad = state.get("scratchpad", {})
    filter_safety_iterations = state.get("filter_safety_iterations", 0)
    
    # Check if Safety requested a recheck
    safety_requested_recheck = scratchpad.get("SafetyRequestsFilterRecheck", False)
    
    if safety_requested_recheck and filter_safety_iterations < 2:
        # Safety requested PII check - perform deep analysis
        user_message = messages[-1].content if messages else ""
        
        response = filter_agent.invoke([
            SystemMessage(content=PII_DETECTION_PROMPT),
            HumanMessage(content=f"Check this message for PII:\n\n{user_message}")
        ])
        
        result = response.content.strip()
        
        if "PII_FOUND" in result.upper():
            # PII detected - inform Safety and continue loop
            return {
                "status": "PII Detected in Input",
                "scratchpad": {
                    "FilterPIICheck": result,
                    "FilterFoundPII": True
                },
                "next": "Safety",
                "filter_safety_iterations": filter_safety_iterations + 1
            }
        else:
            # Clean - send back to Safety with confirmation
            return {
                "status": "Input Validated - No PII",
                "scratchpad": {
                    "FilterPIICheck": result,
                    "FilterFoundPII": False
                },
                "next": "Safety",
                "filter_safety_iterations": filter_safety_iterations + 1
            }
    else:
        # Normal flow - check relevance only
        response = filter_agent.invoke([
            SystemMessage(content=RELEVANCE_PROMPT),
            *messages
        ])
        
        classification = response.content.strip().lower()
        
        if "irrelevant" in classification:
            return {"next": "Rejection", "status": "Query Irrelevant"}
        else:
            return {"next": "Drafter", "status": "Query Accepted"}

