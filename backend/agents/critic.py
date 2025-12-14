from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.state import AgentState
import json
import re

critic_model = ChatOpenAI(model="gpt-4o-mini", max_tokens=1000)  # Increased for detailed feedback

SYSTEM_PROMPT = """You are a Clinical Quality Reviewer for CBT protocols with HIGH STANDARDS.
Evaluate the protocol on these criteria (score each 0.0 to 1.0):

1. **Empathy & Tone (0.0-1.0)**: 
   - Must be warm, supportive, AND validating
   - Should include phrases like "It's understandable..." or "You're not alone..."
   - Deduct points if tone feels clinical or detached

2. **Clarity (0.0-1.0)**: 
   - Steps must be SPECIFIC and actionable (not vague like "think about...")
   - Each step should have concrete actions (e.g., "Write down 3 thoughts" not "reflect on thoughts")
   - Deduct points for abstract or unclear instructions

3. **Technique Fit (0.0-1.0)**: 
   - CBT technique must be explicitly named and explained
   - Must match the specific issue (e.g., graded exposure for phobias, thought records for anxiety)
   - Deduct points if technique is generic

4. **Completeness (0.0-1.0)**: 
   - MUST include concrete examples (not just theory)
   - Should have at least 4-5 specific steps
   - Must include validation/progress tracking guidance
   - Deduct points if missing examples or progress tracking

5. **Safety Appropriateness (0.0-1.0)**: 
   - Appropriate disclaimers for sensitive topics
   - Clear boundaries (e.g., when to seek professional help)

**STRICT GRADING STANDARDS:**
- Score 0.9+ only if ALL criteria are exemplary
- A protocol with even minor gaps should score 0.80-0.88
- Missing examples or vague steps = significant deductions

RESPOND IN THIS EXACT JSON FORMAT:
{
  "empathy_score": 0.X,
  "clarity_score": 0.X,
  "technique_score": 0.X,
  "completeness_score": 0.X,
  "safety_score": 0.X,
  "overall_score": 0.X,
  "feedback": "Specific constructive feedback explaining what needs improvement or what was excellent",
  "safety_concern": "If you have safety concerns that need Safety agent consultation, describe here. Otherwise leave empty."
}

Be demanding. Most first drafts should score 0.80-0.88 and need revision.
"""

def critic_node(state: AgentState):
    artifact = state.get("artifact", "No protocol provided")
    revision_count = state.get("revision_count", 0)
    critic_drafter_iterations = state.get("critic_drafter_iterations", 0)
    critic_safety_iterations = state.get("critic_safety_iterations", 0)
    scratchpad = state.get("scratchpad", {})
    
    # Check if Safety responded to our consultation
    safety_responded = scratchpad.get("SafetyResponded", False)
    safety_consultation = scratchpad.get("SafetyConsultation", "")
    
    if safety_responded and critic_safety_iterations > 0:
        # Safety responded to our consultation - incorporate feedback and proceed
        # For now, just acknowledge and proceed to approval
        return {
            "status": f"Quality Review Complete (Safety Consulted)",
            "scratchpad": {
                "Critic": f"Consultation complete. {safety_consultation}",
                "CriticApproved": True,
                "CriticScore": 0.9
            }
        }
    
    # Normal quality review
    response = critic_model.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Review this CBT protocol:\n\n{artifact}")
    ])
    
    result = response.content
    
    # Try to parse JSON response
    try:
        # Extract JSON from response
        json_match = re.search(r'\{[^{}]+\}', result, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
            overall_score = scores.get("overall_score", 0.5)
            feedback = scores.get("feedback", result)
            safety_concern = scores.get("safety_concern", "")
        else:
            overall_score = 0.7  # Default if parsing fails
            feedback = result
            safety_concern = ""
    except:
        overall_score = 0.7
        feedback = result
        safety_concern = ""
    
    # Check if Critic wants to consult Safety
    if safety_concern and critic_safety_iterations < 2:
        return {
            "status": "Requesting Safety Consultation",
            "scratchpad": {
                "CriticRequestsSafetyConsult": True,
                "CriticSafetyConcern": safety_concern
            },
            "critic_safety_iterations": critic_safety_iterations + 1
        }
    
    # Threshold: 0.9+ means approved
    is_approved = overall_score >= 0.9
    
    # Check if we should iterate with Drafter
    needs_improvement = not is_approved and critic_drafter_iterations < 2
    
    display_result = f"Score: {overall_score:.2f}/1.0\n{feedback}"
    
    if needs_improvement:
        # Request Drafter revision
        return {
            "status": f"Quality Review - Requesting Revision ({overall_score:.2f})",
            "scratchpad": {
                "Critic": display_result,
                "CriticApproved": False,
                "CriticScore": overall_score,
                "CriticFeedback": feedback
            },
            "critic_drafter_iterations": critic_drafter_iterations + 1
        }
    else:
        # Approve (either score >= 0.9 or max iterations reached)
        return {
            "status": f"Quality Review Complete ({overall_score:.2f})",
            "scratchpad": {
                "Critic": display_result,
                "CriticApproved": True,
                "CriticScore": overall_score
            }
        }

