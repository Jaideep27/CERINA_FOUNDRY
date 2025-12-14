import os
from dotenv import load_dotenv

# Load env from the directory where this file exists
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import uuid
from typing import Dict, AsyncGenerator
from .graph import build_graph
from langchain_core.messages import HumanMessage


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store queues for SSE
# Key: thread_id, Value: asyncio.Queue
queues: Dict[str, asyncio.Queue] = {}

class StartRequest(BaseModel):
    query: str
    thread_id: str = None

class ApproveRequest(BaseModel):
    thread_id: str
    feedback: str = None

class ResumeRequest(BaseModel):
    thread_id: str

async def run_graph_and_stream(thread_id: str, input_data: dict, config: dict):
    """
    Runs the graph and pushes events to the SSE queue.
    """
    queue = queues.get(thread_id)
    if not queue:
        return # Should not happen if set up correctly

    try:
        graph = await build_graph()
        
        # Emit initial status
        await queue.put(json.dumps({"type": "status", "content": "🚀 Graph Started", "agent": "System"}))
        
        # Track agent visits for bidirectional detection
        agent_visit_count = {}
        current_agent = None
        output_buffer = []

        async for event in graph.astream_events(input_data, config, version="v1"):
            kind = event["event"]
            name = event.get("name", "")
            
            # Agent starts - announce it
            if kind == "on_chain_start" and name in ["Filter", "Drafter", "Safety", "Critic", "Interrupt", "Rejection"]:
                # If switching agents, flush previous buffer
                if current_agent and current_agent != name and output_buffer:
                    full_output = "".join(output_buffer)
                    await queue.put(json.dumps({
                        "type": "agent_output", 
                        "agent": current_agent,
                        "content": full_output[:500] + ("..." if len(full_output) > 500 else "")
                    }))
                    output_buffer = []
                
                # Track visit count
                agent_visit_count[name] = agent_visit_count.get(name, 0) + 1
                visit_num = agent_visit_count[name]
                
                # Determine if this is a bidirectional revisit
                is_bidirectional = visit_num > 1
                emoji = "🔄" if is_bidirectional else "🔍" if name == "Filter" else "📝" if name == "Drafter" else "🛡️" if name == "Safety" else "🎯" if name == "Critic" else "⏸️"
                
                visit_marker = f" (visit #{visit_num})" if is_bidirectional else ""
                
                current_agent = name
                await queue.put(json.dumps({
                    "type": "agent_start", 
                    "agent": name, 
                    "content": f"Executing...{visit_marker}",
                    "emoji": emoji,
                    "visit_count": visit_num,
                    "is_bidirectional": is_bidirectional
                }))
            
            # Agent ends - send complete output
            elif kind == "on_chain_end" and name in ["Filter", "Drafter", "Safety", "Critic"]:
                if output_buffer:
                    full_output = "".join(output_buffer)
                    await queue.put(json.dumps({
                        "type": "agent_output", 
                        "agent": name,
                        "content": full_output[:500] + ("..." if len(full_output) > 500 else "")
                    }))
                    output_buffer = []
                await queue.put(json.dumps({"type": "agent_end", "agent": name, "content": "Complete"}))
                
            # Collect tokens into buffer (don't send individually)
            elif kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    output_buffer.append(content)

        # Check final state to see if Interrupted or Done
        try:
            snapshot = await graph.aget_state(config)
            
            # Extract iteration counters
            filter_safety_iters = snapshot.values.get("filter_safety_iterations", 0)
            critic_drafter_iters = snapshot.values.get("critic_drafter_iterations", 0)
            critic_safety_iters = snapshot.values.get("critic_safety_iterations", 0)
            
            # Send bidirectional summary if any loops occurred
            if filter_safety_iters > 0 or critic_drafter_iters > 0 or critic_safety_iters > 0:
                loop_summary = "🔄 Bidirectional Loops: "
                loops = []
                if filter_safety_iters > 0:
                    loops.append(f"Filter↔Safety={filter_safety_iters}/2")
                if critic_drafter_iters > 0:
                    loops.append(f"Critic↔Drafter={critic_drafter_iters}/2")
                if critic_safety_iters > 0:
                    loops.append(f"Critic↔Safety={critic_safety_iters}/2")
                loop_summary += ", ".join(loops)
                
                await queue.put(json.dumps({
                    "type": "status",
                    "agent": "System",
                    "content": loop_summary
                }))
            
            if snapshot.next:
                # Technically paused/interrupted
                safe_state = {k: v for k, v in snapshot.values.items() if k != "messages"}
                await queue.put(json.dumps({"type": "control", "content": "Interrupted", "state": safe_state}))
            else:
                safe_state = {k: v for k, v in snapshot.values.items() if k != "messages"}
                await queue.put(json.dumps({"type": "control", "content": "Finished", "state": safe_state}))
        except Exception as state_err:
            # Fallback if async state fails - still send success
            await queue.put(json.dumps({"type": "control", "content": "Finished", "state": {}}))

    except Exception as e:
        await queue.put(json.dumps({"type": "error", "content": str(e)}))
    finally:
        # Signal end of stream logic (but SSE might stay open if we want to support multiple runs? 
        # For now, close execution side)
        pass 
        # We don't close the queue because the client might want to approve and continue on SAME stream?
        # Actually better to keep stream open.

@app.post("/start")
async def start_task(req: StartRequest, background_tasks: BackgroundTasks):
    thread_id = req.thread_id or str(uuid.uuid4())
    
    # Create queue if not exists
    if thread_id not in queues:
        queues[thread_id] = asyncio.Queue()
    
    config = {"configurable": {"thread_id": thread_id}}
    input_data = {"messages": [HumanMessage(content=req.query)]}
    
    background_tasks.add_task(run_graph_and_stream, thread_id, input_data, config)
    
    return {"thread_id": thread_id, "status": "Started"}

@app.post("/approve")
async def approve_task(req: ApproveRequest, background_tasks: BackgroundTasks):
    thread_id = req.thread_id
    if thread_id not in queues:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Get the final state to retrieve the artifact
    graph = await build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state = await graph.aget_state(config)
        artifact = state.values.get("artifact", "")
        
        # Save the approved protocol to file
        if artifact:
            from datetime import datetime
            import re
            
            # Create CBT_Downloaded directory if it doesn't exist
            save_dir = os.path.join(os.path.dirname(__file__), "..", "CBT_Downloaded")
            os.makedirs(save_dir, exist_ok=True)
            
            # Generate filename from protocol title or timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Try to extract title from markdown
            title_match = re.search(r'^#\s+CBT Protocol:\s*(.+)$', artifact, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
                # Sanitize filename
                safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:50]
                filename = f"{safe_title}_{timestamp}.md"
            else:
                filename = f"protocol_{timestamp}.md"
            
            # Save to file
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(artifact)
            
            print(f"✅ Protocol saved to: {filepath}")
    except Exception as e:
        print(f"⚠️ Error saving protocol: {e}")
    
    # Continue workflow
    input_data = None 
    background_tasks.add_task(run_graph_and_stream, thread_id, input_data, config)
    
    return {"status": "Approved", "saved_to": filepath if 'filepath' in locals() else None}

@app.post("/resume")
async def resume_task(req: ResumeRequest, background_tasks: BackgroundTasks):
    """Resume an interrupted workflow from its last checkpoint"""
    thread_id = req.thread_id
    
    # Check if thread exists and is resumable
    graph = await build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state = await graph.aget_state(config)
        if not state.next:
            return {"status": "Already completed", "thread_id": thread_id}
        
        # Resume with input_data=None (continues from checkpoint)
        if thread_id not in queues:
            queues[thread_id] = asyncio.Queue()
        
        background_tasks.add_task(run_graph_and_stream, thread_id, None, config)
        return {"thread_id": thread_id, "status": "Resumed"}
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Thread not found: {str(e)}")

@app.get("/check_thread/{thread_id}")
async def check_thread(thread_id: str):
    """Check thread status and get last state"""
    graph = await build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state = await graph.aget_state(config)
        return {
            "exists": True,
            "completed": not bool(state.next),
            "status": state.values.get("status", "Unknown"),
            "artifact": state.values.get("artifact", ""),
            "next_node": state.next[0] if state.next else None
        }
    except:
        return {"exists": False}

class ReviseRequest(BaseModel):
    thread_id: str
    feedback: str

@app.post("/revise")
async def revise_task(req: ReviseRequest, background_tasks: BackgroundTasks):
    """User requests revision with feedback - routes through Critic to Drafter"""
    thread_id = req.thread_id
    if thread_id not in queues:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Inject user feedback as Critic feedback and trigger revision
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update the graph state with user feedback
    graph = await build_graph()
    
    # Get current state and update scratchpad with user feedback
    try:
        current_state = await graph.aget_state(config)
        # Add user feedback to scratchpad as if Critic gave it
        new_scratchpad = current_state.values.get("scratchpad", {})
        new_scratchpad["UserFeedback"] = req.feedback
        new_scratchpad["Critic"] = f"User Feedback: {req.feedback}"
        new_scratchpad["CriticApproved"] = False
        new_scratchpad["CriticScore"] = 0.5  # Force revision
        
        # Update the state
        await graph.aupdate_state(config, {"scratchpad": new_scratchpad})
    except Exception as e:
        print(f"State update error: {e}")
    
    # Resume with the user feedback triggering revision
    input_data = None
    
    await queues[thread_id].put(json.dumps({
        "type": "status", 
        "agent": "User",
        "content": f"📝 User Feedback: {req.feedback}"
    }))
    
    background_tasks.add_task(run_graph_and_stream, thread_id, input_data, config)
    
    return {"status": "Revision Requested"}

@app.get("/stream/{thread_id}")
async def stream_task(thread_id: str):
    if thread_id not in queues:
        queues[thread_id] = asyncio.Queue()
        
    async def event_generator():
        while True:
            # Wait for data
            data = await queues[thread_id].get()
            yield f"data: {data}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
