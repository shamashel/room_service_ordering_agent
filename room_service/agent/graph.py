from langgraph.graph import END, StateGraph
from langgraph.graph.message import uuid
from langgraph.graph.state import CompiledStateGraph
from room_service.agent.nodes import tool_calling_llm_node, tool_node, should_call_tool
from room_service.models.state import OrderState
from langgraph.checkpoint.memory import MemorySaver

def create_graph() -> tuple[str, CompiledStateGraph]:
  """Create the state graph for the room service agent.

  The graph follows this flow:
  1. LLM generates a response/action
  2. Check if tools need to be called
  3. If yes, call tools and loop back to LLM
  4. If no, end conversation
  """
  # Create graph with OrderState
  workflow = StateGraph(OrderState)

  # Add the tool execution node
  workflow.add_node("tools", tool_node)

  # Add the LLM node for actually generating responses
  workflow.add_node("tool_calling_llm", tool_calling_llm_node)

  # Conditional edges to figure out if tools need to be called
  workflow.add_conditional_edges(
    "tool_calling_llm",
    should_call_tool,
    {
      "tools": "tools",  # If tools needed, go to tools node
      END: END,          # If no tools needed, return response to user
    }
  )

  # Connect tools back to LLM to continue conversation
  workflow.add_edge("tools", "tool_calling_llm")

  # Set the entry point
  workflow.set_entry_point("tool_calling_llm")

  # Add memory so the LLM actually remembers what happened 2 seconds ago
  checkpointer = MemorySaver()

  graph = workflow.compile(checkpointer=checkpointer)
  
  # Initialize the state
  thread_id = str(uuid.uuid4())
  graph.update_state(
    config=graph.config if graph.config else { "configurable": { "thread_id": thread_id }},
    values={
      "messages": [],
      "validated_order": None,
      "validation_result": None,
      "sequential_error_count": 0
    }
  )

  return thread_id, graph
