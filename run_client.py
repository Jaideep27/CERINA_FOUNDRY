import asyncio
import uuid
import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Ensure backend can be imported
sys.path.append(os.path.dirname(__file__))

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))

from backend.graph import build_graph

async def create_protocol(query: str):
    print(f"--- Generating Protocol for: '{query}' ---")
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    input_data = {"messages": [HumanMessage(content=query)]}
    
    try:
        graph = await build_graph()
        
        print("\n" + "="*60)
        print("🚀 CERINA OS V1.0 // BIDIRECTIONAL AGENT EXECUTION")
        print("="*60 + "\n")
        
        step_count = 0
        agent_visits = {}  # Track how many times each agent is visited
        
        # Run the graph and track agent flow
        async for event in graph.astream(input_data, config, stream_mode="updates"):
            for node_name, values in event.items():
                step_count += 1
                
                # Track agent visits
                agent_visits[node_name] = agent_visits.get(node_name, 0) + 1
                visit_count = agent_visits[node_name]
                
                # Get iteration counters
                filter_safety = values.get("filter_safety_iterations", 0)
                critic_drafter = values.get("critic_drafter_iterations", 0)
                critic_safety = values.get("critic_safety_iterations", 0)
                
                # Determine if this is a bidirectional loop
                is_bidirectional = visit_count > 1
                arrow = "🔄" if is_bidirectional else "→"
                visit_marker = f" (visit #{visit_count})" if is_bidirectional else ""
                
                status = values.get("status", "Processing")
                print(f"{arrow} Step {step_count}: {node_name:12} {visit_marker}")
                print(f"   Status: {status}")
                
                # Show iteration counters if any are active
                if filter_safety > 0 or critic_drafter > 0 or critic_safety > 0:
                    print(f"   🔄 Iterations: ", end="")
                    counters = []
                    if filter_safety > 0:
                        counters.append(f"Filter↔Safety={filter_safety}/2")
                    if critic_drafter > 0:
                        counters.append(f"Critic↔Drafter={critic_drafter}/2")
                    if critic_safety > 0:
                        counters.append(f"Critic↔Safety={critic_safety}/2")
                    print(", ".join(counters))
                print()
            
        print("="*60)
        print(f"✅ Completed in {step_count} steps")
        
        # Get final state
        state = graph.get_state(config)
        values = state.values
        
        status = values.get("status", "Unknown")
        artifact = values.get("artifact", "No artifact produced.")
        
        # Show final iteration counts
        final_filter_safety = values.get("filter_safety_iterations", 0)
        final_critic_drafter = values.get("critic_drafter_iterations", 0)
        final_critic_safety = values.get("critic_safety_iterations", 0)
        
        if final_filter_safety > 0 or final_critic_drafter > 0 or final_critic_safety > 0:
            print("\n🔄 BIDIRECTIONAL LOOPS EXECUTED:")
            if final_filter_safety > 0:
                print(f"   • Filter ↔ Safety: {final_filter_safety}/2 iterations")
            if final_critic_drafter > 0:
                print(f"   • Critic ↔ Drafter: {final_critic_drafter}/2 iterations")
            if final_critic_safety > 0:
                print(f"   • Critic ↔ Safety: {final_critic_safety}/2 iterations")
        else:
            print("\nℹ️  No bidirectional loops triggered (agents approved on first pass)")
        
        print("\n" + "="*60)
        print(f"STATUS: {status}")
        print("="*60)
        print(artifact)
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your CBT topic (e.g., 'Sleep Anxiety'): ")
    
    asyncio.run(create_protocol(query))
