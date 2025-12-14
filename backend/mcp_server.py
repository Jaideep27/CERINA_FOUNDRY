import os
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env from the directory where this file exists
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from mcp.server.fastmcp import FastMCP
from backend.graph import build_graph
from langchain_core.messages import HumanMessage
import asyncio
import uuid

# Initialize FastMCP Server
mcp = FastMCP("Cerina Foundry")

@mcp.tool()
async def create_protocol(query: str) -> str:
    """
    Creates a Cognitive Behavioral Therapy (CBT) protocol based on the user's query.
    This tool triggers the Cerina Foundry multi-agent system.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    input_data = {"messages": [HumanMessage(content=query)]}
    
    graph = await build_graph()
    
    # Run the graph until interrupt or end
    async for event in graph.astream(input_data, config, stream_mode="values"):
        # We just consume the stream to let it execute
        pass
        
    # Get final state
    state = graph.get_state(config)
    values = state.values
    
    status = values.get("status", "Unknown")
    artifact = values.get("artifact", "No artifact produced.")
    
    if status == "Waiting for Approval":
        return f"Protocol Drafted. Status: {status}.\nDraft:\n{artifact}\n\nPlease approve via dashboard or provide feedback."
    
    if status == "Rejected":
        return "The request was rejected by the filter."
        
    return f"Protocol Complete.\n\n{artifact}"

if __name__ == "__main__":
    mcp.run()
