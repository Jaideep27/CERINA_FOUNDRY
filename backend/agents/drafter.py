from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.state import AgentState

drafter_model = ChatOpenAI(model="gpt-4o-mini", max_tokens=4000)  # Increased for longer protocols

INITIAL_PROMPT = """You are a CBT Protocol Drafter. Create a high-quality, empathetic Cognitive Behavioral Therapy exercise.

**CRITICAL: Output in MARKDOWN format with proper structure.**

Your protocol MUST follow this Markdown structure:

# CBT Protocol: [Specific Topic Title]

## Understanding the Issue
[Warm, validating acknowledgment paragraph]

## CBT Technique: [Technique Name]
[Brief explanation of the technique - e.g., Cognitive Restructuring, Graded Exposure, etc.]

## Step-by-Step Exercise

### Step 1: [Step Title]
- **Action:** [Clear, specific instruction]
- **Example:** [Concrete example]

### Step 2: [Step Title]
[Continue with 4-6 steps total, each with actions and examples]

## Progress Tracking
- [How to measure progress]
- [Recommended frequency]

## Tips for Success
- [Practical tip 1]
- [Practical tip 2]
- [Practical tip 3]

---
*Remember: [Encouraging, self-compassionate closing statement]*

Tone: Warm, professional, supportive. Use Markdown headings (#, ##, ###), lists (-), and **bold** for emphasis.
"""

REVISION_PROMPT = """You are revising a CBT Protocol based on reviewer feedback.

**CRITICAL: Maintain MARKDOWN formatting in your revision.**

PREVIOUS DRAFT:
{artifact}

FEEDBACK TO ADDRESS:
{feedback}

Create an IMPROVED version that specifically addresses the feedback while:
- Maintaining Markdown format (headings with #, lists with -, bold with **)
- Keeping the same structure
- Enhancing based on suggestions
- Remaining empathetic and actionable

Output the COMPLETE revised protocol in Markdown.
"""

def drafter_node(state: AgentState):
    messages = state["messages"]
    scratchpad = state.get("scratchpad", {})
    artifact = state.get("artifact", "")
    revision_count = state.get("revision_count", 0)
    critic_drafter_iterations = state.get("critic_drafter_iterations", 0)
    
    # Check for feedback from Safety or Critic
    safety_feedback = scratchpad.get("Safety", "")
    critic_feedback = scratchpad.get("Critic", "")
    critic_specific_feedback = scratchpad.get("CriticFeedback", "")
    
    # Determine if this is a revision
    needs_safety_revision = "REVISE" in safety_feedback.upper()
    needs_critic_revision = not scratchpad.get("CriticApproved", True) and (critic_feedback or critic_specific_feedback)
    
    if artifact and (needs_safety_revision or needs_critic_revision):
        # Combine feedback sources
        feedback = ""
        if needs_safety_revision:
            feedback += f"Safety Review: {safety_feedback}\n"
        if needs_critic_revision:
            # Use specific feedback if available, otherwise use full critic result
            if critic_specific_feedback:
                feedback += f"Quality Review: {critic_specific_feedback}\n"
            else:
                feedback += f"Quality Review: {critic_feedback}\n"
        
        revision_prompt = REVISION_PROMPT.format(
            artifact=artifact,
            feedback=feedback
        )
        response = drafter_model.invoke([
            SystemMessage(content="You are revising a CBT protocol based on feedback."),
            HumanMessage(content=revision_prompt)
        ])
        new_revision_count = revision_count + 1
        status = f"Revision {new_revision_count} Complete"
    else:
        # Initial draft
        response = drafter_model.invoke([
            SystemMessage(content=INITIAL_PROMPT),
            *messages
        ])
        new_revision_count = 0
        status = "Initial Draft Complete"
    
    # Clear previous feedback after using it
    return {
        "artifact": response.content,
        "revision_count": new_revision_count,
        "status": status,
        "scratchpad": {}  # Clear scratchpad for fresh reviews
    }
