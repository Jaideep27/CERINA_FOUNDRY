from langgraph.checkpoint.memory import MemorySaver

# Global checkpointer instance
_checkpointer = None

async def get_checkpointer():
    """Get or create the async memory checkpointer."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer
