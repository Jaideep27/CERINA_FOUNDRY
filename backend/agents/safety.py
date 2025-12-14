from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.state import AgentState

safety_model = ChatOpenAI(model="gpt-4o-mini", max_tokens=800)  # Increased for thorough safety reviews

PROTOCOL_SAFETY_PROMPT = """You are a Safety Reviewer for CBT protocols.
Review the protocol for safety concerns:
- Self-harm or suicide content that needs professional referral
- Medical advice that should come from a doctor
- Dangerous or harmful suggestions

Respond in ONE of these formats:

If SAFE: "SAFE: [brief reason why it's appropriate]"
If NEEDS REVISION: "REVISE: [specific issue that the Drafter should fix]"
If DANGEROUS (rare): "STOP: [serious concern requiring human review]"
If RECHECK INPUT NEEDED: "RECHECK_INPUT: [reason to validate user's original input for PII/sensitive data]"

Most CBT protocols are safe. Only flag real issues.
"""

INPUT_VALIDATION_PROMPT = """You are reviewing user input validation results from the Filter agent.
The Filter has checked for PII (Personally Identifiable Information).

Based on the Filter's report, decide:
1. If PII was found and seems problematic → respond: "REQUEST_FILTER_RECHECK: [what to check more carefully]"
2. If no PII or acceptable → respond: "INPUT_SAFE: Proceed with protocol creation"

Be cautious but not overly restrictive. Some personal context is normal in therapy discussions.
"""

CRITIC_CONSULTATION_PROMPT = """You are responding to a consultation from the Critic agent.
The Critic has a safety-related concern about the protocol quality.

Review the protocol and Critic's concern, then respond:
- "SAFETY_CONFIRMED: [reassurance about why it's safe]"
- "SAFETY_CONCERN: [specific safety issue to address]"
"""

def safety_node(state: AgentState):
    artifact = state.get("artifact", "No protocol provided")
    scratchpad = state.get("scratchpad", {})
    filter_safety_iterations = state.get("filter_safety_iterations", 0)
    critic_safety_iterations = state.get("critic_safety_iterations", 0)
    
    # Check if this is a response from Filter about PII
    filter_pii_check = scratchpad.get("FilterPIICheck", "")
    came_from_filter = bool(filter_pii_check)
    
    # Check if Critic requested consultation
    critic_consultation = scratchpad.get("CriticRequestsSafetyConsult", False)
    
    if came_from_filter and filter_safety_iterations > 0:
        # Filter responded with PII check results
        filter_found_pii = scratchpad.get("FilterFoundPII", False)
        
        if filter_found_pii:
            # Filter found PII - flag for human review
            return {
                "status": "PII Detected - Flagged for Review",
                "scratchpad": {
                    "Safety": f"STOP: User input contains PII. {filter_pii_check}",
                    "SafetyPassed": False,
                    "SafetyDangerous": True
                }
            }
        else:
            # Filter confirmed no PII - proceed
            return {
                "status": "Input Validated - Proceeding",
                "scratchpad": {
                    "Safety": "INPUT_SAFE: Filter confirmed no PII in input",
                    "SafetyPassed": True,
                    "SafetyNeedsRevision": False
                }
            }
    
    elif critic_consultation and critic_safety_iterations < 2:
        # Critic requested safety consultation
        critic_concern = scratchpad.get("CriticSafetyConcern", "")
        
        response = safety_model.invoke([
            SystemMessage(content=CRITIC_CONSULTATION_PROMPT),
            HumanMessage(content=f"Protocol:\n{artifact}\n\nCritic's Concern:\n{critic_concern}")
        ])
        
        result = response.content.strip()
        
        return {
            "status": "Safety Consultation Complete",
            "scratchpad": {
                "SafetyConsultation": result,
                "SafetyResponded": True
            },
            "critic_safety_iterations": critic_safety_iterations + 1
        }
    
    else:
        # Normal protocol safety review
        response = safety_model.invoke([
            SystemMessage(content=PROTOCOL_SAFETY_PROMPT),
            HumanMessage(content=f"Review this CBT protocol for safety:\n\n{artifact}")
        ])
        
        result = response.content.strip()
        
        # Check if Safety wants to request Filter recheck
        if result.upper().startswith("RECHECK_INPUT") and filter_safety_iterations < 2:
            return {
                "status": "Requesting Input Validation",
                "scratchpad": {
                    "SafetyRequestsFilterRecheck": True,
                    "SafetyReason": result
                },
                "filter_safety_iterations": filter_safety_iterations + 1
            }
        # Determine routing based on response
        elif result.upper().startswith("REVISE"):
            return {
                "status": "Safety Review - Needs Revision",
                "scratchpad": {
                    "Safety": result,
                    "SafetyPassed": False,
                    "SafetyNeedsRevision": True,
                    "SafetyDangerous": False
                }
            }
        elif result.upper().startswith("STOP"):
            return {
                "status": "Safety Review - Flagged",
                "scratchpad": {
                    "Safety": result,
                    "SafetyPassed": False,
                    "SafetyNeedsRevision": False,
                    "SafetyDangerous": True
                }
            }
        else:  # SAFE
            return {
                "status": "Safety Review Complete",
                "scratchpad": {
                    "Safety": result,
                    "SafetyPassed": True,
                    "SafetyNeedsRevision": False,
                    "SafetyDangerous": False
                }
            }

